# 炎凰SQL（yhp sql）与PostgreSQL语法差异清单

> 本文档系统梳理炎凰SQL与PostgreSQL的主要语法差异，聚焦于AST映射、合规性、LLM生成边界和测试建议。适用于LLM SQL生成、AST链路开发、合规性校验、团队协作等场景。

---

## 1. 子查询（IN/EXISTS/嵌套）

### IN子查询
- **炎凰SQL支持情况**：仅支持WHERE子句中的IN子查询，且只支持非相关子查询（子查询不能引用外层表字段）。子查询返回多列时只取第一列。
- **PostgreSQL支持情况**：支持IN子查询的所有变体，包括相关/非相关、任意嵌套。
- **典型SQL示例**：
  ```sql
  -- 支持
  SELECT * FROM orders WHERE CustomerID IN (SELECT CustomerID FROM customers)
  -- 不支持
  SELECT * FROM orders o WHERE o.CustomerID IN (SELECT c.CustomerID FROM customers c WHERE c.Region = o.Region)
  ```
- **AST映射/合规性建议**：遇到相关子查询应直接报错或降级提示。
- **LLM提示/边界建议**：IN子查询仅支持非相关子查询，不支持引用外层表字段。
- **测试建议**：普通IN子查询、相关IN子查询（应报错）、多列返回（只取第一列）。

### EXISTS子查询
- **炎凰SQL支持情况**：仅支持WHERE子句中的EXISTS表达式，且只支持非相关子查询。不支持SELECT EXISTS (SELECT ...)等表达式。
- **PostgreSQL支持情况**：支持EXISTS的所有变体，包括相关/非相关、任意嵌套、SELECT EXISTS等。
- **典型SQL示例**：
  ```sql
  -- 支持
  SELECT * FROM orders WHERE EXISTS (SELECT 1 FROM customers)
  -- 不支持
  SELECT * FROM orders o WHERE EXISTS (SELECT 1 FROM customers c WHERE c.id = o.id)
  SELECT EXISTS (SELECT 1)
  ```
- **AST映射/合规性建议**：遇到相关EXISTS或SELECT EXISTS应报错。
- **LLM提示/边界建议**：EXISTS仅支持WHERE子句中的非相关子查询。
- **测试建议**：普通EXISTS、相关EXISTS（应报错）、SELECT EXISTS（应报错）。

### 嵌套子查询
- **炎凰SQL支持情况**：支持多层嵌套的非相关子查询。不支持相关嵌套子查询。
- **PostgreSQL支持情况**：支持所有嵌套子查询。
- **AST映射/合规性建议**：嵌套层数无限制，但每层都必须是非相关子查询。
- **LLM提示/边界建议**：嵌套子查询每层都不能引用外层表字段。
- **测试建议**：多层嵌套IN/EXISTS、相关嵌套（应报错）。

---

## 2. CTE（WITH子句）

### CTE支持
- **炎凰SQL支持情况**：支持标准WITH/CTE语法，支持多CTE串联、嵌套CTE、CTE+JOIN、CTE+窗口函数、CTE+UNION等。递归CTE（WITH RECURSIVE）暂不支持。
- **PostgreSQL支持情况**：全面支持CTE，包括递归CTE（WITH RECURSIVE）。
- **典型SQL示例**：
  ```sql
  WITH t1 AS (SELECT ...), t2 AS (SELECT ... FROM t1) SELECT ... FROM t2
  ```
- **AST映射/合规性建议**：递归CTE（WITH RECURSIVE）遇到应报错。
- **LLM提示/边界建议**：暂不支持WITH RECURSIVE递归CTE。
- **测试建议**：多CTE、嵌套CTE、CTE+JOIN、CTE+窗口函数、CTE+UNION、递归CTE（应报错）。

---

## 3. 窗口函数

### 窗口函数支持
- **炎凰SQL支持情况**：支持常见窗口函数（如ROW_NUMBER、RANK、DENSE_RANK、SUM() OVER ...等），支持PARTITION BY、ORDER BY。部分frame/window子句（如RANGE、GROUPS、复杂ROWS）不支持。不支持WINDOW子句（如WINDOW w AS ...）、窗口函数嵌套、窗口函数参与复杂表达式。
- **PostgreSQL支持情况**：全面支持所有窗口函数、frame/window子句、WINDOW命名等。
- **典型SQL示例**：
  ```sql
  -- 支持
  SELECT user_id, RANK() OVER (PARTITION BY user_id ORDER BY amount DESC) FROM orders
  -- 不支持
  SELECT SUM(amount) OVER w FROM orders WINDOW w AS (PARTITION BY user_id)
  SELECT (ROW_NUMBER() OVER (...)) + 1 FROM orders
  ```
