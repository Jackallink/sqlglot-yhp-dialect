from __future__ import annotations

import typing as t

from sqlglot import exp, transforms
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
from sqlglot.dialects.postgres import Postgres
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
            "CONCAT": exp.Concat.from_arg_list,
            "CONTAINS": exp.Anonymous.from_arg_list,
        }

        NO_PAREN_FUNCTION_PARSERS = {
            **Postgres.Parser.NO_PAREN_FUNCTION_PARSERS,
            "APPROXIMATE": lambda self: self._parse_approximate_count(),
            "SYSDATE": lambda self: self.expression(exp.CurrentTimestamp, sysdate=True),
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
            self._match(TokenType.COMMA)
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
            """重写_parse_statement以在解析完成后进行相关子查询检测和窗口函数转换"""
            statement = super()._parse_statement()
            if statement:
                # 先应用兼容性转换（智能降级）
                statement = self._apply_window_function_transforms(statement)
                # 再检查无法降级的限制
                self._check_correlated_subqueries(statement)
                self._check_unsupported_window_features(statement)
                self._check_unsupported_set_operations(statement)
                self._check_distinct_limitations(statement)
                self._check_delete_limitations(statement)
                self._check_tablesample_limitations(statement)
                self._check_table_ddl_limitations(statement)
            return statement

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
            
            if isinstance(expr, exp.Binary):
                # 检查左右操作数是否为窗口函数
                if isinstance(expr.this, exp.Window):
                    windows.append(expr.this)
                if isinstance(expr.expression, exp.Window):
                    windows.append(expr.expression)
                # 递归检查子表达式
                windows.extend(self._find_window_arithmetic_expressions(expr.this))
                windows.extend(self._find_window_arithmetic_expressions(expr.expression))
            elif isinstance(expr, exp.Unary):
                if isinstance(expr.this, exp.Window):
                    windows.append(expr.this)
                windows.extend(self._find_window_arithmetic_expressions(expr.this))
            elif hasattr(expr, 'expressions') and expr.expressions:
                for sub_expr in expr.expressions:
                    windows.extend(self._find_window_arithmetic_expressions(sub_expr))
            elif hasattr(expr, 'args') and expr.args:
                for key, value in expr.args.items():
                    if isinstance(value, exp.Expression):
                        windows.extend(self._find_window_arithmetic_expressions(value))
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, exp.Expression):
                                windows.extend(self._find_window_arithmetic_expressions(item))
            
            return windows

        def _replace_window_in_arithmetic(self, expr, window_expr, alias_name):
            """在运算表达式中替换窗口函数为列引用（已废弃，使用transform方法替代）"""
            return expr

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

        def _replace_window_references(self, expr, window_definitions):
            """替换窗口函数中的窗口引用为内联规格（已废弃，使用transform方法替代）"""
            return expr

        def _check_unsupported_window_features(self, statement):
            """检查无法降级的窗口函数功能"""
            # 只检查RANGE和GROUPS框架，其他功能已经通过转换支持
            for window in statement.find_all(exp.Window):
                if window.args.get("spec"):
                    spec = window.args["spec"]
                    if hasattr(spec, 'args') and spec.args.get("kind"):
                        kind = str(spec.args["kind"]).upper()
                        if kind == "RANGE":
                            self.raise_error("炎凰SQL不支持RANGE窗口框架，请使用ROWS替代")
                        elif kind == "GROUPS":
                            self.raise_error("炎凰SQL不支持GROUPS窗口框架，请使用ROWS替代")

        def _check_correlated_subqueries(self, statement):
            """检查相关子查询和EXISTS位置限制"""
            # 检查EXISTS是否在WHERE子句之外
            if isinstance(statement, exp.Select):
                # 检查SELECT投影中的EXISTS
                for expr in statement.expressions or []:
                    for exists_expr in expr.find_all(exp.Exists):
                        self.raise_error("炎凰SQL不支持在WHERE语句之外使用EXISTS")
                
                # 检查HAVING子句中的EXISTS（如果有的话）
                if statement.args.get("having"):
                    for exists_expr in statement.args["having"].find_all(exp.Exists):
                        self.raise_error("炎凰SQL不支持在WHERE语句之外使用EXISTS")
                
                # 检查ORDER BY子句中的EXISTS（如果有的话）
                if statement.args.get("order"):
                    for exists_expr in statement.args["order"].find_all(exp.Exists):
                        self.raise_error("炎凰SQL不支持在WHERE语句之外使用EXISTS")
            
            # 检查IN子查询
            for in_expr in statement.find_all(exp.In):
                if isinstance(in_expr.args.get("query"), exp.Subquery):
                    subquery = in_expr.args["query"].this
                    self._validate_subquery_correlation(subquery, "IN")
            
            # 检查EXISTS子查询（仅检查WHERE子句中的相关性，位置检查已在上面完成）
            for exists_expr in statement.find_all(exp.Exists):
                if isinstance(exists_expr.this, exp.Select):
                    subquery = exists_expr.this
                    self._validate_subquery_correlation(subquery, "EXISTS")

        # 移除旧的方法，保留必要的辅助方法
        def _check_window_function_restrictions(self, statement):
            """已废弃：使用 _apply_window_function_transforms 和 _check_unsupported_window_features 替代"""
            pass

        def _check_window_function_arithmetic(self, expr):
            """已废弃：使用 _transform_window_function_arithmetic 替代"""
            pass

        def _validate_subquery_correlation(self, subquery, subquery_type):
            """验证子查询是否包含相关引用"""
            # 获取子查询中的所有表别名
            subquery_tables = set()
            if subquery.args.get("from"):
                from_tables = subquery.args["from"].find_all(exp.Table)
                for table in from_tables:
                    if table.alias:
                        subquery_tables.add(str(table.alias).lower())
                    else:
                        subquery_tables.add(str(table.this).lower())
            
            # 检查子查询中是否有引用外层表的列
            for col in subquery.find_all(exp.Column):
                if col.table:
                    table_name = str(col.table).lower()
                    # 如果列引用的表名不在子查询的表列表中，说明是外层引用
                    if table_name not in subquery_tables:
                        self.raise_error(f"炎凰SQL不支持相关{subquery_type}子查询（子查询引用外层表字段）")

        def _parse_in(self, this: t.Optional[exp.Expression], is_global: bool = False) -> t.Optional[exp.In]:
            # 简化：移除检测逻辑，交给_check_correlated_subqueries处理
            return super()._parse_in(this, is_global)

        def _has_correlated_reference(self, subquery: exp.Select, outer_alias: str) -> bool:
            """检查子查询是否包含对外层表别名的相关引用"""
            # 查找WHERE子句中的相关条件
            if subquery.args.get("where"):
                where_clause = subquery.args["where"]
                # 检查是否有引用外层别名的比较操作
                for comparison in where_clause.find_all(exp.EQ):
                    left = comparison.this
                    right = comparison.expression
                    # 检查是否一边是外层别名，一边是内层别名
                    if (isinstance(left, exp.Column) and isinstance(right, exp.Column) and
                        left.table and right.table and
                        str(left.table).lower() != str(right.table).lower() and
                        (str(left.table).lower() == outer_alias or str(right.table).lower() == outer_alias)):
                        return True
            return False

        def _find_from_table(self) -> t.Optional[str]:
            """查找当前查询上下文中的主表别名"""
            # 简化实现：在FROM子句解析阶段，我们应该能跟踪当前表别名
            # 这里使用启发式方法，检查最近解析的表
            # 在实际实现中，可能需要更复杂的上下文跟踪
            return None  # 暂时返回None，需要更复杂的解析上下文

        def _find_ancestor(self, *types):
            """查找指定类型的祖先节点"""
            # 这里是简化版实现，实际项目中可能需要更复杂的逻辑
            return None

        def _check_unsupported_set_operations(self, statement):
            """检查不支持的集合操作"""
            # 检查INTERSECT和EXCEPT
            for union_expr in statement.find_all(exp.Union):
                if hasattr(union_expr, 'kind') and union_expr.kind:
                    kind = str(union_expr.kind).upper()
                    if kind == "INTERSECT":
                        self.raise_error("炎凰SQL不支持INTERSECT集合操作，请使用UNION/UNION ALL")
                    elif kind == "EXCEPT":
                        self.raise_error("炎凰SQL不支持EXCEPT集合操作，请使用UNION/UNION ALL")
            
            # 检查Intersect和Except节点（如果存在）
            for intersect_expr in statement.find_all(exp.Intersect):
                self.raise_error("炎凰SQL不支持INTERSECT集合操作，请使用UNION/UNION ALL")
            
            for except_expr in statement.find_all(exp.Except):
                self.raise_error("炎凰SQL不支持EXCEPT集合操作，请使用UNION/UNION ALL")

        def _check_distinct_limitations(self, statement):
            """检查DISTINCT使用限制"""
            # 检查GROUP BY中的聚合函数DISTINCT限制
            if isinstance(statement, exp.Select) and statement.args.get("group"):
                # 在GROUP BY查询中，检查聚合函数
                for expr in statement.expressions or []:
                    self._check_aggregate_distinct_in_group_by(expr)
                
                # 检查HAVING子句中的聚合函数
                if statement.args.get("having"):
                    self._check_aggregate_distinct_in_group_by(statement.args["having"])

        def _check_aggregate_distinct_in_group_by(self, expr):
            """检查GROUP BY查询中的聚合函数DISTINCT限制"""
            # 查找所有聚合函数
            for agg_func in expr.find_all(exp.AggFunc):
                if hasattr(agg_func, 'this') and isinstance(agg_func.this, exp.Distinct):
                    # 检查是否是COUNT以外的聚合函数
                    func_name = type(agg_func).__name__.upper()
                    if func_name not in ('COUNT', 'APPROXDISTINCT', 'APPROXCOUNTDISTINCT'):
                        self.raise_error(f"炎凰SQL在GROUP BY查询中仅支持COUNT(DISTINCT ...)，不支持{func_name}(DISTINCT ...)")
            
            # 特别检查一些常见的聚合函数类型
            for sum_func in expr.find_all(exp.Sum):
                if hasattr(sum_func, 'this') and isinstance(sum_func.this, exp.Distinct):
                    self.raise_error("炎凰SQL在GROUP BY查询中不支持SUM(DISTINCT ...)，仅支持COUNT(DISTINCT ...)")
            
            for avg_func in expr.find_all(exp.Avg):
                if hasattr(avg_func, 'this') and isinstance(avg_func.this, exp.Distinct):
                    self.raise_error("炎凰SQL在GROUP BY查询中不支持AVG(DISTINCT ...)，仅支持COUNT(DISTINCT ...)")
            
            for min_func in expr.find_all(exp.Min):
                if hasattr(min_func, 'this') and isinstance(min_func.this, exp.Distinct):
                    self.raise_error("炎凰SQL在GROUP BY查询中不支持MIN(DISTINCT ...)，仅支持COUNT(DISTINCT ...)")
            
            for max_func in expr.find_all(exp.Max):
                if hasattr(max_func, 'this') and isinstance(max_func.this, exp.Distinct):
                    self.raise_error("炎凰SQL在GROUP BY查询中不支持MAX(DISTINCT ...)，仅支持COUNT(DISTINCT ...)")

        def _check_delete_limitations(self, statement):
            """检查DELETE语句限制"""
            if isinstance(statement, exp.Delete):
                # 检查RETURNING子句
                if statement.args.get("returning"):
                    self.raise_error("炎凰SQL的DELETE语句不支持RETURNING子句")
                
                # 检查USING子句
                if statement.args.get("using"):
                    self.raise_error("炎凰SQL的DELETE语句不支持USING子句")
                
                # 检查WITH子句（某些DELETE扩展）
                if statement.args.get("with"):
                    self.raise_error("炎凰SQL的DELETE语句不支持WITH子句")

        def _check_tablesample_limitations(self, statement):
            """检查TABLESAMPLE限制，炎凰SQL使用SAMPLE语法"""
            # 检查TABLESAMPLE节点
            for tablesample_expr in statement.find_all(exp.TableSample):
                # 检查是否使用了PostgreSQL的TABLESAMPLE语法
                if hasattr(tablesample_expr, 'method') and tablesample_expr.method:
                    method = str(tablesample_expr.method).upper()
                    if method in ('BERNOULLI', 'SYSTEM'):
                        self.raise_error("炎凰SQL不支持TABLESAMPLE BERNOULLI/SYSTEM语法，请使用SAMPLE ROW/BLOCK语法")
                else:
                    # 如果有TABLESAMPLE但没有明确的方法，也报错
                    self.raise_error("炎凰SQL不支持TABLESAMPLE语法，请使用SAMPLE ROW/BLOCK语法")

        def _check_table_ddl_limitations(self, statement):
            """检查CREATE/DROP TABLE语句限制"""
            if isinstance(statement, exp.Create):
                # 检查是否是CREATE TABLE
                if isinstance(statement.this, exp.Schema):
                    # 检查复杂的表定义特性
                    schema = statement.this
                    
                    # 检查列约束
                    if hasattr(schema, 'expressions') and schema.expressions:
                        for column_def in schema.expressions:
                            if hasattr(column_def, 'constraints') and column_def.constraints:
                                for constraint in column_def.constraints:
                                    constraint_type = type(constraint).__name__
                                    if constraint_type not in ('NotNullColumnConstraint', 'DefaultColumnConstraint'):
                                        self.raise_error(f"炎凰SQL不支持复杂列约束：{constraint_type}")
                    
                    # 检查表级约束
                    if hasattr(statement, 'constraints') and statement.constraints:
                        self.raise_error("炎凰SQL不支持表级约束，仅支持简单的CREATE TABLE语法")
                    
                    # 检查分区定义
                    if hasattr(statement, 'partition_by') and statement.partition_by:
                        self.raise_error("炎凰SQL不支持分区表，仅支持简单的CREATE TABLE语法")
                    
                    # 检查继承
                    if hasattr(statement, 'inherits') and statement.inherits:
                        self.raise_error("炎凰SQL不支持表继承，仅支持简单的CREATE TABLE语法")

    class Tokenizer(Postgres.Tokenizer):
        BIT_STRINGS = []
        HEX_STRINGS = []
        STRING_ESCAPES = ["\\", "'"]

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
        }
        KEYWORDS.pop("VALUES")

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
        WITH_PROPERTIES_PREFIX = " "

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
            exp.Concat: concat_to_dpipe_sql,
            exp.ConcatWs: concat_ws_to_dpipe_sql,
            exp.ApproxDistinct: lambda self, e: f"APPROXIMATE COUNT(DISTINCT {self.sql(e, 'this')})",
            exp.CurrentTimestamp: lambda self, e: (
                "SYSDATE" if e.args.get("sysdate") else "GETDATE()"
            ),
            exp.DateAdd: date_delta_sql("DATEADD"),
            exp.DateDiff: date_delta_sql("DATEDIFF"),
            exp.DistKeyProperty: lambda self, e: self.func("DISTKEY", e.this),
            exp.DistStyleProperty: lambda self, e: self.naked_property(e),
            exp.Explode: lambda self, e: self.explode_sql(e),
            exp.FromBase: rename_func("STRTOL"),
            exp.GeneratedAsIdentityColumnConstraint: generatedasidentitycolumnconstraint_sql,
            exp.JSONExtract: json_extract_segments("JSON_EXTRACT_PATH_TEXT"),
            exp.JSONExtractScalar: json_extract_segments("JSON_EXTRACT_PATH_TEXT"),
            exp.GroupConcat: rename_func("LISTAGG"),
            exp.Hex: lambda self, e: self.func("UPPER", self.func("TO_HEX", self.sql(e, "this"))),
            exp.Select: transforms.preprocess(
                [
                    transforms.eliminate_distinct_on,
                    transforms.eliminate_semi_and_anti_joins,
                    transforms.unqualify_unnest,
                    transforms.unnest_generate_date_array_using_recursive_cte,
                ]
            ),
            exp.SortKeyProperty: lambda self, e: f"{'COMPOUND ' if e.args['compound'] else ''}SORTKEY({self.format_args(*e.this)})",
            exp.StartsWith: lambda self, e: f"{self.sql(e.this)} LIKE {self.sql(e.expression)} || '%'",
            exp.StringToArray: rename_func("SPLIT_TO_ARRAY"),
            exp.TableSample: no_tablesample_sql,
            exp.TsOrDsAdd: date_delta_sql("DATEADD"),
            exp.TsOrDsDiff: date_delta_sql("DATEDIFF"),
            exp.UnixToTime: lambda self, e: f"(TIMESTAMP 'epoch' + {self.sql(e.this)} * INTERVAL '1 SECOND')",
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
            if isinstance(expression.this, exp.Lateral):
                op = self.lateral_op(expression.this)
                right = self.sql(expression.this, "this")
                alias_expr = expression.this.args.get("alias")
                alias = f" {alias_expr.this.this}" if alias_expr is not None else ""
                return f"{op} {right}{alias}"
            return super().join_sql(expression)

        def lateral_op(self, expression):
            cross_apply = expression.args.get("cross_apply")
            if cross_apply is True:
                return "CROSS APPLY"
            if cross_apply is False:
                return "OUTER APPLY"
            return "APPLY"

        def from_sql(self, expression):
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
            """Override to fix APPLY join spacing"""
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
