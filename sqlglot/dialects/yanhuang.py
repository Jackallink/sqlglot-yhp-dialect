from __future__ import annotations

import typing as t
import warnings
from sqlglot import exp, transforms, tokens
from sqlglot.dialects.dialect import (
    NormalizationStrategy,
    concat_to_dpipe_sql,
    concat_ws_to_dpipe_sql,
    date_delta_sql,
    generatedasidentitycolumnconstraint_sql,
    json_extract_segments,
    no_tablesample_sql,
    rename_func,
    map_date_part,
)
from sqlglot.dialects.postgres import Postgres, _build_generate_series
from sqlglot.helper import seq_get
from sqlglot.tokens import TokenType
from sqlglot.parser import build_convert_timezone
from sqlglot.generator import UnsupportedError
from sqlglot.helper import logger

if t.TYPE_CHECKING:
    from sqlglot._typing import E


def _build_date_delta(expr_type: t.Type[E]) -> t.Callable[[t.List], E]:
    def _builder(args: t.List) -> E:
        # 炎凰SQL的DATE_ADD支持两种形式：
        # DATE_ADD(<time_unit>, <delta>) - 基于当前时间
        # DATE_ADD(<time_unit>, <delta>, <base_timestamp>) - 基于指定时间
        
        if len(args) == 2:
            # 两参数形式：DATE_ADD('day', 7) - 基于当前时间
            # 使用Anonymous表达式保持原始函数调用
            unit = seq_get(args, 0)
            delta = seq_get(args, 1)
            func_name = "DATE_ADD" if expr_type is exp.TsOrDsAdd else "DATE_DIFF"
            return exp.Anonymous(this=func_name, expressions=[unit, delta])
        elif len(args) == 3:
            # 三参数形式：DATE_ADD('day', 7, date_col) - 基于指定时间
            expr = expr_type(
                this=seq_get(args, 2),
                expression=seq_get(args, 1),
                unit=map_date_part(seq_get(args, 0)),
            )
            if expr_type is exp.TsOrDsAdd:
                expr.set("return_type", exp.DataType.build("TIMESTAMP"))
            return expr
        else:
            # 参数数量不正确，返回Anonymous表达式
            func_name = "DATE_ADD" if expr_type is exp.TsOrDsAdd else "DATE_DIFF"
            return exp.Anonymous(this=func_name, expressions=args)

    return _builder


def _create_current_timestamp_with_func(original_func):
    """创建带有原始函数名信息的CurrentTimestamp表达式"""
    expr = exp.CurrentTimestamp()
    expr.meta["original_func"] = original_func
    return expr


def _extract_to_date_part(args: t.List) -> exp.Anonymous:
    """将EXTRACT函数降级映射为DATE_PART函数
    
    EXTRACT(YEAR FROM date_col) -> DATE_PART('year', date_col)
    """
    if len(args) != 2:
        # 如果参数不正确，返回原始调用
        return exp.Anonymous(this="EXTRACT", expressions=args)
    
    # args[0] 是时间部分（如YEAR），args[1] 是源表达式（如date_col）
    time_part, source_expr = args
    
    # 转换时间部分为字符串字面量
    if isinstance(time_part, exp.Var):
        part_str = exp.Literal.string(time_part.this.lower())
    elif isinstance(time_part, (exp.Identifier, exp.Column)):
        part_str = exp.Literal.string(str(time_part).lower())
    else:
        part_str = time_part
        
    return exp.Anonymous(this="DATE_PART", expressions=[part_str, source_expr])


def _add_months_to_date_add(args: t.List) -> exp.Anonymous:
    """将ADD_MONTHS函数映射为DATE_ADD函数（修正：炎凰SQL支持DATE_ADD，不支持DATEADD）
    
    ADD_MONTHS(date_col, 3) -> DATE_ADD('m', 3, date_col)
    """
    if len(args) != 2:
        return exp.Anonymous(this="ADD_MONTHS", expressions=args)
    
    date_expr, months_expr = args
    
    # 创建DATE_ADD表达式：DATE_ADD('m', months, date)
    return exp.Anonymous(
        this="DATE_ADD", 
        expressions=[
            exp.Literal.string("m"),  # 炎凰SQL使用'm'表示月份
            months_expr,
            date_expr
        ]
    )


def _similarity_to_jaro_winkler(args: t.List) -> exp.Anonymous:
    """将SIMILARITY函数映射为JARO_WINKLER_SIMILARITY函数
    
    SIMILARITY(string1, string2) -> JARO_WINKLER_SIMILARITY(string1, string2)
    """
    return exp.Anonymous(this="JARO_WINKLER_SIMILARITY", expressions=args)


def _current_timestamp_to_now(args: t.List) -> exp.Anonymous:
    """将CURRENT_TIMESTAMP映射为NOW函数（保持原始函数元数据）
    
    CURRENT_TIMESTAMP -> NOW()
    """
    now_func = exp.Anonymous(this="NOW", expressions=args)
    # 保存原始函数名到meta
    now_func.meta["original_func"] = "CURRENT_TIMESTAMP"
    return now_func


def _current_time_to_strftime(args: t.List) -> exp.Anonymous:
    """将CURRENT_TIME映射为STRFTIME函数获取带时区的TIME值
    
    CURRENT_TIME -> STRFTIME(NOW(), '%H:%M:%S%z')
    """
    strftime_func = exp.Anonymous(
        this="STRFTIME", 
        expressions=[
            exp.Anonymous(this="NOW", expressions=[]),
            exp.Literal.string("%H:%M:%S%z")
        ]
    )
    # 保存原始函数名到meta
    strftime_func.meta["original_func"] = "CURRENT_TIME"
    return strftime_func


def _localtime_to_strftime(args: t.List) -> exp.Anonymous:
    """将LOCALTIME映射为STRFTIME函数获取不带时区的TIME值
    
    LOCALTIME -> STRFTIME(NOW(), '%H:%M:%S')
    """
    strftime_func = exp.Anonymous(
        this="STRFTIME", 
        expressions=[
            exp.Anonymous(this="NOW", expressions=[]),
            exp.Literal.string("%H:%M:%S")
        ]
    )
    # 保存原始函数名到meta
    strftime_func.meta["original_func"] = "LOCALTIME"
    return strftime_func


def _getdate_to_now(args: t.List) -> exp.Anonymous:
    """将GETDATE函数映射为NOW函数
    
    GETDATE() -> NOW()
    """
    now_func = exp.Anonymous(this="NOW", expressions=args)
    now_func.meta["original_func"] = "GETDATE"
    return now_func


def _time_to_str_mapping(args: t.List) -> exp.Anonymous:
    """将TimeToStr映射为STRFTIME函数
    
    TimeToStr(timestamp, format) -> STRFTIME(timestamp, format)
    """
    return exp.Anonymous(this="STRFTIME", expressions=args)


def _str_to_time_mapping(args: t.List) -> exp.Anonymous:
    """将StrToTime映射为STRPTIME函数
    
    StrToTime(string, format) -> STRPTIME(string, format)
    """
    return exp.Anonymous(this="STRPTIME", expressions=args)


def _dateadd_to_date_add(args: t.List) -> exp.Anonymous:
    """将DATEADD函数映射为DATE_ADD函数
    
    DATEADD(year, 1, date_col) -> DATE_ADD('y', 1, date_col)
    """
    if len(args) != 3:
        return exp.Anonymous(this="DATEADD", expressions=args)
    
    unit, delta, date_expr = args
    
    # 转换时间单位
    unit_mapping = {
        "year": "y",
        "month": "m", 
        "day": "d",
        "hour": "h",
        "minute": "min",
        "second": "s"
    }
    
    if isinstance(unit, exp.Var):
        unit_str = unit_mapping.get(unit.this.lower(), unit.this.lower())
    else:
        unit_str = str(unit).lower()
    
    return exp.Anonymous(
        this="DATE_ADD",
        expressions=[
            exp.Literal.string(unit_str),
            delta,
            date_expr
        ]
    )


def _datediff_to_date_diff(args: t.List) -> exp.Anonymous:
    """将DATEDIFF函数映射为DATE_DIFF函数
    
    DATEDIFF(year, date1, date2) -> DATE_DIFF('y', date1, date2)
    """
    if len(args) != 3:
        return exp.Anonymous(this="DATEDIFF", expressions=args)
    
    unit, date1, date2 = args
    
    # 转换时间单位
    unit_mapping = {
        "year": "y",
        "month": "m",
        "day": "d",
        "hour": "h", 
        "minute": "min",
        "second": "s"
    }
    
    if isinstance(unit, exp.Var):
        unit_str = unit_mapping.get(unit.this.lower(), unit.this.lower())
    else:
        unit_str = str(unit).lower()
    
    return exp.Anonymous(
        this="DATE_DIFF",
        expressions=[
            exp.Literal.string(unit_str),
            date1,
            date2
        ]
    )


def _unnest_to_flatten(args: t.List) -> exp.Anonymous:
    """将UNNEST函数降级映射为FLATTEN函数
    
    UNNEST(array) -> FLATTEN(array)
    """
    return exp.Anonymous(this="FLATTEN", expressions=args)


def _array_length_to_array_size(args: t.List) -> exp.Anonymous:
    """将ARRAY_LENGTH函数映射为ARRAY_SIZE函数
    
    ARRAY_LENGTH(array) -> ARRAY_SIZE(array)
    """
    return exp.Anonymous(this="ARRAY_SIZE", expressions=args)


def _strpos_to_position(args: t.List) -> exp.Anonymous:
    """将STRPOS函数映射为POSITION函数（参数顺序调整）
    
    STRPOS(string, substring) -> POSITION(substring, string)  
    """
    if len(args) != 2:
        return exp.Anonymous(this="STRPOS", expressions=args)
    
    string_expr, substring_expr = args
    
    # 交换参数顺序：POSITION(substring, string)
    return exp.Anonymous(
        this="POSITION", 
        expressions=[substring_expr, string_expr]
    )


def _encode_to_base64_encode(args: t.List) -> exp.Anonymous:
    """将ENCODE函数映射为BASE64_ENCODE函数
    
    ENCODE(data, 'base64') -> BASE64_ENCODE(data)
    """
    if len(args) >= 1:
        return exp.Anonymous(this="BASE64_ENCODE", expressions=[args[0]])
    return exp.Anonymous(this="ENCODE", expressions=args)


def _decode_to_base64_decode(args: t.List) -> exp.Anonymous:
    """将DECODE函数映射为BASE64_DECODE函数
    
    DECODE(data, 'base64') -> BASE64_DECODE(data)
    """
    if len(args) >= 1:
        return exp.Anonymous(this="BASE64_DECODE", expressions=[args[0]])
    return exp.Anonymous(this="DECODE", expressions=args)


def _to_hex_to_hex(args: t.List) -> exp.Anonymous:
    """将TO_HEX函数映射为HEX函数
    
    TO_HEX(number) -> HEX(number)
    """
    return exp.Anonymous(this="HEX", expressions=args)


def _md5_hash(args: t.List) -> exp.Anonymous:
    """将MD5函数映射为HASH_MD5函数
    
    MD5(string) -> HASH_MD5(string)
    """
    return exp.Anonymous(this="HASH_MD5", expressions=args)


def _sha1_hash(args: t.List) -> exp.Anonymous:
    """将SHA1函数映射为HASH_SHA1函数
    
    SHA1(string) -> HASH_SHA1(string)
    """
    return exp.Anonymous(this="HASH_SHA1", expressions=args)


def _sha256_hash(args: t.List) -> exp.Anonymous:
    """将SHA256函数映射为HASH_SHA256函数
    
    SHA256(string) -> HASH_SHA256(string)
    """
    return exp.Anonymous(this="HASH_SHA256", expressions=args)


def _regexp_replace_to_regex_replace(args: t.List) -> exp.Anonymous:
    """将REGEXP_REPLACE函数映射为REGEX_REPLACE函数
    
    REGEXP_REPLACE(string, pattern, replacement) -> REGEX_REPLACE(string, pattern, replacement)
    """
    return exp.Anonymous(this="REGEX_REPLACE", expressions=args)


def _regexp_like_to_regex_like(args: t.List) -> exp.Anonymous:
    """将REGEXP_LIKE函数映射为REGEX_LIKE函数
    
    REGEXP_LIKE(string, pattern) -> REGEX_LIKE(string, pattern)
    """
    return exp.Anonymous(this="REGEX_LIKE", expressions=args)


def _generate_uuid_to_uuid(args: t.List) -> exp.Anonymous:
    """将GENERATE_UUID函数映射为UUID函数
    
    GENERATE_UUID() -> UUID()
    """
    return exp.Anonymous(this="UUID", expressions=args)


def _cardinality_to_array_length(args: t.List) -> exp.Anonymous:
    """将CARDINALITY函数映射为ARRAY_LENGTH函数
    
    CARDINALITY(array) -> ARRAY_LENGTH(array)
    """
    return exp.Anonymous(this="ARRAY_LENGTH", expressions=args)


def _split_to_array_split(args: t.List) -> exp.Anonymous:
    """将STRING_SPLIT/SPLIT函数映射为ARRAY_SPLIT函数
    
    SPLIT(string, delimiter) -> ARRAY_SPLIT(string, delimiter)
    """
    return exp.Anonymous(this="ARRAY_SPLIT", expressions=args)


def _array_concat_to_array_cat(args: t.List) -> exp.Anonymous:
    """将ARRAY_CONCAT函数映射为ARRAY_CAT函数
    
    ARRAY_CONCAT(array1, array2) -> ARRAY_CAT(array1, array2)
    """
    return exp.Anonymous(this="ARRAY_CAT", expressions=args)

def _array_to_string_to_array_join(args: t.List) -> exp.Anonymous:
    """将ARRAY_TO_STRING函数映射为ARRAY_JOIN函数
    
    ARRAY_TO_STRING(array, separator) -> ARRAY_JOIN(array, separator)
    ARRAY_TO_STRING(array, separator, null_text) -> ARRAY_JOIN(array, separator)  # 炎凰SQL的ARRAY_JOIN不支持null_text参数
    """
    # 只取前两个参数，忽略可能的第三个null_text参数
    main_args = args[:2] if len(args) >= 2 else args
    return exp.Anonymous(this="ARRAY_JOIN", expressions=main_args)


def _to_timestamp_mapping(args: t.List) -> exp.StrToTime:
    """将TO_TIMESTAMP映射为StrToTime表达式以便后续转换
    
    TO_TIMESTAMP(string, format) -> StrToTime(string, format)
    """
    if len(args) >= 2:
        return exp.StrToTime(this=args[0], format=args[1])
    elif len(args) == 1:
        return exp.StrToTime(this=args[0])
    return exp.StrToTime()


def _to_char_mapping(args: t.List) -> exp.TimeToStr:
    """将TO_CHAR映射为TimeToStr表达式以便后续转换
    
    TO_CHAR(timestamp, format) -> TimeToStr(timestamp, format)
    """
    if len(args) >= 2:
        return exp.TimeToStr(this=args[0], format=args[1])
    elif len(args) == 1:
        return exp.TimeToStr(this=args[0])
    return exp.TimeToStr()


def _interval_to_date_add(args: t.List) -> exp.Anonymous:
    """将INTERVAL表达式映射为DATE_ADD函数（复杂映射）
    
    date + INTERVAL '1 month' -> DATE_ADD('m', 1, date)
    """
    # 这个函数需要在AST转换层面处理，暂时返回原函数
    return exp.Anonymous(this="INTERVAL", expressions=args)


def _age_function_mapping(args: t.List) -> exp.Anonymous:
    """AGE函数映射为DATE_DIFF
    
    AGE(date1, date2) -> DATE_DIFF('d', date2, date1)
    """
    if len(args) == 2:
        return exp.Anonymous(
            this="DATE_DIFF",
            expressions=[
                exp.Literal.string("d"),
                args[1],  # date2
                args[0]   # date1
            ]
        )
    return exp.Anonymous(this="AGE", expressions=args)


def _date_trunc_mapping(args: t.List) -> exp.Anonymous:
    """DATE_TRUNC函数保持不变（炎凰SQL原生支持）
    
    DATE_TRUNC(unit, timestamp) -> DATE_TRUNC(unit, timestamp)
    """
    return exp.Anonymous(this="DATE_TRUNC", expressions=args)


def _overlay_to_replace(args: t.List) -> exp.Anonymous:
    """将OVERLAY函数映射为字符串替换操作
    
    OVERLAY(string PLACING substring FROM position) -> 复杂字符串处理
    """
    # 简化处理，保持原函数名
    return exp.Anonymous(this="OVERLAY", expressions=args)


def _trim_function_mapping(args: t.List) -> exp.Anonymous:
    """标准化TRIM函数参数顺序
    
    TRIM(BOTH 'x' FROM string) -> TRIM(string, 'x')
    """
    return exp.Anonymous(this="TRIM", expressions=args)


def _translate_function_mapping(args: t.List) -> exp.Anonymous:
    """TRANSLATE函数保持不变（炎凰SQL原生支持）
    
    TRANSLATE(string, from_chars, to_chars) -> TRANSLATE(string, from_chars, to_chars)
    """
    return exp.Anonymous(this="TRANSLATE", expressions=args)


def _bool_and_to_min_case(args: t.List) -> exp.Case:
    """将BOOL_AND函数映射为MIN + CASE表达式
    
    BOOL_AND(expr) -> (MIN(CASE WHEN expr THEN 1 ELSE 0 END) = 1)
    
    炎凰数据不支持BOOL_AND，但可以通过复合映射实现相同语义
    """
    if len(args) != 1:
        return exp.Anonymous(this="BOOL_AND", expressions=args)
    
    # 构建 CASE WHEN expr THEN 1 ELSE 0 END
    case_expr = exp.Case(
        ifs=[exp.If(this=args[0], true=exp.Literal.number("1"))],
        default=exp.Literal.number("0")
    )
    
    # 构建 MIN(CASE ...) = 1 的表达式
    min_func = exp.Anonymous(this="MIN", expressions=[case_expr])
    return exp.EQ(this=min_func, expression=exp.Literal.number("1"))


def _bool_or_to_max_case(args: t.List) -> exp.Case:
    """将BOOL_OR函数映射为MAX + CASE表达式
    
    BOOL_OR(expr) -> (MAX(CASE WHEN expr THEN 1 ELSE 0 END) = 1)
    
    炎凰数据不支持BOOL_OR，但可以通过复合映射实现相同语义
    """
    if len(args) != 1:
        return exp.Anonymous(this="BOOL_OR", expressions=args)
    
    # 构建 CASE WHEN expr THEN 1 ELSE 0 END
    case_expr = exp.Case(
        ifs=[exp.If(this=args[0], true=exp.Literal.number("1"))],
        default=exp.Literal.number("0")
    )
    
    # 构建 MAX(CASE ...) = 1 的表达式
    max_func = exp.Anonymous(this="MAX", expressions=[case_expr])
    return exp.EQ(this=max_func, expression=exp.Literal.number("1"))


def _percent_rank_to_row_number(args: t.List) -> exp.Div:
    """将PERCENT_RANK窗口函数映射为ROW_NUMBER + COUNT的复合表达式
    
    PERCENT_RANK() OVER (...) -> (ROW_NUMBER() OVER (...) - 1) / (COUNT(*) OVER (...) - 1)
    
    炎凰数据不支持PERCENT_RANK，但可以通过复合映射实现相同语义
    返回除法表达式，窗口子句将在上层处理时自动应用
    """
    # 构建 ROW_NUMBER() - 1，用括号包围确保优先级
    row_number_func = exp.Anonymous(this="ROW_NUMBER", expressions=[])
    row_number_minus_1 = exp.Paren(
        this=exp.Sub(
            this=row_number_func,
            expression=exp.Literal.number("1")
        )
    )
    
    # 构建 COUNT(*) - 1，用括号包围确保优先级  
    count_func = exp.Anonymous(this="COUNT", expressions=[exp.Star()])
    count_minus_1 = exp.Paren(
        this=exp.Sub(
            this=count_func,
            expression=exp.Literal.number("1")
        )
    )
    
    # 构建除法表达式: (ROW_NUMBER() - 1) / (COUNT(*) - 1)
    return exp.Div(
        this=row_number_minus_1,
        expression=count_minus_1
    )


# =============================================================================
# 高优先级虚继承函数映射（第七批优化）
# =============================================================================

def _time_to_unix_mapping(args: t.List) -> exp.Anonymous:
    """将TimeToUnix映射为DATE_PART('epoch', timestamp)"""
    if len(args) >= 1:
        return exp.Anonymous(
            this="DATE_PART",
            expressions=[
                exp.Literal.string("epoch"),
                args[0]
            ]
        )
    return exp.Anonymous(this="DATE_PART", expressions=[exp.Literal.string("epoch"), exp.Anonymous(this="NOW")])

def _str_position_mapping(args: t.List) -> exp.Anonymous:
    """将StrPosition映射为POSITION函数（修正参数顺序）"""
    if len(args) >= 2:
        # STRPOS(string, substring) -> POSITION(substring, string)
        # 调整参数顺序：第一个参数是string，第二个是substring
        string_expr = args[0]
        substring_expr = args[1]
        return exp.Anonymous(
            this="POSITION",
            expressions=[substring_expr, string_expr]  # substring, string
        )
    return exp.Anonymous(this="POSITION", expressions=args)

def _count_if_to_sum_case(args: t.List) -> exp.Sum:
    """将CountIf映射为SUM(CASE WHEN condition THEN 1 ELSE 0 END)"""
    if len(args) >= 1:
        condition = args[0]
        case_expr = exp.Case(
            ifs=[
                exp.If(
                    this=condition,
                    true=exp.Literal.number("1")
                )
            ],
            default=exp.Literal.number("0")
        )
        return exp.Sum(this=case_expr)
    return exp.Sum(this=exp.Literal.number("0"))

def _rand_to_random(args: t.List) -> exp.Anonymous:
    """将Rand映射为RANDOM函数"""
    # PostgreSQL的RANDOM()函数在炎凰SQL中也支持
    return exp.Anonymous(this="RANDOM", expressions=args)

def _unicode_to_ascii(args: t.List) -> exp.Anonymous:
    """将Unicode映射为ASCII函数"""
    # PostgreSQL的ASCII函数在炎凰SQL中也支持
    return exp.Anonymous(this="ASCII", expressions=args)

def _timestamp_trunc_mapping(args: t.List) -> exp.Anonymous:
    """将TimestampTrunc映射为DATE_TRUNC函数"""
    if len(args) >= 2:
        # PostgreSQL: DATE_TRUNC(field, source [, time_zone])
        # 炎凰SQL: DATE_TRUNC(field, source)
        field = args[0]
        source = args[1]
        
        # 如果有时区参数，暂时忽略（炎凰SQL可能不支持时区参数）
        return exp.Anonymous(
            this="DATE_TRUNC",
            expressions=[field, source]
        )
    return exp.Anonymous(this="DATE_TRUNC", expressions=args)