- **AST映射/合规性建议**：遇到WINDOW命名、复杂frame/window子句、窗口函数嵌套等应报错。
- **LLM提示/边界建议**：仅支持常见窗口函数和简单frame子句，不支持WINDOW命名、复杂frame/window、窗口函数嵌套。
- **测试建议**：常见窗口函数、复杂frame/window、WINDOW命名、窗口函数嵌套（应报错）。

---

## 4. UNION/UNION ALL

### UNION/UNION ALL
- **炎凰SQL支持情况**：支持UNION、UNION ALL，语法与PostgreSQL一致。不支持INTERSECT、EXCEPT等集合操作。
- **PostgreSQL支持情况**：支持UNION、UNION ALL、INTERSECT、EXCEPT等。
- **典型SQL示例**：
  ```sql
  SELECT ... FROM t1 UNION SELECT ... FROM t2
  SELECT ... FROM t1 UNION ALL SELECT ... FROM t2
  ```
- **AST映射/合规性建议**：INTERSECT、EXCEPT等遇到应报错。
- **LLM提示/边界建议**：仅支持UNION/UNION ALL，不支持INTERSECT/EXCEPT。
- **测试建议**：UNION、UNION ALL、INTERSECT/EXCEPT（应报错）。

---

## 5. 其它相关边界

### APPLY/表函数
- **炎凰SQL支持情况**：支持APPLY算子（OUTER APPLY、CROSS APPLY），但仅支持表函数和特殊子查询。right_table_source参数仅支持字段名、常量、表值参数，不支持复杂表达式。
- **PostgreSQL支持情况**：不支持APPLY，需用LATERAL JOIN等替代。
- **AST映射/合规性建议**：LLM生成PG SQL时避免LATERAL/复杂表函数，建议直接用APPLY语法。
- **LLM提示/边界建议**：APPLY仅支持表函数和简单子查询，不支持复杂表达式。
- **测试建议**：APPLY表函数、APPLY子查询、复杂APPLY（应报错）。

---

## 6. COLUMNS批量投影与重命名

### COLUMNS语法
- **炎凰SQL支持情况**：支持`COLUMNS(REGEX)`批量选择字段，支持`EXCEPT`排除、`REPLACE`表达式替换、`AS`批量重命名，支持正则捕获组、命名组、语法糖。支持与`*`联合使用。
- **PostgreSQL支持情况**：标准SQL/PostgreSQL不支持COLUMNS批量投影、正则批量重命名等语法。
- **典型SQL示例**：
  ```sql
  SELECT COLUMNS('^f[1-4]$') EXCEPT (f1) FROM main
  SELECT COLUMNS('^f[1-4]$') REPLACE (f2+1 as f2) FROM main
  SELECT COLUMNS('f_(.*)') AS "host_{0}" FROM tbl
  SELECT * EXCEPT(request_service) REPLACE (lower(request_method) as request_method) FROM main
  ```
- **AST映射/合规性建议**：遇到COLUMNS相关语法，需特殊AST节点支持，PG链路需报错或提示不支持。
- **LLM提示/边界建议**：COLUMNS批量投影、正则重命名、EXCEPT/REPLACE仅炎凰SQL支持，PG不支持。
- **测试建议**：COLUMNS批量、EXCEPT、REPLACE、AS重命名、正则捕获组、语法糖。

---

## 7. CASE表达式

### CASE语法
- **炎凰SQL支持情况**：支持标准CASE WHEN表达式，支持CASE <expr> WHEN ... THEN ... ELSE ... END和CASE WHEN ... THEN ... ELSE ... END两种写法。
- **PostgreSQL支持情况**：全面支持CASE表达式。
- **典型SQL示例**：
  ```sql
  SELECT CASE method WHEN 'GET' THEN 'read' WHEN 'POST' THEN 'write' ELSE 'unknown' END AS operation FROM main
  SELECT CASE WHEN code = '200' THEN 'succeed' ELSE 'failed' END AS code_str FROM main
  ```
- **AST映射/合规性建议**：AST需有CaseWhen节点，映射一致。
- **LLM提示/边界建议**：CASE表达式两端兼容，无特殊限制。
- **测试建议**：CASE <expr> WHEN、CASE WHEN、嵌套CASE。

