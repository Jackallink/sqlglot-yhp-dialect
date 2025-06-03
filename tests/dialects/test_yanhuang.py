from tests.dialects.test_dialect import Validator

class TestYanhuang(Validator):
    maxDiff = None
    dialect = "yanhuang"

    def test_basic_identity(self):
        self.validate_identity("SELECT 1")
        self.validate_identity("SELECT 1 AS a")
        self.validate_identity("SELECT 1 AS a, 2 AS b")
        self.validate_identity("SELECT 1 a, 2 b")
        self.validate_identity("SELECT * FROM main")
        self.validate_identity("SELECT * FROM main WHERE a = 1")
        self.validate_identity("SELECT username, host FROM main WHERE a = 1 AND b = 2")
        self.validate_identity("SELECT * FROM main WHERE a = 1 OR b = 2")
        self.validate_identity("SELECT * FROM main WHERE a = 1 AND b = 2 OR c = 3")
        self.validate_identity("SELECT * FROM abc WHERE a = 1 GROUP BY a")
      
        

    def test_columns_projection(self):
        self.validate_identity("SELECT COLUMNS('^f[1-4]$') FROM main")
        self.validate_identity("SELECT COLUMNS('^f[1-4]$') EXCEPT (f1) FROM main")
        self.validate_identity("SELECT COLUMNS('^f[1-4]$') REPLACE (f2+1 AS f2) FROM main")
        self.validate_identity("SELECT COLUMNS('f_(.*)') AS \"host_{0}\" FROM tbl")
        self.validate_identity("SELECT * EXCEPT (request_service) REPLACE (LOWER(request_method) AS request_method) FROM main")
        # 正则捕获组/命名组/语法糖
        self.validate_identity("SELECT COLUMNS('(?P<host>host_)(?P<host_value>.*)') AS \"ip_{host}_{host_value}\" FROM tbl")
        self.validate_identity("SELECT COLUMNS('result_detail.stonewave.(.*)') AS _ FROM tbl")
        self.validate_identity("SELECT COLUMNS('f_(.*)') AS \"host_{\\0}\\_{0}\" FROM tbl")
        # 主流SQL兼容性
        self.validate_identity("SELECT * FROM main")
        self.validate_identity("SELECT method, host FROM main")
        self.validate_identity("SELECT method AS method_alias, host AS host_alias FROM main")
        # 异常/报错场景
        self.validate_raises("SELECT COLUMNS('^f[1-4]$') EXCEPT () FROM main")
        self.validate_raises("SELECT COLUMNS('^f[1-4]$') REPLACE () FROM main")
        self.validate_raises("SELECT COLUMNS('^f[1-4]$') REPLACE (1+1) FROM main")
        self.validate_raises("SELECT COLUMNS('^f[1-4]$') AS 123 FROM main")

    def test_in_exists_subquery(self):
        # 支持的IN子查询
        self.validate_identity("SELECT * FROM orders WHERE CustomerID IN (SELECT CustomerID FROM customers)")
        # 不支持的相关IN子查询
        self.validate_raises("SELECT * FROM orders o WHERE o.CustomerID IN (SELECT c.CustomerID FROM customers c WHERE c.Region = o.Region)")
        # 支持的EXISTS子查询
        self.validate_identity("SELECT * FROM orders WHERE EXISTS (SELECT 1 FROM customers)")
        # 不支持的相关EXISTS
        self.validate_raises("SELECT * FROM orders o WHERE EXISTS (SELECT 1 FROM customers c WHERE c.id = o.id)")
        # 不支持的SELECT EXISTS
        self.validate_raises("SELECT EXISTS (SELECT 1)")

    def test_cte_recursive(self):
        # 支持的标准CTE
        self.validate_identity("WITH t1 AS (SELECT 1) SELECT * FROM t1")
        # 不支持WITH RECURSIVE
        self.validate_raises("WITH RECURSIVE t1 AS (SELECT 1) SELECT * FROM t1")

    def test_apply(self):
        # 表函数APPLY
        self.validate_identity("SELECT * FROM main OUTER APPLY ip_location(main.ip) ip_table")
        # 子查询APPLY
        self.validate_identity("SELECT * FROM main APPLY (SELECT UPPER(main._message) AS upper_message) AS table_bar")
        # 复杂APPLY（应报错）
        self.validate_raises("SELECT * FROM main APPLY (main.ip + 1)") 

    def test_window_functions(self):
        # 基本窗口函数（支持）
        self.validate_identity("SELECT COUNT(*) OVER (PARTITION BY id ORDER BY time DESC) FROM main")
        self.validate_identity("SELECT SUM(size) OVER (PARTITION BY method) FROM main")
        self.validate_identity("SELECT AVG(size) OVER (PARTITION BY method ORDER BY time) FROM main")
        self.validate_identity("SELECT MIN(size) OVER (PARTITION BY method), MAX(size) OVER (PARTITION BY method) FROM main")
        
        # 非聚合窗口函数（支持）
        self.validate_identity("SELECT ROW_NUMBER() OVER (PARTITION BY group_id ORDER BY price DESC) FROM products")
        self.validate_identity("SELECT FIRST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC) FROM products")
        self.validate_identity("SELECT LAST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) FROM products")
        self.validate_identity("SELECT LAG(sale_value) OVER (ORDER BY sale_value) FROM sale")
        self.validate_identity("SELECT LAG(sale_value, 2) OVER (ORDER BY sale_value) FROM sale")
        self.validate_identity("SELECT LAG(sale_value, 1, 0) OVER (ORDER BY sale_value) FROM sale")
        self.validate_identity("SELECT LEAD(sale_value) OVER (ORDER BY sale_value) FROM sale")
        self.validate_identity("SELECT LEAD(sale_value, 2) OVER (ORDER BY sale_value) FROM sale")
        self.validate_identity("SELECT LEAD(sale_value, 1, 0) OVER (ORDER BY sale_value) FROM sale")
        
        # 窗口框架子句（ROWS支持）
        self.validate_identity("SELECT SUM(size) OVER (ORDER BY time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main")
        self.validate_identity("SELECT SUM(size) OVER (ORDER BY time ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) FROM main")
        self.validate_identity("SELECT SUM(size) OVER (ORDER BY time ROWS BETWEEN 2 PRECEDING AND 1 FOLLOWING) FROM main")
        
        # 文档示例
        self.validate_identity("SELECT SUM(size) OVER (PARTITION BY agent) FROM main WHERE _datatype = 'nginx.access_log'")
        self.validate_identity("SELECT SUM(size) OVER (PARTITION BY agent ORDER BY method ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main WHERE _datatype = 'nginx.access_log'")
        
        # 复杂场景
        self.validate_identity("SELECT ROW_NUMBER() OVER (ORDER BY size), RANK() OVER (ORDER BY size) FROM main")
        self.validate_identity("SELECT * FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY size) AS rn FROM main) WHERE rn <= 10")
        
        # 不支持的功能（应该报错）
        self.validate_raises("SELECT SUM(size) OVER (ORDER BY time RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main")

    def test_window_function_transforms(self):
        """测试窗口函数智能降级转换"""
        
        # 测试ORDER BY中的窗口函数自动转换
        input_sql = "SELECT * FROM main ORDER BY COUNT(*) OVER (PARTITION BY id)"
        expected_sql = "SELECT * FROM (SELECT *, COUNT(*) OVER (PARTITION BY id) AS __window_expr_1 FROM main) AS __window_subquery ORDER BY __window_expr_1"
        
        # 使用validate_all来测试转换
        self.validate_all(
            input_sql,
            write={
                "yanhuang": expected_sql
            }
        )
        
        # 测试窗口函数运算表达式自动转换
        input_sql_arithmetic = "SELECT (COUNT(*) OVER ()) + 1 FROM main"
        expected_sql_arithmetic = "SELECT (__window_expr_1) + 1 FROM (SELECT *, COUNT(*) OVER () AS __window_expr_1 FROM main) AS __window_subquery"
        
        self.validate_all(
            input_sql_arithmetic,
            write={
                "yanhuang": expected_sql_arithmetic
            }
        )
        
        # 测试WINDOW子句自动转换
        input_sql_window = "SELECT COUNT(*) OVER w FROM main WINDOW w AS (PARTITION BY id)"
        expected_sql_window = "SELECT COUNT(*) OVER (PARTITION BY id) FROM main"
        
        self.validate_all(
            input_sql_window,
            write={
                "yanhuang": expected_sql_window
            }
        )

    def test_unsupported_window_features(self):
        """测试无法降级的窗口函数功能"""
        
        # RANGE框架（无法降级，应报错）
        self.validate_raises("SELECT SUM(size) OVER (ORDER BY time RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main")
        
        # GROUPS框架（无法降级，应报错）
        self.validate_raises("SELECT SUM(size) OVER (ORDER BY time GROUPS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main")

    def test_union_intersect_except(self):
        """测试集合操作支持和限制"""
        
        # 支持的UNION和UNION ALL
        self.validate_identity("SELECT method FROM main UNION SELECT action FROM logs")
        self.validate_identity("SELECT method FROM main UNION ALL SELECT action FROM logs")
        self.validate_identity("SELECT * FROM t1 UNION SELECT * FROM t2 UNION SELECT * FROM t3")
        
        # 不支持的INTERSECT和EXCEPT
        self.validate_raises("SELECT method FROM main INTERSECT SELECT action FROM logs")
        self.validate_raises("SELECT method FROM main EXCEPT SELECT action FROM logs")

    def test_distinct_limitations(self):
        """测试DISTINCT使用限制"""
        
        # 支持的SELECT DISTINCT
        self.validate_identity("SELECT DISTINCT code AS status_code FROM main")
        self.validate_identity("SELECT DISTINCT method, host FROM main")
        
        # 支持的非GROUP BY中的聚合DISTINCT
        self.validate_identity("SELECT SUM(DISTINCT CAST(code AS INTEGER)) AS code_sum FROM main")
        self.validate_identity("SELECT COUNT(DISTINCT customer_id) FROM main")
        
        # 支持的GROUP BY中的COUNT(DISTINCT)
        self.validate_identity("SELECT method, COUNT(DISTINCT customer_id) FROM main GROUP BY method")
        
        # 不支持的GROUP BY中的其他聚合DISTINCT
        self.validate_raises("SELECT method, SUM(DISTINCT CAST(code AS INTEGER)) AS code_sum FROM main GROUP BY method")
        self.validate_raises("SELECT method, AVG(DISTINCT size) FROM main GROUP BY method")
        self.validate_raises("SELECT method, MIN(DISTINCT size) FROM main GROUP BY method")
        self.validate_raises("SELECT method, MAX(DISTINCT size) FROM main GROUP BY method")

    def test_delete_limitations(self):
        """测试DELETE语句限制"""
        
        # 支持的基本DELETE语句
        self.validate_identity("DELETE FROM main WHERE id = 1")
        
        # 不支持的DELETE扩展
        self.validate_raises("DELETE FROM main WHERE id = 1 RETURNING *")
        self.validate_raises("DELETE FROM main USING customers WHERE main.customer_id = customers.id")

    def test_sample_limitations(self):
        """测试SAMPLE采样语法和TABLESAMPLE限制"""
        
        # 支持的SAMPLE语法（需要Generator支持才能测试完整功能）
        # 暂时跳过完整的SAMPLE测试，因为需要在Generator中实现
        
        # 不支持的TABLESAMPLE语法
        self.validate_raises("SELECT * FROM main TABLESAMPLE BERNOULLI (50)")
        self.validate_raises("SELECT * FROM main TABLESAMPLE SYSTEM (25)")

    def test_create_drop_table_limitations(self):
        """测试CREATE/DROP TABLE语句限制"""
        
        # 支持的基本CREATE TABLE
        self.validate_identity("CREATE TABLE test_table (id INTEGER, name VARCHAR(MAX))")
        self.validate_identity("DROP TABLE test_table")
        
        # 支持的炎凰SQL特有ENGINE语法（如果解析器支持的话）
        # 暂时注释掉，因为需要特殊的解析器支持
        # self.validate_identity("CREATE TABLE test_event_set ENGINE=event_set")
        # self.validate_identity("CREATE TABLE test_kafka_table ENGINE=kafka WITH (server_url='1.1.1.1')")
        
        # 不支持的复杂表特性（这些在sqlglot中可能需要特殊构造才能测试）
        # 暂时跳过复杂约束测试，因为需要构造复杂的AST 