def _date_sub_mapping(args: t.List) -> exp.Anonymous:
    """将DateSub映射为DATE_ADD的负数形式"""
    if len(args) >= 3:
        # DateSub(date, interval, unit) -> DATE_ADD(unit, -interval, date)
        date_expr = args[0]
        interval_expr = args[1]
        unit_expr = args[2]
        
        # 创建负数间隔
        negative_interval = exp.Neg(this=interval_expr)
        
        return exp.Anonymous(
            this="DATE_ADD",
            expressions=[unit_expr, negative_interval, date_expr]
        )
    elif len(args) >= 2:
        # 简化形式：DateSub(date, interval) -> DATE_ADD('day', -interval, date)
        date_expr = args[0]
        interval_expr = args[1]
        
        negative_interval = exp.Neg(this=interval_expr)
        
        return exp.Anonymous(
            this="DATE_ADD",
            expressions=[exp.Literal.string("day"), negative_interval, date_expr]
        )
    return exp.Anonymous(this="DATE_ADD", expressions=args)

def _uuid_to_uuid_func(args: t.List) -> exp.Anonymous:
    """将Uuid映射为UUID函数"""
    # PostgreSQL的GEN_RANDOM_UUID()在炎凰SQL中映射为UUID()
    return exp.Anonymous(this="UUID", expressions=args)

def _current_user_mapping(args: t.List) -> exp.Anonymous:
    """将CurrentUser映射为USER函数"""
    # PostgreSQL的CURRENT_USER在炎凰SQL中映射为USER()
    return exp.Anonymous(this="USER", expressions=args)

def _unsupported_function_warning(func_name: str, func_type: str, args: t.List) -> exp.Anonymous:
    """为不支持的函数生成告警并返回原函数调用
    
    Args:
        func_name: 函数名
        func_type: 函数类型描述
        args: 函数参数
    
    Returns:
        原函数调用的Anonymous表达式，但会在运行时产生告警
    """
    import warnings
    
    # 发出警告
    warnings.warn(
        f"炎凰数据不支持{func_type} {func_name}。此函数调用可能在运行时失败。",
        UserWarning,
        stacklevel=3
    )
    
    # 返回原函数调用，让运行时处理错误
    return exp.Anonymous(this=func_name, expressions=args)