---

## 8. DELETE语句

### DELETE语法
- **炎凰SQL支持情况**：支持`DELETE FROM <event_set> [WHERE ...] [ORDER BY ...] [LIMIT ...]`，可带WHERE/ORDER BY/LIMIT。无RETURNING等扩展。
- **PostgreSQL支持情况**：支持DELETE FROM，支持RETURNING、USING等扩展。
- **典型SQL示例**：
  ```sql
  DELETE FROM main WHERE CONTAINS('password') ORDER BY _time LIMIT 1
  ```
- **AST映射/合规性建议**：炎凰SQL不支持RETURNING/USING等扩展，遇到应报错。
- **LLM提示/边界建议**：DELETE仅支持基本语法，不支持RETURNING/USING。
- **测试建议**：DELETE基本、带ORDER BY/LIMIT、RETURNING/USING（应报错）。

---

## 9. 类型系统与类型转换

### 类型系统
- **炎凰SQL支持情况**：支持int、long、float、double、string、bool、boolean、decimal(precision, scale)、timestamp等。字段默认string，支持隐式/显式类型转换。部分类型（如bytea、jsonb、enum、array等）不支持。
- **PostgreSQL支持情况**：类型丰富，支持int、float、double、text、boolean、timestamp、bytea、jsonb、enum、array等。
- **典型SQL示例**：
  ```sql
  SELECT sum(cast(size as float)), max(cast(size as int)) FROM main
  ```
- **AST映射/合规性建议**：遇到炎凰SQL不支持的类型应报错或降级，类型转换需遵循炎凰规则。
- **LLM提示/边界建议**：仅支持主流基础类型，复杂类型（bytea/jsonb/array等）不支持。
- **测试建议**：基础类型、类型转换、复杂类型（应报错）。

---

## 10. DESCRIBE 语句

### DESCRIBE 语法
- **炎凰SQL支持情况**：支持 `DESCRIBE <event_set>` 查看数据集结构，支持时间过滤。仅支持事件集（表）结构描述。
- **PostgreSQL支持情况**：标准SQL无DESCRIBE，PostgreSQL通过 `\d`、`\d+`、`information_schema` 查询表结构。
- **典型SQL示例**：
  ```sql
  DESCRIBE main
  ```
- **AST映射/合规性建议**：炎凰SQL为专用命令，PG链路需提示不支持或用元数据查询替代。
- **LLM提示/边界建议**：DESCRIBE仅炎凰SQL支持，PG需用元数据表查询。
- **测试建议**：DESCRIBE事件集、带时间过滤。

---

## 11. CREATE TABLE / DROP TABLE

### CREATE TABLE 语法
- **炎凰SQL支持情况**：支持 `CREATE [OR REPLACE] TABLE ... ENGINE=event_set|kafka WITH (...)`，支持部分表属性。仅支持event_set/kafka两类表引擎。
- **PostgreSQL支持情况**：支持标准 `CREATE TABLE`，支持丰富的数据类型、约束、分区、继承等。
- **典型SQL示例**：
  ```sql
  CREATE TABLE test_event_set ENGINE=event_set
  CREATE TABLE test_kafka_table ENGINE=kafka WITH (server_url='1.1.1.1',server_port='9999',topic='new-events')
  DROP TABLE test_event_set
  ```
- **AST映射/合规性建议**：炎凰SQL表结构简单，PG链路遇到复杂表结构/约束应报错。
- **LLM提示/边界建议**：仅支持event_set/kafka表，复杂表结构/约束不支持。
- **测试建议**：CREATE/DROP基础表、复杂表结构（应报错）。

---

## 12. SAMPLE 采样

### SAMPLE 语法
- **炎凰SQL支持情况**：支持 `SAMPLE ROW|BLOCK (percent)`，可用于表、JOIN右表等，提升查询性能。
- **PostgreSQL支持情况**：支持 `TABLESAMPLE BERNOULLI|SYSTEM (percent)`，但语法和行为与炎凰SQL不同。
- **典型SQL示例**：
  ```sql
  SELECT * FROM main SAMPLE ROW (50.0)
  SELECT * FROM Orders LEFT SEMI JOIN Customers SAMPLE ROW (50) ON Orders.CustomerID=Customers.CustomerID
  ```
