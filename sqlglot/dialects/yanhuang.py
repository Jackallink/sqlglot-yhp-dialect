from __future__ import annotations

import typing as t

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

if t.TYPE_CHECKING:
    from sqlglot._typing import E


def _build_date_delta(expr_type: t.Type[E]) -> t.Callable[[t.List], E]:
    def _builder(args: t.List) -> E:
        expr = expr_type(
            this=seq_get(args, 2),
            expression=seq_get(args, 1),
            unit=map_date_part(seq_get(args, 0)),
        )
        if expr_type is exp.TsOrDsAdd:
            expr.set("return_type", exp.DataType.build("TIMESTAMP"))

        return expr

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


def _add_months_to_dateadd(args: t.List) -> exp.TsOrDsAdd:
    """将ADD_MONTHS函数降级映射为DATEADD函数
    
    ADD_MONTHS(date_col, 3) -> DATEADD('month', 3, date_col)
    """
    if len(args) != 2:
        # 如果参数不正确，返回原始调用
        return exp.Anonymous(this="ADD_MONTHS", expressions=args)
    
    date_expr, months_expr = args
    
    # 创建DATEADD表达式：DATEADD('month', months, date)
    return exp.TsOrDsAdd(
        this=date_expr,
        expression=months_expr,
        unit=exp.Literal.string("month")
    )


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

    # ref: https://docs.aws.amazon.com/redshift/latest/dg/r_FORMAT_strings.html
    TIME_FORMAT = "'YYYY-MM-DD HH24:MI:SS'"
    TIME_MAPPING = {**Postgres.TIME_MAPPING, "MON": "%b", "HH24": "%H", "HH": "%I"}
    
    # BYTE_START和BYTE_END由metaclass根据tokenizer的BYTE_STRINGS自动设置

    class Parser(Postgres.Parser):
        FUNCTIONS = {
            **Postgres.Parser.FUNCTIONS,
            # 添加降级映射：不支持的函数映射到支持的等价函数
            "EXTRACT": _extract_to_date_part,  # EXTRACT降级映射为DATE_PART
            "ADD_MONTHS": _add_months_to_dateadd,  # ADD_MONTHS降级映射为DATEADD
            "CONVERT_TIMEZONE": lambda args: build_convert_timezone(args, "UTC"),
            "DATEADD": _build_date_delta(exp.TsOrDsAdd),
            "DATE_ADD": _build_date_delta(exp.TsOrDsAdd),
            "DATEDIFF": _build_date_delta(exp.TsOrDsDiff),
            "DATE_DIFF": _build_date_delta(exp.TsOrDsDiff),
            "GETDATE": lambda args: _create_current_timestamp_with_func('GETDATE'),
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
            "CHAR_LENGTH": lambda args: exp.Length.from_arg_list(args),
            "CHARACTER_LENGTH": lambda args: exp.Length.from_arg_list(args),
            "LEFT": lambda args: exp.Left.from_arg_list(args),
            "RIGHT": lambda args: exp.Right.from_arg_list(args),
            "REVERSE": lambda args: exp.Anonymous(this="REVERSE", expressions=args),
            "REPEAT": lambda args: exp.Repeat.from_arg_list(args),
            "LPAD": lambda args: exp.Anonymous(this="LPAD", expressions=args),
            "RPAD": lambda args: exp.Anonymous(this="RPAD", expressions=args),
            "TRIM": lambda args: exp.Trim.from_arg_list(args),
            "LTRIM": lambda args: exp.Anonymous(this="LTRIM", expressions=args),
            "RTRIM": lambda args: exp.Anonymous(this="RTRIM", expressions=args),
            "REPLACE": lambda args: exp.Anonymous(this="REPLACE", expressions=args),
            "TRANSLATE": lambda args: exp.Anonymous(this="TRANSLATE", expressions=args),
            "ASCII": lambda args: exp.Anonymous(this="ASCII", expressions=args),
            "CHR": lambda args: exp.Anonymous(this="CHR", expressions=args),
            "INITCAP": lambda args: exp.Anonymous(this="INITCAP", expressions=args),
            "SPLIT_PART": lambda args: exp.Anonymous(this="SPLIT_PART", expressions=args),
            
            # 数学函数补充
            "ABS": lambda args: exp.Abs.from_arg_list(args),
            "CEIL": lambda args: exp.Ceil.from_arg_list(args),
            "CEILING": lambda args: exp.Ceil.from_arg_list(args),
            "FLOOR": lambda args: exp.Floor.from_arg_list(args),
            "ROUND": lambda args: exp.Round.from_arg_list(args),
            "SQRT": lambda args: exp.Sqrt.from_arg_list(args),
            "POWER": lambda args: exp.Pow.from_arg_list(args),
            "POW": lambda args: exp.Pow.from_arg_list(args),
            "MOD": lambda args: exp.Anonymous(this="MOD", expressions=args),
            "SIN": lambda args: exp.Anonymous(this="SIN", expressions=args),
            "COS": lambda args: exp.Anonymous(this="COS", expressions=args),
            "TAN": lambda args: exp.Anonymous(this="TAN", expressions=args),
            "ASIN": lambda args: exp.Anonymous(this="ASIN", expressions=args),
            "ACOS": lambda args: exp.Anonymous(this="ACOS", expressions=args),
            "ATAN": lambda args: exp.Anonymous(this="ATAN", expressions=args),
            "ATAN2": lambda args: exp.Anonymous(this="ATAN2", expressions=args),
            "LOG": lambda args: exp.Log.from_arg_list(args),
            "LOG10": lambda args: exp.Anonymous(this="LOG10", expressions=args),
            "LN": lambda args: exp.Ln.from_arg_list(args),
            "EXP": lambda args: exp.Exp.from_arg_list(args),
            "SIGN": lambda args: exp.Anonymous(this="SIGN", expressions=args),
            "TRUNC": lambda args: exp.Anonymous(this="TRUNC", expressions=args),
            "TRUNCATE": lambda args: exp.Anonymous(this="TRUNCATE", expressions=args),
            "RANDOM": lambda args: exp.Anonymous(this="RANDOM", expressions=args),
            "PI": lambda args: exp.Anonymous(this="PI", expressions=args),
            "DEGREES": lambda args: exp.Anonymous(this="DEGREES", expressions=args),
            "RADIANS": lambda args: exp.Anonymous(this="RADIANS", expressions=args),
            
            # 日期时间函数补充 - 仅保留炎凰数据明确支持的函数
            "NOW": lambda args: _create_current_timestamp_with_func('NOW'),
            "CURRENT_TIMESTAMP": lambda args: _create_current_timestamp_with_func('CURRENT_TIMESTAMP'),
            "CURRENT_DATE": exp.CurrentDate.from_arg_list,
            "CURRENT_TIME": exp.CurrentTime.from_arg_list,
            # 移除EXTRACT - 炎凰数据不支持此函数，只支持DATE_PART
            # "EXTRACT": exp.Extract.from_arg_list,
            "DATE_PART": lambda args: exp.Anonymous(this="DATE_PART", expressions=args),  # 保持原始函数名
            "DATE_TRUNC": lambda args: exp.Anonymous(this="DATE_TRUNC", expressions=args),
            "AGE": lambda args: exp.Anonymous(this="AGE", expressions=args),
            "TO_TIMESTAMP": lambda args: exp.Anonymous(this="TO_TIMESTAMP", expressions=args),
            "TO_DATE": lambda args: exp.Anonymous(this="TO_DATE", expressions=args),
            "TO_CHAR": lambda args: exp.Anonymous(this="TO_CHAR", expressions=args),
            "EPOCH": lambda args: exp.Anonymous(this="EPOCH", expressions=args),
            
            # 炎凰SQL特有的TIME函数（用于时间聚合，支持多参数）
            "TIME": lambda args: exp.Anonymous(this="TIME", expressions=args),
            
            # 条件函数 - 重写DECODE以避免转换为CASE
            "IF": lambda args: exp.If.from_arg_list(args),
            "DECODE": lambda args: exp.Anonymous(this="DECODE", expressions=args),
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
            "REGEX_REPLACE": lambda args: exp.Anonymous(this="REGEX_REPLACE", expressions=args),
            "IP_TO_COUNTRY": lambda args: exp.Anonymous(this="IP_TO_COUNTRY", expressions=args),
            "IP_TO_REGION": lambda args: exp.Anonymous(this="IP_TO_REGION", expressions=args),
            "IP_TO_CITY": lambda args: exp.Anonymous(this="IP_TO_CITY", expressions=args),
            "GEOHASH": lambda args: exp.Anonymous(this="GEOHASH", expressions=args),
            "GEOHASH_DECODE": lambda args: exp.Anonymous(this="GEOHASH_DECODE", expressions=args),
            "UUID": lambda args: exp.Anonymous(this="UUID", expressions=args),
            "MD5": lambda args: exp.Anonymous(this="MD5", expressions=args),
            "SHA1": lambda args: exp.Anonymous(this="SHA1", expressions=args),
            "SHA256": lambda args: exp.Anonymous(this="SHA256", expressions=args),
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
            "PERCENT_RANK": lambda args: exp.Anonymous(this="PERCENT_RANK", expressions=args),
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
            "EXPLODE": lambda args: exp.Anonymous(this="EXPLODE", expressions=args),
            "EXPLODE_OUTER": lambda args: exp.Anonymous(this="EXPLODE_OUTER", expressions=args),
            "POSEXPLODE": lambda args: exp.Anonymous(this="POSEXPLODE", expressions=args),
            "POSEXPLODE_OUTER": lambda args: exp.Anonymous(this="POSEXPLODE_OUTER", expressions=args),
            "UNNEST": lambda args: exp.Anonymous(this="UNNEST", expressions=args),
            
            # JSON函数支持
            "JSON_EXTRACT": lambda args: exp.Anonymous(this="JSON_EXTRACT", expressions=args),
            "JSON_EXTRACT_PATH_TEXT": lambda args: exp.Anonymous(this="JSON_EXTRACT_PATH_TEXT", expressions=args),
            "JSON_ARRAY_LENGTH": lambda args: exp.Anonymous(this="JSON_ARRAY_LENGTH", expressions=args),
            "JSON_OBJECT_KEYS": lambda args: exp.Anonymous(this="JSON_OBJECT_KEYS", expressions=args),
            "JSON_TYPEOF": lambda args: exp.Anonymous(this="JSON_TYPEOF", expressions=args),
            "JSON_VALID": lambda args: exp.Anonymous(this="JSON_VALID", expressions=args),
            "JSON_PRETTY": lambda args: exp.Anonymous(this="JSON_PRETTY", expressions=args),
            
            # 数组函数支持
            "ARRAY_LENGTH": lambda args: exp.Anonymous(this="ARRAY_LENGTH", expressions=args),
            "ARRAY_APPEND": lambda args: exp.Anonymous(this="ARRAY_APPEND", expressions=args),
            "ARRAY_PREPEND": lambda args: exp.Anonymous(this="ARRAY_PREPEND", expressions=args),
            "ARRAY_CAT": lambda args: exp.Anonymous(this="ARRAY_CAT", expressions=args),
            "ARRAY_POSITION": lambda args: exp.Anonymous(this="ARRAY_POSITION", expressions=args),
            "ARRAY_REMOVE": lambda args: exp.Anonymous(this="ARRAY_REMOVE", expressions=args),
            "ARRAY_REPLACE": lambda args: exp.Anonymous(this="ARRAY_REPLACE", expressions=args),
            "ARRAY_TO_STRING": lambda args: exp.Anonymous(this="ARRAY_TO_STRING", expressions=args),
            "STRING_TO_ARRAY": lambda args: exp.Anonymous(this="STRING_TO_ARRAY", expressions=args),
            
            # 其他工具函数
            "VERSION": lambda args: exp.Anonymous(this="VERSION", expressions=args),
            "USER": lambda args: exp.Anonymous(this="USER", expressions=args),
            "DATABASE": lambda args: exp.Anonymous(this="DATABASE", expressions=args),
            "SCHEMA": lambda args: exp.Anonymous(this="SCHEMA", expressions=args),
            "CONNECTION_ID": lambda args: exp.Anonymous(this="CONNECTION_ID", expressions=args),
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
                    this.set("unpack", True)
                    
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
        QUERY_HINTS = False
        VALUES_AS_TABLE = False
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
            exp.DataType.Type.BINARY: "VARBYTE",
            exp.DataType.Type.BLOB: "VARBYTE",
            exp.DataType.Type.INT: "INTEGER",
            exp.DataType.Type.TIMETZ: "TIME",
            exp.DataType.Type.TIMESTAMPTZ: "TIMESTAMP",
            exp.DataType.Type.VARBINARY: "VARBYTE",
            exp.DataType.Type.ROWVERSION: "VARBYTE",
            exp.DataType.Type.FLOAT: "FLOAT",
            exp.DataType.Type.DOUBLE: "DOUBLE",
            exp.DataType.Type.DECIMAL: "DECIMAL",
            exp.DataType.Type.BOOLEAN: "BOOLEAN",
        }

        TRANSFORMS = {
            **Postgres.Generator.TRANSFORMS,
            exp.ArrayConcat: lambda self, e: self.arrayconcat_sql(e, name="ARRAY_CONCAT"),
            exp.Concat: lambda self, e: self.func("CONCAT", *e.expressions),
            exp.ConcatWs: concat_ws_to_dpipe_sql,
            exp.ApproxDistinct: lambda self, e: f"APPROXIMATE COUNT(DISTINCT {self.sql(e, 'this')})",
            exp.CurrentTimestamp: lambda self, e: self.currenttimestamp_sql(e),
            exp.CurrentTime: lambda self, e: "CURRENT_TIME",  # 修复CURRENT_TIME不加括号
            exp.DateAdd: lambda self, e: self.date_add_sql(e),  # 使用炎凰语法
            exp.DateDiff: lambda self, e: self.date_diff_sql(e),  # 使用炎凰语法
            exp.Delete: lambda self, e: self.delete_sql(e),
            exp.DistKeyProperty: lambda self, e: self.func("DISTKEY", e.this),
            exp.DistStyleProperty: lambda self, e: self.naked_property(e),
            exp.Explode: lambda self, e: self.func("EXPLODE", e.this),
            exp.GeneratedAsIdentityColumnConstraint: generatedasidentitycolumnconstraint_sql,
            exp.GroupConcat: lambda self, e: self.func("STRING_AGG", e.this, e.args.get("separator")),
            exp.JSONExtract: lambda self, e: json_extract_segments("JSON_EXTRACT_PATH_TEXT")(self, e),
            exp.JSONExtractScalar: lambda self, e: json_extract_segments("JSON_EXTRACT_PATH_TEXT")(self, e),
            exp.JSONPathKey: lambda self, e: self.sql(e, "this"),
            exp.JSONPathRoot: lambda self, e: "",
            exp.JSONPathSubscript: lambda self, e: self.sql(e, "this"),
            exp.Lateral: lambda self, e: self.sql(e, "this"),
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
            exp.Returning: lambda self, e: "",
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
            
            # 表函数转换
            exp.ExplodingGenerateSeries: lambda self, e: self.func("GENERATE_SERIES", e.args.get("start"), e.args.get("end"), e.args.get("step")) if e.args.get("step") else self.func("GENERATE_SERIES", e.args.get("start"), e.args.get("end")),
            exp.Unnest: lambda self, e: self.func("UNNEST", *e.expressions) if e.expressions else self.func("UNNEST"),
            
            # 字符串函数转换
            exp.Substring: lambda self, e: self.func("SUBSTRING", e.this, e.args.get("start"), e.args.get("length")) if e.args.get("length") else self.func("SUBSTRING", e.this, e.args.get("start")),
            
            # 聚合函数转换 - 保持炎凰SQL原生函数名
            exp.GroupConcat: lambda self, e: self.func("STRING_AGG", e.this, e.args.get("separator")),
            
            # 字符串转义支持
            exp.UnicodeString: lambda self, e: self.unicodestring_sql(e),
            
            # 条件函数转换
            exp.If: lambda self, e: self.func("IF", e.this, e.args.get("true"), e.args.get("false")),
        }

        # Postgres maps exp.Pivot to no_pivot_sql, but Redshift support pivots
        TRANSFORMS.pop(exp.Pivot)

        # Postgres doesn't support JSON_PARSE, but Redshift does
        TRANSFORMS.pop(exp.ParseJSON)

        # Redshift supports these functions
        TRANSFORMS.pop(exp.AnyValue)
        TRANSFORMS.pop(exp.LastDay)
        TRANSFORMS.pop(exp.SHA2)

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
            args = expression.expressions
            num_args = len(args)

            if num_args != 1:
                self.unsupported(f"Unsupported number of arguments in UNNEST: {num_args}")
                return ""

            if isinstance(expression.find_ancestor(exp.From, exp.Join, exp.Select), exp.Select):
                self.unsupported("Unsupported UNNEST when not used in FROM/JOIN clauses")
                return ""

            arg = self.sql(seq_get(args, 0))

            alias = self.expressions(expression.args.get("alias"), key="columns", flat=True)
            return f"{arg} AS {alias}" if alias else arg

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

        def anonymous_sql(self, expression):
            """生成匿名函数SQL，保持表函数名原始大小写"""
            # 保持表函数名原始大小写
            func_name = expression.this
            
            # 特殊处理TIME函数的参数格式
            if func_name == "TIME":
                if expression.expressions:
                    # TIME函数的已知参数名列表（这些参数即使是关键字也不应该加引号）
                    TIME_PARAMS = {"start", "end", "column", "span", "alignment"}
                    
                    # 对于TIME函数，参数是key=value格式，不要在等号两边加空格
                    args = []
                    for expr in expression.expressions:
                        if isinstance(expr, exp.EQ):
                            # 处理参数名
                            left_expr = expr.this
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
                                left = param_name  # 直接使用参数名，不加引号
                            else:
                                left = self.sql(left_expr)  # 其他情况使用标准生成
                            
                            right = self.sql(expr.expression)
                            args.append(f"{left}={right}")
                        else:
                            args.append(self.sql(expr))
                    return f"{func_name}({', '.join(args)})"
            
            # 其他匿名函数的标准处理
            if expression.expressions:
                return f"{func_name}({self.expressions(expression, flat=True)})"
            else:
                return f"{func_name}()"

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
            # 保证EXISTS与括号之间有空格
            return f"EXISTS ({self.sql(expression, 'this')})"

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
            """生成CREATE语句SQL，支持炎凰SQL的ENGINE和WITH语法"""
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
            
            如果表达式在meta中存储了原始函数名，使用原始名称；
            否则使用CURRENT_TIMESTAMP
            """
            original_func = expression.meta.get("original_func")
            if original_func == "NOW":
                return "NOW()"
            return "CURRENT_TIMESTAMP"

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
