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

    class Parser(Postgres.Parser):
        FUNCTIONS = {
            **Postgres.Parser.FUNCTIONS,
            "ADD_MONTHS": lambda args: exp.TsOrDsAdd(
                this=seq_get(args, 0),
                expression=seq_get(args, 1),
                unit=exp.var("month"),
                return_type=exp.DataType.build("TIMESTAMP"),
            ),
            "CONVERT_TIMEZONE": lambda args: build_convert_timezone(args, "UTC"),
            "DATEADD": _build_date_delta(exp.TsOrDsAdd),
            "DATE_ADD": _build_date_delta(exp.TsOrDsAdd),
            "DATEDIFF": _build_date_delta(exp.TsOrDsDiff),
            "DATE_DIFF": _build_date_delta(exp.TsOrDsDiff),
            "GETDATE": exp.CurrentTimestamp.from_arg_list,
            "LISTAGG": exp.GroupConcat.from_arg_list,
            "SPLIT_TO_ARRAY": lambda args: exp.StringToArray(
                this=seq_get(args, 0), expression=seq_get(args, 1) or exp.Literal.string(",")
            ),
            "STRTOL": exp.FromBase.from_arg_list,
            "CAST": exp.Cast.from_arg_list,
            "CONTAINS": lambda args: exp.Anonymous(this="CONTAINS", expressions=args),
            
            # 字符串函数补充
            "SUBSTRING": lambda args: exp.Substring.from_arg_list(args),
            "SUBSTR": lambda args: exp.Substring.from_arg_list(args),  # 炎凰SQL支持SUBSTR别名
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
            
            # 日期时间函数补充
            "NOW": exp.CurrentTimestamp.from_arg_list,
            "CURRENT_TIMESTAMP": exp.CurrentTimestamp.from_arg_list,
            "CURRENT_DATE": exp.CurrentDate.from_arg_list,
            "CURRENT_TIME": exp.CurrentTime.from_arg_list,
            "EXTRACT": exp.Extract.from_arg_list,
            "DATE_PART": exp.Extract.from_arg_list,
            "DATE_TRUNC": lambda args: exp.Anonymous(this="DATE_TRUNC", expressions=args),
            "AGE": lambda args: exp.Anonymous(this="AGE", expressions=args),
            "TO_TIMESTAMP": lambda args: exp.Anonymous(this="TO_TIMESTAMP", expressions=args),
            "TO_DATE": lambda args: exp.Anonymous(this="TO_DATE", expressions=args),
            "TO_CHAR": lambda args: exp.Anonymous(this="TO_CHAR", expressions=args),
            "EPOCH": lambda args: exp.Anonymous(this="EPOCH", expressions=args),
            
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
        # 这样DECODE会使用FUNCTIONS字典中的匿名函数定义而不是_parse_decode方法
        FUNCTION_PARSERS = {
            **Postgres.Parser.FUNCTION_PARSERS,
        }
        FUNCTION_PARSERS.pop("DECODE", None)  # 移除DECODE的特殊解析方法

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

        def _parse_table(
            self,
            schema: bool = False,
            joins: bool = False,
            alias_tokens: t.Optional[t.Collection[TokenType]] = None,
            parse_bracket: bool = False,
            is_db_reference: bool = False,
            parse_partition: bool = False,
        ) -> t.Optional[exp.Expression]:
            main_table = super()._parse_table(
                schema=schema,
                joins=False,
                alias_tokens=alias_tokens,
                parse_bracket=parse_bracket,
                is_db_reference=is_db_reference,
                parse_partition=parse_partition,
            )
            
            # 检查多表合并语法 table1 | table2
            if self._match(TokenType.PIPE):
                # 创建一个特殊的表达式来表示多表合并
                right_table = self._parse_table(
                    schema=schema,
                    joins=False,
                    alias_tokens=alias_tokens,
                    parse_bracket=parse_bracket,
                    is_db_reference=is_db_reference,
                    parse_partition=parse_partition,
                )
                if right_table:
                    # 使用Union来表示多表合并，但标记为特殊类型
                    union_expr = self.expression(
                        exp.Union,
                        this=exp.select("*").from_(main_table),
                        expression=exp.select("*").from_(right_table),
                        distinct=False
                    )
                    # 标记这是多表合并而不是普通UNION
                    union_expr.set("is_table_merge", True)
                    return union_expr
            
            joins_list = []
            while True:
                if self._match_texts(["APPLY", "OUTER APPLY", "CROSS APPLY"]):
                    op = self._prev.text.upper()
                    cross_apply = None
                    if op == "OUTER APPLY":
                        cross_apply = False
                    elif op == "CROSS APPLY":
                        cross_apply = True
                    
                    if self._match(TokenType.L_PAREN):
                        # 解析子查询
                        select_expr = self._parse_select(nested=True, parse_subquery_alias=False)
                        self._match(TokenType.R_PAREN)
                        
                        # 解析AS alias
                        alias = None
                        if self._match_texts(["AS"]):
                            pass  # AS关键字已经消费掉了
                        if self._curr and self._curr.token_type in (TokenType.VAR, TokenType.IDENTIFIER):
                            alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
                        
                        if not alias:
                            self.raise_error("APPLY子查询必须指定别名，如APPLY (SELECT ...) AS alias")
                        
                        right = self.expression(exp.Subquery, this=select_expr, alias=alias)
                    else:
                        right = self._parse_table()
                        alias = self._parse_table_alias(alias_tokens=alias_tokens or self.TABLE_ALIAS_TOKENS)
                    
                    lateral = self.expression(
                        exp.Lateral,
                        this=right,
                        cross_apply=cross_apply,
                    )
                    join = self.expression(exp.Join, this=lateral)
                    joins_list.append(join)
                else:
                    break
            if joins:
                for join in self._parse_joins():
                    joins_list.append(join)
            if main_table is not None and joins_list:
                for join in joins_list:
                    main_table.append("joins", join)
            return main_table

        def _parse_convert(
            self, strict: bool, safe: t.Optional[bool] = None
        ) -> t.Optional[exp.Expression]:
            to = self._parse_types()
            this = self._parse_bitwise()
            return self.expression(exp.TryCast, this=this, to=to, safe=safe)

        def _parse_approximate_count(self) -> t.Optional[exp.ApproxDistinct]:
            index = self._index - 1
            func = self._parse_function()

            if isinstance(func, exp.Count) and isinstance(func.this, exp.Distinct):
                return self.expression(exp.ApproxDistinct, this=seq_get(func.this.expressions, 0))
            self._retreat(index)
            return None

        def _parse_alias(self, this: t.Optional[exp.Expression], explicit: bool = False) -> t.Optional[exp.Alias]:
            """Override to track explicit AS keyword usage"""
            # 先检查是否有AS关键字，但不消费它
            has_as_keyword = self._match(TokenType.ALIAS, advance=False)
            
            # 调用父类方法来处理别名解析，它会正确处理AS关键字
            alias = super()._parse_alias(this, explicit)
            
            # 如果解析成功且有AS关键字，设置标记
            if alias and has_as_keyword and isinstance(alias, exp.Alias):
                alias.set("explicit_as", True)
                
            return alias

        def _parse_projections(self) -> t.List[exp.Expression]:
            if self._match_texts(["COLUMNS"]):
                # COLUMNS('regex')
                this = self._parse_wrapped(self._parse_string)
                columns = self.expression(exp.Columns, this=this)
                # EXCEPT (f1, f2)
                if self._match_texts(["EXCEPT"]):
                    self._match_l_paren()
                    excepts = self._parse_csv(self._parse_id_var)
                    if not excepts:
                        self.raise_error("COLUMNS EXCEPT子句不能为空")
                    self._match_r_paren()
                    columns.set("except", excepts)
                # REPLACE (expr AS col, ...)
                if self._match_texts(["REPLACE"]):
                    self._match_l_paren()
                    replaces = self._parse_csv(lambda: self._parse_alias(self._parse_expression()))
                    if not replaces:
                        self.raise_error("COLUMNS REPLACE子句不能为空")
                    # 验证REPLACE中的表达式
                    for replace in replaces:
                        if not isinstance(replace, exp.Alias):
                            self.raise_error("COLUMNS REPLACE子句必须包含AS别名表达式")
                    self._match_r_paren()
                    columns.set("replace", replaces)
                # AS "host_{0}"/AS ...
                if self._match_texts(["AS"]):
                    # 兼容字符串、双引号标识符和普通标识符
                    if self._curr and self._curr.token_type == TokenType.STRING:
                        alias = self._parse_string()
                    elif self._curr and self._curr.token_type in (TokenType.IDENTIFIER, TokenType.VAR):
                        alias = self._parse_id_var()
                    elif self._curr and self._curr.token_type == TokenType.NUMBER:
                        # 数字不能作为别名
                        self.raise_error("COLUMNS AS后不能使用数字作为别名")
                    else:
                        # 尝试解析双引号标识符 - sqlglot会自动处理引号
                        try:
                            alias = self._parse_id_var()
                        except:
                            self.raise_error("COLUMNS AS后必须为字符串或标识符")
                    columns.set("alias", alias)
                return [columns]
            # 其它主流投影走PG，但补充省略AS的写法
            projections = []
            while True:
                expr = self._parse_expression()
                if expr is None:
                    break
                
                # 使用 _parse_alias 处理别名
                alias = self._parse_alias(expr)
                if alias:
                    projections.append(alias)
                else:
                    projections.append(expr)
                    
                if not self._match(TokenType.COMMA):
                    break
            return projections

        def _parse_with(self, skip_with_token: bool = False) -> t.Optional[exp.With]:
            if not skip_with_token and not self._match(TokenType.WITH):
                return None

            comments = self._prev_comments
            if self._match(TokenType.RECURSIVE):
                self.raise_error("炎凰SQL不支持WITH RECURSIVE递归CTE")
            last_comments = None
            expressions = []
            while True:
                cte = self._parse_cte()
                if isinstance(cte, exp.CTE):
                    expressions.append(cte)
                    if last_comments:
                        cte.add_comments(last_comments)
                if not self._match(TokenType.COMMA) and not self._match(TokenType.WITH):
                    break
                else:
                    self._match(TokenType.WITH)
                last_comments = self._prev_comments
            return self.expression(
                exp.With,
                comments=comments,
                expressions=expressions,
                recursive=False,
                search=None,
            )

        def _parse_statement(self):
            """解析语句并应用炎凰SQL特定的转换和限制检查"""
            # 直接回退到父类实现，避免复杂的自定义逻辑导致问题
            try:
                statement = super()._parse_statement()
                if statement is None:
                    return None
                
                # 对所有语句都应用集合操作检查
                statement = self._check_unsupported_set_operations(statement)
                
                # 根据语句类型应用特定检查
                if isinstance(statement, exp.Select):
                    statement = self._apply_window_function_transforms(statement)
                    statement = self._check_unsupported_window_features(statement)
                    statement = self._check_correlated_subqueries(statement)
                    statement = self._check_window_function_restrictions(statement)
                    statement = self._check_tablesample_limitations(statement)
                    statement = self._check_distinct_limitations(statement)
                    statement = self._check_complex_types(statement)
                elif isinstance(statement, exp.Delete):
                    statement = self._check_delete_limitations(statement)
                    statement = self._check_complex_types(statement)
                elif isinstance(statement, exp.Create):
                    statement = self._check_table_ddl_limitations(statement)
                    statement = self._check_complex_types(statement)
                else:
                    # 对其他类型的语句也检查复杂类型
                    statement = self._check_complex_types(statement)
                
                return statement
            except AttributeError as e:
                if "'NoneType' object has no attribute 'add_comments'" in str(e):
                    # 如果父类返回None但尝试调用add_comments，返回None
                    return None
                raise

        def _apply_window_function_transforms(self, statement):
            """应用窗口函数兼容性转换（智能降级）"""
            if not isinstance(statement, exp.Select):
                return statement
            
            # 1. 转换ORDER BY中的窗口函数
            statement = self._transform_order_by_window_functions(statement)
            
            # 2. 转换窗口函数运算表达式
            statement = self._transform_window_function_arithmetic(statement)
            
            # 3. 转换WINDOW子句为内联OVER子句
            statement = self._transform_window_clauses(statement)
            
            return statement

        def _transform_order_by_window_functions(self, statement):
            """转换ORDER BY中的窗口函数为子查询"""
            if not statement.args.get("order"):
                return statement
            
            window_expressions = []
            for order_expr in statement.args["order"].expressions:
                windows = list(order_expr.find_all(exp.Window))
                if windows:
                    window_expressions.extend(windows)
            
            if not window_expressions:
                return statement
            
            # 创建窗口函数表达式别名
            window_aliases = []
            for i, window_expr in enumerate(window_expressions):
                alias_name = f"__window_expr_{i + 1}"
                window_aliases.append((window_expr, alias_name))
            
            # 修改SELECT投影，添加窗口函数
            new_expressions = list(statement.expressions or [])
            for window_expr, alias_name in window_aliases:
                alias = self.expression(exp.Alias, this=window_expr.copy(), alias=alias_name)
                new_expressions.append(alias)
            
            # 修改ORDER BY，替换窗口函数为别名引用
            new_order_expressions = []
            for order_expr in statement.args["order"].expressions:
                new_expr = order_expr.copy()
                # 使用transform方法来替换窗口函数
                for window_expr, alias_name in window_aliases:
                    def replace_window(node):
                        if node == window_expr:
                            return exp.Column(this=alias_name)
                        return node
                    new_expr = new_expr.transform(replace_window)
                new_order_expressions.append(new_expr)
            
            # 创建子查询
            inner_select = statement.copy()
            inner_select.set("expressions", new_expressions)
            inner_select.set("order", None)  # 移除内层ORDER BY
            
            # 创建外层查询
            outer_select = self.expression(
                exp.Select,
                expressions=[exp.Star()],
                **{"from": self.expression(exp.From, this=self.expression(exp.Subquery, this=inner_select, alias="__window_subquery"))}
            )
            
            # 设置新的ORDER BY
            outer_select.set("order", self.expression(exp.Order, expressions=new_order_expressions))
            
            # 保留其他子句（如LIMIT等）
            for clause in ["limit", "offset"]:
                if statement.args.get(clause):
                    outer_select.set(clause, statement.args[clause])
                    inner_select.set(clause, None)
            
            return outer_select

        def _transform_window_function_arithmetic(self, statement):
            """转换窗口函数运算表达式为子查询"""
            window_expressions = []
            
            # 查找所有包含窗口函数运算的表达式
            for expr in statement.expressions or []:
                windows_in_arithmetic = self._find_window_arithmetic_expressions(expr)
                window_expressions.extend(windows_in_arithmetic)
            
            if not window_expressions:
                return statement
            
            # 为每个窗口函数创建别名
            window_aliases = []
            for i, window_expr in enumerate(window_expressions):
                alias_name = f"__window_expr_{i + 1}"
                window_aliases.append((window_expr, alias_name))
            
            # 修改SELECT投影
            new_expressions = []
            for expr in statement.expressions or []:
                new_expr = expr.copy()
                # 替换窗口函数运算为分离的表达式
                for window_expr, alias_name in window_aliases:
                    def replace_window(node):
                        if node == window_expr:
                            return exp.Column(this=alias_name)
                        return node
                    new_expr = new_expr.transform(replace_window)
                new_expressions.append(new_expr)
            
            # 创建子查询
            inner_select = statement.copy()
            inner_select.set("expressions", [exp.Star()] + [
                self.expression(exp.Alias, this=window_expr.copy(), alias=alias_name)
                for window_expr, alias_name in window_aliases
            ])
            
            # 创建外层查询
            outer_select = self.expression(
                exp.Select,
                expressions=new_expressions,
                **{"from": self.expression(exp.From, this=self.expression(exp.Subquery, this=inner_select, alias="__window_subquery"))}
            )
            
            # 复制其他子句
            for clause in ["where", "group", "having", "order", "limit", "offset"]:
                if statement.args.get(clause):
                    outer_select.set(clause, statement.args[clause])
            
            return outer_select

        def _find_window_arithmetic_expressions(self, expr):
            """查找表达式中的窗口函数运算"""
            windows = []
            
            if expr is None:
                return windows
            
            # 只在运算表达式中查找窗口函数，不处理单独的窗口函数
            if isinstance(expr, exp.Binary):
                # 检查左右操作数是否为窗口函数 - 这才是真正的窗口函数运算
                left_is_window = isinstance(expr.this, exp.Window)
                right_is_window = isinstance(expr.expression, exp.Window)
                
                if left_is_window or right_is_window:
                    # 这是窗口函数参与的运算，需要转换
                    if left_is_window:
                        windows.append(expr.this)
                    if right_is_window:
                        windows.append(expr.expression)
                else:
                    # 递归检查子表达式中的窗口函数运算
                    windows.extend(self._find_window_arithmetic_expressions(expr.this))
                    windows.extend(self._find_window_arithmetic_expressions(expr.expression))
            elif isinstance(expr, exp.Unary):
                # 一元运算符作用于窗口函数
                if isinstance(expr.this, exp.Window):
                    windows.append(expr.this)
                else:
                    windows.extend(self._find_window_arithmetic_expressions(expr.this))
            # 不要将单独的窗口函数视为需要转换的情况
            # elif isinstance(expr, exp.Window):
            #     # 直接是窗口函数 - 这是标准用法，不需要转换
            #     pass
            elif hasattr(expr, 'expressions') and expr.expressions is not None:
                # 有expressions属性的表达式类型（如Coalesce, Anonymous等）
                try:
                    for sub_expr in expr.expressions:
                        windows.extend(self._find_window_arithmetic_expressions(sub_expr))
                except TypeError:
                    # 如果expressions不可迭代，跳过
                    pass
            elif hasattr(expr, 'args') and expr.args:
                # 通过args属性遍历其他子表达式
                for key, value in expr.args.items():
                    if isinstance(value, exp.Expression):
                        windows.extend(self._find_window_arithmetic_expressions(value))
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, exp.Expression):
                                windows.extend(self._find_window_arithmetic_expressions(item))
            
            return windows

        def _transform_window_clauses(self, statement):
            """转换WINDOW子句为内联OVER子句"""
            if not statement.args.get("windows"):
                return statement
            
            # 获取WINDOW定义
            window_definitions = {}
            for window_def in statement.args["windows"]:
                if hasattr(window_def, 'this'):
                    # window_def是Window对象，this是窗口名
                    window_name = str(window_def.this)
                    window_definitions[window_name] = window_def
            
            # 在SELECT投影中查找窗口函数引用
            new_expressions = []
            for expr in statement.expressions or []:
                def replace_window_refs(node):
                    if isinstance(node, exp.Window):
                        # 检查是否是窗口名引用（如 COUNT(*) OVER w）
                        # 在这种情况下，alias字段存储的是窗口名引用
                        if (hasattr(node, 'alias') and node.alias and 
                            str(node.alias) in window_definitions and
                            node.args.get('over') == 'OVER' and
                            not node.args.get('partition_by') and 
                            not node.args.get('order')):
                            # 这是一个窗口引用，用窗口定义替换
                            window_def = window_definitions[str(node.alias)]
                            new_window = node.copy()
                            # 复制窗口规格到新窗口函数
                            if window_def.args.get('partition_by'):
                                new_window.set('partition_by', window_def.args['partition_by'])
                            if window_def.args.get('order'):
                                new_window.set('order', window_def.args['order'])
                            if window_def.args.get('spec'):
                                new_window.set('spec', window_def.args['spec'])
                            # 移除窗口名引用
                            new_window.set('alias', None)
                            return new_window
                    return node
                
                new_expr = expr.transform(replace_window_refs)
                new_expressions.append(new_expr)
            
            # 创建新的语句，移除WINDOW子句
            new_statement = statement.copy()
            new_statement.set("expressions", new_expressions)
            new_statement.set("windows", None)
            
            return new_statement

        def _check_unsupported_window_features(self, statement):
            """检查无法降级的窗口函数功能"""
            if statement is None:
                return None
                
            def check_node(node):
                if isinstance(node, exp.Window):
                    # 检查RANGE框架
                    spec = node.args.get("spec")
                    if spec and hasattr(spec, 'args'):
                        # spec.args中包含kind信息
                        kind_str = spec.args.get('kind')
                        
                        if kind_str == "RANGE":
                            self.raise_error("RANGE window frames are not supported in Yanhuang SQL, use ROWS instead")
                        elif kind_str == "GROUPS":
                            self.raise_error("GROUPS window frames are not supported in Yanhuang SQL, use ROWS instead")
                
                return node
            
            return statement.transform(check_node)

        def _check_correlated_subqueries(self, statement):
            """检查关联子查询限制"""
            # 暂时简化：跳过复杂的关联子查询检查
            # 这个功能需要更深入的AST分析，暂时禁用
            return statement

        def _check_window_function_restrictions(self, statement):
            """检查窗口函数使用限制"""
            if statement is None:
                return None
                
            def check_node(node):
                # 简化：暂时跳过复杂的窗口函数限制检查
                return node
            
            return statement.transform(check_node)

        def _check_unsupported_set_operations(self, statement):
            """检查不支持的集合操作"""
            if statement is None:
                return None
                
            def check_node(node):
                if isinstance(node, exp.Intersect):
                    self.raise_error("INTERSECT is not supported in Yanhuang SQL")
                elif isinstance(node, exp.Except):
                    self.raise_error("EXCEPT is not supported in Yanhuang SQL")
                
                return node
            
            return statement.transform(check_node)

        def _check_tablesample_limitations(self, statement):
            """检查TABLESAMPLE限制"""
            if statement is None:
                return None
                
            # 炎凰SQL现在支持SAMPLE语法，不再需要检查TableSample
            # 只检查原始的TABLESAMPLE关键字使用（这个在tokenizer层面处理）
            return statement

        def _check_distinct_limitations(self, statement):
            """检查DISTINCT使用限制"""
            if statement is None:
                return None
                
            def check_node(node):
                if isinstance(node, exp.Select) and node.args.get("group"):
                    # 检查GROUP BY查询中的聚合DISTINCT限制
                    for expr in node.expressions:
                        self._check_aggregate_distinct_in_group_by(expr)
                
                return node
            
            return statement.transform(check_node)

        def _check_aggregate_distinct_in_group_by(self, expr):
            """检查GROUP BY中的聚合DISTINCT限制"""
            def check_agg_node(node):
                if isinstance(node, (exp.Sum, exp.Avg, exp.Min, exp.Max)) and isinstance(node.this, exp.Distinct):
                    self.raise_error(f"炎凰SQL在GROUP BY中不支持{node.__class__.__name__}(DISTINCT ...)")
                # COUNT(DISTINCT)是允许的，不检查
                for child in node.iter_expressions():
                    check_agg_node(child)
            
            check_agg_node(expr)

        def _check_delete_limitations(self, statement):
            """检查DELETE语句限制"""
            if statement is None:
                return None
                
            def check_node(node):
                if isinstance(node, exp.Delete):
                    # 检查RETURNING子句
                    if node.args.get("returning"):
                        self.raise_error("DELETE RETURNING is not supported in Yanhuang SQL")
                    
                    # 检查USING子句
                    if node.args.get("using"):
                        self.raise_error("DELETE USING is not supported in Yanhuang SQL")
                
                return node
            
            return statement.transform(check_node)

        def _check_table_ddl_limitations(self, statement):
            """检查表DDL限制"""
            if statement is None:
                return None
                
            def check_node(node):
                if isinstance(node, exp.Create) and node.args.get("kind") == "TABLE":
                    # 检查schema中的约束
                    schema = node.args.get("this")  # schema在this字段中
                    if schema and isinstance(schema, exp.Schema) and hasattr(schema, 'expressions'):
                        for expr in schema.expressions:
                            if isinstance(expr, exp.ColumnDef):
                                # 检查列级约束
                                constraints = expr.args.get("constraints", [])
                                for constraint in constraints:
                                    if isinstance(constraint, exp.ColumnConstraint):
                                        kind = constraint.args.get("kind")
                                        if isinstance(kind, exp.PrimaryKeyColumnConstraint):
                                            self.raise_error("PRIMARY KEY constraints are not supported in Yanhuang SQL")
                                        elif isinstance(kind, exp.Reference):
                                            self.raise_error("FOREIGN KEY constraints are not supported in Yanhuang SQL")
                                        elif isinstance(kind, exp.UniqueColumnConstraint):
                                            self.raise_error("UNIQUE constraints are not supported in Yanhuang SQL")
                                        elif isinstance(kind, exp.CheckColumnConstraint):
                                            self.raise_error("CHECK constraints are not supported in Yanhuang SQL")
                                    # 直接的约束类型（不在ColumnConstraint包装中）
                                    elif isinstance(constraint, exp.PrimaryKeyColumnConstraint):
                                        self.raise_error("PRIMARY KEY constraints are not supported in Yanhuang SQL")
                                    elif isinstance(constraint, exp.Reference):
                                        self.raise_error("FOREIGN KEY constraints are not supported in Yanhuang SQL")
                                    elif isinstance(constraint, exp.UniqueColumnConstraint):
                                        self.raise_error("UNIQUE constraints are not supported in Yanhuang SQL")
                                    elif isinstance(constraint, exp.CheckColumnConstraint):
                                        self.raise_error("CHECK constraints are not supported in Yanhuang SQL")
                            # 表级约束
                            elif isinstance(expr, exp.PrimaryKey):
                                self.raise_error("PRIMARY KEY constraints are not supported in Yanhuang SQL")
                            elif isinstance(expr, exp.ForeignKey):
                                self.raise_error("FOREIGN KEY constraints are not supported in Yanhuang SQL")
                            elif isinstance(expr, exp.Unique):
                                self.raise_error("UNIQUE constraints are not supported in Yanhuang SQL")
                            elif isinstance(expr, exp.Check):
                                self.raise_error("CHECK constraints are not supported in Yanhuang SQL")
                
                return node
            
            return statement.transform(check_node)

        def _check_complex_types(self, statement):
            """检查复杂类型使用限制"""
            if statement is None:
                return None
                
            def check_node(node):
                # 检查ARRAY类型和字面量
                if isinstance(node, exp.Array):
                    self.raise_error("ARRAY types are not supported in Yanhuang SQL")
                elif isinstance(node, exp.DataType):
                    # 检查数据类型
                    type_name = node.this
                    if isinstance(type_name, exp.DataType.Type):
                        type_str = type_name.value
                    else:
                        type_str = str(type_name).upper()
                    
                    # 移除VARBINARY，因为炎凰SQL支持VARBINARY
                    unsupported_types = ['JSONB', 'JSON', 'BYTEA', 'ARRAY', 'HSTORE', 'UUID']
                    if type_str in unsupported_types:
                        self.raise_error(f"{type_str} type is not supported in Yanhuang SQL")
                
                # 检查PostgreSQL特有的类型转换语法
                elif isinstance(node, exp.Cast):
                    to_type = node.args.get("to")
                    if to_type and isinstance(to_type, exp.DataType):
                        type_name = to_type.this
                        if isinstance(type_name, exp.DataType.Type):
                            type_str = type_name.value
                        else:
                            type_str = str(type_name).upper()
                        
                        # 检查不支持的类型转换，但VARBINARY是支持的
                        unsupported_types = ['JSONB', 'JSON', 'BYTEA', 'ARRAY']
                        if type_str in unsupported_types:
                            self.raise_error(f"Casting to {type_str} type is not supported in Yanhuang SQL")
                
                return node
            
            return statement.transform(check_node)

        def _parse_describe(self) -> t.Optional[exp.Describe]:
            """解析DESCRIBE语句"""
            self._match(TokenType.DESCRIBE)
            return self.expression(
                exp.Describe,
                this=self._parse_table()
            )

        def _parse_delete(self) -> exp.Delete:
            """
            解析DELETE语句，支持炎凰SQL的增强语法：
            DELETE FROM table WHERE condition ORDER BY column LIMIT number
            """
            # 先调用父类的DELETE解析器
            delete_stmt = super()._parse_delete()
            
            # 如果父类解析成功，检查并添加ORDER BY和LIMIT支持
            if delete_stmt:
                # 检查是否有ORDER BY（父类可能没有解析）
                if not delete_stmt.args.get("order"):
                    order = self._parse_order()
                    if order:
                        delete_stmt.set("order", order)
                
                # 检查是否有LIMIT（父类可能没有解析）
                if not delete_stmt.args.get("limit"):
                    limit = self._parse_limit()
                    if limit:
                        delete_stmt.set("limit", limit)
            
            return delete_stmt

        def _parse_values(self) -> t.Optional[exp.Values]:
            """
            解析VALUES语句，支持别名
            VALUES (expression [, ...]) [, ...] [AS alias[(column1, column2, ...)]]
            """
            self._match(TokenType.VALUES)
            
            expressions = []
            while True:
                if not self._match(TokenType.L_PAREN):
                    break
                    
                row_expressions = self._parse_csv(self._parse_expression)
                if not self._match(TokenType.R_PAREN):
                    self.raise_error("Expected ')' after VALUES row")
                    
                expressions.append(
                    self.expression(exp.Tuple, expressions=row_expressions)
                )
                
                if not self._match(TokenType.COMMA):
                    break
            
            values_expr = self.expression(exp.Values, expressions=expressions)
            
            # 检查是否有AS别名
            if self._match(TokenType.ALIAS):
                alias_name = self._parse_id_var()
                if not alias_name:
                    self.raise_error("Expected alias name after AS")
                
                # 检查是否有列名列表
                column_names = None
                if self._match(TokenType.L_PAREN):
                    column_names = self._parse_csv(self._parse_id_var)
                    if not self._match(TokenType.R_PAREN):
                        self.raise_error("Expected ')' after column names")
                
                # 创建表别名结构
                if column_names:
                    # 创建TableAlias对象包含列名
                    table_alias = self.expression(
                        exp.TableAlias,
                        this=alias_name,
                        columns=column_names
                    )
                else:
                    # 只有表别名，没有列名
                    table_alias = self.expression(
                        exp.TableAlias,
                        this=alias_name
                    )
                
                # 将VALUES包装为带别名的Alias表达式
                return self.expression(exp.Alias, this=values_expr, alias=table_alias)
            
            return values_expr
            
        def _parse_show(self) -> t.Optional[exp.Show]:
            """
            解析SHOW语句
            SHOW [FULL] TABLES [WHERE condition]
            """
            self._match(TokenType.SHOW)
            
            full = self._match_text_seq("FULL")
            
            if self._match_text_seq("TABLES"):
                where = self._parse_where()
                return self.expression(
                    exp.Show,
                    this="TABLES",
                    full=full,
                    where=where
                )
            else:
                # 其他SHOW语句类型
                target = self._parse_string() or self._parse_var()
                return self.expression(
                    exp.Show,
                    this=target
                )

        def _parse_create_table_ddl(self) -> t.Optional[exp.Create]:
            """
            解析CREATE TABLE语句，支持炎凰SQL的ENGINE语法：
            CREATE [OR REPLACE] TABLE table_name [ENGINE=engine_type [WITH (setting_1=value_1[, setting_2=value2, ...])]]
            """
            # 先调用父类的CREATE TABLE解析
            create_stmt = super()._parse_create()
            
            if not create_stmt or create_stmt.args.get("kind") != "TABLE":
                return create_stmt
                
            # 检查是否有ENGINE子句
            if self._match_text_seq("ENGINE"):
                self._match(TokenType.EQ)
                engine_type = self._parse_var() or self._parse_string()
                
                if not engine_type:
                    self.raise_error("Expected engine type after ENGINE=")
                
                # 检查是否有WITH子句
                with_properties = None
                if self._match_text_seq("WITH"):
                    if not self._match(TokenType.L_PAREN):
                        self.raise_error("Expected '(' after WITH")
                    
                    properties = []
                    while not self._match(TokenType.R_PAREN):
                        prop_name = self._parse_var() or self._parse_string()
                        if not prop_name:
                            self.raise_error("Expected property name")
                            
                        self._match(TokenType.EQ)
                        prop_value = self._parse_primary()
                        if not prop_value:
                            self.raise_error("Expected property value")
                            
                        properties.append(
                            self.expression(exp.Property, this=prop_name, value=prop_value)
                        )
                        
                        if not self._match(TokenType.COMMA):
                            break
                    
                    if not self._match(TokenType.R_PAREN):
                        self.raise_error("Expected ')' after WITH properties")
                        
                    with_properties = properties
                
                # 将ENGINE和WITH信息添加到CREATE语句中
                create_stmt.set("engine", engine_type)
                if with_properties:
                    create_stmt.set("engine_properties", with_properties)
            
            return create_stmt

        def _parse_pivot_statement(self) -> t.Optional[exp.Pivot]:
            """解析PIVOT语句"""
            # PIVOT table_name ON pivot_column [IN (values)] USING aggregations GROUP BY columns [ORDER BY ...]
            
            # 解析表名
            table = self._parse_table()
            if not table:
                self.raise_error("PIVOT语句必须指定表名")
            
            # 解析ON子句
            if not self._match(TokenType.ON):
                self.raise_error("PIVOT语句必须包含ON子句")
            
            pivot_column = self._parse_bitwise()
            if not pivot_column:
                self.raise_error("PIVOT ON子句必须指定透视列")
            
            # 解析可选的IN子句
            pivoted_values = None
            if self._match(TokenType.IN):
                self._match_l_paren()
                # 修复：解析带引号的字符串字面量
                pivoted_values = []
                while not self._curr or self._curr.token_type != TokenType.R_PAREN:
                    # 尝试解析字符串、数字或标识符
                    if self._curr.token_type == TokenType.STRING:
                        value = self._parse_string()
                    elif self._curr.token_type == TokenType.NUMBER:
                        value = self._parse_number()
                    elif self._curr.token_type in (TokenType.VAR, TokenType.IDENTIFIER):
                        value = self._parse_id_var()
                    else:
                        # 使用通用表达式解析
                        value = self._parse_bitwise()
                    
                    if value:
                        pivoted_values.append(value)
                    
                    if not self._match(TokenType.COMMA):
                        break
                
                self._match_r_paren()
            
            # 解析USING子句
            if not self._match(TokenType.USING):
                self.raise_error("PIVOT语句必须包含USING子句")
            
            using_expressions = self._parse_csv(self._parse_expression)
            if not using_expressions:
                self.raise_error("PIVOT USING子句不能为空")
            
            # 解析GROUP BY子句
            group_by = None
            if self._match(TokenType.GROUP_BY):
                # 使用特殊的GROUP BY解析逻辑来支持TIME()函数
                group_by_expr = self._parse_group(skip_group_by_token=True)
                if group_by_expr:
                    group_by = group_by_expr.expressions
            
            # 构造fields参数 - 包含透视列和可选的值列表
            fields = []
            if pivoted_values:
                # 创建一个In表达式来表示 pivot_column IN (values)
                in_expr = self.expression(exp.In, this=pivot_column, expressions=pivoted_values)
                fields.append(in_expr)
            else:
                # 只有透视列，没有IN子句
                fields.append(pivot_column)
            
            # 构造group参数
            group_expr = None
            if group_by:
                group_expr = self.expression(exp.Group, expressions=group_by)
            
            # 解析ORDER BY子句
            order_by = None
            if self._match(TokenType.ORDER_BY):
                order_by = self._parse_order(skip_order_token=True)
            
            # 创建PIVOT表达式
            pivot = self.expression(
                exp.Pivot,
                this=table,
                expressions=using_expressions,  # USING部分的聚合表达式
                fields=fields,                  # ON部分的透视字段
                group=group_expr               # GROUP BY部分
            )
            
            # 如果有ORDER BY，创建包装的SELECT查询
            if order_by:
                select = self.expression(
                    exp.Select,
                    expressions=[exp.Star()],
                    **{"from": self.expression(exp.From, this=pivot)},
                    order=order_by
                )
                return select
            
            return pivot

        def _parse_wrapped_select(self, table: bool = False) -> t.Optional[exp.Expression]:
            """重写_parse_wrapped_select方法以支持炎凰SQL的PIVOT语法"""
            if self._match_set((TokenType.PIVOT, TokenType.UNPIVOT)):
                if self._prev.token_type == TokenType.PIVOT:
                    # 使用炎凰SQL的PIVOT解析方法
                    this: t.Optional[exp.Expression] = self._parse_pivot_statement()
                else:
                    # UNPIVOT仍使用标准方法
                    this: t.Optional[exp.Expression] = self._parse_simplified_pivot(is_unpivot=True)
            elif self._match(TokenType.FROM):
                from_ = self._parse_from(skip_from_token=True)
                # Support parentheses for duckdb FROM-first syntax
                select = self._parse_select()
                if select:
                    select.set("from", from_)
                    this = select
                else:
                    this = exp.select("*").from_(t.cast(exp.From, from_))
            else:
                this = (
                    self._parse_table()
                    if table
                    else self._parse_select(nested=True, parse_set_operation=False)
                )

                # Transform exp.Values into a exp.Table to pass through parse_query_modifiers
                # in case a modifier (e.g. join) is following
                if table and isinstance(this, exp.Values) and this.alias:
                    alias = this.args["alias"].pop()
                    this = exp.Table(this=this, alias=alias)

                this = self._parse_query_modifiers(self._parse_set_operations(this))

            return this

        def _parse_table_sample(self, as_modifier: bool = False) -> t.Optional[exp.TableSample]:
            """解析SAMPLE语法，支持炎凰SQL的SAMPLE ROW|BLOCK语法"""
            # 检查是否是TABLESAMPLE关键字，如果是则拒绝
            if self._match_texts(["TABLESAMPLE"]):
                self.raise_error("炎凰SQL不支持TABLESAMPLE语法，请使用SAMPLE语法")
            
            # 消费SAMPLE token
            if not self._match(TokenType.TABLE_SAMPLE):
                return None
            
            # 解析采样方法：ROW 或 BLOCK
            method = None
            if self._match(TokenType.ROW) or self._match_texts(["BERNOULLI"]):
                method = exp.var("ROW")
            elif self._match_texts(["BLOCK"]) or self._match_texts(["SYSTEM"]):
                method = exp.var("BLOCK")
            else:
                # 如果没有指定方法，默认为ROW
                method = exp.var("ROW")
            
            # 解析概率值
            if not self._match(TokenType.L_PAREN):
                self.raise_error("SAMPLE语法需要括号包围概率值")
            
            percent = self._parse_number()
            if not percent:
                self.raise_error("SAMPLE语法需要指定概率值")
            
            if not self._match(TokenType.R_PAREN):
                self.raise_error("SAMPLE语法缺少右括号")
            
            return self.expression(
                exp.TableSample,
                method=method,
                percent=percent
            )

        def _parse_group(self, skip_group_by_token: bool = False) -> t.Optional[exp.Group]:
            """Override to support GROUP BY TIME() syntax"""
            if not skip_group_by_token and not self._match(TokenType.GROUP_BY):
                return None

            expressions = []

            while True:
                # 检查TIME()语法
                if self._match_texts(["TIME"]):
                    if not self._match(TokenType.L_PAREN):
                        self.raise_error("TIME后必须跟括号")

                    # 解析TIME()参数，格式为key=value
                    time_args = []
                    while True:
                        # 尝试解析参数名
                        if self._curr:
                            key_expr = self._parse_id_var()
                            if key_expr:
                                if not self._match(TokenType.EQ):
                                    self.raise_error("TIME参数期望格式为key=value")
                                value = self._parse_string() or self._parse_number() or self._parse_id_var()
                                if not value:
                                    self.raise_error("TIME参数值不能为空")
                                
                                # 创建参数表达式，使用PropertyEQ来表示key=value
                                param_expr = self.expression(
                                    exp.PropertyEQ,
                                    this=key_expr,
                                    expression=value
                                )
                                time_args.append(param_expr)
                            else:
                                break
                        else:
                            break
                        
                        if not self._match(TokenType.COMMA):
                            break

                    if not self._match(TokenType.R_PAREN):
                        self.raise_error("TIME()缺少右括号")

                    # 创建TIME特殊表达式
                    time_expr = self.expression(
                        exp.Anonymous,
                        this="TIME",
                        expressions=time_args
                    )
                    expressions.append(time_expr)
                else:
                    # 常规GROUP BY表达式
                    expr = self._parse_bitwise()
                    if not expr:
                        break
                    expressions.append(expr)

                if not self._match(TokenType.COMMA):
                    break

            return self.expression(exp.Group, expressions=expressions) if expressions else None

    class Tokenizer(Postgres.Tokenizer):
        BIT_STRINGS = []
        HEX_STRINGS = []
        BYTE_STRINGS = [("e'", "'"), ("E'", "'")]  # E前缀字符串，用于C-style转义
        STRING_ESCAPES = ["\\", "'"]
        
        # 支持炎凰SQL的Unicode字符串前缀
        UNICODE_STRINGS = [
            (prefix + q, q)
            for q in t.cast(t.List[str], tokens.Tokenizer.QUOTES)
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
            "FULL": TokenType.VAR,      # SHOW FULL TABLES语法
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

        # Redshift doesn't have `WITH` as part of their with_properties so we remove it
        # 炎凰SQL需要保留WITH关键字，但在properties_sql中处理
        WITH_PROPERTIES_PREFIX = ""

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
            exp.CurrentTimestamp: lambda self, e: (
                "SYSDATE" if e.args.get("sysdate") else "GETDATE()"
            ),
            exp.DateAdd: date_delta_sql("DATEADD"),
            exp.DateDiff: date_delta_sql("DATEDIFF"),
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
            exp.TsOrDsAdd: lambda self, e: self.dateadd_sql(e),
            exp.TsOrDsDiff: lambda self, e: self.datediff_sql(e),
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
            exp.ByteString: lambda self, e: self.bytestring_sql(e),
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
            "type",
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
            """处理JOIN语句，包括APPLY"""
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
                
                return f"{join_type} {self.sql(table_func)}{alias_sql}"
            else:
                # 普通JOIN处理 - 直接使用父类方法，不添加额外空格
                return super().join_sql(expression)

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
            joins_sql = " ".join(self.sql(join) for join in joins) if joins else ""
            if from_sql:
                select += f" FROM {from_sql}"
            if joins_sql:
                select += f" {joins_sql}"
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
            # 保持表函数名原始大小写
            name = expression.name
            args = self.expressions(expression, "expressions")
            return f"{name}({args})"

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
            """Generate alias with appropriate AS keyword based on context"""
            sql = self.sql(expression, "this")
            alias = alias or self.sql(expression, "alias")
            if alias:
                # 检查是否在子查询内部
                parent = expression.parent
                in_subquery = False
                while parent:
                    if isinstance(parent, exp.Subquery):
                        in_subquery = True
                        break
                    parent = parent.parent
                
                # 如果在子查询内部，始终使用AS关键字
                if in_subquery:
                    return f"{sql} AS {alias}"
                
                # 否则检查是否有显式AS标记
                explicit_as = expression.args.get("explicit_as", False)  # 默认为False以匹配测试期望
                print(f"[DEBUG] alias_sql: in_subquery={in_subquery}, explicit_as={explicit_as}, expression={sql} alias={alias}")
                if explicit_as:
                    return f"{sql} AS {alias}"
                else:
                    return f"{sql} {alias}"
            return sql

        def table_sql(self, expression: exp.Table, sep: str = " AS ") -> str:
            """Override to fix APPLY join spacing and handle table merges"""
            # 检查是否是多表合并Union
            if isinstance(expression.this, exp.Union) and expression.this.args.get("is_table_merge"):
                return self.union_sql(expression.this)
            
            table = self.table_parts(expression)
            only = "ONLY " if expression.args.get("only") else ""
            partition = self.sql(expression, "partition")
            partition = f" {partition}" if partition else ""
            version = self.sql(expression, "version")
            version = f" {version}" if version else ""
            alias = self.sql(expression, "alias")
            alias = f"{sep}{alias}" if alias else ""

            sample = self.sql(expression, "sample")
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
            
            # 处理fields参数（包含ON子句信息）
            if expression.fields:
                field = expression.fields[0]
                if isinstance(field, exp.In):
                    # 有IN子句的情况：pivot_column IN (values)
                    pivot_column = field.this
                    pivoted_values = field.expressions
                    sql += f" ON {self.sql(pivot_column)}"
                    if pivoted_values:
                        values = ", ".join(self.sql(v) for v in pivoted_values)
                        sql += f" IN ({values})"
                else:
                    # 只有透视列，没有IN子句
                    sql += f" ON {self.sql(field)}"
            
            # 处理expressions参数（USING子句）
            if expression.expressions:
                using = ", ".join(self.sql(expr) for expr in expression.expressions)
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
                    # 处理TIME()语法
                    params = []
                    for param_expr in expr.expressions:
                        if isinstance(param_expr, exp.PropertyEQ):
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
            生成SAMPLE语法的SQL，支持炎凰SQL的SAMPLE语法
            """
            method = expression.args.get("method")
            percent = expression.args.get("percent")
            
            if not method or not percent:
                return ""
            
            # 将method转换为炎凰SQL支持的格式
            method_name = method.name if hasattr(method, 'name') else str(method)
            if method_name.upper() in ("BERNOULLI", "ROW"):
                method_name = "ROW"
            elif method_name.upper() in ("SYSTEM", "BLOCK"):
                method_name = "BLOCK"
            else:
                method_name = "ROW"  # 默认使用ROW
            
            percent_value = self.sql(percent)
            return f" SAMPLE {method_name} ({percent_value})"

        def bytestring_sql(self, expression: exp.ByteString) -> str:
            """
            生成E前缀字符串的SQL，用于C-style转义字符
            """
            string_value = expression.this
            # 转义字符串中的特殊字符
            escaped_string = self.escape_str(string_value)
            return f"E'{escaped_string}'"

        def unicodestring_sql(self, expression: exp.UnicodeString) -> str:
            """生成Unicode字符串SQL"""
            prefix = "U&"
            quote_char = "'"  # 使用固定的单引号
            value = expression.this
            
            # 处理UESCAPE
            escape_char = expression.args.get("escape")
            if escape_char:
                # escape_char可能是Literal对象，需要获取其值
                escape_value = escape_char.this if hasattr(escape_char, 'this') else escape_char
                return f"{prefix}{quote_char}{value}{quote_char} UESCAPE {quote_char}{escape_value}{quote_char}"
            else:
                return f"{prefix}{quote_char}{value}{quote_char}"
                
        def show_sql(self, expression: exp.Show) -> str:
            """生成SHOW语句SQL"""
            target = expression.this
            full = expression.args.get("full")
            where = expression.args.get("where")
            
            parts = ["SHOW"]
            
            if full:
                parts.append("FULL")
                
            if isinstance(target, str):
                parts.append(target)
            else:
                parts.append(self.sql(target))
                
            if where:
                parts.append(f"WHERE {self.sql(where)}")
                
            return " ".join(parts)

        def properties_sql(self, expression: exp.Properties) -> str:
            """生成Properties SQL，为炎凰SQL添加WITH关键字"""
            if not expression or not expression.expressions:
                return ""
            
            props = []
            for prop in expression.expressions:
                if isinstance(prop, exp.EngineProperty):
                    # ENGINE属性不在括号内
                    props.append(f"ENGINE={self.sql(prop.this)}")
                else:
                    # 其他属性在WITH括号内
                    prop_sql = self.sql(prop)
                    props.append(prop_sql)
            
            # 分离ENGINE和其他属性
            engine_props = [p for p in props if p.startswith("ENGINE=")]
            other_props = [p for p in props if not p.startswith("ENGINE=")]
            
            result = ""
            if engine_props:
                result += " ".join(engine_props)
            if other_props:
                result += f" WITH ({', '.join(other_props)})"
                
            return result