- **AST映射/合规性建议**：SAMPLE节点需区分ROW/BLOCK，PG链路需提示语法差异。
- **LLM提示/边界建议**：SAMPLE语法、采样方式与PG不同，需注意兼容性。
- **测试建议**：SAMPLE ROW、SAMPLE BLOCK、TABLESAMPLE（应报错）。

---

## 13. DISTINCT 关键字

### DISTINCT 语法
- **炎凰SQL支持情况**：支持SELECT DISTINCT、聚合函数内DISTINCT（仅COUNT），不支持GROUP BY聚合函数内DISTINCT（如SUM(DISTINCT ...), AVG(DISTINCT ...)，仅COUNT(DISTINCT ...)）。
- **PostgreSQL支持情况**：支持SELECT DISTINCT、所有聚合函数内DISTINCT。
- **典型SQL示例**：
  ```sql
  SELECT DISTINCT code as status_code FROM main
  SELECT SUM(DISTINCT CAST(code as int)) as code_sum FROM main
  -- 不支持
  SELECT SUM(DISTINCT CAST(code as int)) as code_sum, method FROM main GROUP BY method
  ```
- **AST映射/合规性建议**：遇到不支持的聚合DISTINCT应报错。
- **LLM提示/边界建议**：仅COUNT(DISTINCT ...)支持，其他聚合DISTINCT不支持。
- **测试建议**：SELECT DISTINCT、COUNT/SUM/AVG(DISTINCT ...)、GROUP BY聚合DISTINCT（应报错）。

---

## 14. 标量函数（Scalar Function）

### 标量函数支持
- **炎凰SQL支持情况**：支持常见内置标量函数（UPPER、LOWER、SUBSTR、CAST、COALESCE等），支持用户自定义标量函数（CREATE FUNCTION ... RETURNS ... RETURN ...）。参数类型支持STRING、INT、FLOAT、BOOL、DOUBLE、BOOLEAN。支持隐式类型转换。函数重载仅支持参数个数不同，不支持同名同参不同类型。
- **PostgreSQL支持情况**：支持丰富的内置/自定义标量函数，参数类型、重载、返回类型灵活，支持多种复杂表达式和类型。
- **典型SQL示例**：
  ```sql
  SELECT UPPER(_host) AS upper_case_host FROM _internal
  CREATE FUNCTION case_when_sf(@key int) RETURNS string RETURN CASE @key WHEN 1 THEN 'abc' ELSE 'unknown' END
  SELECT case_when_sf(1)
  ```
- **AST映射/合规性建议**：炎凰SQL函数参数类型、重载、返回类型有限，PG链路遇到复杂类型/重载应报错。
- **LLM提示/边界建议**：仅支持主流标量函数和简单自定义函数，复杂类型/重载/表达式不支持。
- **测试建议**：内置函数、自定义函数、重载、复杂类型（应报错）。

---

## 15. 表函数（Table Function）

### 表函数支持
- **炎凰SQL支持情况**：支持用户自定义表函数（CREATE FUNCTION ... RETURNS TABLE/AS ...），参数仅支持字面常量或表值参数。表函数可作为APPLY、FROM等表来源。参数类型有限，支持default参数。表函数重载仅支持参数个数不同，不支持同名同参不同类型。表函数参数不支持复杂表达式。
- **PostgreSQL支持情况**：支持丰富的表函数（set-returning function），参数类型、重载、返回类型灵活，支持LATERAL、UNNEST、generate_series等复杂用法。
- **典型SQL示例**：
  ```sql
  CREATE FUNCTION get_events_from_dataset(@data_set table, @key string) AS (SELECT * FROM @data_set WHERE CONTAINS(@key))
  SELECT * FROM get_events_from_dataset(main, 'GET')
  -- 带default参数
  CREATE OR REPLACE FUNCTION multi_default_val_tf(@key string = 'GET', @data_set table, @limit int default 1)AS (SELECT * FROM @data_set where contains(@key) limit @limit)
  SELECT * FROM multi_default_val_tf(default, main, default)
  ```
- **AST映射/合规性建议**：炎凰SQL表函数参数类型、重载、返回类型有限，PG链路遇到复杂类型/重载/表达式应报错。
- **LLM提示/边界建议**：仅支持主流表函数和简单参数，复杂类型/重载/表达式不支持。
- **测试建议**：内置表函数、自定义表函数、重载、复杂类型/表达式（应报错）。

---

## 16. 标量函数与表函数详细对比

### 16.1 标量函数（Scalar Function）对比

