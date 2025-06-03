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