def _make_time_mapping(args: t.List) -> exp.Anonymous:
    """将MAKE_TIME映射为STRPTIME + CONCAT组合
    
    MAKE_TIME(hour, minute, second) -> STRPTIME(CONCAT(LPAD(CAST(hour AS STRING), 2, '0'), ':', LPAD(CAST(minute AS STRING), 2, '0'), ':', LPAD(CAST(second AS STRING), 2, '0')), '%H:%M:%S')
    """
    if len(args) != 3:
        return exp.Anonymous(this="MAKE_TIME", expressions=args)
    
    hour, minute, second = args
    
    # 构建时间字符串：HH:MM:SS
    hour_str = exp.Anonymous(
        this="LPAD",
        expressions=[
            exp.Cast(this=hour, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    minute_str = exp.Anonymous(
        this="LPAD", 
        expressions=[
            exp.Cast(this=minute, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    second_str = exp.Anonymous(
        this="LPAD",
        expressions=[
            exp.Cast(this=second, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    # 拼接时间字符串
    time_string = exp.Anonymous(
        this="CONCAT",
        expressions=[
            hour_str,
            exp.Literal.string(":"),
            minute_str,
            exp.Literal.string(":"),
            second_str
        ]
    )
    
    # 使用STRPTIME解析
    return exp.Anonymous(
        this="STRPTIME",
        expressions=[time_string, exp.Literal.string("%H:%M:%S")]
    )


def _str_to_date_mapping(args: t.List) -> exp.Anonymous:
    """将STR_TO_DATE映射为CAST(STRPTIME(...) AS DATE)
    
    STR_TO_DATE(string, format) -> CAST(STRPTIME(string, format) AS DATE)
    """
    if len(args) != 2:
        return exp.Anonymous(this="STR_TO_DATE", expressions=args)
    
    string_expr, format_expr = args
    
    # 使用STRPTIME解析，然后CAST为DATE
    strptime_expr = exp.Anonymous(
        this="STRPTIME",
        expressions=[string_expr, format_expr]
    )
    
    return exp.Cast(this=strptime_expr, to=exp.DataType.build("DATE"))


def _str_to_time_mapping_fixed(args: t.List) -> exp.Anonymous:
    """将STR_TO_TIME映射为CAST(STRPTIME(...) AS TIME)
    
    STR_TO_TIME(string, format) -> CAST(STRPTIME(string, format) AS TIME)
    """
    if len(args) != 2:
        return exp.Anonymous(this="STR_TO_TIME", expressions=args)
    
    string_expr, format_expr = args
    
    # 使用STRPTIME解析，然后CAST为TIME
    strptime_expr = exp.Anonymous(
        this="STRPTIME",
        expressions=[string_expr, format_expr]
    )
    
    return exp.Cast(this=strptime_expr, to=exp.DataType.build("TIME"))


def _make_timestamp_mapping(args: t.List) -> exp.Anonymous:
    """将MAKE_TIMESTAMP映射为STRPTIME + CONCAT组合
    
    MAKE_TIMESTAMP(year, month, day, hour, minute, second) -> STRPTIME(CONCAT(...), '%Y-%m-%d %H:%M:%S')
    """
    if len(args) != 6:
        return exp.Anonymous(this="MAKE_TIMESTAMP", expressions=args)
    
    year, month, day, hour, minute, second = args
    
    # 构建日期时间字符串：YYYY-MM-DD HH:MM:SS
    year_str = exp.Anonymous(
        this="LPAD",
        expressions=[
            exp.Cast(this=year, to=exp.DataType.build("STRING")),
            exp.Literal.number("4"),
            exp.Literal.string("0")
        ]
    )
    
    month_str = exp.Anonymous(
        this="LPAD",
        expressions=[
            exp.Cast(this=month, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    day_str = exp.Anonymous(
        this="LPAD",
        expressions=[
            exp.Cast(this=day, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    hour_str = exp.Anonymous(
        this="LPAD",
        expressions=[
            exp.Cast(this=hour, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    minute_str = exp.Anonymous(
        this="LPAD", 
        expressions=[
            exp.Cast(this=minute, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    second_str = exp.Anonymous(
        this="LPAD",
        expressions=[
            exp.Cast(this=second, to=exp.DataType.build("STRING")),
            exp.Literal.number("2"),
            exp.Literal.string("0")
        ]
    )
    
    # 拼接日期时间字符串
    datetime_string = exp.Anonymous(
        this="CONCAT",
        expressions=[
            year_str,
            exp.Literal.string("-"),
            month_str,
            exp.Literal.string("-"),
            day_str,
            exp.Literal.string(" "),
            hour_str,
            exp.Literal.string(":"),
            minute_str,
            exp.Literal.string(":"),
            second_str
        ]
    )
    
    # 使用STRPTIME解析
    return exp.Anonymous(
        this="STRPTIME",
        expressions=[datetime_string, exp.Literal.string("%Y-%m-%d %H:%M:%S")]
    )


def _trim_to_ltrim_rtrim(args: t.List) -> exp.Anonymous:
    """将TRIM映射为LTRIM(RTRIM(...))组合
    
    TRIM(string) -> LTRIM(RTRIM(string))
    TRIM(BOTH chars FROM string) -> LTRIM(RTRIM(string, chars), chars)
    TRIM(LEADING chars FROM string) -> LTRIM(string, chars)
    TRIM(TRAILING chars FROM string) -> RTRIM(string, chars)
    """
    if len(args) == 0:
        return exp.Anonymous(this="LTRIM", expressions=[exp.Literal.string("")])
    
    if len(args) == 1:
        # 简单的TRIM(string)情况
        string_expr = args[0]
        # 使用LTRIM(RTRIM(string))组合
        rtrim_expr = exp.Anonymous(this="RTRIM", expressions=[string_expr])
        return exp.Anonymous(this="LTRIM", expressions=[rtrim_expr])
    
    # 复杂的TRIM情况，暂时返回原始实现
    # 实际应用中可能需要更复杂的解析
    return exp.Anonymous(this="LTRIM", expressions=[exp.Anonymous(this="RTRIM", expressions=args)])


def _btrim_to_ltrim_rtrim(args: t.List) -> exp.Anonymous:
    """将BTRIM映射为LTRIM(RTRIM(...))组合
    
    BTRIM(string) -> LTRIM(RTRIM(string))
    BTRIM(string, chars) -> LTRIM(RTRIM(string, chars), chars)
    """
    if len(args) == 0:
        return exp.Anonymous(this="LTRIM", expressions=[exp.Literal.string("")])
    
    if len(args) == 1:
        # 简单的BTRIM(string)情况
        string_expr = args[0]
        # 使用LTRIM(RTRIM(string))组合
        rtrim_expr = exp.Anonymous(this="RTRIM", expressions=[string_expr])
        return exp.Anonymous(this="LTRIM", expressions=[rtrim_expr])
    
    if len(args) == 2:
        # BTRIM(string, chars)情况
        string_expr, chars_expr = args
        # 使用LTRIM(RTRIM(string, chars), chars)组合
        rtrim_expr = exp.Anonymous(this="RTRIM", expressions=[string_expr, chars_expr])
        return exp.Anonymous(this="LTRIM", expressions=[rtrim_expr, chars_expr])
    
    # 复杂情况，返回原始实现
    return exp.Anonymous(this="LTRIM", expressions=[exp.Anonymous(this="RTRIM", expressions=args)])


def _percentile_cont_to_quantile(args: t.List) -> exp.Anonymous:
    """将PERCENTILE_CONT映射为QUANTILE_T_DIGEST
    
    PERCENTILE_CONT(0.5) -> APPROX_MEDIAN (特殊情况优化)
    PERCENTILE_CONT(fraction) -> QUANTILE_T_DIGEST
    """
    if len(args) < 1:
        # 参数不足，返回默认
        return exp.Anonymous(this="QUANTILE_T_DIGEST", expressions=[exp.Literal.string("NULL"), exp.Literal.number("0.5")])
    
    fraction = args[0]
    
    # 检查是否为0.5的特殊情况（中位数）
    if (isinstance(fraction, exp.Literal) and 
        fraction.this == "0.5"):
        # 返回占位符，在TRANSFORMS中进一步处理为APPROX_MEDIAN
        return exp.Anonymous(this="APPROX_MEDIAN_PLACEHOLDER", expressions=args)
    
    # 返回占位符，在TRANSFORMS中进一步处理
    return exp.Anonymous(this="QUANTILE_T_DIGEST_PLACEHOLDER", expressions=args)


def _percentile_disc_to_quantile(args: t.List) -> exp.Anonymous:
    """将PERCENTILE_DISC映射为QUANTILE_T_DIGEST
    
    PERCENTILE_DISC(fraction) -> QUANTILE_T_DIGEST
    """
    if len(args) < 1:
        # 参数不足，返回默认
        return exp.Anonymous(this="QUANTILE_T_DIGEST", expressions=[exp.Literal.string("NULL"), exp.Literal.number("0.5")])
    
    # 返回占位符，在TRANSFORMS中进一步处理
    return exp.Anonymous(this="QUANTILE_T_DIGEST_PLACEHOLDER", expressions=args)


class Yanhuang(Postgres):
    """
    炎凰SQL方言，继承自Postgres。
    只对创新/差异点做patch，主流程全部复用PG。
    """

    # https://docs.aws.amazon.com/redshift/latest/dg/r_names.html
    NORMALIZATION_STRATEGY = NormalizationStrategy.UPPERCASE

    SUPPORTS_USER_DEFINED_TYPES = False
    INDEX_OFFSET = 0
    COPY_PARAMS_ARE_CSV = False
    HEX_LOWERCASE = True
    HAS_DISTINCT_ARRAY_CONSTRUCTORS = True
    VALUES_AS_TABLE = True  # 炎凰数据原生支持VALUES语法

    # ref: https://docs.aws.amazon.com/redshift/latest/dg/r_FORMAT_strings.html
    TIME_FORMAT = "'YYYY-MM-DD HH24:MI:SS'"
    TIME_MAPPING = {
        # 先定义长模式，确保优先匹配
        "Day": "%A",     # 完整星期名
        "Month": "%B",   # 完整月份名
        "Mon": "%b",     # 简写月份名
        "DY": "%a",      # 简写星期名
        # 然后继承PostgreSQL的映射
        **Postgres.TIME_MAPPING, 
        "MON": "%b", 
        "HH24": "%H", 
        "HH": "%I",
        # 保持原有的D映射
        "D": "%w",       # 星期数字(0-6)
    }
    
    # BYTE_START和BYTE_END由metaclass根据tokenizer的BYTE_STRINGS自动设置

    class Parser(Postgres.Parser):
        FUNC_TOKENS = {
            *Postgres.Parser.FUNC_TOKENS,
            TokenType.DATABASE,  # 声明DATABASE可以作为函数使用
        }
        
        FUNCTIONS = {
            **Postgres.Parser.FUNCTIONS,
            # ===== 映射转换函数（35个，需要语法调整） =====
            
            # 1. 时间函数映射
            "EXTRACT": _extract_to_date_part,  # EXTRACT降级映射为DATE_PART
            "ADD_MONTHS": _add_months_to_date_add,  # ADD_MONTHS映射为DATE_ADD
            "ADDMONTHS": _add_months_to_date_add,  # ADDMONTHS别名也映射为DATE_ADD
            "CURRENT_TIMESTAMP": _current_timestamp_to_now,  # CURRENT_TIMESTAMP映射为NOW（保持元数据）
            "CURRENT_TIME": _current_time_to_strftime,  # CURRENT_TIME映射为STRFTIME获取带时区TIME值
            "LOCALTIME": _localtime_to_strftime,  # LOCALTIME映射为STRFTIME获取不带时区TIME值
            "GETDATE": _getdate_to_now,  # GETDATE映射为NOW
            "DATEADD": _dateadd_to_date_add,  # DATEADD映射为DATE_ADD
            "DATEDIFF": _datediff_to_date_diff,  # DATEDIFF映射为DATE_DIFF
            "AGE": _age_function_mapping,  # AGE映射为DATE_DIFF
            "DATE_TRUNC": _date_trunc_mapping,  # DATE_TRUNC保持不变
            "TO_TIMESTAMP": _to_timestamp_mapping,  # TO_TIMESTAMP保持不变
            "TO_CHAR": _to_char_mapping,  # TO_CHAR保持不变
            
            # 2. 字符串相似度函数映射
            "SIMILARITY": _similarity_to_jaro_winkler,  # SIMILARITY映射为JARO_WINKLER_SIMILARITY
            
            # 3. 数组函数映射  
            # UNNEST在TABLE_FUNCTIONS中定义，这里不重复定义避免冲突
            # "UNNEST": _unnest_to_flatten,  # UNNEST降级映射为FLATTEN（表函数）
            # "ARRAY_LENGTH": _array_length_to_array_size,  # 移除：炎凰数据原生支持ARRAY_LENGTH函数
            "CARDINALITY": _cardinality_to_array_length,  # CARDINALITY映射为ARRAY_LENGTH  
            "ARRAY_CONCAT": _array_concat_to_array_cat,  # ARRAY_CONCAT映射为ARRAY_CAT
            "ARRAY_TO_STRING": _array_to_string_to_array_join,  # ARRAY_TO_STRING映射为ARRAY_JOIN
            "SPLIT": _split_to_array_split,  # SPLIT映射为ARRAY_SPLIT
            "STRING_SPLIT": _split_to_array_split,  # STRING_SPLIT映射为ARRAY_SPLIT
            
            # 4. 字符串函数映射（参数顺序调整）
            "STRPOS": _strpos_to_position,  # STRPOS映射为POSITION（参数顺序调整）
            # TRIM函数通过exp.Trim在TRANSFORMS中处理，不在FUNCTIONS中映射
            "TRANSLATE": _translate_function_mapping,  # TRANSLATE保持不变
            "OVERLAY": _overlay_to_replace,  # OVERLAY映射处理
            
            # 5. 编码/解码函数映射
            "ENCODE": _encode_to_base64_encode,  # ENCODE映射为BASE64_ENCODE
            "DECODE": _decode_to_base64_decode,  # DECODE映射为BASE64_DECODE
            "TO_HEX": _to_hex_to_hex,  # TO_HEX映射为HEX
            
            # 6. 哈希函数映射
            "MD5": _md5_hash,  # MD5映射为HASH_MD5
            "SHA1": _sha1_hash,  # SHA1映射为HASH_SHA1  
            "SHA256": _sha256_hash,  # SHA256映射为HASH_SHA256
            
            # 7. 正则表达式函数映射
            "REGEXP_REPLACE": _regexp_replace_to_regex_replace,  # REGEXP_REPLACE映射为REGEX_REPLACE
            "REGEXP_LIKE": _regexp_like_to_regex_like,  # REGEXP_LIKE映射为REGEX_LIKE
            
            # 8. UUID函数映射
            "GENERATE_UUID": _generate_uuid_to_uuid,  # GENERATE_UUID映射为UUID
            
            # 9. 错误继承函数的复合映射（炎凰数据不支持但PostgreSQL支持的函数）
            # BOOL_AND和BOOL_OR已移至TRANSFORMS中处理
            # PERCENT_RANK已移至TRANSFORMS中处理
            
            # 10. 高优先级虚继承函数映射（第七批优化）
            "TIME_TO_UNIX": _time_to_unix_mapping,  # TimeToUnix映射为DATE_PART('epoch', timestamp)
            "STRPOS": _str_position_mapping,  # StrPosition映射为POSITION函数
            "COUNT_IF": _count_if_to_sum_case,  # CountIf映射为SUM(CASE WHEN ... THEN 1 ELSE 0 END)
            "RAND": _rand_to_random,  # Rand映射为RANDOM函数
            "UNICODE": _unicode_to_ascii,  # Unicode映射为ASCII函数
            "TIMESTAMP_TRUNC": _timestamp_trunc_mapping,  # TimestampTrunc映射为DATE_TRUNC
            "DATE_SUB": _date_sub_mapping,  # DateSub映射为DATE_ADD的负数形式
            "UUID_GENERATE": _uuid_to_uuid_func,  # Uuid映射为UUID函数
            "CURRENT_USER": _current_user_mapping,  # CurrentUser映射为USER函数
            
            # 11. 百分位数函数映射（第十一批优化）
            "PERCENTILE_CONT": _percentile_cont_to_quantile,  # PERCENTILE_CONT映射为QUANTILE_T_DIGEST或APPROX_MEDIAN
            "PERCENTILE_DISC": _percentile_disc_to_quantile,  # PERCENTILE_DISC映射为QUANTILE_T_DIGEST
            
            # 12. 时间构造函数映射（第十二批优化）
            "MAKE_TIME": _make_time_mapping,  # MAKE_TIME映射为STRPTIME + CONCAT组合
            "MAKE_TIMESTAMP": _make_timestamp_mapping,  # MAKE_TIMESTAMP映射为STRPTIME + CONCAT组合
            "STR_TO_DATE": _str_to_date_mapping,  # STR_TO_DATE映射为CAST(STRPTIME(...) AS DATE)
            "STR_TO_TIME": _str_to_time_mapping_fixed,  # STR_TO_TIME映射为CAST(STRPTIME(...) AS TIME)
            
            # 13. 类型转换函数映射（虚拟继承函数）
            "SAFE_CAST": lambda args: exp.Anonymous(this="SAFE_CAST", expressions=args),
            "TRY_CAST": lambda args: exp.Anonymous(this="TRY_CAST", expressions=args),
            
            # ===== 基于炎凰数据官方文档验证的新增函数映射 =====
            
            # 14. 时间函数增量映射（需要映射的PostgreSQL函数）
            "CLOCK_TIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 映射为NOW()
            "STATEMENT_TIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 映射为NOW()
            "TRANSACTION_TIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 映射为NOW()
            "TIMEOFDAY": lambda args: exp.Anonymous(this="STRFTIME", expressions=[exp.Anonymous(this="NOW", expressions=[]), exp.Literal.string("%a %b %d %H:%M:%S.%f %Y %Z")]),  # 映射为STRFTIME(NOW(), format)
            "LOCALTIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 映射为NOW()
            
            # 15. 字符串函数增量映射（需要映射的PostgreSQL函数）
            # 注意：炎凰数据不支持QUOTE_IDENT等函数，需要告警处理
            # "QUOTE_IDENT": lambda args: exp.Anonymous(this="QUOTE", expressions=args),  # 移除：炎凰数据不支持标识符引用函数
            # "QUOTE_LITERAL": lambda args: exp.Anonymous(this="QUOTE", expressions=args),  # 移除：炎凰数据不支持字面量引用函数
            # "QUOTE_NULLABLE": lambda args: exp.Anonymous(this="QUOTE", expressions=args),  # 移除：炎凰数据不支持可空值引用函数
            
            # 16. 数组函数增量映射（需要映射的PostgreSQL函数）
            # 注意：炎凰数据只支持一维数组，不需要维度函数
            # "ARRAY_DIMS": lambda args: exp.Anonymous(this="ARRAY_SIZE", expressions=args),  # 移除：炎凰数据不支持数组维度函数
            # "ARRAY_UPPER": 移除错误映射，炎凰数据不支持ARRAY_UPPER函数
            # ARRAY_UPPER: 移除错误映射，炎凰数据不支持ARRAY_UPPER函数，已在告警函数中处理
            "ARRAY_NDIMS": lambda args: exp.Literal.number("1"),  # 炎凰数据只支持一维数组
            # "ARRAY_APPEND": 移除错误映射，炎凰数据原生支持ARRAY_APPEND函数
            # "ARRAY_PREPEND": 移除错误映射，炎凰数据原生支持ARRAY_PREPEND函数
            "ARRAY_REMOVE": lambda args: exp.Anonymous(this="ARRAY_FILTER", expressions=args),  # 映射为ARRAY_FILTER的否定形式
            "ARRAY_REPLACE": lambda args: exp.Anonymous(this="ARRAY_REPLACE", expressions=args),  # 假设炎凰数据支持ARRAY_REPLACE
            
            # ===== 不支持函数的映射/降级/告警处理 =====
            
            # 18. 系统信息函数（不支持，提供告警）
            "PG_BACKEND_PID": lambda args: _unsupported_function_warning("PG_BACKEND_PID", "PostgreSQL系统函数", args),
            "PG_CANCEL_BACKEND": lambda args: _unsupported_function_warning("PG_CANCEL_BACKEND", "PostgreSQL系统函数", args),
            "VERSION": lambda args: _unsupported_function_warning("VERSION", "系统版本函数", args),
            "CURRENT_DATABASE": lambda args: _unsupported_function_warning("CURRENT_DATABASE", "当前数据库函数", args),
            "CURRENT_SCHEMA": lambda args: _unsupported_function_warning("CURRENT_SCHEMA", "当前模式函数", args),
            
            # 19. 网络地址函数（不支持，提供告警）
            "INET": lambda args: _unsupported_function_warning("INET", "网络地址函数", args),
            "ABBREV": lambda args: _unsupported_function_warning("ABBREV", "地址缩写函数", args),
            "BROADCAST": lambda args: _unsupported_function_warning("BROADCAST", "广播地址函数", args),
            "FAMILY": lambda args: _unsupported_function_warning("FAMILY", "地址族函数", args),
            "HOST": lambda args: _unsupported_function_warning("HOST", "主机地址函数", args),
            "HOSTMASK": lambda args: _unsupported_function_warning("HOSTMASK", "主机掩码函数", args),
            "MASKLEN": lambda args: _unsupported_function_warning("MASKLEN", "掩码长度函数", args),
            "NETMASK": lambda args: _unsupported_function_warning("NETMASK", "网络掩码函数", args),
            "NETWORK": lambda args: _unsupported_function_warning("NETWORK", "网络地址函数", args),
            "SET_MASKLEN": lambda args: _unsupported_function_warning("SET_MASKLEN", "设置掩码长度函数", args),
            
            # 20. 全文搜索函数（不支持，提供告警）
            "TO_TSVECTOR": lambda args: _unsupported_function_warning("TO_TSVECTOR", "全文搜索函数", args),
            "TO_TSQUERY": lambda args: _unsupported_function_warning("TO_TSQUERY", "全文搜索函数", args),
            "PLAINTO_TSQUERY": lambda args: _unsupported_function_warning("PLAINTO_TSQUERY", "全文搜索函数", args),
            "PHRASETO_TSQUERY": lambda args: _unsupported_function_warning("PHRASETO_TSQUERY", "全文搜索函数", args),
            "WEBSEARCH_TO_TSQUERY": lambda args: _unsupported_function_warning("WEBSEARCH_TO_TSQUERY", "全文搜索函数", args),
            "TS_RANK": lambda args: _unsupported_function_warning("TS_RANK", "全文搜索排名函数", args),
            "TS_RANK_CD": lambda args: _unsupported_function_warning("TS_RANK_CD", "全文搜索排名函数", args),
            "TS_HEADLINE": lambda args: _unsupported_function_warning("TS_HEADLINE", "全文搜索标题函数", args),
            "TS_REWRITE": lambda args: _unsupported_function_warning("TS_REWRITE", "全文搜索重写函数", args),
            "TSQUERY_PHRASE": lambda args: _unsupported_function_warning("TSQUERY_PHRASE", "全文搜索查询函数", args),
            "TSVECTOR_TO_ARRAY": lambda args: _unsupported_function_warning("TSVECTOR_TO_ARRAY", "全文搜索函数", args),
            
            # 21. 几何函数（不支持，提供告警）
            "POINT": lambda args: _unsupported_function_warning("POINT", "几何函数", args),
            "LINE": lambda args: _unsupported_function_warning("LINE", "几何函数", args),
            "LSEG": lambda args: _unsupported_function_warning("LSEG", "几何函数", args),
            "BOX": lambda args: _unsupported_function_warning("BOX", "几何函数", args),
            "PATH": lambda args: _unsupported_function_warning("PATH", "几何函数", args),
            "POLYGON": lambda args: _unsupported_function_warning("POLYGON", "几何函数", args),
            "CIRCLE": lambda args: _unsupported_function_warning("CIRCLE", "几何函数", args),
            "AREA": lambda args: _unsupported_function_warning("AREA", "几何函数", args),
            "CENTER": lambda args: _unsupported_function_warning("CENTER", "几何函数", args),
            "DIAMETER": lambda args: _unsupported_function_warning("DIAMETER", "几何函数", args),
            "HEIGHT": lambda args: _unsupported_function_warning("HEIGHT", "几何函数", args),
            "ISCLOSED": lambda args: _unsupported_function_warning("ISCLOSED", "几何函数", args),
            "ISOPEN": lambda args: _unsupported_function_warning("ISOPEN", "几何函数", args),
            "NPOINTS": lambda args: _unsupported_function_warning("NPOINTS", "几何函数", args),
            "PCLOSE": lambda args: _unsupported_function_warning("PCLOSE", "几何函数", args),
            "POPEN": lambda args: _unsupported_function_warning("POPEN", "几何函数", args),
            "RADIUS": lambda args: _unsupported_function_warning("RADIUS", "几何函数", args),
            "WIDTH": lambda args: _unsupported_function_warning("WIDTH", "几何函数", args),
            
            # 22. XML函数（不支持，提供告警）
            "XMLPARSE": lambda args: _unsupported_function_warning("XMLPARSE", "XML函数", args),
            "XMLSERIALIZE": lambda args: _unsupported_function_warning("XMLSERIALIZE", "XML函数", args),
            "XMLCOMMENT": lambda args: _unsupported_function_warning("XMLCOMMENT", "XML函数", args),
            "XMLCONCAT": lambda args: _unsupported_function_warning("XMLCONCAT", "XML函数", args),
            "XMLELEMENT": lambda args: _unsupported_function_warning("XMLELEMENT", "XML函数", args),
            "XMLFOREST": lambda args: _unsupported_function_warning("XMLFOREST", "XML函数", args),
            "XMLPI": lambda args: _unsupported_function_warning("XMLPI", "XML函数", args),
            "XMLROOT": lambda args: _unsupported_function_warning("XMLROOT", "XML函数", args),
            "XMLEXISTS": lambda args: _unsupported_function_warning("XMLEXISTS", "XML函数", args),
            "XPATH_EXISTS": lambda args: _unsupported_function_warning("XPATH_EXISTS", "XML函数", args),
            "XMLTABLE": lambda args: _unsupported_function_warning("XMLTABLE", "XML函数", args),
            "TABLE_TO_XML": lambda args: _unsupported_function_warning("TABLE_TO_XML", "XML函数", args),
            "QUERY_TO_XML": lambda args: _unsupported_function_warning("QUERY_TO_XML", "XML函数", args),
            
            # 23. 字符串引用函数（不支持，提供告警）
            "QUOTE_IDENT": lambda args: _unsupported_function_warning("QUOTE_IDENT", "标识符引用函数", args),
            "QUOTE_LITERAL": lambda args: _unsupported_function_warning("QUOTE_LITERAL", "字面量引用函数", args),
            "QUOTE_NULLABLE": lambda args: _unsupported_function_warning("QUOTE_NULLABLE", "可空值引用函数", args),
            
            # 24. 数组维度函数（不支持，提供告警）
            "ARRAY_DIMS": lambda args: _unsupported_function_warning("ARRAY_DIMS", "数组维度函数", args),
            "ARRAY_LOWER": lambda args: _unsupported_function_warning("ARRAY_LOWER", "数组下界函数", args),
            "ARRAY_UPPER": lambda args: _unsupported_function_warning("ARRAY_UPPER", "数组上界函数", args),
            
            # 25. 聚合函数（不支持，提供告警）
            "ARRAY_AGG": lambda args: _unsupported_function_warning("ARRAY_AGG", "数组聚合函数", args),
            "JSON_AGG": lambda args: _unsupported_function_warning("JSON_AGG", "JSON聚合函数", args),
            "JSONB_AGG": lambda args: _unsupported_function_warning("JSONB_AGG", "JSONB聚合函数", args),
            "BIT_AND": lambda args: _unsupported_function_warning("BIT_AND", "位运算聚合函数", args),
            "BIT_OR": lambda args: _unsupported_function_warning("BIT_OR", "位运算聚合函数", args),
            "MODE": lambda args: _unsupported_function_warning("MODE", "众数聚合函数", args),
            
            # 26. 窗口函数（不支持，提供告警）
            "NTH_VALUE": lambda args: _unsupported_function_warning("NTH_VALUE", "窗口函数", args),
            
            # 27. JSON表函数（不支持，提供告警）
            "JSON_ARRAY_ELEMENTS": lambda args: _unsupported_function_warning("JSON_ARRAY_ELEMENTS", "JSON表函数", args),
            "JSON_EACH": lambda args: _unsupported_function_warning("JSON_EACH", "JSON表函数", args),
            "JSON_OBJECT_KEYS": lambda args: _unsupported_function_warning("JSON_OBJECT_KEYS", "JSON表函数", args),
            "JSON_POPULATE_RECORD": lambda args: _unsupported_function_warning("JSON_POPULATE_RECORD", "JSON表函数", args),
            "JSON_POPULATE_RECORDSET": lambda args: _unsupported_function_warning("JSON_POPULATE_RECORDSET", "JSON表函数", args),
            "JSON_STRIP_NULLS": lambda args: _unsupported_function_warning("JSON_STRIP_NULLS", "JSON表函数", args),
            "JSON_TO_RECORD": lambda args: _unsupported_function_warning("JSON_TO_RECORD", "JSON表函数", args),
            "JSON_TO_RECORDSET": lambda args: _unsupported_function_warning("JSON_TO_RECORDSET", "JSON表函数", args),
            "JSONB_ARRAY_ELEMENTS": lambda args: _unsupported_function_warning("JSONB_ARRAY_ELEMENTS", "JSONB表函数", args),
            "JSONB_EACH": lambda args: _unsupported_function_warning("JSONB_EACH", "JSONB表函数", args),
            "JSONB_OBJECT_KEYS": lambda args: _unsupported_function_warning("JSONB_OBJECT_KEYS", "JSONB表函数", args),
            "JSONB_POPULATE_RECORD": lambda args: _unsupported_function_warning("JSONB_POPULATE_RECORD", "JSONB表函数", args),
            "JSONB_POPULATE_RECORDSET": lambda args: _unsupported_function_warning("JSONB_POPULATE_RECORDSET", "JSONB表函数", args),
            "JSONB_STRIP_NULLS": lambda args: _unsupported_function_warning("JSONB_STRIP_NULLS", "JSONB表函数", args),
            "JSONB_TO_RECORD": lambda args: _unsupported_function_warning("JSONB_TO_RECORD", "JSONB表函数", args),
            "JSONB_TO_RECORDSET": lambda args: _unsupported_function_warning("JSONB_TO_RECORDSET", "JSONB表函数", args),
            
            # 17. 聚合函数增量映射（需要映射的PostgreSQL函数）
            # 注意：以下函数炎凰数据不支持，需要告警或降级处理
            # "CORR": lambda args: exp.Anonymous(this="CORR", expressions=args),  # 移除：炎凰数据不支持相关系数函数
            # "COVAR_POP": lambda args: exp.Anonymous(this="COVAR_POP", expressions=args),  # 移除：炎凰数据不支持协方差函数
            # "COVAR_SAMP": lambda args: exp.Anonymous(this="COVAR_SAMP", expressions=args),  # 移除：炎凰数据不支持协方差函数
            # "REGR_SLOPE": lambda args: exp.Anonymous(this="REGR_SLOPE", expressions=args),  # 移除：炎凰数据不支持回归函数
            # "REGR_INTERCEPT": lambda args: exp.Anonymous(this="REGR_INTERCEPT", expressions=args),  # 移除：炎凰数据不支持回归函数
            # "REGR_R2": lambda args: exp.Anonymous(this="REGR_R2", expressions=args),  # 移除：炎凰数据不支持回归函数
            
            # ===== 炎凰SQL原生支持函数（147个，无需映射） =====
            
            "CONVERT_TIMEZONE": lambda args: build_convert_timezone(args, "UTC"),
            "DATE_ADD": _build_date_delta(exp.TsOrDsAdd),
            "DATE_DIFF": _build_date_delta(exp.TsOrDsDiff),
            "LISTAGG": exp.GroupConcat.from_arg_list,
            "SPLIT_TO_ARRAY": lambda args: exp.StringToArray(
                this=seq_get(args, 0), expression=seq_get(args, 1) or exp.Literal.string(",")
            ),
            "STRTOL": exp.FromBase.from_arg_list,
            "CAST": exp.Cast.from_arg_list,
            "CONTAINS": lambda args: exp.Anonymous(this="CONTAINS", expressions=args),
            # COLUMNS函数的特殊处理在FUNCTION_PARSERS中定义
            
            # 字符串函数补充
            "SUBSTRING": lambda args: exp.Substring.from_arg_list(args),
            "SUBSTR": lambda args: exp.Anonymous(this="SUBSTR", expressions=args),  # 炎凰SQL支持SUBSTR别名，保持函数名一致性
            "POSITION": lambda args: exp.StrPosition.from_arg_list(args),
            "CHAR_LENGTH": lambda args: exp.Anonymous(this="CHAR_LENGTH", expressions=args),
            "CHARACTER_LENGTH": lambda args: exp.Anonymous(this="CHARACTER_LENGTH", expressions=args),
            "LEFT": lambda args: exp.Left.from_arg_list(args),
            "RIGHT": lambda args: exp.Right.from_arg_list(args),
            "REVERSE": lambda args: exp.Anonymous(this="REVERSE", expressions=args),
            "REPEAT": lambda args: exp.Repeat.from_arg_list(args),
            "LPAD": lambda args: exp.Anonymous(this="LPAD", expressions=args),
            "RPAD": lambda args: exp.Anonymous(this="RPAD", expressions=args),
            "LTRIM": lambda args: exp.Anonymous(this="LTRIM", expressions=args + [exp.Literal.string(" ")] if len(args) == 1 else args),
            "RTRIM": lambda args: exp.Anonymous(this="RTRIM", expressions=args + [exp.Literal.string(" ")] if len(args) == 1 else args),
            "REPLACE": lambda args: exp.Anonymous(this="REPLACE", expressions=args),
            "ASCII": lambda args: exp.Anonymous(this="ASCII", expressions=args),
            "CHR": lambda args: exp.Anonymous(this="CHR", expressions=args),
            "INITCAP": lambda args: exp.Anonymous(this="INITCAP", expressions=args),
            "SPLIT_PART": lambda args: exp.Anonymous(this="SPLIT_PART", expressions=args),
            
            # 第一批数学函数优化完成 - ABS, CEIL, FLOOR, ROUND (通过PostgreSQL继承)
            # 第二批数学函数优化完成 - EXP, LOG, LOG10, POW, POWER, CEILING (通过PostgreSQL继承)
            # 注释：以上函数在PostgreSQL和炎凰SQL中100%语义相同，现通过继承实现
            # "CEILING": lambda args: exp.Ceil.from_arg_list(args),  # 已删除：CEILING→CEIL自动转换
            # "POWER": lambda args: exp.Pow.from_arg_list(args),     # 已删除：通过继承实现
            # "POW": lambda args: exp.Pow.from_arg_list(args),       # 已删除：POW→POWER自动转换
            # "LOG": lambda args: exp.Log.from_arg_list(args),       # 已删除：通过继承实现
            # "LOG10": lambda args: exp.Anonymous(this="LOG10", expressions=args),  # 已删除：通过继承实现
            # "EXP": lambda args: exp.Exp.from_arg_list(args),       # 已删除：通过继承实现
            
            # 数学函数补充（保留炎凰SQL特有或需要Anonymous的函数）
            "SQRT": lambda args: exp.Sqrt.from_arg_list(args),
            "MOD": lambda args: exp.Anonymous(this="MOD", expressions=args),
            "LN": lambda args: exp.Ln.from_arg_list(args),
            "SIGN": lambda args: exp.Anonymous(this="SIGN", expressions=args),
            "TRUNC": lambda args: exp.Anonymous(this="TRUNC", expressions=args),
            "TRUNCATE": lambda args: exp.Anonymous(this="TRUNCATE", expressions=args),
            "RANDOM": lambda args: exp.Anonymous(this="RANDOM", expressions=args),
            
            # 添加scalar_functions.md中缺失的数学函数
            "CBRT": lambda args: exp.Anonymous(this="CBRT", expressions=args),
            "COSH": lambda args: exp.Anonymous(this="COSH", expressions=args),
            "COT": lambda args: exp.Anonymous(this="COT", expressions=args),
            "SINH": lambda args: exp.Anonymous(this="SINH", expressions=args),
            "TANH": lambda args: exp.Anonymous(this="TANH", expressions=args),
            "BROUND": lambda args: exp.Anonymous(this="BROUND", expressions=args),
            "FACTORIAL": lambda args: exp.Anonymous(this="FACTORIAL", expressions=args),
            "RAND": _rand_to_random,  # RAND映射为RANDOM函数
            "PMOD": lambda args: exp.Anonymous(this="PMOD", expressions=args),
            
            # 位运算函数
            "BITWISE_AND": lambda args: exp.Anonymous(this="BITWISE_AND", expressions=args),
            "BITWISE_NOT": lambda args: exp.Anonymous(this="BITWISE_NOT", expressions=args),
            "BITWISE_OR": lambda args: exp.Anonymous(this="BITWISE_OR", expressions=args),
            "BITWISE_XOR": lambda args: exp.Anonymous(this="BITWISE_XOR", expressions=args),
            
            # 进制转换函数
            "BIN": lambda args: exp.Anonymous(this="BIN", expressions=args),
            "HEX": lambda args: exp.Anonymous(this="HEX", expressions=args),
            "CONV": lambda args: exp.Anonymous(this="CONV", expressions=args),
            
            # 字符串长度相关函数
            "BIT_LENGTH": lambda args: exp.Anonymous(this="BIT_LENGTH", expressions=args),
            "BTRIM": lambda args: exp.Anonymous(this="BTRIM", expressions=args),
            "OCTET_LENGTH": lambda args: exp.Anonymous(this="OCTET_LENGTH", expressions=args),
            "LENGTH": lambda args: exp.Length.from_arg_list(args),
            
            # 字符串处理函数
            "ENDS_WITH": lambda args: exp.Anonymous(this="ENDS_WITH", expressions=args),
            "IS_ASCII": lambda args: exp.Anonymous(this="IS_ASCII", expressions=args),
            "IS_SUBSTR": lambda args: exp.Anonymous(this="IS_SUBSTR", expressions=args),
            "LOCATE": lambda args: exp.Anonymous(this="LOCATE", expressions=args),
            "MASK_FIRST_N": lambda args: exp.Anonymous(this="MASK_FIRST_N", expressions=args),
            "MASK_LAST_N": lambda args: exp.Anonymous(this="MASK_LAST_N", expressions=args),
            "QUOTE": lambda args: exp.Anonymous(this="QUOTE", expressions=args),
            "REMOVE_CHARS": lambda args: exp.Anonymous(this="REMOVE_CHARS", expressions=args),
            "SOUNDEX": lambda args: exp.Anonymous(this="SOUNDEX", expressions=args),
            "SPACE": lambda args: exp.Anonymous(this="SPACE", expressions=args),
            "STARTS_WITH": lambda args: exp.Anonymous(this="STARTS_WITH", expressions=args),
            
            # 数组函数（完整列表）
            "ARRAY_AT": lambda args: exp.Anonymous(this="ARRAY_AT", expressions=args),
            "ARRAY_APPEND_AT": lambda args: exp.Anonymous(this="ARRAY_APPEND_AT", expressions=args),
            "ARRAY_CONTAINS": lambda args: exp.Anonymous(this="ARRAY_CONTAINS", expressions=args),
            "ARRAY_DISTINCT": lambda args: exp.Anonymous(this="ARRAY_DISTINCT", expressions=args),
            "ARRAY_GENERATE_RANGE": lambda args: exp.Anonymous(this="ARRAY_GENERATE_RANGE", expressions=args),
            "ARRAY_JOIN": lambda args: exp.Anonymous(this="ARRAY_JOIN", expressions=args),
            "ARRAY_MAX": lambda args: exp.Anonymous(this="ARRAY_MAX", expressions=args),
            "ARRAY_MIN": lambda args: exp.Anonymous(this="ARRAY_MIN", expressions=args),
            "ARRAY_REGEX_LIKE": lambda args: exp.Anonymous(this="ARRAY_REGEX_LIKE", expressions=args),
            "ARRAY_REMOVE_AT": lambda args: exp.Anonymous(this="ARRAY_REMOVE_AT", expressions=args),
            "ARRAY_SLICE": lambda args: exp.Anonymous(this="ARRAY_SLICE", expressions=args),
            "ARRAY_SORT": lambda args: exp.Anonymous(this="ARRAY_SORT", expressions=args),
            "ARRAY_SPLIT": lambda args: exp.Anonymous(this="ARRAY_SPLIT", expressions=args),
            "ARRAY_INTERSECT": lambda args: exp.Anonymous(this="ARRAY_INTERSECT", expressions=args),
            "ARRAY_EXCEPT": lambda args: exp.Anonymous(this="ARRAY_EXCEPT", expressions=args),
            
            # 哈希函数
            "CRC32": lambda args: exp.Anonymous(this="CRC32", expressions=args),
            "HASH": lambda args: exp.Anonymous(this="HASH", expressions=args),
            "HASH32": lambda args: exp.Anonymous(this="HASH32", expressions=args),
            "HASH64": lambda args: exp.Anonymous(this="HASH64", expressions=args),
            "HASH_MD5": lambda args: exp.Anonymous(this="HASH_MD5", expressions=args),
            "HASH_SHA1": lambda args: exp.Anonymous(this="HASH_SHA1", expressions=args),
            "HASH_SHA256": lambda args: exp.Anonymous(this="HASH_SHA256", expressions=args),
            
            # IP地址处理函数
            "INT_TO_IP": lambda args: exp.Anonymous(this="INT_TO_IP", expressions=args),
            "IP_TO_INT": lambda args: exp.Anonymous(this="IP_TO_INT", expressions=args),
            "IPV4_TO_IPV6": lambda args: exp.Anonymous(this="IPV4_TO_IPV6", expressions=args),
            "IS_IPV4": lambda args: exp.Anonymous(this="IS_IPV4", expressions=args),
            "IS_IPV4_LOOPBACK": lambda args: exp.Anonymous(this="IS_IPV4_LOOPBACK", expressions=args),
            "IS_IPV6": lambda args: exp.Anonymous(this="IS_IPV6", expressions=args),
            "IS_IPV6_LOOPBACK": lambda args: exp.Anonymous(this="IS_IPV6_LOOPBACK", expressions=args),
            "CIDR_MATCH": lambda args: exp.Anonymous(this="CIDR_MATCH", expressions=args),
            "TYPEOF": lambda args: exp.Anonymous(this="TYPEOF", expressions=args),
            
            # URL处理函数
            "CUT_QUERY_STRING": lambda args: exp.Anonymous(this="CUT_QUERY_STRING", expressions=args),
            "CUT_QUERY_STRING_AND_FRAGMENT": lambda args: exp.Anonymous(this="CUT_QUERY_STRING_AND_FRAGMENT", expressions=args),
            "CUT_WWW": lambda args: exp.Anonymous(this="CUT_WWW", expressions=args),
            "DOMAIN": lambda args: exp.Anonymous(this="DOMAIN", expressions=args),
            "DOMAIN_WITHOUT_WWW": lambda args: exp.Anonymous(this="DOMAIN_WITHOUT_WWW", expressions=args),
            "FRAGMENT": lambda args: exp.Anonymous(this="FRAGMENT", expressions=args),
            "IS_VALID_URL": lambda args: exp.Anonymous(this="IS_VALID_URL", expressions=args),
            "NETLOC": lambda args: exp.Anonymous(this="NETLOC", expressions=args),
            "NETLOC_USERNAME": lambda args: exp.Anonymous(this="NETLOC_USERNAME", expressions=args),
            "NETLOC_PASSWORD": lambda args: exp.Anonymous(this="NETLOC_PASSWORD", expressions=args),
            "PATH": lambda args: exp.Anonymous(this="PATH", expressions=args),
            "PATH_FULL": lambda args: exp.Anonymous(this="PATH_FULL", expressions=args),
            "PORT": lambda args: exp.Anonymous(this="PORT", expressions=args),
            "PROTOCOL": lambda args: exp.Anonymous(this="PROTOCOL", expressions=args),
            "QUERY_STRING": lambda args: exp.Anonymous(this="QUERY_STRING", expressions=args),
            "TOP_LEVEL_DOMAIN": lambda args: exp.Anonymous(this="TOP_LEVEL_DOMAIN", expressions=args),
            
            # 距离/相似度计算函数
            "DAMERAU_LEVENSHTEIN_DISTANCE": lambda args: exp.Anonymous(this="DAMERAU_LEVENSHTEIN_DISTANCE", expressions=args),
            "HAMMING_DISTANCE": lambda args: exp.Anonymous(this="HAMMING_DISTANCE", expressions=args),
            "JARO_SIMILARITY": lambda args: exp.Anonymous(this="JARO_SIMILARITY", expressions=args),
            "JARO_WINKLER_SIMILARITY": lambda args: exp.Anonymous(this="JARO_WINKLER_SIMILARITY", expressions=args),
            "LEVENSHTEIN": lambda args: exp.Anonymous(this="LEVENSHTEIN", expressions=args),
            "NORMALIZED_DAMERAU_LEVENSHTEIN_DISTANCE": lambda args: exp.Anonymous(this="NORMALIZED_DAMERAU_LEVENSHTEIN_DISTANCE", expressions=args),
            "NORMALIZED_LEVENSHTEIN_DISTANCE": lambda args: exp.Anonymous(this="NORMALIZED_LEVENSHTEIN_DISTANCE", expressions=args),
            "OSA_DISTANCE": lambda args: exp.Anonymous(this="OSA_DISTANCE", expressions=args),
            "SORENSEN_DICE_SIMILARITY": lambda args: exp.Anonymous(this="SORENSEN_DICE_SIMILARITY", expressions=args),
            
            # 格式化函数
            "BAR": lambda args: exp.Anonymous(this="BAR", expressions=args),
            "FORMAT": lambda args: exp.Anonymous(this="FORMAT", expressions=args),
            "ELT": lambda args: exp.Anonymous(this="ELT", expressions=args),
            
            # 条件/比较函数
            "ILIKE": lambda args: exp.Anonymous(this="ILIKE", expressions=args),
            
            # JSON函数
            "JSON_POINTER": lambda args: exp.Anonymous(this="JSON_POINTER", expressions=args),
            "JSON_POINTER_MV": lambda args: exp.Anonymous(this="JSON_POINTER_MV", expressions=args),
            "VALID_JSON": lambda args: exp.Anonymous(this="VALID_JSON", expressions=args),
            
            # 正则表达式函数
            "REGEX_LIKE": lambda args: exp.Anonymous(this="REGEX_LIKE", expressions=args),
            "REGEX_REPLACE": lambda args: exp.Anonymous(this="REGEX_REPLACE", expressions=args),
            
            # 时间函数补充
            "STRFTIME": lambda args: exp.Anonymous(this="STRFTIME", expressions=args),
            "STRPTIME": lambda args: exp.Anonymous(this="STRPTIME", expressions=args),
            
            # 字符串编码/解码函数
            "UNBASE64_STRING": lambda args: exp.Anonymous(this="UNBASE64_STRING", expressions=args),
            
            # 日期时间函数补充 - 仅保留炎凰数据明确支持的函数
            "NOW": lambda args: _create_current_timestamp_with_func('NOW'),
            "CURRENT_DATE": exp.CurrentDate.from_arg_list,
            # 移除EXTRACT - 炎凰数据不支持此函数，只支持DATE_PART
            # "EXTRACT": exp.Extract.from_arg_list,
            "DATE_PART": lambda args: exp.Anonymous(this="DATE_PART", expressions=args),  # 保持原始函数名
            "EPOCH": lambda args: exp.Anonymous(this="EPOCH", expressions=args),
            
            # 炎凰SQL特有的TIME函数（用于时间聚合，支持多参数）
            "TIME": lambda args: exp.Anonymous(this="TIME", expressions=args),
            
            # 条件函数 - 重写DECODE以避免转换为CASE
            "IF": lambda args: exp.If.from_arg_list(args),
            "COALESCE": lambda args: exp.Coalesce.from_arg_list(args),
            "NULLIF": lambda args: exp.Anonymous(this="NULLIF", expressions=args),  # 使用Anonymous替代
            "GREATEST": lambda args: exp.Anonymous(this="GREATEST", expressions=args),
            "LEAST": lambda args: exp.Anonymous(this="LEAST", expressions=args),
            
            # 类型转换函数
            "TO_NUMBER": lambda args: exp.Anonymous(this="TO_NUMBER", expressions=args),
            "TO_BINARY": lambda args: exp.Anonymous(this="TO_BINARY", expressions=args),
            
            # 炎凰SQL特有函数
            "TIME_BUCKET": lambda args: exp.Anonymous(this="TIME_BUCKET", expressions=args),
            "REGEX_EXTRACT": lambda args: exp.Anonymous(this="REGEX_EXTRACT", expressions=args),
            "REGEX_MATCH": lambda args: exp.Anonymous(this="REGEX_MATCH", expressions=args),
            "IP_TO_COUNTRY": lambda args: exp.Anonymous(this="IP_TO_COUNTRY", expressions=args),
            "IP_TO_REGION": lambda args: exp.Anonymous(this="IP_TO_REGION", expressions=args),
            "IP_TO_CITY": lambda args: exp.Anonymous(this="IP_TO_CITY", expressions=args),
            "GEOHASH": lambda args: exp.Anonymous(this="GEOHASH", expressions=args),
            "GEOHASH_DECODE": lambda args: exp.Anonymous(this="GEOHASH_DECODE", expressions=args),
            "UUID": lambda args: exp.Anonymous(this="UUID", expressions=args),
            "BASE64_ENCODE": lambda args: exp.Anonymous(this="BASE64_ENCODE", expressions=args),
            "BASE64_DECODE": lambda args: exp.Anonymous(this="BASE64_DECODE", expressions=args),
            "URL_ENCODE": lambda args: exp.Anonymous(this="URL_ENCODE", expressions=args),
            "URL_DECODE": lambda args: exp.Anonymous(this="URL_DECODE", expressions=args),
            
            # 补充遗漏的聚合函数（根据炎凰SQL语法文档）
            "MAX_STR": lambda args: exp.Anonymous(this="MAX_STR", expressions=args),
            "MIN_STR": lambda args: exp.Anonymous(this="MIN_STR", expressions=args),
            "STDDEV_POP": lambda args: exp.Anonymous(this="STDDEV_POP", expressions=args),
            "STDDEV_SAMP": lambda args: exp.Anonymous(this="STDDEV_SAMP", expressions=args),
            "VAR_POP": lambda args: exp.Anonymous(this="VAR_POP", expressions=args),
            "VAR_SAMP": lambda args: exp.Anonymous(this="VAR_SAMP", expressions=args),
            "STRING_AGG": lambda args: exp.Anonymous(this="STRING_AGG", expressions=args),
            "QUANTILE_T_DIGEST": lambda args: exp.Anonymous(this="QUANTILE_T_DIGEST", expressions=args),
            "PERCENTILE": lambda args: exp.Anonymous(this="PERCENTILE", expressions=args),
            "APPROX_COUNT_DISTINCT": lambda args: exp.Anonymous(this="APPROX_COUNT_DISTINCT", expressions=args),
            "APPROX_MEDIAN": lambda args: exp.Anonymous(this="APPROX_MEDIAN", expressions=args),
            "PRODUCT": lambda args: exp.Anonymous(this="PRODUCT", expressions=args),
            "LATEST_VALUE": lambda args: exp.Anonymous(this="LATEST_VALUE", expressions=args),
            "EARLIEST_VALUE": lambda args: exp.Anonymous(this="EARLIEST_VALUE", expressions=args),
            "FIRST_VALUE": lambda args: exp.Anonymous(this="FIRST_VALUE", expressions=args),
            "LAST_VALUE": lambda args: exp.Anonymous(this="LAST_VALUE", expressions=args),
            "ARRAY_AGG": lambda args: exp.Anonymous(this="ARRAY_AGG", expressions=args),
            "JSON_AGG": lambda args: exp.Anonymous(this="JSON_AGG", expressions=args),
            "JSON_OBJECT_AGG": lambda args: exp.Anonymous(this="JSON_OBJECT_AGG", expressions=args),
            
            # 窗口函数补充
            "ROW_NUMBER": lambda args: exp.Anonymous(this="ROW_NUMBER", expressions=args),
            "RANK": lambda args: exp.Anonymous(this="RANK", expressions=args),
            "DENSE_RANK": lambda args: exp.Anonymous(this="DENSE_RANK", expressions=args),
            # "PERCENT_RANK": 已在上面通过复合映射处理
            "CUME_DIST": lambda args: exp.Anonymous(this="CUME_DIST", expressions=args),
            "NTILE": lambda args: exp.Anonymous(this="NTILE", expressions=args),
            "LAG": lambda args: exp.Anonymous(this="LAG", expressions=args),
            "LEAD": lambda args: exp.Anonymous(this="LEAD", expressions=args),
            
            # 表函数支持
            "GENERATE_SERIES": _build_generate_series,  # 复用PostgreSQL实现
            "PARSE_JSON": lambda args: exp.Anonymous(this="PARSE_JSON", expressions=args),
            "PARSE_CSV": lambda args: exp.Anonymous(this="PARSE_CSV", expressions=args),
            "PARSE_REGEX": lambda args: exp.Anonymous(this="PARSE_REGEX", expressions=args),
            "PARSE_KV": lambda args: exp.Anonymous(this="PARSE_KV", expressions=args),
            "PARSE_XML": lambda args: exp.Anonymous(this="PARSE_XML", expressions=args),
            "PARSE_URL": lambda args: exp.Anonymous(this="PARSE_URL", expressions=args),
            "PARSE_USER_AGENT": lambda args: exp.Anonymous(this="PARSE_USER_AGENT", expressions=args),
            "IP_LOCATION": lambda args: exp.Anonymous(this="IP_LOCATION", expressions=args),
            "GEO_DISTANCE": lambda args: exp.Anonymous(this="GEO_DISTANCE", expressions=args),
            "LOAD_CSV": lambda args: exp.Anonymous(this="LOAD_CSV", expressions=args),
            "LOAD_JSON": lambda args: exp.Anonymous(this="LOAD_JSON", expressions=args),
            "LOAD_PARQUET": lambda args: exp.Anonymous(this="LOAD_PARQUET", expressions=args),
            "LOAD_XML": lambda args: exp.Anonymous(this="LOAD_XML", expressions=args),
            exp.Explode: lambda self, e: f"FLATTEN({self.sql(e, 'this')})",  # 将Explode转换为FLATTEN
            "EXPLODE_OUTER": lambda args: exp.Anonymous(this="EXPLODE_OUTER", expressions=args),
            "POSEXPLODE": lambda args: exp.Anonymous(this="POSEXPLODE", expressions=args),
            "POSEXPLODE_OUTER": lambda args: exp.Anonymous(this="POSEXPLODE_OUTER", expressions=args),
            # UNNEST映射在上面已定义
            
            # JSON函数支持
            "JSON_EXTRACT": lambda args: exp.Anonymous(this="JSON_EXTRACT", expressions=args),
            "JSON_EXTRACT_PATH_TEXT": lambda args: exp.Anonymous(this="JSON_EXTRACT_PATH_TEXT", expressions=args),
            "JSON_ARRAY_LENGTH": lambda args: exp.Anonymous(this="JSON_ARRAY_LENGTH", expressions=args),
            "JSON_OBJECT_KEYS": lambda args: exp.Anonymous(this="JSON_OBJECT_KEYS", expressions=args),
            "JSON_TYPEOF": lambda args: exp.Anonymous(this="JSON_TYPEOF", expressions=args),
            "JSON_VALID": lambda args: exp.Anonymous(this="JSON_VALID", expressions=args),
            "JSON_PRETTY": lambda args: exp.Anonymous(this="JSON_PRETTY", expressions=args),
            
            # 数组函数支持
            "ARRAY_APPEND": lambda args: exp.Anonymous(this="ARRAY_APPEND", expressions=args),
            "ARRAY_PREPEND": lambda args: exp.Anonymous(this="ARRAY_PREPEND", expressions=args),
            "ARRAY_CAT": lambda args: exp.Anonymous(this="ARRAY_CAT", expressions=args),
            "ARRAY_POSITION": lambda args: exp.Anonymous(this="ARRAY_POSITION", expressions=args),
            "ARRAY_REMOVE": lambda args: exp.Anonymous(this="ARRAY_REMOVE", expressions=args),
            "ARRAY_REPLACE": lambda args: exp.Anonymous(this="ARRAY_REPLACE", expressions=args),
            # "ARRAY_TO_STRING": 已移除原生定义，现在通过映射转换为ARRAY_JOIN
            "STRING_TO_ARRAY": lambda args: exp.Anonymous(this="STRING_TO_ARRAY", expressions=args),
            
            # 其他工具函数
            "VERSION": lambda args: exp.Anonymous(this="VERSION", expressions=args),
            "USER": lambda args: exp.Anonymous(this="USER", expressions=args),
            "DATABASE": lambda args: exp.Anonymous(this="DATABASE", expressions=args),
            "SCHEMA": lambda args: exp.Anonymous(this="SCHEMA", expressions=args),
            "CONNECTION_ID": lambda args: exp.Anonymous(this="CONNECTION_ID", expressions=args),
            
            # 不支持的函数 - 提供解析支持但在生成时警告
            "NORMALIZE": lambda args: exp.Anonymous(this="NORMALIZE", expressions=args),
            "JSON_OBJECT": lambda args: exp.Anonymous(this="JSON_OBJECT", expressions=args),
            "GAP_FILL": lambda args: exp.Anonymous(this="GAP_FILL", expressions=args),
            
            # Python表函数支持
            "LOAD_EXCEL": lambda args: exp.Anonymous(this="LOAD_EXCEL", expressions=args),
            "PARSE_FORMAT": lambda args: exp.Anonymous(this="PARSE_FORMAT", expressions=args),
            "PARSE_GROK": lambda args: exp.Anonymous(this="PARSE_GROK", expressions=args),
            "PARSE_SQL": lambda args: exp.Anonymous(this="PARSE_SQL", expressions=args),
            "FAKER": lambda args: exp.Anonymous(this="FAKER", expressions=args),
            "SUMMARIZE": lambda args: exp.Anonymous(this="SUMMARIZE", expressions=args),
            "PIVOT_TABLE": lambda args: exp.Anonymous(this="PIVOT_TABLE", expressions=args),
            "UNPIVOT_TABLE": lambda args: exp.Anonymous(this="UNPIVOT_TABLE", expressions=args),
            "TRANSPOSE": lambda args: exp.Anonymous(this="TRANSPOSE", expressions=args),
            "URL": lambda args: exp.Anonymous(this="URL", expressions=args),
            
            # Java表函数支持
            "JDBC": lambda args: exp.Anonymous(this="JDBC", expressions=args),
            
            # Rust表函数支持
            "DISSECT": lambda args: exp.Anonymous(this="DISSECT", expressions=args),
            
            # 附加的C++表函数
            "PARSE_AUTOKV": lambda args: exp.Anonymous(this="PARSE_AUTOKV", expressions=args),
            "PARSE_DELIMITED": lambda args: exp.Anonymous(this="PARSE_DELIMITED", expressions=args),
            "PARSE_JSON_KV_TABLE": lambda args: exp.Anonymous(this="PARSE_JSON_KV_TABLE", expressions=args),
            "XPATH": lambda args: exp.Anonymous(this="XPATH", expressions=args),
            "LOOKUP": lambda args: exp.Anonymous(this="LOOKUP", expressions=args),
            "MULTI_LOOKUP": lambda args: exp.Anonymous(this="MULTI_LOOKUP", expressions=args),
            "LOAD_JOB_RESULT": lambda args: exp.Anonymous(this="LOAD_JOB_RESULT", expressions=args),
            "SAVED_SEARCH": lambda args: exp.Anonymous(this="SAVED_SEARCH", expressions=args),
            "CURRENT_JOB_META": lambda args: exp.Anonymous(this="CURRENT_JOB_META", expressions=args),
            "GENERATE_TIME_BUCKETS": lambda args: exp.Anonymous(this="GENERATE_TIME_BUCKETS", expressions=args),
            
            # ===== 基于炎凰数据官方文档验证的新增函数映射 =====
            
            # 14. 字符串拼接函数（炎凰数据原生支持）
            "CONCAT_WS": lambda args: exp.Anonymous(this="CONCAT_WS", expressions=args),  # 原生支持，最多5个字符串
            
            # 15. 聚合字符串拼接函数（炎凰数据原生支持）
            "STRING_AGG": lambda args: exp.Anonymous(this="STRING_AGG", expressions=args),  # 原生支持聚合字符串拼接
            
            # 16. 字符串分割函数（炎凰数据原生支持）
            "SPLIT_PART": lambda args: exp.Anonymous(this="SPLIT_PART", expressions=args),  # 原生支持字符串分割
            
            # 17. 时间函数增量映射（需要映射的PostgreSQL函数）
            # 注意：移除重复定义，保持第一个定义
            # "CLOCK_TIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 移除重复：已在第14节定义
            # "STATEMENT_TIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 移除重复：已在第14节定义
            # "TRANSACTION_TIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 移除重复：已在第14节定义
            # "TIMEOFDAY": lambda args: exp.Anonymous(this="STRFTIME", expressions=[exp.Literal.string("%Y-%m-%d %H:%M:%S %Z")]),  # 移除重复：已在第14节定义
            # "LOCALTIMESTAMP": lambda args: exp.Anonymous(this="NOW", expressions=[]),  # 移除重复：已在第14节定义
            "DATE": lambda args: exp.Anonymous(this="CAST", expressions=[args[0] if args else exp.Anonymous(this="NOW", expressions=[]), exp.DataType.build("DATE")]),  # 映射为CAST(...AS DATE)
            # "TIME": 移除错误的CAST映射，TIME函数在炎凰数据中用于GROUP BY时间分组，不是类型转换
            
            # 18. 字符串函数增量映射（需要映射的PostgreSQL函数）
            # 注意：炎凰数据不支持QUOTE_IDENT等函数，已移除错误映射
            # "QUOTE_IDENT": lambda args: exp.Anonymous(this="QUOTE", expressions=args),  # 移除：炎凰数据不支持标识符引用函数
            # "QUOTE_LITERAL": lambda args: exp.Anonymous(this="QUOTE", expressions=args),  # 移除：炎凰数据不支持字面量引用函数
            # "QUOTE_NULLABLE": lambda args: exp.Anonymous(this="QUOTE", expressions=args),  # 移除：炎凰数据不支持可空值引用函数
            "FORMAT": lambda args: exp.Anonymous(this="FORMAT", expressions=args),  # 炎凰数据原生支持FORMAT
            "INITCAP": lambda args: exp.Anonymous(this="INITCAP", expressions=args),  # 炎凰数据原生支持INITCAP
            "LPAD": lambda args: exp.Anonymous(this="LPAD", expressions=args),  # 炎凰数据原生支持LPAD
            "RPAD": lambda args: exp.Anonymous(this="RPAD", expressions=args),  # 炎凰数据原生支持RPAD
            
            # 19. 数组函数增量映射（需要映射的PostgreSQL函数）
            # 注意：炎凰数据只支持一维数组，不需要维度函数
            # "ARRAY_DIMS": lambda args: exp.Anonymous(this="ARRAY_SIZE", expressions=args),  # 移除：炎凰数据不支持数组维度函数
            # "ARRAY_UPPER": 移除错误映射，炎凰数据不支持ARRAY_UPPER函数
            # ARRAY_UPPER: 移除错误映射，炎凰数据不支持ARRAY_UPPER函数，已在告警函数中处理
            "ARRAY_NDIMS": lambda args: exp.Literal.number("1"),  # 炎凰数据只支持一维数组
            # "ARRAY_APPEND": 移除错误映射，炎凰数据原生支持ARRAY_APPEND函数
            # "ARRAY_PREPEND": 移除错误映射，炎凰数据原生支持ARRAY_PREPEND函数
            "ARRAY_REMOVE": lambda args: exp.Anonymous(this="ARRAY_FILTER", expressions=args),  # 映射为ARRAY_FILTER的否定形式
            "ARRAY_REPLACE": lambda args: exp.Anonymous(this="ARRAY_REPLACE", expressions=args),  # 假设炎凰数据支持ARRAY_REPLACE
            
            # 20. 聚合函数增量映射（需要映射的PostgreSQL函数）
            # 注意：以下函数炎凰数据不支持，已移除错误映射
            # "CORR": lambda args: exp.Anonymous(this="CORR", expressions=args),  # 移除：炎凰数据不支持相关系数函数
            # "COVAR_POP": lambda args: exp.Anonymous(this="COVAR_POP", expressions=args),  # 移除：炎凰数据不支持协方差函数
            # "COVAR_SAMP": lambda args: exp.Anonymous(this="COVAR_SAMP", expressions=args),  # 移除：炎凰数据不支持协方差函数
            # "REGR_SLOPE": lambda args: exp.Anonymous(this="REGR_SLOPE", expressions=args),  # 移除：炎凰数据不支持回归函数
            # "REGR_INTERCEPT": lambda args: exp.Anonymous(this="REGR_INTERCEPT", expressions=args),  # 移除：炎凰数据不支持回归函数
            # "REGR_R2": lambda args: exp.Anonymous(this="REGR_R2", expressions=args),  # 移除：炎凰数据不支持回归函数
        }
        
        # 重写FUNCTION_PARSERS来移除DECODE的特殊解析
        FUNCTION_PARSERS = {
            **Postgres.Parser.FUNCTION_PARSERS,
            "COLUMNS": lambda self: self._parse_columns_with_ops(),
            "EXTRACT": lambda self: self._parse_extract(),  # 添加EXTRACT降级映射
        }
        FUNCTION_PARSERS.pop("DECODE", None)  # 移除DECODE的特殊解析方法
        FUNCTION_PARSERS.pop("DATE_PART", None)  # 移除DATE_PART的特殊解析方法，使用FUNCTIONS中的Anonymous定义

        # 完全重写STRING_PARSERS以修复UNICODE_STRING的处理
        # 避免基类的inline UESCAPE处理逻辑
        STRING_PARSERS = {
            **Postgres.Parser.STRING_PARSERS,
            tokens.TokenType.UNICODE_STRING: lambda self, token: self._parse_unicode_string(token),
        }

        NO_PAREN_FUNCTION_PARSERS = {
            **Postgres.Parser.NO_PAREN_FUNCTION_PARSERS,
            "APPROXIMATE": lambda self: self._parse_approximate_count(),
            "SYSDATE": lambda self: self.expression(exp.CurrentTimestamp, sysdate=True),
            "CURRENT_TIME": lambda self: _current_time_to_strftime([]),
            "LOCALTIME": lambda self: _localtime_to_strftime([]),
        }

        # 注册DELETE和DESCRIBE解析器
        STATEMENT_PARSERS = {
            **Postgres.Parser.STATEMENT_PARSERS,
            TokenType.DELETE: lambda self: self._parse_delete(),
            TokenType.DESCRIBE: lambda self: self._parse_describe(),
            TokenType.VALUES: lambda self: self._parse_values(),
            TokenType.SHOW: lambda self: self._parse_show(),
        }

        SUPPORTS_IMPLICIT_UNNEST = True

        def _parse_unicode_string(self, token):
            """解析Unicode字符串，支持 U&'str' 格式"""
            value = token.text
            
            # 去掉前缀和引号
            if value.lower().startswith('u&'):
                content = value[3:-1]  # 去掉U&'和'
            else:
                content = value[2:-1]  # 去掉u&'和'
            
            return self.expression(
                exp.UnicodeString,
                this=content,
                prefix="U&"
            )

        def _parse_alias(
            self, this: t.Optional[exp.Expression], explicit: bool = False
        ) -> t.Optional[exp.Expression]:
            """重写_parse_alias方法来正确处理explicit_as标记"""
            # 检查是否能解析LIMIT或OFFSET子句
            if self._can_parse_limit_or_offset():
                return this

            # 检查是否有显式的AS关键字
            any_token = self._match(tokens.TokenType.ALIAS)
            comments = self._prev_comments or []

            if explicit and not any_token:
                return this

            if self._match(tokens.TokenType.L_PAREN):
                aliases = self.expression(
                    exp.Aliases,
                    comments=comments,
                    this=this,
                    expressions=self._parse_csv(lambda: self._parse_id_var(any_token)),
                )
                self._match_r_paren(aliases)
                return aliases

            alias = self._parse_id_var(any_token, tokens=self.ALIAS_TOKENS) or (
                self.STRING_ALIASES and self._parse_string_as_identifier()
            )

            if alias:
                comments.extend(alias.pop_comments())
                # 创建Alias表达式
                this = self.expression(
                    exp.Alias, 
                    comments=comments, 
                    this=this, 
                    alias=alias
                )
                
                # 通过meta属性保存explicit_as信息
                # 先访问meta属性让它自动初始化
                _ = this.meta
                this.meta["explicit_as"] = any_token
                
                column = this.this

                # 将注释移到别名旁边
                if not this.comments and column and column.comments:
                    this.comments = column.pop_comments()

            return this

        def _parse_values(self) -> exp.Values:
            """解析VALUES语句"""
            return self.expression(
                exp.Values,
                expressions=self._parse_csv(self._parse_value),
                alias=self._parse_table_alias(),
            )

        def _parse_columns_with_ops(self) -> exp.Columns:
            """解析COLUMNS函数，支持EXCEPT、REPLACE和RENAME子句"""
            # 解析COLUMNS(regex)的基础部分
            this = self._parse_expression()
            
            # 创建COLUMNS表达式
            columns_expr = self.expression(exp.Columns, this=this)
            
            return columns_expr
            
        def _parse_function(
            self,
            functions: t.Optional[t.Dict[str, t.Callable]] = None,
            anonymous: bool = False,
            optional_parens: bool = True,
            any_token: bool = False,
        ) -> t.Optional[exp.Expression]:
            """重写_parse_function方法来正确处理COLUMNS函数的EXCEPT语法"""
            # 调用父类方法
            result = super()._parse_function(functions, anonymous, optional_parens, any_token)
            
            # 如果解析的是COLUMNS函数，检查是否有EXCEPT、REPLACE或RENAME
            if isinstance(result, exp.Columns):
                result.set("unpack", True)
                
                # 解析EXCEPT、REPLACE和RENAME子句
                except_expressions = self._parse_star_op("EXCEPT", "EXCLUDE")
                replace_expressions = self._parse_star_op("REPLACE")
                rename_expressions = self._parse_star_op("RENAME")
                
                # 设置到COLUMNS表达式中
                if except_expressions:
                    result.set("except", except_expressions)
                if replace_expressions:
                    result.set("replace", replace_expressions)
                if rename_expressions:
                    result.set("rename", rename_expressions)
                    
            return result

        def _parse_columns(self) -> exp.Columns:
            """解析COLUMNS函数，基础版本，EXCEPT和REPLACE在表达式层面处理"""
            # COLUMNS(regex)
            this = self._parse_expression()
            
            return self.expression(
                exp.Columns,
                this=this,
            )

        def _parse_star_ops(self) -> t.Optional[exp.Expression]:
            """重写_parse_star_ops方法来正确处理COLUMNS函数的EXCEPT和REPLACE语法"""
            # 完全重写：首先检查COLUMNS函数
            if self._match_texts(("COLUMNS",), advance=False):
                this = self._parse_function()
                if isinstance(this, exp.Columns):
                    # 移除unpack设置，避免生成*COLUMNS而不是COLUMNS
                    # this.set("unpack", True)  # 这个设置导致*COLUMNS问题
                    
                    # 解析EXCEPT、REPLACE和RENAME子句
                    except_expressions = self._parse_star_op("EXCEPT", "EXCLUDE")
                    replace_expressions = self._parse_star_op("REPLACE")
                    rename_expressions = self._parse_star_op("RENAME")
                    
                    # 设置到COLUMNS表达式中
                    if except_expressions:
                        this.set("except", except_expressions)
                    if replace_expressions:
                        this.set("replace", replace_expressions)
                    if rename_expressions:
                        this.set("rename", rename_expressions)
                        
                return this

            # 处理普通的*表达式
            return self.expression(
                exp.Star,
                **{  # type: ignore
                    "except": self._parse_star_op("EXCEPT", "EXCLUDE"),
                    "replace": self._parse_star_op("REPLACE"),
                    "rename": self._parse_star_op("RENAME"),
                },
            )

        def _parse_describe(self) -> exp.Describe:
            """解析DESCRIBE语句"""
            table = self._parse_table()
            return self.expression(exp.Describe, this=table)

        def _parse_show(self) -> exp.Show:
            """解析SHOW语句"""
            full = self._match_text_seq("FULL")
            kind = self._parse_var() or self._parse_string()
            
            # 处理复杂情况，如 "SHOW FULL TABLES WHERE ..."
            if full and kind:
                # 将 "FULL" 和 kind 组合
                if isinstance(kind, exp.Var):
                    combined_kind = f"FULL {kind.this}"
                    kind = exp.Var(this=combined_kind)
                elif isinstance(kind, exp.Literal):
                    combined_kind = f"FULL {kind.this}"
                    kind = exp.Literal.string(combined_kind)
            
            # 解析可选的WHERE子句
            where = None
            if self._match(TokenType.WHERE):
                where = self._parse_assignment()
            
            # 解析可选的FROM子句
            from_table = None
            if self._match(TokenType.FROM):
                from_table = self._parse_table()
            
            return self.expression(
                exp.Show, 
                this=kind, 
                **{"from": from_table}, 
                where=where,
                full=full
            )

        def _parse_simplified_pivot(self, is_unpivot: t.Optional[bool] = None) -> exp.Pivot:
            """
            解析简化PIVOT语法，支持炎凰SQL的ORDER BY子句
            语法格式：PIVOT table ON column [IN (values)] USING aggregates GROUP BY columns ORDER BY columns
            """
            def _parse_on() -> t.Optional[exp.Expression]:
                this = self._parse_bitwise()

                if self._match(TokenType.IN):
                    # PIVOT ... ON col IN (row_val1, row_val2)
                    return self._parse_in(this)
                if self._match(TokenType.ALIAS, advance=False):
                    # UNPIVOT ... ON (col1, col2, col3) AS row_val
                    return self._parse_alias(this)

                return this

            this = self._parse_table()
            expressions = self._match(TokenType.ON) and self._parse_csv(_parse_on)
            into = self._parse_unpivot_columns()
            using = self._match(TokenType.USING) and self._parse_csv(
                lambda: self._parse_alias(self._parse_function())
            )
            group = self._parse_group()
            
            # 炎凰SQL特有：支持ORDER BY子句
            order = None
            if self._match(TokenType.ORDER_BY):
                order = self._parse_order(skip_order_token=True)

            pivot_expr = self.expression(
                exp.Pivot,
                this=this,
                expressions=expressions,
                using=using,
                group=group,
                unpivot=is_unpivot,
                into=into,
            )
            
            # 设置order参数
            if order:
                pivot_expr.set("order", order)
            
            return pivot_expr

        def _parse_extract(self) -> exp.Anonymous:
            """重写EXTRACT解析，将其降级映射为DATE_PART函数"""
            # 解析时间部分 (YEAR, MONTH, DAY等)
            this = self._parse_function() or self._parse_var_or_string(upper=True)
            
            if self._match(TokenType.FROM):
                # 解析源表达式
                expression = self._parse_bitwise()
                
                # 转换时间部分为字符串字面量
                if isinstance(this, exp.Var):
                    part_str = exp.Literal.string(this.this.lower())
                elif isinstance(this, (exp.Identifier, exp.Column)):
                    part_str = exp.Literal.string(str(this).lower())
                else:
                    part_str = this
                
                # 返回DATE_PART函数调用
                return exp.Anonymous(this="DATE_PART", expressions=[part_str, expression])
            
            if not self._match(TokenType.COMMA):
                self.raise_error("Expected FROM or comma after EXTRACT", self._prev)
            
            # 处理逗号分隔的语法 (虽然不常见)
            expression = self._parse_bitwise()
            
            # 转换时间部分为字符串字面量
            if isinstance(this, exp.Var):
                part_str = exp.Literal.string(this.this.lower())
            elif isinstance(this, (exp.Identifier, exp.Column)):
                part_str = exp.Literal.string(str(this).lower())
            else:
                part_str = this
                
            return exp.Anonymous(this="DATE_PART", expressions=[part_str, expression])

    class Tokenizer(Postgres.Tokenizer):
        BIT_STRINGS = []
        HEX_STRINGS = []
        BYTE_STRINGS = [("e'", "'"), ("E'", "'")]  # 小写e前缀在前，确保metaclass自动设置使用小写e
        
        # 支持炎凰SQL的Unicode字符串前缀
        UNICODE_STRINGS = [
            (prefix + q, q)
            for q in ["'", '"']  # 明确支持单引号和双引号
            for prefix in ("U&", "u&")  # Unicode编码字符串
        ]
        
        KEYWORDS = {
            **Postgres.Tokenizer.KEYWORDS,
            "(+)": TokenType.JOIN_MARKER,
            "HLLSKETCH": TokenType.HLLSKETCH,
            "MINUS": TokenType.EXCEPT,
            "SUPER": TokenType.SUPER,
            "TOP": TokenType.TOP,
            "UNLOAD": TokenType.COMMAND,
            "VARBYTE": TokenType.VARBINARY,
            "BINARY VARYING": TokenType.VARBINARY,
            "APPLY": TokenType.APPLY,
            "SAMPLE": TokenType.TABLE_SAMPLE,  # 将SAMPLE映射到TABLE_SAMPLE token
            "TABLESAMPLE": TokenType.COMMAND,  # 将TABLESAMPLE映射到COMMAND，后续会被拒绝
            
            # 炎凰SQL特有关键词
            "ENGINE": TokenType.VAR,  # CREATE TABLE语句中的ENGINE关键字
            "BERNOULLI": TokenType.VAR,  # SAMPLE语法中的采样方法
            "ROW": TokenType.ROW,       # SAMPLE语法中的采样方法  
            "BLOCK": TokenType.VAR,     # SAMPLE语法中的采样方法
            "SYSTEM": TokenType.VAR,    # SAMPLE语法中的采样方法
            "UESCAPE": TokenType.VAR,   # Unicode字符串转义语法
        }

        # Redshift allows # to appear as a table identifier prefix
        SINGLE_TOKENS = Postgres.Tokenizer.SINGLE_TOKENS.copy()
        SINGLE_TOKENS.pop("#")

    class Generator(Postgres.Generator):
        LOCKING_READS_SUPPORTED = False
        TZ_TO_WITH_TIME_ZONE = True
        NVL2_SUPPORTED = True
        LAST_DAY_SUPPORTS_DATE_PART = False
        CAN_IMPLEMENT_ARRAY_ANY = False
        MULTI_ARG_DISTINCT = True
        COPY_PARAMS_ARE_WRAPPED = False
        HEX_FUNC = "TO_HEX"
        PARSE_JSON_NAME = "JSON_PARSE"
        ARRAY_CONCAT_IS_VAR_LEN = False
        SUPPORTS_CONVERT_TIMEZONE = True
        EXCEPT_INTERSECT_SUPPORT_ALL_CLAUSE = False
        SUPPORTS_MEDIAN = True
        ALTER_SET_TYPE = "TYPE"
        SUPPORTS_UESCAPE = True  # 炎凰SQL支持UESCAPE语法

        # Redshift doesn't have `WITH` as part of their with_properties so we remove it
        # 炎凰SQL需要保留WITH关键字，但在properties_sql中处理
        WITH_PROPERTIES_PREFIX = ""
        
        # BYTE_START和BYTE_END由metaclass根据tokenizer的BYTE_STRINGS自动设置

        TYPE_MAPPING = {
            **Postgres.Generator.TYPE_MAPPING,
            # 根据炎凰数据CAST语法文档优化类型映射
            exp.DataType.Type.INT: "int",  # 炎凰数据使用小写int
            exp.DataType.Type.BIGINT: "long",  # BIGINT映射为long
            exp.DataType.Type.FLOAT: "float",  # 炎凰数据使用小写float
            exp.DataType.Type.DOUBLE: "double",  # 炎凰数据使用小写double
            exp.DataType.Type.TEXT: "string",  # 炎凰数据使用小写string
            exp.DataType.Type.VARCHAR: "string",  # VARCHAR映射为string
            exp.DataType.Type.CHAR: "string",  # CHAR映射为string
            exp.DataType.Type.BOOLEAN: "boolean",  # 炎凰数据使用小写boolean
            exp.DataType.Type.DECIMAL: "decimal",  # 保持decimal，支持precision和scale
            
            # 其他类型保持原有映射或使用合理的替代
            exp.DataType.Type.BINARY: "string",  # 二进制数据映射为string
            exp.DataType.Type.BLOB: "string",  # BLOB映射为string
            exp.DataType.Type.VARBINARY: "string",  # VARBINARY映射为string
            exp.DataType.Type.ROWVERSION: "string",  # ROWVERSION映射为string
            exp.DataType.Type.TIMETZ: "string",  # 带时区的TIME映射为string
            exp.DataType.Type.TIMESTAMPTZ: "string",  # 带时区的TIMESTAMP映射为string
            exp.DataType.Type.DATE: "string",  # DATE映射为string（炎凰数据通过字符串处理日期）
            exp.DataType.Type.TIME: "string",  # TIME映射为string
            exp.DataType.Type.TIMESTAMP: "string",  # TIMESTAMP映射为string
        }

        TRANSFORMS = {
            **Postgres.Generator.TRANSFORMS,
            exp.ArrayConcat: lambda self, e: self.arrayconcat_sql(e, name="ARRAY_CONCAT"),
            # exp.ArraySize: lambda self, e: self.func("ARRAY_SIZE", e.this),  # 移除：炎凰数据原生支持ARRAY_LENGTH函数
            exp.Concat: lambda self, e: self.func("CONCAT", *e.expressions),
            # exp.ConcatWs: concat_ws_to_dpipe_sql,  # 移除：炎凰数据原生支持CONCAT_WS函数
            exp.ApproxDistinct: lambda self, e: f"APPROXIMATE COUNT(DISTINCT {self.sql(e, 'this')})",
            exp.CurrentTimestamp: lambda self, e: self.currenttimestamp_sql(e),
            exp.CurrentTime: lambda self, e: "STRFTIME(NOW(), '%H:%M:%S%z')",  # CURRENT_TIME映射为STRFTIME获取带时区TIME值
            exp.CurrentDate: lambda self, e: "DATE_TRUNC('day', NOW())",  # 炎凰SQL不支持CURRENT_DATE
            exp.DateAdd: lambda self, e: self.date_add_sql(e),  # 使用炎凰语法
            exp.DateDiff: lambda self, e: self.date_diff_sql(e),  # 使用炎凰语法
            exp.Delete: lambda self, e: self.delete_sql(e),
            exp.DistKeyProperty: lambda self, e: self.func("DISTKEY", e.this),
            exp.DistStyleProperty: lambda self, e: self.naked_property(e),
            exp.Explode: lambda self, e: "FLATTEN(" + self.sql(e, "this") + ")",
            exp.GeneratedAsIdentityColumnConstraint: generatedasidentitycolumnconstraint_sql,
            exp.GroupConcat: lambda self, e: self.func("STRING_AGG", e.this, e.args.get("separator")),
            exp.JSONExtract: lambda self, e: json_extract_segments("JSON_EXTRACT_PATH_TEXT")(self, e),
            exp.JSONExtractScalar: lambda self, e: json_extract_segments("JSON_EXTRACT_PATH_TEXT")(self, e),
            exp.JSONPathKey: lambda self, e: self.sql(e, "this"),
            exp.JSONPathRoot: lambda self, e: "",
            exp.JSONPathSubscript: lambda self, e: self.sql(e, "this"),
            exp.Lateral: lambda self, e: self.lateral_sql(e),  # 添加LATERAL处理
            exp.Limit: lambda self, e: self.limit_sql(e, top=False),  # 炎凰SQL使用LIMIT而不是TOP
            exp.Literal: lambda self, e: self.literal_sql(e),  # 添加字面量处理
            exp.Map: lambda self, e: f"OBJECT({self.expressions(e, flat=True)})",
            exp.Merge: lambda self, e: self.merge_sql(e),
            exp.Offset: lambda self, e: self.offset_sql(e),
            exp.OnConflict: lambda self, e: "",
            exp.Pivot: lambda self, e: self.pivot_sql(e),
            exp.Qualify: lambda self, e: self.qualify_sql(e),
            exp.RegexpLike: lambda self, e: self.binary(e, "~"),
            exp.RegexpILike: lambda self, e: self.binary(e, "~*"),
            exp.Returning: lambda self, e: self.returning_sql(e),  # 添加RETURNING处理
            exp.Select: lambda self, e: self.select_sql(e),
            exp.SortKeyProperty: lambda self, e: f"SORTKEY({self.expressions(e, flat=True)})",
            exp.TableSample: lambda self, e: self.tablesample_sql(e),
            exp.ToChar: lambda self, e: self.function_fallback_sql(e),
            exp.TryCast: lambda self, e: self.cast_sql(e),
            exp.TsOrDsAdd: lambda self, e: self.date_add_sql(e),  # 使用炎凰语法
            exp.TsOrDsDiff: lambda self, e: self.date_diff_sql(e),  # 使用炎凰语法
            exp.UnixToTime: lambda self, e: f"DATEADD(second, {self.sql(e, 'this')}, '1970-01-01')",
            exp.Values: lambda self, e: self.values_sql(e),
            exp.Variance: rename_func("VAR_SAMP"),
            exp.VariancePop: rename_func("VAR_POP"),
            exp.With: lambda self, e: self.with_sql(e),
            exp.WithinGroup: lambda self, e: self.withingroup_sql(e),
            exp.Show: lambda self, e: self.show_sql(e),  # 添加SHOW语句支持
            
            # 不支持的语法 - 抛出错误
            exp.Intersect: lambda self, e: self.intersect_sql(e),  # 添加INTERSECT处理
            exp.Except: lambda self, e: self.except_sql(e),  # 添加EXCEPT处理
            
            # 表函数转换
            exp.ExplodingGenerateSeries: lambda self, e: self.func("GENERATE_SERIES", e.args.get("start"), e.args.get("end"), e.args.get("step")) if e.args.get("step") else self.func("GENERATE_SERIES", e.args.get("start"), e.args.get("end")),
            exp.Unnest: lambda self, e: self.unnest_sql(e),  # 使用自定义的unnest_sql方法转换为FLATTEN
            exp.Explode: lambda self, e: f"FLATTEN({self.sql(e, 'this')})",  # 将Explode转换为FLATTEN而不是EXPLODE
            
            # 字符串函数转换
            exp.Substring: lambda self, e: self.func("SUBSTRING", e.this, e.args.get("start"), e.args.get("length")) if e.args.get("length") else self.func("SUBSTRING", e.this, e.args.get("start")),
            
            # 聚合函数转换 - 保持炎凰SQL原生函数名
            exp.GroupConcat: lambda self, e: self.func("STRING_AGG", e.this, e.args.get("separator")),
            
            # 字符串转义支持
            exp.UnicodeString: lambda self, e: self.unicodestring_sql(e),
            
            # 条件函数转换
            exp.If: lambda self, e: self.func("IF", e.this, e.args.get("true"), e.args.get("false")),
            
            # 哈希函数转换 (第四批优化)
            exp.MD5: lambda self, e: f"HASH_MD5({self.sql(e, 'this')})",
            exp.SHA: lambda self, e: f"HASH_SHA1({self.sql(e, 'this')})",
            exp.SHA2: lambda self, e: f"HASH_SHA256({self.sql(e, 'this')})" if not hasattr(e, 'length') or not e.length or e.length.this == "256" else f"HASH_SHA{e.length.this}({self.sql(e, 'this')})",
            
            # 编码函数转换 (第五批优化) - 基于炎凰数据实际支持情况
            exp.Encode: lambda self, e: self._handle_unsupported_encode(e),
            exp.Decode: lambda self, e: f"UNBASE64_STRING({self.sql(e, 'this')})" if e.args.get('charset') and 'base64' in self.sql(e.args.get('charset')).lower() else f"DECODE({self.sql(e, 'this')}, {self.sql(e.args.get('charset'))})",
            
            # 第六批优化：不支持函数的转换实现在anonymous_sql中处理
            # exp.SafeCast和exp.TryCast等不存在，改为在anonymous_sql中处理
            
            # 第七批优化：高优先级虚继承函数转换
            exp.TimeToUnix: lambda self, e: self.func("DATE_PART", exp.Literal.string("epoch"), e.this),
            exp.StrPosition: lambda self, e: self.func("POSITION", e.args.get('substr'), e.args.get('this')) if e.args.get('substr') and e.args.get('this') else self.func("POSITION", *e.expressions),
            exp.CountIf: lambda self, e: f"SUM(CASE WHEN {self.sql(e.this)} THEN 1 ELSE 0 END)",
            exp.Rand: lambda self, e: "RANDOM()",
            exp.Unicode: lambda self, e: self.func("ASCII", e.this),
            exp.TimestampTrunc: lambda self, e: self.func("DATE_TRUNC", exp.Literal.string(e.unit.this.lower()) if hasattr(e.unit, 'this') else e.unit, e.this) if hasattr(e, 'unit') and hasattr(e, 'this') else self.func("DATE_TRUNC", *e.expressions),
            exp.DateSub: lambda self, e: self.func("DATE_ADD", e.unit, exp.Neg(this=e.expression), e.this) if hasattr(e, 'unit') else self.date_add_sql(e),
            exp.Uuid: lambda self, e: "UUID()",
            exp.CurrentUser: lambda self, e: "USER()",
            exp.Extract: lambda self, e: self.func("DATE_PART", exp.Literal.string(e.this.this.lower()) if hasattr(e.this, 'this') else e.this, e.expression),
            exp.Filter: lambda self, e: f"SUM(CASE WHEN {self.sql(e.expression.this)} THEN 1 ELSE 0 END)" if isinstance(e.this, exp.Count) else f"SUM(CASE WHEN {self.sql(e.expression.this)} THEN {self.sql(e.this.this)} ELSE 0 END)",
            exp.Sub: lambda self, e: self.func("DATE_ADD", e.this, exp.Neg(this=e.expression.this), e.expression.unit) if isinstance(e.expression, exp.Interval) else self.binary(e, "-"),
            
            # 第八批优化：中优先级虚继承函数转换
            exp.ArrayConcat: lambda self, e: self.func("ARRAY_CAT", *e.expressions),
            exp.Add: lambda self, e: self.func("DATE_ADD", e.this, e.expression.this, e.expression.unit) if isinstance(e.expression, exp.Interval) else self.binary(e, "+"),
            exp.Anonymous: lambda self, e: self.func("DATE_DIFF", e.expressions[1], e.expressions[0]) if e.this == "AGE" and len(e.expressions) >= 2 else (self.func("ARRAY_LENGTH", e.expressions[0]) if e.this == "CARDINALITY" and len(e.expressions) == 1 else self.anonymous_sql(e)),
            exp.RegexpLike: lambda self, e: self.func("REGEXP_LIKE", e.this, e.expression),
            
            # 第九批优化：错误继承函数的复合映射转换
            exp.LogicalAnd: lambda self, e: f"(MIN(CASE WHEN {self.sql(e.this)} THEN 1 ELSE 0 END) = 1)",
            exp.LogicalOr: lambda self, e: f"(MAX(CASE WHEN {self.sql(e.this)} THEN 1 ELSE 0 END) = 1)",
            
            # 第十批优化：时间日期函数映射转换
            exp.TimeToStr: lambda self, e: self.func("STRFTIME", e.this, self._convert_time_format(e.args.get('format'))),
            exp.StrToTime: lambda self, e: self.func("STRPTIME", e.this, self._convert_time_format(e.args.get('format'))),
            
            # 第十一批优化：百分位数函数映射转换
            exp.PercentileCont: lambda self, e: self.percentile_cont_sql(e),
            exp.PercentileDisc: lambda self, e: self.percentile_disc_sql(e),
            
            # TRIM函数映射转换（使用LTRIM和RTRIM组合）
            exp.Trim: lambda self, e: self.trim_sql(e),
            

        }

        # Postgres maps exp.Pivot to no_pivot_sql, but Redshift support pivots
        TRANSFORMS.pop(exp.Pivot)

        # Postgres doesn't support JSON_PARSE, but Redshift does
        TRANSFORMS.pop(exp.ParseJSON)

        # Redshift supports these functions
        TRANSFORMS.pop(exp.AnyValue)
        TRANSFORMS.pop(exp.LastDay)
        # SHA2转换已在上面的TRANSFORMS中定义，不再移除

        RESERVED_KEYWORDS = {
            "aes128",
            "aes256",
            "all",
            "allowoverwrite",
            "analyse",
            "analyze",
            "and",
            "any",
            "array",
            "as",
            "asc",
            "authorization",
            "az64",
            "backup",
            "between",
            "binary",
            "blanksasnull",
            "both",
            "bytedict",
            "bzip2",
            "case",
            "cast",
            "check",
            "collate",
            "column",
            "constraint",
            "create",
            "credentials",
            "cross",
            "current_date",
            "current_time",
            "current_timestamp",
            "current_user",
            "current_user_id",
            "default",
            "deferrable",
            "deflate",
            "defrag",
            "delta",
            "delta32k",
            "desc",
            "disable",
            "distinct",
            "do",
            "else",
            "emptyasnull",
            "enable",
            "encode",
            "encrypt     ",
            "encryption",
            "end",
            "except",
            "explicit",
            "false",
            "for",
            "foreign",
            "freeze",
            "from",
            "full",
            "globaldict256",
            "globaldict64k",
            "grant",
            "group",
            "gzip",
            "having",
            "identity",
            "ignore",
            "ilike",
            "in",
            "initially",
            "inner",
            "intersect",
            "interval",
            "into",
            "is",
            "isnull",
            "join",
            "leading",
            "left",
            "like",
            "limit",
            "localtime",
            "localtimestamp",
            "lun",
            "luns",
            "lzo",
            "lzop",
            "minus",
            "mostly16",
            "mostly32",
            "mostly8",
            "natural",
            "new",
            "not",
            "notnull",
            "null",
            "nulls",
            "off",
            "offline",
            "offset",
            "oid",
            "old",
            "on",
            "only",
            "open",
            "or",
            "order",
            "outer",
            "overlaps",
            "parallel",
            "partition",
            "percent",
            "permissions",
            "pivot",
            "placing",
            "primary",
            "raw",
            "readratio",
            "recover",
            "references",
            "rejectlog",
            "resort",
            "respect",
            "restore",
            "right",
            "select",
            "session_user",
            "similar",
            "snapshot",
            "some",
            "sysdate",
            "system",
            "table",
            "tag",
            "tdes",
            "text255",
            "text32k",
            "then",
            "timestamp",
            "to",
            "top",
            "trailing",
            "true",
            "truncatecolumns",
            "union",
            "unique",
            "unnest",
            "unpivot",
            "user",
            "using",
            "verbose",
            "wallet",
            "when",
            "where",
            "with",
            "without",
        }

        def unnest_sql(self, expression: exp.Unnest) -> str:
            """将UNNEST转换为FLATTEN"""
            args = self.expressions(expression, flat=True)
            return f"FLATTEN({args})"

        def cast_sql(self, expression: exp.Cast, safe_prefix: t.Optional[str] = None) -> str:
            if expression.is_type(exp.DataType.Type.JSON):
                # Redshift doesn't support a JSON type, so casting to it is treated as a noop
                return self.sql(expression, "this")

            return super().cast_sql(expression, safe_prefix=safe_prefix)

        def datatype_sql(self, expression: exp.DataType) -> str:
            """
            Redshift converts the `TEXT` data type to `VARCHAR(255)` by default when people more generally mean
            VARCHAR of max length which is `VARCHAR(max)` in Redshift. Therefore if we get a `TEXT` data type
            without precision we convert it to `VARCHAR(max)` and if it does have precision then we just convert
            `TEXT` to `VARCHAR`.
            """
            if expression.is_type("text"):
                expression.set("this", exp.DataType.Type.VARCHAR)
                precision = expression.args.get("expressions")

                if not precision:
                    expression.append("expressions", exp.var("MAX"))
                    
            # 兼容性检查：检查不支持的数据类型
            unsupported_types = {
                'BYTEA', 'JSONB', 'HSTORE', 'ARRAY', 'ENUM', 
                'UUID', 'INET', 'CIDR', 'MACADDR', 'TSVECTOR'
            }
            
            # 获取数据类型名称
            type_name = expression.this.name if hasattr(expression.this, 'name') else str(expression.this)
            
            if type_name.upper() in unsupported_types:
                self._warn_compatibility(
                    f"{type_name} data type",
                    "basic types (INT, STRING, FLOAT, DOUBLE, BOOLEAN)"
                )

            return super().datatype_sql(expression)

        def alterset_sql(self, expression: exp.AlterSet) -> str:
            exprs = self.expressions(expression, flat=True)
            exprs = f" TABLE PROPERTIES ({exprs})" if exprs else ""
            location = self.sql(expression, "location")
            location = f" LOCATION {location}" if location else ""
            file_format = self.expressions(expression, key="file_format", flat=True, sep=" ")
            file_format = f" FILE FORMAT {file_format}" if file_format else ""

            return f"SET{exprs}{location}{file_format}"

        def array_sql(self, expression: exp.Array) -> str:
            if expression.args.get("bracket_notation"):
                return super().array_sql(expression)

            return rename_func("ARRAY")(self, expression)

        def explode_sql(self, expression: exp.Explode) -> str:
            self.unsupported("Unsupported EXPLODE() function")
            return ""

        def join_sql(self, expression):
            """处理JOIN语句，包括APPLY，修复空格问题"""
            if isinstance(expression.this, exp.Lateral):
                # 处理APPLY语法
                lateral = expression.this
                cross_apply = lateral.args.get("cross_apply")
                if cross_apply is False:
                    join_type = "OUTER APPLY"
                elif cross_apply is True:
                    join_type = "CROSS APPLY"
                else:
                    join_type = "APPLY"
                
                # 获取表函数调用
                table_func = lateral.this
                alias = lateral.alias
                
                if alias:
                    alias_sql = f" {self.sql(alias)}"
                else:
                    alias_sql = ""
                
                # 修复：确保APPLY前有正确的空格
                return f" {join_type} {self.sql(table_func)}{alias_sql}"
            else:
                # 普通JOIN处理 - 重新实现以避免额外空格
                if not self.SEMI_ANTI_JOIN_WITH_SIDE and expression.kind in ("SEMI", "ANTI"):
                    side = None
                else:
                    side = expression.side

                op_sql = " ".join(
                    op
                    for op in (
                        expression.method,
                        "GLOBAL" if expression.args.get("global") else None,
                        side,
                        expression.kind,
                        expression.hint if self.JOIN_HINTS else None,
                    )
                    if op
                )
                
                match_cond = self.sql(expression, "match_condition")
                match_cond = f" MATCH_CONDITION ({match_cond})" if match_cond else ""
                on_sql = self.sql(expression, "on")
                using = expression.args.get("using")

                if not on_sql and using:
                    on_sql = ", ".join(self.sql(column) for column in using)

                this = expression.this
                this_sql = self.sql(this)

                exprs = self.expressions(expression)
                if exprs:
                    this_sql = f"{this_sql}, {exprs}"

                if on_sql:
                    on_sql = self.indent(on_sql, skip_first=True)
                    space = " " * self.pad if self.pretty else " "
                    if using:
                        on_sql = f" USING ({on_sql})"
                    else:
                        on_sql = f" ON {on_sql}"
                elif not op_sql:
                    if isinstance(this, exp.Lateral) and this.args.get("cross_apply") is not None:
                        return f" {this_sql}"
                    return f", {this_sql}"

                if op_sql != "STRAIGHT_JOIN":
                    op_sql = f"{op_sql} JOIN" if op_sql else "JOIN"

                pivots = self.expressions(expression, key="pivots", sep="", flat=True)
                
                # 关键修复：不使用self.seg()，直接拼接避免额外空格
                return f" {op_sql} {this_sql}{match_cond}{on_sql}{pivots}"

        def lateral_op(self, expression):
            cross_apply = expression.args.get("cross_apply")
            if cross_apply is True:
                return "CROSS APPLY"
            if cross_apply is False:
                return "OUTER APPLY"
            return "APPLY"

        def from_sql(self, expression):
            # 检查是否是多表合并Union
            if isinstance(expression.this, exp.Union) and expression.this.args.get("is_table_merge"):
                return self.union_sql(expression.this)
            # 只返回主表部分，不拼接join
            return self.sql(expression, "this")

        def select_sql(self, expression):
            # 先拼接SELECT主干
            select = self.seg("SELECT") + " "
            if expression.args.get("distinct"):
                select += "DISTINCT "
            select += self.expressions(expression, "expressions")
            from_expr = expression.args.get("from")
            from_sql = self.sql(from_expr) if from_expr else ""
            joins = expression.args.get("joins") or []
            # 修复：不要在每个JOIN前添加额外空格，因为join_sql已经处理了前导空格
            joins_sql = "".join(self.sql(join) for join in joins) if joins else ""
            if from_sql:
                select += f" FROM {from_sql}"
            if joins_sql:
                select += joins_sql  # 修复：移除额外的空格
            # 拼接WHERE、GROUP BY、HAVING、ORDER BY、LIMIT等
            where_sql = self.sql(expression, "where").strip()
            group_sql = self.sql(expression, "group").strip()
            having_sql = self.sql(expression, "having").strip()
            order_sql = self.sql(expression, "order").strip()
            limit_sql = self.sql(expression, "limit").strip()
            offset_sql = self.sql(expression, "offset").strip()
            # 依次拼接
            if where_sql:
                select += f" {where_sql}"
            if group_sql:
                select += f" {group_sql}"
            if having_sql:
                select += f" {having_sql}"
            if order_sql:
                select += f" {order_sql}"
            if limit_sql:
                select += f" {limit_sql}"
            if offset_sql:
                select += f" {offset_sql}"
            # 拼接CTE（WITH）
            if expression.args.get("with"):
                with_sql = self.sql(expression, "with").strip()
                select = f"{with_sql} {select.strip()}"
            return select.strip()

        def _handle_unsupported_encode(self, expression: exp.Encode) -> str:
            """处理不支持的ENCODE函数"""
            from sqlglot.errors import UnsupportedError
            raise UnsupportedError(
                "ENCODE() function is not supported in Yanhuang SQL.\n"
                "替代方案：\n"
                "- 对于BASE64编码：建议在应用层进行编码\n"
                "- 对于其他编码：请查阅炎凰数据文档确认支持的编码函数"
            )

        def _unsupported_function_sql(self, func_name: str, expression: exp.Anonymous) -> str:
            """为不支持的函数提供友好的错误信息和替代建议"""
            from sqlglot.errors import UnsupportedError
            
            # 针对不同函数类型提供特定的错误信息和建议
            if func_name in ["JSON_OBJECT", "JSON_OBJECTAGG", "JSON_TABLE", "JSONB_EXISTS"]:
                alternative = "炎凰数据提供其他JSON处理函数，如JSON_EXTRACT、JSON_AGG等，请查阅文档获取完整列表"
            elif func_name in ["XMLELEMENT", "XMLTABLE"]:
                alternative = "炎凰数据提供PARSE_XML表函数进行XML处理"
            elif func_name == "GAP_FILL":
                alternative = "可使用窗口函数LAG/LEAD配合CASE WHEN实现数据填充"
            elif func_name == "OPENJSON":
                alternative = "使用PARSE_JSON表函数处理JSON数据"
            elif func_name in ["ARGMAX", "ARGMIN"]:
                alternative = "使用窗口函数：FIRST_VALUE(id) OVER (ORDER BY value DESC/ASC)"
            elif func_name == "NORMALIZE":
                alternative = "可使用字符串函数REPLACE配合正则表达式实现标准化"
            elif func_name == "OVERLAY":
                alternative = "使用SUBSTRING和CONCAT函数组合实现字符串替换"
            else:
                alternative = "请查阅炎凰数据官方文档寻找等效函数"
            
            raise UnsupportedError(
                f"{func_name}() function is not supported in Yanhuang SQL.\n"
                f"替代方案：{alternative}"
            )
        
        def anonymous_sql(self, expression: exp.Anonymous) -> str:
            """处理匿名函数，基于炎凰数据实际支持的功能进行虚拟继承函数映射"""
            func_name = expression.this
            
            # 虚拟继承函数处理 - 基于炎凰数据实际支持的功能
            if hasattr(self, 'VIRTUAL_INHERITANCE_FUNCTIONS') and func_name in self.VIRTUAL_INHERITANCE_FUNCTIONS:
                handler = self.VIRTUAL_INHERITANCE_FUNCTIONS[func_name]
                return handler(self, expression)
            
            # 高可行性函数映射（推荐直接使用）
            if func_name == "PI":
                # PI() → 3.141592653589793 常量
                return "3.141592653589793"
            elif func_name == "ATAND":
                # ATAND(x) → DEGREES(ATAN(x))
                if len(expression.expressions) != 1:
                    from sqlglot.errors import UnsupportedError
                    raise UnsupportedError("ATAND() requires exactly one argument")
                arg = self.sql(expression.expressions[0])
                return f"DEGREES(ATAN({arg}))"
            
            # ===== 不支持函数的告警处理 =====
            elif func_name in ["JSON_OBJECT", "JSON_OBJECTAGG", "JSON_TABLE", "JSONB_EXISTS", 
                               "XMLELEMENT", "XMLTABLE", "GAP_FILL", "OPENJSON", "ARGMAX", "ARGMIN",
                               "NORMALIZE", "OVERLAY"]:
                return self._unsupported_function_sql(func_name, expression)
            
            # 使用父类的匿名函数处理
            return super().anonymous_sql(expression)

        def columns_sql(self, expression: exp.Columns) -> str:
            sql = f"COLUMNS({self.sql(expression, 'this')})"
            if expression.args.get("except"):
                excepts = ", ".join(self.sql(e) for e in expression.args["except"])
                sql += f" EXCEPT ({excepts})"
            if expression.args.get("replace"):
                def tight_alias(e):
                    # 只处理Alias类型，表达式+AS+别名，AS大写，无多余空格
                    if isinstance(e, exp.Alias):
                        expr_sql = self.sql(e.this).replace(" ","")
                        alias_sql = self.sql(e.alias)
                        return f"{expr_sql} AS {alias_sql}"
                    return self.sql(e)
                replaces = ", ".join(tight_alias(e) for e in expression.args["replace"])
                sql += f" REPLACE ({replaces})"
            if expression.args.get("rename"):
                # 处理RENAME子句，格式：RENAME (old_name AS new_name, ...)
                def format_rename_alias(e):
                    if isinstance(e, exp.Alias):
                        old_name_sql = self.sql(e.this)
                        new_name_sql = self.sql(e.alias)
                        return f"{old_name_sql} AS {new_name_sql}"
                    return self.sql(e)
                renames = ", ".join(format_rename_alias(e) for e in expression.args["rename"])
                sql += f" RENAME ({renames})"
            if expression.args.get("alias"):
                alias = expression.args["alias"]
                alias_sql = self.sql(alias)
                sql += f" AS {alias_sql}"
            return sql

        def star_sql(self, expression: exp.Star) -> str:
            """Handle Star with EXCEPT/REPLACE"""
            sql = "*"
            
            # Handle EXCEPT
            if expression.args.get("except"):
                excepts = []
                for e in expression.args["except"]:
                    if isinstance(e, exp.Column) and e.table is None:
                        # 如果是Column但没有表名，只显示字段名
                        excepts.append(self.sql(e.this))
                    else:
                        excepts.append(self.sql(e))
                sql += f" EXCEPT ({', '.join(excepts)})"
            
            # Handle REPLACE  
            if expression.args.get("replace"):
                def format_replace_alias(e):
                    if isinstance(e, exp.Alias):
                        expr_sql = self.sql(e.this)
                        alias_sql = self.sql(e.alias)
                        return f"{expr_sql} AS {alias_sql}"
                    return self.sql(e)
                replaces = ", ".join(format_replace_alias(e) for e in expression.args["replace"])
                sql += f" REPLACE ({replaces})"
                
            return sql

        def exists_sql(self, expression: exp.Exists) -> str:
            """处理EXISTS子查询的兼容性检查"""
            if self._check_subquery_correlation(expression.this):
                self._warn_compatibility(
                    "correlated EXISTS subqueries", 
                    "non-correlated subqueries"
                )
            # 确保EXISTS与括号之间有空格
            return f"EXISTS ({self.sql(expression, 'this')})"

        def column_sql(self, expression: exp.Column) -> str:
            """处理列引用，特殊处理LOCALTIME"""
            # 检查是否是LOCALTIME关键字作为函数使用
            # 需要检查标识符的名称，不是直接比较对象
            # 只有在没有表限定符且没有引号的情况下才映射为函数
            if (hasattr(expression.this, 'name') and 
                expression.this.name == "LOCALTIME" and 
                not expression.table and
                not getattr(expression.this, 'quoted', False)):
                # LOCALTIME 作为时间函数使用，映射为STRFTIME获取不带时区TIME值
                return "STRFTIME(NOW(), '%H:%M:%S')"
            # 其他情况使用标准column处理
            return super().column_sql(expression)

        def alias_sql(self, expression: exp.Alias, alias: t.Optional[str] = None) -> str:
            """
            生成别名SQL，正确处理引号标识符
            """
            # 获取表达式部分
            this_sql = self.sql(expression, "this")
            
            # 获取别名部分 - 从args中获取真正的Identifier对象
            if alias:
                # 如果外部传入了别名，使用传入的别名
                alias_sql = alias
            else:
                # 从args中获取真正的Identifier对象
                alias_expr = expression.args.get("alias")
                if not alias_expr:
                    return this_sql
                
                # 处理别名 - 保持原有的引号状态或添加必要的引号
                if isinstance(alias_expr, exp.Identifier):
                    # 检查标识符是否是quoted的
                    is_quoted = alias_expr.args.get("quoted", False)
                    alias_name = alias_expr.this
                    
                    if is_quoted:
                        # 已经明确标记为quoted，直接添加引号
                        alias_sql = f'"{alias_name}"'
                    elif alias_name.upper() in self.RESERVED_KEYWORDS:
                        # 如果是保留关键字，必须添加引号
                        alias_sql = f'"{alias_name}"'
                    else:
                        # 普通标识符，不添加引号
                        alias_sql = alias_name
                else:
                    alias_sql = self.sql(alias_expr) if alias_expr else ""
            
            # 组合结果，AS大写，空格规范
            if alias_sql:
                return f"{this_sql} AS {alias_sql}"
            return this_sql

        def table_sql(self, expression: exp.Table, sep: str = " AS ") -> str:
            """生成表名SQL，确保正确处理SAMPLE语法"""
            only = "ONLY " if expression.args.get("only") else ""
            table = self.sql(expression, "this")
            partition = self.sql(expression, "partition")
            partition = f" {partition}" if partition else ""
            version = self.sql(expression, "version")
            version = f" {version}" if version else ""
            
            # 动态确定表别名分隔符
            alias_expr = expression.args.get("alias")
            if alias_expr:
                # 检查表别名是否显式使用了AS
                alias_sql = self.sql(alias_expr)
                explicit_as = getattr(alias_expr, 'meta', {}).get("explicit_as", False) if hasattr(alias_expr, 'meta') else False
                
                # 对于TableAlias，我们需要检查解析时是否有AS关键字
                # 但由于TableAlias没有explicit_as标记，我们采用启发式方法
                # 如果sep参数不是默认值，使用传入的sep；否则使用空格
                if sep == " AS ":  # 默认值，说明没有特殊指定
                    alias = f" {alias_sql}"  # 只用空格，不用AS
                else:
                    alias = f"{sep}{alias_sql}"  # 使用指定的分隔符
            else:
                alias = ""

            # 修复sample处理 - 确保前面有空格
            sample = self.sql(expression, "sample")
            # sample_sql方法已经包含前面的空格，但需要确保不丢失
            if sample and not sample.startswith(' '):
                sample = f" {sample}"

            if self.dialect.ALIAS_POST_TABLESAMPLE:
                sample_pre_alias = sample
                sample_post_alias = ""
            else:
                sample_pre_alias = ""
                sample_post_alias = sample

            hints = self.expressions(expression, key="hints", sep=" ")
            hints = f" {hints}" if hints and self.TABLE_HINTS else ""
            pivots = self.expressions(expression, key="pivots", sep="", flat=True)
            
            # Special handling for APPLY joins to ensure proper spacing
            joins_expressions = expression.args.get("joins", [])
            joins_sqls = []
            for join_expr in joins_expressions:
                join_sql = self.sql(join_expr)
                # Ensure APPLY has proper spacing
                if isinstance(join_expr.this, exp.Lateral) and not join_sql.startswith(' '):
                    join_sql = f" {join_sql}"
                joins_sqls.append(join_sql)
            joins = "".join(joins_sqls)
            
            laterals = self.expressions(expression, key="laterals", sep="")

            file_format = self.sql(expression, "format")
            if file_format:
                pattern = self.sql(expression, "pattern")
                pattern = f", PATTERN => {pattern}" if pattern else ""
                file_format = f" (FILE_FORMAT => {file_format}{pattern})"

            ordinality = expression.args.get("ordinality") or ""
            if ordinality:
                ordinality = f" WITH ORDINALITY{alias}"
                alias = ""

            when = self.sql(expression, "when")
            if when:
                table = f"{table} {when}"

            changes = self.sql(expression, "changes")
            changes = f" {changes}" if changes else ""

            rows_from = self.expressions(expression, key="rows_from")
            if rows_from:
                table = f"ROWS FROM {self.wrap(rows_from)}"

            return f"{only}{table}{changes}{partition}{version}{file_format}{sample_pre_alias}{alias}{hints}{pivots}{sample_post_alias}{joins}{laterals}{ordinality}"

        def contains_sql(self, expression: exp.Contains) -> str:
            """生成CONTAINS函数SQL"""
            if len(expression.expressions) == 0:
                return "CONTAINS()"
            elif len(expression.expressions) == 1:
                # CONTAINS('keyword')，默认作用于_message字段
                return f"CONTAINS({self.sql(expression.expressions[0])})"
            elif len(expression.expressions) == 2:
                # CONTAINS(field, 'keyword')
                field, keyword = expression.expressions
                return f"CONTAINS({self.sql(field)}, {self.sql(keyword)})"
            elif len(expression.expressions) == 3:
                # CONTAINS(field, 'keyword', tokenized)
                field, keyword, tokenized = expression.expressions
                return f"CONTAINS({self.sql(field)}, {self.sql(keyword)}, {self.sql(tokenized)})"
            else:
                # 其他情况，使用Anonymous处理
                return self.anonymous_sql(expression)

        def pivot_sql(self, expression: exp.Pivot) -> str:
            """生成PIVOT语句SQL"""
            sql = f"PIVOT {self.sql(expression.this)}"
            
            # 炎凰SQL简化PIVOT语法处理
            # expressions 包含 ON 子句的列
            # using 包含 USING 子句的聚合函数
            
            # 处理ON子句（从expressions获取）
            if expression.expressions:
                # 炎凰SQL简化语法：expressions包含ON子句的列
                on_columns = []
                for expr in expression.expressions:
                    if isinstance(expr, exp.In):
                        # 有IN子句的情况：pivot_column IN (values)
                        pivot_column = expr.this
                        pivoted_values = expr.expressions
                        on_columns.append(self.sql(pivot_column))
                        if pivoted_values:
                            values = ", ".join(self.sql(v) for v in pivoted_values)
                            on_columns[-1] += f" IN ({values})"
                    else:
                        # 只有透视列，没有IN子句
                        on_columns.append(self.sql(expr))
                sql += f" ON {', '.join(on_columns)}"
            
            # 处理USING子句（从using参数获取）
            if expression.args.get("using"):
                using_exprs = expression.args["using"]
                using = ", ".join(self.sql(expr) for expr in using_exprs)
                sql += f" USING {using}"
            
            # 处理group参数（GROUP BY子句）
            if expression.args.get("group"):
                group_expr = expression.args["group"]
                if isinstance(group_expr, exp.Group) and group_expr.expressions:
                    group_by = ", ".join(self.sql(expr) for expr in group_expr.expressions)
                    sql += f" GROUP BY {group_by}"
            
            # 处理order参数（ORDER BY子句）
            if expression.args.get("order"):
                order_expr = expression.args["order"]
                if isinstance(order_expr, exp.Order) and order_expr.expressions:
                    order_by = ", ".join(self.sql(expr) for expr in order_expr.expressions)
                    sql += f" ORDER BY {order_by}"
            
            return sql

        def describe_sql(self, expression: exp.Describe) -> str:
            """生成DESCRIBE语句SQL"""
            return f"DESCRIBE {self.sql(expression.this)}"

        def delete_sql(self, expression: exp.Delete) -> str:
            """生成DELETE语句SQL，支持ORDER BY和LIMIT"""
            sql = f"DELETE FROM {self.sql(expression.this)}"
            
            if expression.args.get("where"):
                sql += self.sql(expression.args['where'])
            
            if expression.args.get("order"):
                sql += self.sql(expression.args['order'])
            
            if expression.args.get("limit"):
                sql += self.sql(expression.args['limit'])
            
            return sql

        def union_sql(self, expression: exp.Union) -> str:
            """处理UNION和多表合并语法"""
            # 检查是否是多表合并语法
            if expression.args.get("is_table_merge"):
                # 提取表名
                left_table = None
                right_part = None
                
                if isinstance(expression.this, exp.Select) and expression.this.args.get("from"):
                    left_table = expression.this.args["from"].this
                if isinstance(expression.expression, exp.Select) and expression.expression.args.get("from"):
                    right_expr = expression.expression.args["from"].this
                    # 如果右边也是Union（多表合并），递归处理
                    if isinstance(right_expr, exp.Union) and right_expr.args.get("is_table_merge"):
                        right_part = self.union_sql(right_expr)
                    else:
                        right_part = self.sql(right_expr)
                
                if left_table and right_part:
                    return f"{self.sql(left_table)} | {right_part}"
            
            # 普通UNION处理
            return super().union_sql(expression)

        def create_sql(self, expression: exp.Create) -> str:
            """生成CREATE语句，添加对炎凰SQL特性的支持"""
            from sqlglot import UnsupportedError
            
            # 检查是否是存储过程（LANGUAGE plpgsql等）
            if expression.kind == "FUNCTION":
                # 检查是否包含LANGUAGE plpgsql/sql等存储过程语法
                if hasattr(expression, 'properties') and expression.properties:
                    for prop in expression.properties.expressions:
                        if isinstance(prop, exp.SchemaCommentProperty) and hasattr(prop, 'this'):
                            if isinstance(prop.this, exp.Var) and prop.this.this.upper() in ('PLPGSQL', 'SQL'):
                                raise UnsupportedError("Stored procedures with LANGUAGE plpgsql/sql are not supported in Yanhuang SQL. Use table functions instead.")
                
                # 检查是否包含BEGIN/END块（存储过程特征）
                if hasattr(expression, 'expression') and expression.expression:
                    sql_text = str(expression.expression)
                    if 'BEGIN' in sql_text.upper() and 'END' in sql_text.upper():
                        raise UnsupportedError("Stored procedures with BEGIN/END blocks are not supported in Yanhuang SQL. Use table functions instead.")
            
            # 炎凰SQL的CREATE语句支持
            sql = super().create_sql(expression)
            
            # 如果是CREATE TABLE且有ENGINE信息，添加ENGINE子句
            if expression.args.get("kind") == "TABLE":
                engine = expression.args.get("engine")
                if engine:
                    sql += f" ENGINE={self.sql(engine)}"
                    
                # 如果有ENGINE属性，添加WITH子句
                engine_properties = expression.args.get("engine_properties")
                if engine_properties:
                    properties_sql = []
                    for prop in engine_properties:
                        prop_name = self.sql(prop.this)
                        prop_value = self.sql(prop.args.get("value"))
                        properties_sql.append(f"{prop_name}={prop_value}")
                    
                    sql += f" WITH ({', '.join(properties_sql)})"
            
            return sql

        def group_sql(self, expression: exp.Group) -> str:
            """生成GROUP BY语句，支持TIME()语法"""
            if not expression.expressions:
                return ""
            
            group_items = []
            for expr in expression.expressions:
                if isinstance(expr, exp.Anonymous) and expr.this == "TIME":
                    # 处理TIME()语法 - 使用与anonymous_sql相同的逻辑
                    # TIME函数的已知参数名列表（这些参数即使是关键字也不应该加引号）
                    TIME_PARAMS = {"start", "end", "column", "span", "alignment"}
                    
                    params = []
                    for param_expr in expr.expressions:
                        if isinstance(param_expr, exp.EQ):
                            # 处理参数名
                            left_expr = param_expr.this
                            param_name = None
                            
                            # 获取参数名的原始文本
                            if isinstance(left_expr, exp.Column) and isinstance(left_expr.this, exp.Identifier):
                                param_name = left_expr.this.this
                            elif isinstance(left_expr, exp.Identifier):
                                param_name = left_expr.this
                            elif hasattr(left_expr, 'name'):
                                param_name = left_expr.name
                            else:
                                param_name = str(left_expr)
                            
                            # 对于TIME函数的已知参数，强制不加引号
                            if param_name and param_name.lower() in TIME_PARAMS:
                                key = param_name  # 直接使用参数名，不加引号
                            else:
                                key = self.sql(left_expr)  # 其他情况使用标准生成
                            
                            value = self.sql(param_expr.expression)
                            params.append(f"{key}={value}")
                        elif isinstance(param_expr, exp.PropertyEQ):
                            # 对于PropertyEQ，直接使用this的名称，不加引号
                            if isinstance(param_expr.this, exp.Identifier):
                                key = param_expr.this.this  # 获取标识符的原始名称
                            else:
                                key = self.sql(param_expr.this)
                            value = self.sql(param_expr.expression)
                            params.append(f"{key}={value}")
                        else:
                            params.append(self.sql(param_expr))
                    group_items.append(f"TIME({', '.join(params)})")
                else:
                    group_items.append(self.sql(expr))
            
            return f"GROUP BY {', '.join(group_items)}"

        def tablesample_sql(
            self,
            expression: exp.TableSample,
            tablesample_keyword: t.Optional[str] = None,
        ) -> str:
            """
            生成表采样语句
            
            支持的语法：
            - SAMPLE BERNOULLI (percent)
            - SAMPLE BLOCK (percent)  
            - SAMPLE ROW (percent)
            - SAMPLE (percent)  - 默认为ROW方法
            """
            # 获取采样方法和百分比
            method = expression.args.get("method")
            percent = expression.args.get("percent")
            
            # 处理采样方法
            if method:
                method_name = method.name if hasattr(method, 'name') else str(method)
                if method_name == "BERNOULLI":
                    method_sql = "BERNOULLI"
                elif method_name == "BLOCK":
                    method_sql = "BLOCK"
                elif method_name == "ROW":
                    method_sql = "ROW"
                else:
                    method_sql = str(method)
            else:
                method_sql = "ROW"  # 默认方法
            
            percent_sql = self.sql(percent) if percent else "1.0"
            
            return f"SAMPLE {method_sql} ({percent_sql})"

        def unicodestring_sql(self, expression: exp.UnicodeString) -> str:
            """生成Unicode字符串SQL，保持原始转义格式"""
            value = expression.this
            escape_char = expression.args.get("escape")
            
            if escape_char:
                return f"U&'{value}' UESCAPE '{escape_char}'"
            else:
                return f"U&'{value}'"
                
        def show_sql(self, expression: exp.Show) -> str:
            """生成SHOW语句SQL"""
            parts = ["SHOW"]
            
            # 处理this参数（SHOW的目标，如TABLES）
            target = expression.this
            if target:
                if isinstance(target, exp.Literal):
                    parts.append(target.this)
                elif isinstance(target, exp.Var):
                    parts.append(target.this)
                else:
                    parts.append(self.sql(target))
            
            # 处理FROM子句
            from_table = expression.args.get("from")
            if from_table:
                parts.append("FROM")
                parts.append(self.sql(from_table))
            
            # 处理WHERE子句
            where = expression.args.get("where")
            if where:
                parts.append("WHERE")
                parts.append(self.sql(where))
                
            return " ".join(parts)

        def properties_sql(self, expression: exp.Properties) -> str:
            """生成属性SQL，支持炎凰SQL的ENGINE和WITH语法"""
            if not expression.expressions:
                return ""
            
            props = []
            with_props = []
            
            for prop in expression.expressions:
                if isinstance(prop, exp.EngineProperty):
                    props.append(f"ENGINE={self.sql(prop.this)}")
                else:
                    # 其他属性作为WITH子句的一部分
                    prop_name = self.sql(prop.this)
                    
                    # 正确的方式：通过args字典获取value参数
                    prop_value_expr = prop.args.get("value")
                    
                    if prop_value_expr is not None:
                        prop_value = self.sql(prop_value_expr)
                        with_props.append(f"{prop_name}={prop_value}")
                    else:
                        with_props.append(prop_name)
            
            result_parts = []
            if props:
                result_parts.extend(props)
            
            if with_props:
                with_clause = f"WITH ({', '.join(with_props)})"
                result_parts.append(with_clause)
            
            return " ".join(result_parts) if result_parts else ""
        
        def currenttimestamp_sql(self, expression: exp.CurrentTimestamp) -> str:
            """生成CURRENT_TIMESTAMP SQL
            
            炎凰SQL不支持CURRENT_TIMESTAMP，统一转换为NOW()函数。
            检查meta信息以确定原始函数类型：
            - meta["original_func"] = "CURRENT_TIMESTAMP" -> 保持原始语义
            - 其他情况 -> 默认为NOW()
            """
            # 检查是否有原始函数元数据
            original_func = expression.meta.get("original_func") if hasattr(expression, '_meta') and expression._meta else None
            
            if original_func == "CURRENT_TIMESTAMP":
                # 如果原始是CURRENT_TIMESTAMP，可能需要特殊处理
                # 但炎凰SQL仍然不支持CURRENT_TIMESTAMP，所以转换为NOW()
                return "NOW()"
            elif original_func == "NOW":
                # 如果原始是NOW()函数，保持NOW()
                return "NOW()"
            else:
                # 默认情况：炎凰SQL不支持CURRENT_TIMESTAMP，统一使用NOW()
                return "NOW()"

        def date_add_sql(self, expression: exp.DateAdd | exp.TsOrDsAdd) -> str:
            """生成炎凰数据的DATE_ADD函数SQL
            
            炎凰数据的DATE_ADD语法：
            - DATE_ADD(<time_unit>, <delta>) - 基于当前系统时间
            - DATE_ADD(<time_unit>, <delta>, <base_timestamp>) - 基于指定时间戳
            
            参数顺序与标准SQL不同：time_unit在前，delta在中间，base_timestamp在最后
            """
            # 从表达式中提取参数
            if isinstance(expression, exp.DateAdd):
                # DateAdd(this=base, expression=delta, unit=unit)
                base = expression.this
                delta = expression.expression
                unit = expression.args.get("unit")
            else:  # TsOrDsAdd
                # TsOrDsAdd(this=base, expression=delta, unit=unit)
                base = expression.this
                delta = expression.expression
                unit = expression.args.get("unit")
            
            # 处理时间单位
            if unit:
                unit_str = unit.name.lower() if hasattr(unit, 'name') else str(unit).lower()
                # 将完整单位名转换为炎凰数据的简写形式
                unit_mapping = {
                    'day': 'd', 'days': 'd',
                    'hour': 'h', 'hours': 'h', 
                    'minute': 'm', 'minutes': 'm',
                    'second': 's', 'seconds': 's',
                    'month': 'M', 'months': 'M',
                    'year': 'y', 'years': 'y'
                }
                unit_str = unit_mapping.get(unit_str, unit_str)
            else:
                unit_str = 'd'  # 默认为天
            
            # 生成SQL
            if base:
                # 三参数形式：DATE_ADD(<time_unit>, <delta>, <base_timestamp>)
                return self.func("DATE_ADD", f"'{unit_str}'", delta, base)
            else:
                # 二参数形式：DATE_ADD(<time_unit>, <delta>)
                return self.func("DATE_ADD", f"'{unit_str}'", delta)

        def date_diff_sql(self, expression: exp.DateDiff | exp.TsOrDsDiff) -> str:
            """生成炎凰数据的DATE_DIFF函数SQL
            
            炎凰数据的DATE_DIFF语法：
            DATE_DIFF(<time_unit>, <start_timestamp>, <end_timestamp>)
            计算 end_timestamp - start_timestamp
            """
            # 从表达式中提取参数
            if isinstance(expression, exp.DateDiff):
                # DateDiff(this=end, expression=start, unit=unit)
                end = expression.this
                start = expression.expression
                unit = expression.args.get("unit")
            else:  # TsOrDsDiff
                # TsOrDsDiff(this=end, expression=start, unit=unit)
                end = expression.this
                start = expression.expression
                unit = expression.args.get("unit")
            
            # 处理时间单位
            if unit:
                unit_str = unit.name.lower() if hasattr(unit, 'name') else str(unit).lower()
                # 将完整单位名转换为炎凰数据的简写形式
                unit_mapping = {
                    'day': 'd', 'days': 'd',
                    'hour': 'h', 'hours': 'h', 
                    'minute': 'm', 'minutes': 'm',
                    'second': 's', 'seconds': 's',
                    'month': 'M', 'months': 'M',
                    'year': 'y', 'years': 'y'
                }
                unit_str = unit_mapping.get(unit_str, unit_str)
            else:
                unit_str = 'd'  # 默认为天
            
            # 生成SQL：DATE_DIFF(<time_unit>, <start_timestamp>, <end_timestamp>)
            return self.func("DATE_DIFF", f"'{unit_str}'", start, end)

        def literal_sql(self, expression: exp.Literal) -> str:
            """处理字面量的SQL生成，特别是字符串转义"""
            if expression.is_string:
                value = expression.this
                # 使用双引号转义方式处理单引号
                escaped_value = value.replace("'", "''")
                return f"'{escaped_value}'"
            else:
                # 对于非字符串字面量，使用父类处理
                return super().literal_sql(expression)

            return text

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._compatibility_warnings = []

        def _warn_compatibility(self, feature: str, alternative: str = None):
            """发出兼容性警告"""
            msg = f"Yanhuang SQL doesn't support {feature}"
            if alternative:
                msg += f". Consider using {alternative} instead"
            
            logger.warning(msg)
            self._compatibility_warnings.append(msg)

        def _check_subquery_correlation(self, node: exp.Expression) -> bool:
            """检查子查询是否为相关子查询"""
            # 简化实现：检查子查询中是否引用了外层表的字段
            # 实际实现需要更复杂的作用域分析
            return False  # 暂时返回False，需要完整的实现

        # 重写相关方法以添加兼容性检查
        def in_sql(self, expression: exp.In) -> str:
            """处理IN子查询的兼容性检查"""
            if isinstance(expression.this, exp.Subquery):
                if self._check_subquery_correlation(expression.this):
                    self._warn_compatibility(
                        "correlated IN subqueries", 
                        "non-correlated subqueries"
                    )
            return super().in_sql(expression)

        def exists_sql(self, expression: exp.Exists) -> str:
            """处理EXISTS子查询的兼容性检查"""
            if self._check_subquery_correlation(expression.this):
                self._warn_compatibility(
                    "correlated EXISTS subqueries", 
                    "non-correlated subqueries"
                )
            # 确保EXISTS与括号之间有空格
            return f"EXISTS ({self.sql(expression, 'this')})"

        def cte_sql(self, expression: exp.CTE) -> str:
            """检查递归CTE"""
            if hasattr(expression, 'recursive') and expression.recursive:
                raise UnsupportedError("WITH RECURSIVE is not supported in Yanhuang SQL")
            return super().cte_sql(expression)

        def window_sql(self, expression: exp.Window) -> str:
            """检查窗口函数的兼容性"""
            # 检查WINDOW命名子句
            if hasattr(expression, 'alias') and expression.alias:
                self._warn_compatibility(
                    "WINDOW naming clause", 
                    "inline window specifications"
                )
            
            # 检查复杂的frame子句（修复：检查frame属性而不是kind）
            if hasattr(expression, 'frame') and expression.frame:
                frame = expression.frame
                if hasattr(frame, 'kind') and frame.kind and frame.kind.upper() not in ['ROWS']:
                    self._warn_compatibility(
                        f"{frame.kind} window frame", 
                        "ROWS frame"
                    )
            
            return super().window_sql(expression)

        def intersect_sql(self, expression: exp.Intersect) -> str:
            """INTERSECT不支持"""
            raise UnsupportedError("INTERSECT is not supported in Yanhuang SQL. Use INNER JOIN instead.")

        def except_sql(self, expression: exp.Except) -> str:
            """EXCEPT不支持"""
            raise UnsupportedError("EXCEPT is not supported in Yanhuang SQL. Use LEFT JOIN with NULL check instead.")

        def returning_sql(self, expression: exp.Returning) -> str:
            """RETURNING子句不支持"""
            raise UnsupportedError("RETURNING clause is not supported in Yanhuang SQL")

        def lateral_sql(self, expression: exp.Lateral) -> str:
            """LATERAL JOIN不支持"""
            self._warn_compatibility(
                "LATERAL JOIN", 
                "APPLY operator"
            )
            raise UnsupportedError("LATERAL JOIN is not supported. Use APPLY operator instead.")

        def datatype_sql(self, expression: exp.DataType) -> str:
            """检查不支持的数据类型"""
            unsupported_types = {
                'BYTEA', 'JSONB', 'HSTORE', 'ARRAY', 'ENUM', 
                'UUID', 'INET', 'CIDR', 'MACADDR', 'TSVECTOR'
            }
            
            # 修复：正确获取数据类型名称
            type_name = expression.this.name if hasattr(expression.this, 'name') else str(expression.this)
            
            if type_name.upper() in unsupported_types:
                self._warn_compatibility(
                    f"{type_name} data type",
                    "basic types (INT, STRING, FLOAT, DOUBLE, BOOLEAN)"
                )
                
            return super().datatype_sql(expression)

        def distinct_sql(self, expression: exp.Distinct) -> str:
            """检查聚合函数中的DISTINCT使用"""
            parent = expression.parent
            if isinstance(parent, exp.AggFunc) and not isinstance(parent, exp.Count):
                # 在GROUP BY上下文中，只有COUNT(DISTINCT)支持
                if self._in_group_by_context():
                    raise UnsupportedError(
                        f"DISTINCT in {parent.__class__.__name__} is not supported in GROUP BY context. "
                        "Only COUNT(DISTINCT ...) is supported."
                    )
            
            return super().distinct_sql(expression)

        def _in_group_by_context(self) -> bool:
            """检查是否在GROUP BY上下文中"""
            # 简化实现，实际需要检查AST树的上下文
            return False  # 需要完整实现

        def _convert_time_format(self, format_expr: exp.Expression) -> exp.Expression:
            """将PostgreSQL时间格式转换为炎凰数据格式
            
            PostgreSQL格式 → 炎凰数据格式映射：
            YYYY → %Y (4位年份)
            MM → %m (2位月份)
            DD → %d (2位日期)
            HH24 → %H (24小时制小时)
            HH12 → %I (12小时制小时)
            MI → %M (分钟)
            SS → %S (秒)
            MS → %f (微秒，6位)
            US → %f (微秒，6位)
            AM/PM → %p (AM/PM标识)
            TZ → %z (时区偏移)
            Day → %A (完整星期名)
            Month → %B (完整月份名)
            """
            if not isinstance(format_expr, exp.Literal):
                # 如果不是字面量，直接返回
                return format_expr
            
            format_str = format_expr.this
            if not isinstance(format_str, str):
                return format_expr
            
            # PostgreSQL到炎凰数据的格式映射
            # 注意：长的模式要放在前面，避免被短模式误匹配
            format_mapping = [
                ('YYYY', '%Y'),    # 4位年份
                ('HH24', '%H'),    # 24小时制小时
                ('HH12', '%I'),    # 12小时制小时
                ('Month', '%B'),   # 完整月份名
                ('Day', '%A'),     # 完整星期名
                ('Mon', '%b'),     # 简写月份名
                ('YY', '%y'),      # 2位年份
                ('MM', '%m'),      # 2位月份
                ('DD', '%d'),      # 2位日期
                ('HH', '%I'),      # 默认12小时制
                ('MI', '%M'),      # 分钟
                ('SS', '%S'),      # 秒
                ('MS', '%f'),      # 毫秒/微秒
                ('US', '%f'),      # 微秒
                ('AM', '%p'),      # AM/PM标识
                ('PM', '%p'),      # AM/PM标识
                ('TZ', '%Z'),      # 时区名称
                ('DY', '%a'),      # 简写星期名
                ('D', '%w'),       # 星期数字(0-6)
                ('WW', '%U'),      # 年中第几周
                ('W', '%W'),       # 年中第几周
                ('J', '%j'),       # 年中第几天
                ('Q', '%q'),       # 季度
            ]
            
            # 执行格式转换（按长度排序，长模式优先避免部分匹配）
            converted_format = format_str
            # 按长度降序排序，确保长模式先被替换
            sorted_mapping = sorted(format_mapping, key=lambda x: len(x[0]), reverse=True)
            for pg_format, yanhuang_format in sorted_mapping:
                converted_format = converted_format.replace(pg_format, yanhuang_format)
            
            # 后处理：修复PostgreSQL TIME_MAPPING造成的问题
            # PostgreSQL在解析时已经将Day中的D替换为%u，需要修复
            converted_format = converted_format.replace('%uay', '%A')  # Day -> %A
            converted_format = converted_format.replace('%uY', '%a')   # DY -> %a (如果有的话)
            
            # 返回转换后的字面量
            return exp.Literal.string(converted_format)

        def percentile_cont_sql(self, expression: exp.PercentileCont) -> str:
            """处理PERCENTILE_CONT函数的SQL生成"""
            # 获取分位数值
            fraction = expression.this
            
            # 检查是否为0.5的特殊情况（中位数）
            if (isinstance(fraction, exp.Literal) and 
                fraction.this == "0.5"):
                return "APPROX_MEDIAN_PLACEHOLDER"
            
            return f"QUANTILE_T_DIGEST_PLACEHOLDER({self.sql(fraction)})"

        def percentile_disc_sql(self, expression: exp.PercentileDisc) -> str:
            """处理PERCENTILE_DISC函数的SQL生成"""
            # 获取分位数值
            fraction = expression.this
            return f"QUANTILE_T_DIGEST_PLACEHOLDER({self.sql(fraction)})"

        def withingroup_sql(self, expression: exp.WithinGroup) -> str:
            """处理WITHIN GROUP子句的SQL生成"""
            
            # 获取内部函数和ORDER BY子句
            inner_func = expression.this
            order_expr = expression.expression
            
            if isinstance(inner_func, (exp.PercentileCont, exp.PercentileDisc)):
                # 获取分位数值
                fraction = inner_func.this
                
                # 获取排序列
                if isinstance(order_expr, exp.Order) and order_expr.expressions:
                    order_column = order_expr.expressions[0].this
                    
                    # 检查是否为PERCENTILE_CONT(0.5)的特殊情况
                    if (isinstance(inner_func, exp.PercentileCont) and 
                        isinstance(fraction, exp.Literal) and 
                        fraction.this == "0.5"):
                        return f"APPROX_MEDIAN({self.sql(order_column)})"
                    
                    # 一般情况：使用QUANTILE_T_DIGEST
                    return f"QUANTILE_T_DIGEST({self.sql(order_column)}, {self.sql(fraction)})"
            
            # 处理占位符情况
            if hasattr(inner_func, 'this') and isinstance(inner_func.this, str):
                if inner_func.this == "APPROX_MEDIAN_PLACEHOLDER":
                    if isinstance(order_expr, exp.Order) and order_expr.expressions:
                        order_column = order_expr.expressions[0].this
                        return f"APPROX_MEDIAN({self.sql(order_column)})"
                elif inner_func.this == "QUANTILE_T_DIGEST_PLACEHOLDER":
                    if isinstance(order_expr, exp.Order) and order_expr.expressions:
                        order_column = order_expr.expressions[0].this
                        if inner_func.expressions:
                            fraction = inner_func.expressions[0]
                            return f"QUANTILE_T_DIGEST({self.sql(order_column)}, {self.sql(fraction)})"
            
            # 默认情况
            return f"{self.sql(inner_func)} WITHIN GROUP ({self.sql(order_expr)})"

        def trim_sql(self, expression: exp.Trim) -> str:
            """处理TRIM函数的SQL生成，映射为LTRIM和RTRIM组合"""
            
            # 获取TRIM的参数
            this = expression.this  # 要处理的字符串
            position = expression.args.get("position")  # LEADING, TRAILING, BOTH
            expression_chars = expression.expression  # 要移除的字符
            
            # 如果没有指定字符，默认移除空格
            if not expression_chars:
                chars_sql = "' '"
            else:
                chars_sql = self.sql(expression_chars)
            
            string_sql = self.sql(this)
            
            # 根据position决定使用哪种TRIM方式
            if position:
                position_str = position.name if hasattr(position, 'name') else str(position)
                if position_str == "LEADING":
                    # TRIM(LEADING chars FROM string) -> LTRIM(string, chars)
                    return f"LTRIM({string_sql}, {chars_sql})"
                elif position_str == "TRAILING":
                    # TRIM(TRAILING chars FROM string) -> RTRIM(string, chars)
                    return f"RTRIM({string_sql}, {chars_sql})"
                elif position_str == "BOTH":
                    # TRIM(BOTH chars FROM string) -> LTRIM(RTRIM(string, chars), chars)
                    return f"LTRIM(RTRIM({string_sql}, {chars_sql}), {chars_sql})"
            
            # 默认情况：TRIM(string) -> LTRIM(RTRIM(string))
            if expression_chars:
                # TRIM(string, chars) -> LTRIM(RTRIM(string, chars), chars)
                return f"LTRIM(RTRIM({string_sql}, {chars_sql}), {chars_sql})"
            else:
                # TRIM(string) -> LTRIM(RTRIM(string))
                return f"LTRIM(RTRIM({string_sql}))"

        # 虚拟继承函数映射 - 基于炎凰数据实际支持的功能
        VIRTUAL_INHERITANCE_FUNCTIONS = {
            # === 聚合函数映射（基于炎凰数据明确支持的聚合函数）===
            "BOOL_AND": lambda self, e: self._bool_and_to_case_when(e),
            "BOOL_OR": lambda self, e: self._bool_or_to_case_when(e),
            "EVERY": lambda self, e: self._bool_and_to_case_when(e),  # EVERY等价于BOOL_AND
            
            # === 类型转换函数映射（基于炎凰数据CAST支持）===
            # 注意：SAFE_CAST和TRY_CAST在PostgreSQL中不是标准函数，需要特殊处理
            "SAFE_CAST": lambda self, e: self._safe_cast_to_cast(e),
            "TRY_CAST": lambda self, e: self._try_cast_to_cast(e),
            # CONVERT已在FUNCTIONS中映射，不在这里重复处理
            
            # === 分析函数映射（基于炎凰数据支持的聚合函数）===
            # 注意：这些函数在FUNCTIONS中没有映射，需要在anonymous_sql中处理
            "ARGMAX": lambda self, e: self._argmax_to_case_when(e),
            "ARGMIN": lambda self, e: self._argmin_to_case_when(e),
            "MAX_BY": lambda self, e: self._argmax_to_case_when(e),
            "MIN_BY": lambda self, e: self._argmin_to_case_when(e),
            
            # === 表函数映射（基于炎凰数据明确支持的表函数）===
            # 注意：UNNEST和EXPLODE在TRANSFORMS中已处理，这里作为备用
            "UNNEST": lambda self, e: self._unnest_to_flatten(e),
            "EXPLODE": lambda self, e: self._explode_to_flatten(e),
            
            # === 窗口函数映射（基于炎凰数据支持的窗口函数）===
            "PERCENT_RANK": lambda self, e: self._percent_rank_to_formula(e),
            "CUME_DIST": lambda self, e: self._cume_dist_to_formula(e),
            
            # === 不支持的函数 - 提供警告和替代建议 ===
            # 数学函数（炎凰数据不支持）
            "ATAN2": lambda self, e: self._warn_unsupported_math_function("ATAN2", e),
            "ATAN2D": lambda self, e: self._warn_unsupported_math_function("ATAN2D", e),
            "ATANH": lambda self, e: self._warn_unsupported_math_function("ATANH", e),
            
            # 编码函数（炎凰数据部分支持）
            # 注意：ENCODE已在FUNCTIONS中映射到BASE64_ENCODE，这里处理其他编码
            "URL_ENCODE": lambda self, e: self._warn_unsupported_encode_function("URL_ENCODE", e),
            
            # 系统函数（炎凰数据不支持）
            "CONNECTION_ID": lambda self, e: self._warn_unsupported_system_function("CONNECTION_ID", e),
            "DATABASE": lambda self, e: self._warn_unsupported_system_function("DATABASE", e),
            "SCHEMA": lambda self, e: self._warn_unsupported_system_function("SCHEMA", e),
            "USER": lambda self, e: self._warn_unsupported_system_function("USER", e),
            "VERSION": lambda self, e: self._warn_unsupported_system_function("VERSION", e),
        }

        def _bool_and_to_case_when(self, expression: exp.Anonymous) -> str:
            """将BOOL_AND转换为基于MIN和CASE WHEN的实现"""
            if not expression.expressions:
                return "TRUE"  # 空集的BOOL_AND结果为TRUE
            
            expr = expression.expressions[0]
            return f"(MIN(CASE WHEN {self.sql(expr)} THEN 1 ELSE 0 END) = 1)"

        def _bool_or_to_case_when(self, expression: exp.Anonymous) -> str:
            """将BOOL_OR转换为基于MAX和CASE WHEN的实现"""
            if not expression.expressions:
                return "FALSE"  # 空集的BOOL_OR结果为FALSE
            
            expr = expression.expressions[0]
            return f"(MAX(CASE WHEN {self.sql(expr)} THEN 1 ELSE 0 END) = 1)"

        def _safe_cast_to_cast(self, expression: exp.Anonymous) -> str:
            """将SAFE_CAST转换为CAST（炎凰数据不支持错误处理）"""
            if len(expression.expressions) < 2:
                return "NULL"
            
            value, target_type = expression.expressions[0], expression.expressions[1]
            # 处理类型名称，确保是有效的炎凰数据类型
            type_str = self.sql(target_type)
            if isinstance(target_type, exp.Identifier):
                type_str = target_type.this
            elif isinstance(target_type, exp.Var):
                type_str = target_type.this
            
            return f"CAST({self.sql(value)} AS {type_str})"

        def _try_cast_to_cast(self, expression: exp.Anonymous) -> str:
            """将TRY_CAST转换为CAST（炎凰数据不支持错误处理）"""
            return self._safe_cast_to_cast(expression)

        def _convert_to_cast(self, expression: exp.Anonymous) -> str:
            """将CONVERT转换为CAST"""
            if len(expression.expressions) < 2:
                return "NULL"
            
            # CONVERT通常是CONVERT(value, type)或CONVERT(type, value)
            # 假设第一个参数是值，第二个是类型
            value, target_type = expression.expressions[0], expression.expressions[1]
            return f"CAST({self.sql(value)} AS {self.sql(target_type)})"

        def _argmax_to_case_when(self, expression: exp.Anonymous) -> str:
            """将ARGMAX转换为基于窗口函数的实现"""
            if len(expression.expressions) < 2:
                return "NULL"
            
            id_expr, value_expr = expression.expressions[0], expression.expressions[1]
            # 使用FIRST_VALUE和ORDER BY实现ARGMAX
            return f"FIRST_VALUE({self.sql(id_expr)}) OVER (ORDER BY {self.sql(value_expr)} DESC)"

        def _argmin_to_case_when(self, expression: exp.Anonymous) -> str:
            """将ARGMIN转换为基于窗口函数的实现"""
            if len(expression.expressions) < 2:
                return "NULL"
            
            id_expr, value_expr = expression.expressions[0], expression.expressions[1]
            # 使用FIRST_VALUE和ORDER BY实现ARGMIN
            return f"FIRST_VALUE({self.sql(id_expr)}) OVER (ORDER BY {self.sql(value_expr)} ASC)"

        def _unnest_to_flatten(self, expression: exp.Anonymous) -> str:
            """将UNNEST转换为FLATTEN表函数"""
            if not expression.expressions:
                return "FLATTEN(ARRAY[])"
            
            array_expr = expression.expressions[0]
            return f"FLATTEN({self.sql(array_expr)})"

        def _explode_to_flatten(self, expression: exp.Anonymous) -> str:
            """将EXPLODE转换为FLATTEN表函数"""
            return self._unnest_to_flatten(expression)

        def _percent_rank_to_formula(self, expression: exp.Anonymous) -> str:
            """将PERCENT_RANK转换为基于ROW_NUMBER和COUNT的公式"""
            # PERCENT_RANK() = (ROW_NUMBER() - 1) / (COUNT(*) - 1)
            return "((ROW_NUMBER() OVER () - 1) / NULLIF(COUNT(*) OVER () - 1, 0))"

        def _cume_dist_to_formula(self, expression: exp.Anonymous) -> str:
            """将CUME_DIST转换为基于ROW_NUMBER和COUNT的公式"""
            # CUME_DIST() = ROW_NUMBER() / COUNT(*)
            return "(ROW_NUMBER() OVER () / COUNT(*) OVER ())"

        def _warn_unsupported_math_function(self, func_name: str, expression: exp.Anonymous) -> str:
            """为不支持的数学函数提供警告和替代方案"""
            alternatives = {
                "ATAN2": "使用 CASE WHEN x > 0 THEN ATAN(y/x) WHEN x < 0 AND y >= 0 THEN ATAN(y/x) + PI() ... END",
                "ATAN2D": "使用 DEGREES(ATAN2(...)) 的等价实现",
                "ATANH": "使用 0.5 * LN((1 + x) / (1 - x)) 公式实现"
            }
            
            alternative = alternatives.get(func_name, "请查阅炎凰数据文档寻找等效函数")
            
            print(f"⚠️  警告: {func_name}() 函数在炎凰数据中不支持")
            print(f"   替代方案: {alternative}")
            
            # 返回注释形式，保持SQL可执行性
            args_str = ", ".join(self.sql(arg) for arg in expression.expressions)
            return f"/* {func_name}不支持，建议: {alternative} */ NULL"

        def _warn_unsupported_encode_function(self, func_name: str, expression: exp.Anonymous) -> str:
            """为不支持的编码函数提供警告和替代方案"""
            alternatives = {
                "ENCODE": "炎凰数据仅支持BASE64编码，使用应用层处理其他编码",
                "URL_ENCODE": "炎凰数据仅支持URL_DECODE，建议在应用层进行URL编码"
            }
            
            alternative = alternatives.get(func_name, "请在应用层处理编码需求")
            
            print(f"⚠️  警告: {func_name}() 函数在炎凰数据中不支持")
            print(f"   替代方案: {alternative}")
            
            args_str = ", ".join(self.sql(arg) for arg in expression.expressions)
            return f"/* {func_name}不支持，建议: {alternative} */ NULL"

        def _warn_unsupported_system_function(self, func_name: str, expression: exp.Anonymous) -> str:
            """为不支持的系统函数提供警告和替代方案"""
            alternatives = {
                "CONNECTION_ID": "使用应用层生成唯一标识符",
                "DATABASE": "在应用层配置数据库名称",
                "SCHEMA": "在应用层配置模式名称",
                "USER": "在应用层获取用户信息",
                "VERSION": "查询炎凰数据系统表获取版本信息"
            }
            
            alternative = alternatives.get(func_name, "请在应用层处理系统信息需求")
            
            print(f"⚠️  警告: {func_name}() 函数在炎凰数据中不支持")
            print(f"   替代方案: {alternative}")
            
            return f"/* {func_name}不支持，建议: {alternative} */ NULL"

        def _unsupported_function_sql(self, func_name: str, expression: exp.Anonymous) -> str:
            """为完全不支持的函数提供警告和替代方案"""
            alternatives = {
                "JSON_OBJECT": "炎凰数据不支持JSON对象构造，建议在应用层处理JSON",
                "JSON_OBJECTAGG": "炎凰数据不支持JSON聚合，建议在应用层处理JSON",
                "JSON_TABLE": "炎凰数据不支持JSON表函数，建议使用JSON_POINTER函数",
                "JSONB_EXISTS": "炎凰数据不支持JSONB类型，建议使用JSON_POINTER函数",
                "XMLELEMENT": "炎凰数据不支持XML函数，建议在应用层处理XML",
                "XMLTABLE": "炎凰数据不支持XML表函数，建议在应用层处理XML",
                "GAP_FILL": "炎凰数据不支持时间序列填充，建议使用generate_series表函数",
                "OPENJSON": "炎凰数据不支持OPENJSON，建议使用JSON_POINTER函数",
                "NORMALIZE": "炎凰数据不支持Unicode规范化，建议在应用层处理",
                "OVERLAY": "炎凰数据不支持OVERLAY函数，建议使用REPLACE函数"
            }
            
            alternative = alternatives.get(func_name, "请查阅炎凰数据文档寻找等效函数")
            
            print(f"⚠️  警告: {func_name}() 函数在炎凰数据中不支持")
            print(f"   替代方案: {alternative}")
            
            # 返回注释形式，保持SQL可执行性
            args_str = ", ".join(self.sql(arg) for arg in expression.expressions)
            return f"/* {func_name}不支持，建议: {alternative} */ NULL"

# 添加兼容性检查函数
def check_yanhuang_compatibility(expression: exp.Expression) -> list[str]:
    """检查表达式的炎凰SQL兼容性"""
    warnings = []
    
    # 递归检查所有节点
    for node in expression.walk():
        if isinstance(node, exp.Recursive):
            warnings.append("WITH RECURSIVE is not supported")
        elif isinstance(node, exp.Intersect):
            warnings.append("INTERSECT is not supported")
        elif isinstance(node, exp.Except):
            warnings.append("EXCEPT is not supported")
        elif isinstance(node, exp.Returning):
            warnings.append("RETURNING clause is not supported")
        elif isinstance(node, exp.Lateral):
            warnings.append("LATERAL JOIN is not supported")
            
    return warnings