| 对比项         | 炎凰SQL                                             | PostgreSQL                                             |
|----------------|-----------------------------------------------------|--------------------------------------------------------|
| 内置函数       | 支持UPPER、LOWER、SUBSTR、CAST、COALESCE等常用函数 | 支持丰富（字符串、数学、日期、类型、聚合等）           |
| 用户自定义     | 支持（CREATE FUNCTION ... RETURNS ... RETURN ...）   | 支持（CREATE FUNCTION/PROCEDURE ...）                  |
| 参数类型       | STRING、INT、FLOAT、BOOL、DOUBLE、BOOLEAN           | 任意SQL类型（int、text、jsonb、array等）               |
| 返回类型       | STRING、INT、FLOAT、BOOL、DOUBLE、BOOLEAN           | 任意SQL类型                                           |
| 隐式类型转换   | 支持，规则有限                                      | 支持，类型系统更丰富                                   |
| 重载           | 仅支持参数个数不同，不支持同名同参不同类型           | 支持参数个数/类型/返回类型多重重载                     |
| 默认参数       | 支持default关键字                                   | 支持（可选）                                           |
| 复杂表达式     | 支持简单表达式，复杂表达式/嵌套有限                 | 支持任意复杂表达式、嵌套                               |
| 调用方式       | SELECT func(args)                                   | SELECT func(args)                                      |
| 典型示例       | `SELECT UPPER(_host)`<br>`CREATE FUNCTION f(@k int) RETURNS string RETURN ...` | `SELECT upper(col)`<br>`CREATE FUNCTION f(int) RETURNS text AS $$...$$ LANGUAGE plpgsql;` |
| 不支持         | 复杂类型、数组、jsonb、bytea、复杂重载、PL/pgSQL等   | 基本无明显限制                                         |

#### 说明与建议
- 炎凰SQL标量函数适合常见数据清洗、转换、简单自定义逻辑。
- PG标量函数适合复杂数据处理、类型系统、过程控制、异常处理等。
- LLM链路如需跨平台，建议仅用炎凰SQL支持的函数和类型。

---

### 16.2 表函数（Table Function）对比

| 对比项         | 炎凰SQL                                             | PostgreSQL                                             |
|----------------|-----------------------------------------------------|--------------------------------------------------------|
| 内置表函数     | 少量（如ip_location等平台内置）                     | 丰富（generate_series、unnest、jsonb_array_elements等）|
| 用户自定义     | 支持（CREATE FUNCTION ... RETURNS TABLE/AS ...）     | 支持（CREATE FUNCTION RETURNS SETOF ...）              |
| 参数类型       | 仅支持字面常量、表值参数，类型有限                  | 任意SQL类型、支持复杂表达式、LATERAL参数               |
| 返回类型       | 仅支持TABLE（事件集结构）                            | 任意表结构、可返回复合类型、嵌套表                     |
| 重载           | 仅支持参数个数不同，不支持同名同参不同类型           | 支持参数个数/类型/返回类型多重重载                     |
| 默认参数       | 支持default关键字                                   | 支持（可选）                                           |
| 复杂表达式     | 不支持复杂表达式、LATERAL、UNNEST等                  | 支持任意复杂表达式、LATERAL、UNNEST、嵌套              |
| 调用方式       | FROM/OUTER APPLY/CROSS APPLY/SELECT * FROM func(...) | FROM/LATERAL/SELECT * FROM func(...)                   |
| 典型示例       | `CREATE FUNCTION get_events(@ds table, @k string) AS (SELECT * FROM @ds WHERE CONTAINS(@k))`<br>`SELECT * FROM get_events(main, 'GET')` | `SELECT * FROM generate_series(1,10)`<br>`SELECT * FROM unnest(array[1,2,3])`<br>`CREATE FUNCTION f(int) RETURNS SETOF record AS $$...$$ LANGUAGE plpgsql;` |
| 不支持         | LATERAL、UNNEST、复杂类型、嵌套表、PL/pgSQL等        | 基本无明显限制                                         |

#### 说明与建议
- 炎凰SQL表函数适合简单数据集过滤、批量处理、平台内置增强。
- PG表函数适合复杂数据生成、数组/JSON处理、递归、过程控制等。
- LLM链路如需跨平台，建议仅用炎凰SQL支持的表函数和参数类型。

---

> 如需继续梳理其它语法（如SHOW TABLES、DROP FUNCTION、WITH参数、类型推断等），请补充下方章节。 