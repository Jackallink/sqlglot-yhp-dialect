---
title: SQL 语法
---

# SQL 语法

## SQL 标识符

### 不带引号的标识符

支持字符有：`_`, `$`, `0-9`, `a-z`，也支持中文字符，可以表达：

- 字段名，**大小写敏感**，这里不同于关系型数据库，平台允许数据集同时存在`FIELD`和`field`两个不同字段

  下述查询返回的结果是**不同**的。
  
  ```sql
  SELECT field FROM main
  
  SELECT Field FROM main
  ```

  给字段一个中文别名：

  ```sql
  SELECT _source AS 来源 FROM main
  ```
  
- 数据集名称，大小写不敏感

  ```sql
  -- 这些查询等效
  SELECT main.Field FROM main
  
  SElECT MAIN.Field FROM main
  
  SELECT main.Field FROM mAIn
  ```
  
- 函数名称，大小写不敏感

### 单引号标识符

字符串常量。

示例：

```sql
SELECT 'literal value' as field_name FROM main LIMIT 1
```

结果集：

|  field_name   |
| :-----------: |
| literal value |

如果字符串常量中有 c-style 转义字符 ```['\n', '\r', '\b', '\f', '\t']```，需要使用前缀 ```E``` 来表示。其他 ```\x``` 格式会默认转义为 ```x```。

示例 1：

```sql
SELECT E'abc\ndef\gh' as field_name FROM main LIMIT 1
```

结果集 1：

|  field_name   |
|:-------------:|
| abc<br/>defgh |

示例 2：

```sql
SELECT 'abc\nd' as field_name FROM main LIMIT 1
```

结果集 2：

| field_name |
|:----------:|
|   abc\nd   |

如果字符串常量中有 4-digit/6-digit unicode 编码（格式为 ```[\xxxx, \+xxxxxx]```），需要使用前缀 ```U&``` 来表示。同时支持使用 ```UESCAPE``` 关键字来改变默认转义标识符号 ```'\'```。如果需要显示转义标识符，可以通过两个转义标识符进行转义。

示例 1：

```sql
SELECT U&'\0061bcd' as field_name FROM main LIMIT 1
```

结果集 1：

| field_name |
|:----------:|
|    abcd    |

示例 2：

```sql
SELECT '\0061bcd' as field_name FROM main LIMIT 1
```

结果集 2：

| field_name |
|:----------:|
|  \0061bcd  |

示例 3：

```sql
SELECT U&'!0061bcd!!' UESCAPE '!' as field_name FROM main LIMIT 1
```

结果集 3：

| field_name |
|:----------:|
|   abcd!    |

:::tip

如果字符串常量中有单引号，需要使用单引号转义

示例：

```sql
SELECT 'tom''s cat' as field_name FROM main LIMIT 1
```

结果集：

| field_name |
| :--------: |
| tom's cat  |

:::

### 双引号标识符

用双引号引起来的表达都是大小写敏感的，表意同不带引号的标识符，主要用于含有特殊字符的标识符。

- 字段名，大小写敏感
- 数据集名称，大小写敏感
- 函数名称，大小写敏感

示例：

```sql
SELECT table_left."field left", table_right."FIELD right"
FROM table_left JOIN table_right
ORDER BY table_left."order Field"
GROUP BY table_right."group field"
```

同时也支持 4-digit/6-digit unicode 编码格式，使用方式同单引号标识符。

:::tip

如果双引号标识符中含有双引号，需要使用双引号转义

```sql
SELECT 1 as "escape double ""quotes" 
```

结果集：

| escape double "quotes |
| :-------------------: |
|           1           |

:::

### 数值类型运算

平台支持如下的二元数值运算操作符，所有的二元运算符都需要符合 `<expr1> <op> <expr2>`的语法，`expr1`是左值，`expr2`是右值，`op`是运算操作符。
1. `+`：加法
1. `-`：减法
1. `*`：乘法
1. `/`：除法
1. `%`：取模

:::tip 

1. 所有的左值和右值都可以是字段名，常量或者是另外一个表达式的结果
2. 如果左值或者右值不是数字类型的话，会执行隐式转换，具体转换规则，可以参考[隐式转换](#隐式转换)章节
3. 运算符的默认优先级是 `*` `/` `%` 大于 `+` `-`
4. 可以使用括号来定义表达式运算的优先级

:::


## SQL 语法关键字

### APPLY

使用`APPLY`算子可以对表进行丰富(Table Enrichment)，达到增加字段的目的。可以将`APPLY`算子看作特殊的相关子查询或侧向join的表达。不同于相关子查询的是，`APPLY`算子可以返回多个列及多个行的二维表结构。`APPLY`算子对左表每一行计算组合得到右表后，将左右表联合在一起返回。目前只支持非SQL表函数的`APPLY`操作，对于SQL表函数，可以用`JOIN`表达类似的效果。


APPLY语法如下：
```sql
FROM left_table_source OUTER/CROSS APPLY right_table_source
```
- 通过`APPLY`算子，可以将表函数生成的结果集作为右表`right_table_source`和原始表`left_table_source`进行关联
- `CROSS`和`OUTER`的区别在于，当左表某一行没有计算结果时，`CROSS APPLY`会去掉这一行，而`OUTER APPLY`会保留这一行，对应的右表会用空值填充
  :::caution
  
  `right_table_source`可以引用`left_table_source`的字段，目前支持两种形式
  - **非SQL表函数**(Table Function)，表函数参数可以引用左表中的字段，但**不可使用表达式字段**
  - APPLY投影：`( SELECT expression [, expression]* )`，这里的投影不同于基础查询中的投影，执行发生在不同时间

  :::
- 为了区分`left_table_source`和`right_table_source`中的字段，请**给表以别名**，并对**所有字段限定表名**，不可省略

:::caution

在平台中，APPLY表函数参数只适用于**字段名**(Field Name)，**字面常量**(Literal Value)或**表值参数**(Table-valued Parameters)

:::

样例：
1. 查询ip字段，将ip对应的位置信息增强到表当中
   ```sql
   SELECT * 
   FROM main 
        OUTER APPLY ip_location(main.ip) ip_table
   ```
   
1. 对字段进行标量计算增强到表当中
   ```sql
   SELECT table_bar.upper_message, main._message
   FROM main
   APPLY (SELECT UPPER(main._message) AS upper_message) AS table_bar
   WHERE table_bar.upper_message LIKE '%GET%'
   ```
   这里可以解决下面的无效查询所表达的内容：
   ```sql
   --- 这个查询无效
   SELECT *, UPPER(main._message) AS upper_message
   FROM main
   WHERE upper_message LIKE '%GET%'
   ```
   
1. `APPLY`算子可以和`JOIN`级联表达丰富的字段增强
   ```sql
   SELECT *
   FROM main
       OUTER APPLY ip_location(main.ip) ip_table
       APPLY (SELECT SUBSTR(ip_table.location, 3) AS city) city_table
       INNER JOIN user_account ON main.user_id=user_account.id
   ```
   
1. APPLY投影

   ```sql
   SELECT *
     FROM main
          APPLY (
            SELECT LOWER(main.request_method) AS upper_request_method,
                   SUBSTR(main.message, 3, 5) AS host
            ) AS table_bar
   ```



### CAST


使用`cast`操作符对数据类型进行转换。
- 基本的语法 `cast(<expr> as <type>)`，其中`expr`可以是一个字段名，一个函数运算表达式或者是数值运算表达式，
  或者是一个常量值。`type`可以是如下的关键字之一，`int long float double string bool boolean`。
- 当在字符串和浮点数之间转换的时候，浮点数精度是38位数字，并且小数点后只保留5位。
- 整数`int`和`long`的范围是 [-2<sup>63</sup>, 2<sup>63</sup>-1]
- 浮点数`float`和`double`的范围是 [-10<sup>34</sup>+10<sup>-5</sup>, 10<sup>34</sup>-10<sup>-5</sup>]
- 小数类型 `decimal(precision, scale)` 的范围是 `precision` [1, 38]， `scale` [0, `precision`]；注意，当给定的数值整数部分的位数小于`precision-scale`时，例如`123.4`对应的类型是`decimal(3,1)`时，因数值越界将返回空值`NULL`

:::tip

在平台当中，原始数据提取的字段，默认都是字符串类型的，因为原始数据是通过文本方式存储的。在查询过程中，为了方便使用，会根据使用场景进行[隐式转换](#隐式转换)。因此，在常见的使用场景中是不需要进行额外类型转换的；而在少数隐式转换没有发生的情况下，对字段进行类型转换是必要的。

:::

样例：
1. 查询ngnix accesslog
   ```sql
   SELECT sum(cast(size as float)), max(cast(size as int)), method, agent
   FROM main 
   WHERE _datatype='nginx.access_log'
   GROUP BY method, agent
   ```



### CONTAINS  {#contains}

`CONTAINS`函数帮助用户完成全文检索的功能。该函数默认作用于数据集的原始事件(raw event)，即 **_message** 字段，用以过滤包含指定关键字的事件。也可以用于指定字段的过滤，比如 `CONTAINS(foo, 'get')`，用于搜索字段 `foo` 中包含 `get` 关键字的事件。
该函数用在事件过滤`WHERE`语法中，且只能使用字符串字面常量(Literal Value)作为参数。

#### 大小写
检索关键字是大小写**不敏感**的，`CONTAINS('gEt')` 和`CONTAINS('get')`是等效的：

```sql
SELECT _message FROM main WHERE CONTAINS('gEt')
-- 返回结果集
|                                   _message                  |
| ..."GET /administrator/ HTTP/1.1" 200 4263 "-" Mozilla/...  |
| ..."GET /templates/_system/css/general.css HTTP/1.1" 40...  |

```
#### 分词
`CONTAINS`默认会对传入的关键字做分词(`tokenization`)，在分词过程中会根据主要分词符(`Major Breaker`)和次要分词符(`Minor Breaker`)将输入的关键字做切分成多个词项进行检索。

* 主要分词符`Major Breaker`: `[]<>(){}|!;,'"*\n\r\t &?+`
* 次要分词符`Minor Breaker`: `/:=@.-$#%\_`


比如`CONTAINS('foo bar')`会被切分成`foo`，`bar`两个词项来搜索，等效于`CONTAINS('foo') AND CONTAINS('bar')`。

使用更精准的词项查询，可以提高查询的效率。如果不想让`CONTAINS`的参数分词，可以添加`tokenized`参数，设置为`false`。比如查询`CONTAINS('192.168.1.1', false)`会将`192.168.1.1`整体当作一个词项去查询索引，而不是分成`192`/`168`/`1`三个词项去查询索引。一般来说，当一个关键字中包含了一个或者多个次要分词符例如`.`或者`/`，但是希望将关键字作为一个词项查询加速查找时可以设置`tokenized`参数为`false`。

多字节的每个字符会被当作一个词项，比如`CONTAINS('中文')`会被分成`中`/`文`两个词项去查询索引。
目前关键字中的主要分词符会被忽略，比如`CONTAINS('foo,bar')`会被分成`foo`/`bar`两个词项去查询索引，又比如`CONTAINS('[INFO]')`中的`[`和`]`会被忽略，会被分成`INFO`一个词项去查询索引。
#### 通配符搜索
`CONTAINS`函数支持通配符搜索，可以使用`*`和`?`两种通配符，其中:
* `*`表示匹配任意多个字符
* `?`表示匹配任意一个字符

通过使用通配符，可以查找与通配符匹配的多个词项。比如`CONTAINS('foo*')`会匹配`foo`，`foobar`，`foobaz`等多个词项，而`CONTAINS('foo?')`只会匹配`fooa`，`foob`等词项。
关键字中可以包含多个通配符，比如`CONTAINS('foo*bar?')`会匹配`foobar`，`foobarz`，`foo1barz`等多个词项。

:::caution

 当查询中包含多个数据集时，例如`JOIN`查询，平台无法认知对哪一个数据集进行过滤，此时需要用户显示指定表名和对应的`_message`， 例如： `CONTAINS(table_name._message, 'keyword term')`。

请不要使用通配符去匹配标点符号。比如数据中包含`index1.php`，可以通过`CONTAINS('index*.php')`或者`CONTAINS('index?.php')`来检索，但是无法通过`CONTAINS('index???hp')`来检索因为这一表达式会被期望匹配一个长度为10个字符的单个词项。

:::
#### 样例

1. 基本的`AND`条件查询：查询`method`为`GET`的`nginx.accesslog`
   ```sql
   SELECT
     *
   FROM
     main
   WHERE
     _datatype = 'nginx.accesslog'
     AND method = 'GET'
   ```
   
2. 使用`CONTAINS`函数过滤`_message`字段包含特定字符串的事件，查询tweet数据集当中，不包含`awesome`的事件
   ```sql
   SELECT
     user,
     "text" -- 这里双引号字符串 text 是一个字段
   FROM
     tweet
   WHERE
     NOT CONTAINS('awesome') -- 注意这里只能使用单引号的字符串字面常量(Literal Value)
   ```
   
   ```sql
   SELECT
     *
   FROM
     table_a
     inner join table_b ON table_a.col_a = table_b.col_b
   WHERE
     CONTAINS(table_a._message, 'keyword term')
   ```
   
3. 多个布尔条件运算的优先级可以使用括号来表示，查询`nginx.accesslog`，过滤出`method`为`GET`，`agent`是`Firefox`，或者路径不是`/index.html`的日志。

   ```sql
   SELECT
     *
   FROM
     main
   WHERE
     _datatype = 'nginx.accesslog'
     AND (
       (
         method = 'GET'
         AND agent LIKE '%Firefox%' -- 注意这里只能使用单引号的字符串字面常量(Literal Value)，并且大小写敏感
       )
       OR path NOT LIKE '%index.html' -- 平台不支持 column like column
     )
   ```
   
4. 筛选时间范围

   ```sql
   SELECT
     *
   FROM
     main
   WHERE
     _time >= '2015-12-12T20:00:00.000Z'
     AND _time <= '2015-12-11T20:00:00.000Z'
   ```

### CASE

使用CASE来表达多路条件选择。语法
```sql
 CASE <expression_case> 
    WHEN <expression_when> 
    THEN <expression_then> 
    ELSE <expression_else>  
 END
```

- `CASE`后可以跟需要比较的字段名，该字段名是可选的。
- `WHEN`后可以跟条件表达式，当该条件表达式是true的时候，执行`THEN`关键字之后的操作。
- `ELSE`是一个可选的部分，后跟着默认需要执行的操作，当所有的条件都不满足的时候，执行该默认的操作。

样例：
1. 查询nginx accesslog，根据method的情况，对字段`operation`进行赋值
   ```sql
   SELECT 
    CASE method 
      WHEN 'GET' 
      THEN 'read' 
      WHEN 'POST' 
      THEN 'write' 
      ELSE 'unknown' 
    END AS operation, method
   FROM main WHERE _datatype = 'nginx.access_log'
   ```
2. 查询nginx accesslog，根据status code返回字符串
   ```sql
   SELECT 
    CASE
        WHEN code = '200'
        THEN 'succeed'
        ELSE 'failed'
    END AS code_str, code
   FROM main WHERE _datatype = 'nginx.access_log'
   ```

### COLUMNS

使用`COLUMNS(REGEX)`，将所有字段名称与正则表达式进行匹配，匹配到的字段名称将会被加入结果集中做一个批量选择。正则表达式匹配字段名称时，会以search方式进行搜索。另外，当`COLUMNS(REGEX)`与`as`一起使用时，将会对匹配到的字段做批量重命名。

#### 批量投影列表

- `COLUMNS`修饰符 : `EXCEPT`与`REPLACE`
- `COLUMNS(REGEX) EXCEPT ( column_name [, column_name]* )`指定要从结果中排除的一个或多个列的名称，只能和查询星号或`COLUMNS`一起使用
- `COLUMNS(REGEX) REPLACE ( expr as column_name[,expar as column_name]* )`可以指定将对某个列按传入的表达式进行计算并替换，但只能和查询星号或或`COLUMNS`一起使用
- `COLUMNS(REGEX) EXCEPT(column_name [, column_name]* ) REPLACE ( expr as column_name[,expar as column_name]* )` 可以指定对某个列按传入的表达式进行计算并替换，并排除指定的列

1. 批量选择并排除指定列
   
   ```sql
   -- 批量选择所有f1，f2,f3,f4这四个字段并排除f1
   SELECT COLUMNS('^f[1-4]$') EXCEPT (f1) from main
   ```

2. 批量选择并输入表达式替换指定列
    ```sql
    -- 批量选择所有f1，f2,f3,f4这四个字段并使用f2+1的计算结果替换f2
   SELECT COLUMNS('^f[1-4]$') REPLACE (f2+1 as f2) 
   from main
   ```

 3. 排除指定列并输入表达式替换指定列
    ```sql
    -- 批量选择所有f1，f2,f3,f4这四个字段，排除f1字段并使用 f2+1的计算结果替换f2
    SELECT * EXCEPT(request_service) REPLACE (lower(request_method) as request_method) 
    from main
    ```

 #### 批量重命名
使用`COLUMNS(REGEX)` 与`AS `可以实现批量重命名的功能。具体示例如下:
1. 使用正则表达式匿名捕获组进行重命名
   ```sql
   select columns('f_(.*)') as "host_{0}" 
   from tbl;
   ```
     | origin field name     | rename field name      |
     | --------------------- | -----------------------|
     | f_1                   | host_1                 |
     | f_2                   | host_2                 |
     | f_3                   | host_3                 |
     | f_4                   | host_4                 |
 2. 使用正则表达式对json类型进行重命名    
    ```sql
    select columns('result_detail.stonewave.(.*)') as "{0}" 
    from tbl;
    ```
    | origin field name       | rename field name      |
    | ----------------------- | -----------------------|
    | result_detail.host.time | time                   |
    | result_detail.host.data | data                   |
 3. 使用正则表达式对join后的结果集做重命名
    ```sql
    select columns('(ID)') as "orders_customer_{0}"
    from orders
    inner join customers
    on Orders.CustomerID=Customers.CustomerID AND Orders.OrderID=Customers.CustomerID
    ```
   
    | origin field name       | rename field name      |
    | ----------------------- | -----------------------|
    | OrderID | orders_customer_OrderID                |
    | CustomerID (orders) | orders_customer_CustomerID |
    | CustomerID (customer)|orders_customer_CustomerID$1
  4. 使用命名捕获组对结果集做重命名
     ```sql
     select columns('(?P<host>host_)(?P<host_value>.*)') as "ip_{host}_{host_value}"
     from tbl
     ``` 
     | origin field name     | rename field name      |
     | --------------------- | -----------------------|
     | host_1                | ip_host_1              |
     | host_2                | ip_host_2              |
     | host_3                | ip_host_3              |
     | host_4                | ip_host_4              |
   5. columns重命名的转义字符'{'与'}'
      ```sql
      SELECT COLUMNS('f_(.*)') as "host_{\0}\_{0}"
      from tbl
      ```   
      
      | origin field name     | rename field name          |
      | --------------------- | -----------------------    |
      | f_1                   | host_{0}_1                 |
      | f_2                   | host_{0}_2                 |
      | f_3                   | host_{0}_3                 |
      | f_4                   | host_{0}_4                 |
   6. columns重命名语法糖
      ```sql
      -- _单独使用时，将会直接用第一个捕获组进行重命名
      select columns('result_detail.stonewave.(.*)') as _ 
      from tbl;
      ```     
      | origin field name       | rename field name      |
      | ----------------------- | -----------------------|
      | result_detail.host.time | time                   |
      | result_detail.host.data | data                   |
   
### DELETE

使用`DELETE FROM`可以删除满足对应查询条件的事件。

```sql
DELETE FROM <event_set>
	[WHERE where_condition]
	[ORDER BY ...]
	[LIMIT <limit_clause>]
```

* `WHERE`/`ORDER BY`/`LIMIT`都是可选的，语法可以参考对应章节；
* `DELETE FROM main` 类似这样没有指定过滤条件的删除语句会把对应数据集里面的数据都删掉，结果是一个空的数据集；
* 执行删除操作之前最好通过对应的查询确保要删除的数据是对的，以防误删；

示例：

```sql
DELETE FROM main WHERE CONTAINS('password') ORDER BY _time LIMIT 1
```

这个删除操作会删除数据集`main`中按时间升序排列后包含`password` 关键字的第一条数据。

:::tip

删除数据要求用户对该数据集有管理权限。 

:::

### DESCRIBE

使用 `DESCRIBE` 可以查看数据集结构。

```sql
DESCRIBE <event_set>
```

这个命令会列出对应数据集中的索引字段，例如：

| field     | type      |
| --------- | --------- |
| _host     | string    |
| _source   | string    |
| _datatype | string    |
| _time     | timestamp |

> 时间过滤条件对于该命令有效，即可以查看对应时间段内该数据集内的索引字段

### DISTINCT

使用`DISTINCT`关键字对字段进行去重。

样例：
1. 查询nginx accesslog, 对`status_code`去重。
   ```sql
   SELECT 
    DISTINCT code as status_code
   FROM main WHERE _datatype = 'nginx.access_log'
   ```
2. `DISTINCT`可以用于聚合函数中，包括`MIN`，`MAX`，`SUM`，`COUNT`，`AVG`。查询nginx accesslog, 把不重复的`code`加和。
   
   ```sql
   SELECT 
    SUM(DISTINCT CAST(code as int)) as code_sum
   FROM main WHERE _datatype = 'nginx.access_log'
   ```

:::caution

在GROUP BY的聚合函数当中，`DISTINCT` 语法仅支持 `COUNT`，因此如下的SQL是不支持的

:::

```sql
   SELECT 
    SUM(DISTINCT CAST(code as int)) as code_sum, method
   FROM main WHERE _datatype = 'nginx.access_log'
   GROUP BY method
```


### EXISTS

* 子查询：目前仅有`WHERE`语句中的`EXISTS`表达式支持子查询，例如以下查询会先执行子查询获取customers数据集中CustomerID字段，当子查询结果集非空时才执行外层查询显示orders数据集的数据
   ```sql
   SELECT * FROM orders WHERE EXISTS (
      SELECT CustomerID 
      FROM customers
      )
   ```
   * 暂不支持关联子查询，例如
   ```sql
   SELECT CustomerID FROM orders AS outside WHERE EXISTS(
        SELECT CustomerID
        FROM customers AS inside
        WHERE inside.CustomerID = outside.CustomerID
        )
   ```
   * 暂不支持在`WHERE`语句之外使用`EXISTS`，例如
   ```sql
   SELECT EXISTS (SELECT 1)
   ```

### FROM

`FROM`子句表示要从中检索行的一个或多个表，并指定如何将这些行联接在一起来生成单个行流，以便在查询的其余部分进行处理。
可以在`FROM`子句中引入显示别名。
数据集子句列表：

- 现有表的名称：table_name
- 多表`|`分隔表达合集，此表达会将所列数据集纵向连接：`table_name_1 | table_name_2 [ | table_name_n ]`
- join子句，请参见[关联join](#关联join)
- 多表逗号分隔表达join：`table_name_1, table_name_2 [ , table_name_n ]`
- 表子查询或with查询名，请参见[表子查询和公用表表达式common-table-expression](#CTE)
- 表函数，请参见[表函数](../sql_function/table_function.mdx)

样例：
1. 查询main表
   ```sql
   SELECT *
   FROM main
   ```
2. 查询多表合集
   ```sql
   SELECT * 
   FROM access_log_svc_1 | access_log_svc_2
   ```

### 聚合函数

可以使用如下聚合函数进行聚合分析:

|算子名|功能|语法
|:--|:--|:--|
|`COUNT`|统计行数，不包括NULL值，`COUNT(*)`包括NULL值|`COUNT(expression)`
|`SUM`|统计和|`SUM(expression)`
|`AVG`|统计平均值|`AVG(expression)`
|`MAX`|统计最大值|`MAX(expression)`
|`MIN`|统计最小值|`MIN(expression)`
|`MAX_STR`|按照字符串规则统计最大值|`MAX(expression)`
|`MIN_STR`|按照字符串规则统计最小值|`MIN(expression)`
|`STDDEV_POP`|计算总体标准差|`STDDEV_POP(expression)`
|`STDDEV_SAMP`|计算样本标准差|`STDDEV_SAMP(expression)`
|`VAR_POP`|计算总体方差|`VAR_POP(expression)`
|`VAR_SAMP`|计算样本方差|`VAR_SAMP(expression)`
|`STRING_AGG`|实验性功能：拼接每行表达式`expression`的值，并在其间放置分隔符`separator`|`STRING_AGG(expression, separator)`
|`QUANTILE_T_DIGEST`|实验性功能：使用T-Digest算法计算数值数据的近似分位数|`QUANTILE_T_DIGEST(expression, fraction)`，其中`fraction`为分位数水平，允许值范围为[0,1]
|`PERCENTILE`|实验性功能：等价于`QUANTILE_T_DIGEST`|`PERCENTILE(expression, fraction)`
|`APPROX_COUNT_DISTINCT`|近似值计算函数，使用概率数据结构来估算唯一值的数值，适用于大数据量下在可接受的误差范围内快速返回结果|`APPROX_COUNT_DISTINCT(expression)`
|`APPROX_MEDIAN`|使用T-Digest算法计算数值数组的近似中位数|`APPROX_MEDIAN(expression)`
|`PRODUCT`|用于计算给定列的数值的乘积|`PRODUCT(expression)`
|`FIRST_VALUE`|默认返回组内的第一个非空值|`FIRST_VALUE(expression)`
|`LAST_VALUE`|默认返回组内的第一个非空值|`LAST_VALUE(expression)`
|`LATEST_VALUE`|返回组内时间属性_time最大的值所在行的对应字段值，若存在多个_time最大值，则返回字段值的结果不确定|`LATEST_VALUE(expression)`
|`EARLIEST_VALUE`|返回组内时间属性_time最小的值所在行的对应字段值，若存在多个_time最小值，则返回字段值的结果不确定|`EARLIEST_VALUE(expression)`

### GROUP BY

使用`group by`配合以下聚合运算算子，可以对数据进行聚合分析。需要注意

1. `group by`后的列只能是`int`或者`string`类型的，对于浮点类型的列，是不支持的，需要使用`cast`功能转换成别的类型。
1. 不支持不明确的非聚合列的查询。例如，以下查询是不支持的，因为`select`中的非聚合列method未出现在`group by`语句中。
```sql
SELECT method, agent, SUM(size) FROM main GROUP BY agent;
```
1. 支持的聚合算子如下：包括 `COUNT SUM AVG MAX MIN`

|算子名|功能|语法
|:--|:--|:--|
|`COUNT`|统计行数，不包括NULL值，`COUNT(*)`包括NULL值|`COUNT(expression)`
|`SUM`|统计和|`SUM(expression)`
|`AVG`|统计平均值|`AVG(expression)`
|`MAX`|统计最大值|`MAX(expression)`
|`MIN`|统计最小值|`MIN(expression)`
|`MAX_STR`|按照字符串规则统计最大值|`MAX(expression)`
|`MIN_STR`|按照字符串规则统计最小值|`MIN(expression)`
|`STDDEV_POP`|计算总体标准差|`STDDEV_POP(expression)`
|`STDDEV_SAMP`|计算样本标准差|`STDDEV_SAMP(expression)`
|`VAR_POP`|计算总体方差|`VAR_POP(expression)`
|`VAR_SAMP`|计算样本方差|`VAR_SAMP(expression)`
|`STRING_AGG`|实验性功能：拼接每行表达式`expression`的值，并在其间放置分隔符`separator`|`STRING_AGG(expression, separator)`
|`QUANTILE_T_DIGEST`|实验性功能：使用T-Digest算法计算数值数据的近似分位数|`QUANTILE_T_DIGEST(expression, fraction)`，其中`fraction`为分位数水平，允许值范围为[0,1]
|`PERCENTILE`|实验性功能：等价于`QUANTILE_T_DIGEST`|`PERCENTILE(expression, fraction)`
|`APPROX_MEDIAN`|使用T-Digest算法计算数值数组的近似中位数|`APPROX_MEDIAN(expression)`
|`PRODUCT`|用于计算给定列的数值的乘积|`PRODUCT(expression)`
|`FIRST_VALUE`|默认返回组内的第一个非空值|`FIRST_VALUE(expression)`
|`LAST_VALUE`|默认返回组内的第一个非空值|`LAST_VALUE(expression)`
|`LATEST_VALUE`|返回组内时间属性_time最大的值所在行的对应字段值，若存在多个_time最大值，则返回字段值的结果不确定|`LATEST_VALUE(expression)`
|`EARLIEST_VALUE`|返回组内时间属性_time最小的值所在行的对应字段值，若存在多个_time最小值，则返回字段值的结果不确定|`EARLIEST_VALUE(expression)`

样例：
1. 查询nginx accesslog，得到size的统计信息
   ```sql
   SELECT 
      avg(cast(size as int)), 
      count(size), 
      sum(cast(size as int)), 
      max(cast(size as int)), 
      min(cast(size as float)), 
      stddev_pop(cast(size as int)),
      var_samp(cast(size as int)),
      quantile_t_digest(cast(size as int), 0.5),
      method, 
      agent  
   FROM main 
   WHERE _datatype='nginx.access_log'
   GROUP BY method, agent
   ```
   注意：
   - 在使用`AVG SUM MAX MIN STDDEV_POP STDDEV_SAMP VAR_POP VAR_SAMP`这样的数值运算操作的时候，需要保证输入的列类型是`int`或者`float`，因此，需要使用
        `cast`功能将列转换成数值类型。
   - 在计算标准差、方差时必须要加上`GROUP BY`，如果不需要分组，则可以加上`GROUP BY dummy_field`进行填充。
   - `STRING_AGG`是实验性功能，未来行为可能改变。
      - 需要保证输入的列类型是`string`，否则需要使用`cast`功能转换成`string`类型。
      - 空值`NULL`会被忽略，且不会添加相应的分隔符
      - `separator`没有默认值，需要显式给定一个单引号包围的字符串，如`‘_’`, `‘,‘`
      - 必须和`GROUP BY`一起使用，即使不需要分组也需要添加一个不存在的字段的分组，如`SELECT STRING_AGG(expr, ',') FROM event_set`需要写为`SELECT STRING_AGG(expr, ',') FROM event_set GROUP BY "dummy"`
   - `QUANTILE_T_DIGEST`/`PERCENTILE`是实验性功能，未来语法或行为可能改变。
      - 必须和`GROUP BY`一起使用，即使不需要分组也需要添加一个不存在的字段的分组，如`SELECT QUANTILE_T_DIGEST(expr, 0.5) FROM event_set`需要写为`SELECT QUANTILE_T_DIGEST(expr, 0.5) FROM event_set GROUP BY "dummy"`
      - 暂不支持在窗口函数中使用
      - 分位数结果是近似值，可能出现不存在于输入数据中的数值结果

#### GROUP BY TIME 按时间间隔分组
在 `GROUP BY` 后面除了连接一般的表达式之外，还可以连接扩展选项 `TIME()` ，以生成连续的时间桶（TIME BUCKET）并对此进行分组聚合运算。
`TIME()` 支持以下参数以键值对的方式配置，所有参数均可缺省。
- start，生成时间桶的起始时间，缺省值为当前查询的时间范围的起始时间
- end，生成时间桶的结束时间，缺省值为当前查询的时间范围的结束时间
- column，生成时间桶对应的原始字段，缺省值为 `_time`
- span，生成时间桶的时间跨度，缺省值会根据其他参数动态计算
- alignment，生成时间桶的对齐时间，缺省值会根据其他参数动态计算

:::info

使用场景为，在给定的时间范围内，以时间分桶作为分组，并补全中间缺失分桶的情况

:::

##### 样例
原始数据 `cities` 如下表

|_time|country|name|year|population|
|--|--|--|--|--|
|2000-01-01T00:00:00|NL|Amsterdam|2000|1005|
|2010-01-01T00:00:00|NL|Amsterdam|2010|1065|
|2020-01-01T00:00:00|NL|Amsterdam|2020|1158|
|2000-01-01T00:00:00|US|Seattle|2000|564|
|2010-01-01T00:00:00|US|Seattle|2010|608|
|2020-01-01T00:00:00|US|Seattle|2020|738|
|2000-01-01T00:00:00|US|NewYorkCity|2000|8015|
|2010-01-01T00:00:00|US|NewYorkCity|2010|8175|
|2020-01-01T00:00:00|US|NewYorkCity|2020|8772|

运行以下查询，生成 `1990-01-01T00:00:00` 到 `2020-01-01T00:00:00` 之间以 `5 years` 为跨度的时间分桶对应统计结果

```sql
select  _time, country, sum(population) from cities
group by country, time(start='1990-01-01T00:00:00', end='2020-01-01T00:00:00', span='5 years')
order by _time asc
```

得到以下结果

|_time|country|sum(population)|
|--|--|--|
|1990-01-01T00:00:00.000+08:00|Null|Null|
|1995-01-01T00:00:00.000+08:00|Null|Null|
|2000-01-01T00:00:00.000+08:00|NL|1005|
|2000-01-01T00:00:00.000+08:00|US|8579|
|2000-01-01T00:00:00.000+08:00|Null|Null|
|2005-01-01T00:00:00.000+08:00|Null|Null|
|2010-01-01T00:00:00.000+08:00|NL|1065|
|2010-01-01T00:00:00.000+08:00|US|8783|
|2010-01-01T00:00:00.000+08:00|Null|Null|
|2015-01-01T00:00:00.000+08:00|Null|Null|
|2020-01-01T00:00:00.000+08:00|NL|1158|
|2020-01-01T00:00:00.000+08:00|US|9510|
|2020-01-01T00:00:00.000+08:00|Null|Null|

### HAVING

使用`HAVING`关键字可以过滤事件。

- `HAVING`关键字后面可以包含`AND`和`OR`组合的布尔表达式,`HAVING`关键字后面布尔表达式与`WHERE`关键字表现类似，具体可以参考上方`WHERE`文档。
- `HAVING`关键字必须跟在`GROUP BY`关键词后面，支持聚合函数（Aggregation）的过滤。现在暂不支持直接使用`HAVING`过滤。
- `HAVING`关键字对于有歧义的字段会以投影中出现的第一个匹配的字段进行过滤（详情见样例3）。

#### 样例

1.对于查询`GROUP BY`中的变量进行过滤。

   ```sql
   SELECT _datatype
   FROM main
   GROUP BY _datatype
   HAVING _datatype LIKE '%access_log%'
   ```

2.对于查询使用聚合函数进行过滤

   ```sql
   SELECT count(*)
   FROM main
   GROUP BY _datatype
   HAVING sum(_value1) > 10
   ```

3.有歧义的字段如下方所示，会以第一个出现的命名为_datatype的字段作为过滤，即count（*）作为过滤字段。
   ```sql
   SELECT count(*) as a, _datatype as a
   FROM main
   GROUP BY _datatype
   HAVING a > 10
   ```

### IN

* 在使用`IN`关键字查询的时候，字段值类型会根据`IN`后续的表达式列表中的数据类型做自动的类型转换，例如 `field_a IN ('abc', 123)`， 则字段`field_a`会先转换成字符串类型判断是否为`'abc'`，如果不是，再转换成数值类型判断是否是数值`123`。
* 如果字段`field_a`是索引字段并且`IN`后续表达式是常量表达式，平台会自动使用字段的索引加速查询。例如`field_a IN ('abc', 123)`，平台会以`123`和`abc`为关键字去查询字段`field_a`的索引。
* 不建议将浮点数放在`IN`后续的表达式中，因为浮点数在一些情况下因为精度损失问题没办法直接进行相等比较。
* 子查询：目前仅有`WHERE`语句中的`IN`表达式支持子查询，例如以下查询将以子查询的结果过滤orders数据集的CustomerID字段
   ```sql
   SELECT * FROM orders WHERE CustomerID 
   IN (SELECT CustomerID FROM customers)
   ```
  * 子查询支持逻辑运算，例如
   ```sql
   SELECT * FROM orders WHERE CustomerID 
   IN (SELECT CustomerID FROM customers) AND CustomerID > 10
   ```
  * 如果子查询返回多列，则取第一列数据
  * 暂不支持关联子查询，例如
   ```sql
   SELECT CustomerID FROM orders AS outside WHERE outside.b IN(
        SELECT CustomerID
        FROM customers AS inside
        WHERE inside.CustomerID = outside.CustomerID
        )
   ```
  * 子查询返回值较多时，查询速度会较慢，内存消耗会较大，可以通过在子查询中加上`DISTINCT`进行优化，例如
   ```sql
   SELECT * FROM orders WHERE CustomerID 
   IN (SELECT DISTINCT CustomerID FROM customers)
   ```

### JOIN

`JOIN`子句合并两个`table_source_item`，以便`SELECT`子句可以将它们作为一个源进行查询。`join_type`和`ON`子句(**联接条件**)指定如何组合和舍弃两个`table_source_item`中的行来形成单个源。

语法如下
```sql
joinPart:
    table_source_item [ join_type ] JOIN table_source_item
    [ ON bool_expression ]

join_type:
    { INNER | CROSS | LEFT [OUTER] }
```

- `join`的左值和右值必须是两张表
- `ON`之后跟随的表达式必须是用`AND`连接的相等条件逻辑表达式
- 目前`join`的实现方式是hash join，默认会对右表建立哈希表，因此尽量将短表放在右边
- 在`join`查询中，所有的字段名请限定表名
- 如果不指定类型，默认是`INNER JOIN`

样例：
```sql
-- left join
SELECT * FROM Orders 
LEFT JOIN Customers 
ON Orders.CustomerID=Customers.CustomerID

-- cross join
SELECT * FROM Orders 
CROSS JOIN Customers

-- inner join
SELECT Orders.CustomerID, Orders.OrderID, Customers.CustomerID, Customers.CustomerName, Customers.Country
FROM Orders 
INNER JOIN Customers
ON Orders.CustomerID=Customers.CustomerID

-- 多重联接条件
SELECT Orders.CustomerID, Orders.OrderID, Customers.CustomerID 
FROM Orders 
INNER JOIN Customers 
ON Orders.CustomerID=Customers.CustomerID AND Orders.OrderID=Customers.CustomerID

-- 联接条件含表达式
SELECT Orders.*, Customers.CustomerName
FROM Orders 
INNER JOIN Customers 
ON Orders.CustomerID+1=Customers.CustomerID
```

:::tip 

目前，join的实现是hash join，因此，所有的join都会发生在内存，所以当两个大表join的时候，需要保证有足够多的内存。 

:::




### LIMIT

使用`limit`可以限制一个查询的结果集的数量。 limit语句支持如下两种语法：
1. `LIMIT <number_limit> (OFFSET number_offset)`
2. `LIMIT number_offset, number_limit`

两种语法能实现同样的功能，例如，需要获取结果集的从第3条开始的10条数据，可以使用 `LIMIT 10 OFFSET 3` 或者 `LIMIT 3, 10`。

样例：
1. 查询nginx accesslog，返回第10条到第20条数据
    ```sql
    SELECT * 
    FROM main 
    WHERE _datatype = 'nginx.access_log'
    LIMIT 10 OFFSET 10
    ```


### ORDER BY


使用`order by`对查询结果进行排序
- `order by`后续可以接`asc`或者`desc`分别表示升序或者降序排列结果集，默认是升序
- `order by`会根据数据类型选择不同的两两比较方式，其规则如下：
   - 数据是数字则会按照数字大小进行比较，例如`1 < 2 < 10`
   - 数据是字符串则会考虑是否有数字前缀选择不同的比较方式
      - 两个字符串均有数字前缀则会先按照数字前缀大小比较，再以后面的字符串按照字典序比较，例如`2.1a < 2.1b < 10`
      - `inf`, `infinity`, `NaN`等可以表达特殊数字的字母组合无论大小写均会被认为是字符串而不是数字，例如`1 < -inf < b < c < inf < z`
      - 一个字符串无数字前缀则按照字典序比较，例如`1 < 1a < b < c`
      - 无论升序或者降序，空值(`null`)总会置于结果最后

样例：
1. 查询 nginx accesslog
   ```sql
   SELECT content_size, method, agent FROM (
        SELECT CAST(size AS int) AS content_size, method, agent FROM main 
            WHERE _datatype='nginx.access_log') 
   ORDER BY method ASC, content_size DESC
   ```


:::tip

在平台当中，默认的字段类型搜索的时候都是字符串类型，因此，size是一个字符串类型。`order by`会自动把size按照数字类型进行比较。

:::

### PARTITION BY (窗口函数)

窗口函数可以对数据进行分组计算，与`GROUP BY`不同的是，
窗口函数可以为每组数据返回多个值，目前支持的功能如下：

|功能|样例|支持程度|
|:--|:--|:--|
|在`SELECT`中使用基本窗口函数|`SELECT COUNT(*) OVER (PARTITION BY id ORDER BY time DESC)`|支持|
|在`ORDER BY`中使用窗口函数|`SELECT * ORDER BY COUNT(*) OVER (PARTITION BY id)`|不支持|
|对窗口函数进行运算|`(COUNT(*) OVER ()) + 1`|不支持，可以使用子查询替代|
|窗口分区子句`PARTITION BY`|`COUNT(*) OVER (PARTITION BY id)`|支持|
|窗口排序子句`ORDER BY`|`COUNT(*) OVER (ORDER BY id)`|部分支持，由于暂不支持`RANGE`子句，若未指定框架子句，则会加上默认窗口子句`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`|
|窗口框架(Frame)子句|`ROWS RANGE INTERVAL GROUPS`|支持`ROWS`|
|`WINDOW`子句|`WINDOW w AS`|不支持|
|聚合函数|`COUNT SUM AVG MAX MIN`|支持前述函数|
|非聚合函数|`RANK ROW_NUMBER`等|支持以下函数<br/>`ROW_NUMBER()` <br/>`FIRST_VALUE(<EXPRESSION>)` <br/>`LAST_VALUE(<EXPRESSION>)` <br/> `LAG(<EXPRESSION>)`<br/> `LEAD(<EXPRESSION>)`|

样例：
1. 查询nginx accesslog，统计每类agent的size总和
   ```sql
   SELECT  
      sum(size) OVER(PARTITION BY agent)
   FROM main 
   WHERE _datatype='nginx.access_log'
   ```
1. 查询nginx accesslog，得到每类agent按照method排序后关于size的累加和
   ```sql
   SELECT  
      sum(size) OVER(PARTITION BY agent ORDER BY method ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
   FROM main 
   WHERE _datatype='nginx.access_log'
   ```

#### 窗口框架(Window Frame)
窗口框架用于在窗口分区内对行进一步限制。
语法：

```sql
frame_clause:
    frame_units frame_extent

frame_units:
    {ROWS}    

frame_extent:
    {frame_start | frame_between}

frame_between:
    BETWEEN frame_start AND frame_end

frame_start, frame_end: {
    CURRENT ROW
  | UNBOUNDED PRECEDING
  | UNBOUNDED FOLLOWING
  | expr PRECEDING
  | expr FOLLOWING
}    
```
> 目前`frame_units`仅支持`ROWS`

示例：
```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
```
在没有指定窗口框架子句(`frame_clause`)的情况下，默认的`frame`和是否有`ORDER BY`有关
* 有`ORDER BY`，默认的`frame`包含从当前分区开始到当前行，等价于：
```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```
* 没有`ORDER BY`，默认的`frame`包含当前分区的所有行，等价于：
```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
```

#### 非聚合窗口函数

| Function      | Window Frame |
| ------------- | ------------ |
| `FIRST_VALUE` | Yes          |
| `LAST_VALUE`  | Yes          |
| `ROW_NUMBER`  | No           |
| `LAG`         | No           |
| `LEAD`        | No           |

##### FIRST_VALUE

`FIRST_VALUE`返回有序数据集中的第一个值，如果指定`ignore_null=true`，则会返回第一个非`null`的值。

语法：

```sql
FIRST_VALUE (column_expr, ignore_null=false) OVER ( [ partition_by_clause ] order_by_clause [ frame_clause ] )
```

* `column_expr`是需要取值的列名；
* `ignore_null`指定是否需要忽略`null`值，默认是`false`；
* `frame_clause`目前仅支持`ROWS`窗口框架(Window Frame)子句；

例如数据集`products`中有如下数据：

| id   | name   | price | group_id |
| ---- | ------ | ----- | -------- |
| 1    | iPhone | 5000  | 1        |
| 2    | Mi     | 3000  | 1        |
| 3    | Huawei | 4000  | 1        |
| 4    | Lenovo | 8000  | 2        |
| 5    | Dell   | 6000  | 2        |

使用如下查询语句：
```sql
SELECT
   name, price, FIRST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC)
FROM products   
```
可以得到如下结果:

| name   | price | first_price |
| ------ | ----- | ----------- |
| iPhone | 5000  | 5000        |
| Huawei | 4000  | 5000        |
| Mi     | 3000  | 5000        |
| Lenovo | 8000  | 8000        |
| Dell   | 6000  | 8000        |

##### LAST_VALUE
`LAST_VALUE`返回有序数据集中的最后一个值。

语法：

```sql
LAST_VALUE (column_expr) OVER ( [ partition_by_clause ] order_by_clause [ frame_clause ] )
```

* `column_expr`是需要取值的列名；
* `frame_clause`目前仅支持`ROWS`窗口框架(Window Frame)子句；

对于上述数据集`products`，使用如下查询语句：
```sql
SELECT
   name, price, LAST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) last_price
FROM products   
```

可以得到如下结果:

| name   | price | last_price  |
| ------ | ----- | ----------- |
| iPhone | 5000  | 3000        |
| Huawei | 4000  | 3000        |
| Mi     | 3000  | 3000        |
| Lenovo | 8000  | 6000        |
| Dell   | 6000  | 6000        |

##### ROW_NUMBER
`ROW_NUMBER`用来给分区结果集加上从1开始的序列号。
语法：
```sql
ROW_NUMBER() OVER ([ partition_by_clause ] order_by_clause )
```

对于上述数据集`products`如下查询语句：

```sql
SELECT 
	name, price, ROW_NUMBER() OVER ( PARTITION BY group_id ORDER BY price DESC) row_id 
FROM products
```

可以得到如下结果:

| name   | price | row_id |
| ------ | ----- | ------ |
| iPhone | 5000  | 1      |
| Huawei | 4000  | 2      |
| Mi     | 3000  | 3      |
| Lenovo | 8000  | 1      |
| Dell   | 6000  | 2      |

##### LAG
`LAG`窗口函数用于返回窗口分区内位于当前行上方第`offset`行的值。在`SELECT`语句中使用此分析函数可将当前行中的值与先前行中的值进行比较。
语法:

```sql
LAG (column_expr [,offset] [,default]) OVER ( [ partition_by_clause ] order_by_clause )  
```
* `column_expr`是需要取值的列名；
* `offset`是取值时相对当前行向上的偏移量，默认是1, 必须是一个非负整数；
* `default`是偏移量超出分区范围时返回的字面量值，默认是`NULL`。如果给定的默认值类型和`column_expr`的类型不一致，会尝试转换成对应的类型，如果转换失败则会使用默认值`NULL`。目前支持的类型包括`INT64`/`STRING`/`DOUBLE`/`BOOL`；

例如在我们的数据集`sale`中有如下的数据：

| id   | seller_name | sale_value |
| ---- | ----------- | ---------- |
| 3    | Bob         | 7000       |
| 1    | Alice       | 12000      |
| 2    | Lily        | 25000      |

用包含`LAG`的如下的查询语句：

```sql
SELECT seller_name, sale_value,
  LAG(sale_value) OVER(ORDER BY sale_value) as previous_sale_value
FROM sale;
```

可以得到如下结果：

| seller_name | sale_value | previous_sale_value |
| ----------- | ---------- | ------------------- |
| Bob         | 7000       | NULL                |
| Alice       | 12000      | 7000                |
| Lily        | 25000      | 12000               |

##### LEAD
`LEAD`窗口函数用于返回窗口分区内位于当前行下方第`offset`行的值。在`SELECT`语句中使用此分析函数可将当前行中的值与后续行中的值进行比较。
语法:
```sql
LEAD (column_expr [,offset] [,default]) OVER ( [partition_by_clause ] order_by_clause )  
```
* `column_expr`是需要取值的列名；
* `offset`是取值时相对当前行向下的偏移量，默认是1, 必须是一个非负整数；
* `default`是偏移量超出分区范围时返回的字面量值，默认是`NULL`。如果给定的默认值类型和`column_expr`的类型不一致，会尝试转换成对应的类型，如果转换失败则会使用默认值`NULL`。目前支持的类型包括`INT64`/`STRING`/`DOUBLE`/`BOOL`；

对于上述同样的一个数据集`sale`，采用如下包含`LEAD`的查询语句：

```sql
SELECT seller_name, sale_value,
  LEAD(sale_value) OVER(ORDER BY sale_value) as next_sale_value
FROM sale;
```

可以得到如下结果：

| seller_name | sale_value | next_sale_value |
| ----------- | ---------- | --------------- |
| Bob         | 7000       | 12000           |
| Alice       | 12000      | 25000           |
| Lily        | 25000      | NULL            |

**LAG/LEAD 函数视频教程**
<iframe src="//player.bilibili.com/player.html?aid=942676771&bvid=BV1eW4y1q765&cid=821609604&page=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" width= "100%" height="600px"> </iframe>


### PIVOT
将给定的结果集进行透视转换

#### 语法
```sql
PIVOT table_name ON pivot_column [IN (pivoted_value_1[, pivoted_value_2 ...])]
USING aggregate_expression_or_func_have_aggregate_expression_1[, aggregate_expression_or_func_have_aggregate_expression_2 ...]
GROUP BY group_by_expression_1[, group_by_expression_2 ...]
```

#### 样例
原始数据 `cities` 如下表

|_time|country|name|year|population|
|--|--|--|--|--|
|2000-01-01T00:00:00|NL|Amsterdam|2000|1005|
|2010-01-01T00:00:00|NL|Amsterdam|2010|1065|
|2020-01-01T00:00:00|NL|Amsterdam|2020|1158|
|2000-01-01T00:00:00|US|Seattle|2000|564|
|2010-01-01T00:00:00|US|Seattle|2010|608|
|2020-01-01T00:00:00|US|Seattle|2020|738|
|2000-01-01T00:00:00|US|NewYorkCity|2000|8015|
|2010-01-01T00:00:00|US|NewYorkCity|2010|8175|
|2020-01-01T00:00:00|US|NewYorkCity|2020|8772|

1. 不指定透视转换的列值

```sql
pivot cities on year using sum(population) group by country order by country desc
```

得到所有透视转换列值并作为列名输出，结果如下

|country|2020|2010|2000|
|--|--|--|--|
|US|9510|8783|8579|
|NL|1158|1065|1005|

```sql
pivot cities on year using sum(population)+1 group by country order by country desc
```

得到所有透视转换列值并作为列名输出，结果如下

|country|2020|2010|2000|
|--|--|--|--|
|US|9511|8784|8590|
|NL|1159|1066|1006|

2. 指定透视转换的列值

```sql
pivot cities on year in (2000, 2020) using sum(population) group by country order by country desc
```

仅输出对应 `IN(...)` 中指定的列值，结果如下

|country|2000|2020|
|--|--|--|
|US|8579|9510|
|NL|1005|1158|

3. 结合 `GROUP BY TIME()` 使用以生成时序统计图数据

```sql
pivot cities on country using sum(population)
group by time(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') order by _time
```

以连续时间分桶为分组，并将给定时间范围内缺失的分桶补齐，然后进行进行透视转换

|_time|NL|US|NULL|
|--|--|--|--|
|1990-01-01T00:00:00.000+08:00|Null|Null|Null|
|1995-01-01T00:00:00.000+08:00|Null|Null|Null|
|2000-01-01T00:00:00.000+08:00|1005|8579|Null|
|2005-01-01T00:00:00.000+08:00|Null|Null|Null|
|2010-01-01T00:00:00.000+08:00|1065|8783|Null|
|2015-01-01T00:00:00.000+08:00|Null|Null|Null|
|2020-01-01T00:00:00.000+08:00|1158|9510|Null|

:::info

透视转换结果中包含名 `NULL` 且全空的字段，是因为在补齐时间桶时会生成 `country` `population` 均为空的条目，在透视转换过程中则会把 `country` 对应的空值取出作为最终的列名，列值中的空值则为 `sum(population)` 的结果。可通过 `EXCEPT` 语法将 `NULL` 一列过滤。

:::

```sql
select * except ("NULL") from (
   pivot cities on country using sum(population)
   group by time(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') order by _time
)
```

得到结果如下

|_time|NL|US|
|--|--|--|
|1990-01-01T00:00:00.000+08:00|Null|Null|
|1995-01-01T00:00:00.000+08:00|Null|Null|
|2000-01-01T00:00:00.000+08:00|1005|8579|
|2005-01-01T00:00:00.000+08:00|Null|Null|
|2010-01-01T00:00:00.000+08:00|1065|8783|
|2015-01-01T00:00:00.000+08:00|Null|Null|
|2020-01-01T00:00:00.000+08:00|1158|9510|


### SAMPLE/TABLESAMPLE

对指定数据集或者数据源进行采样并返回子集。

YHP提供`BERNOULLI`采样方式: 用户指定抽样的表和抽样概率。返回的行数取决于表的大小和请求的概率。

语法
```
SELECT ...
FROM ...
  { SAMPLE | TABLESAMPLE } [ samplingMethod ] ({ <probability> })
[ ... ]

samplingMethod ::= { { BERNOULLI | ROW } |
                     { SYSTEM | BLOCK } }
```

概率`<probability>`指定用于选择样本的百分比概率。可以是介于0（不选择行）和100（选择所有行）之间的任何小数。

采样方法:
- `BERNOULLI | ROW` : 颗粒度为行数的采样，每一行会有`p/100`概率被采样。
- `SYSTEM | BLOCK` : 颗粒度为块的采样，每`8*1024`的行数的块会有`p/100`概率被采样。


样例:
```sql
SELECT * FROM main SAMPLE ROW (100) -- 全部采样，等同于select * from main
SELECT * FROM main SAMPLE ROW (0) -- 返回空的结果集
SELECT * FROM main SAMPLE ROW (50.0) -- 返回的结果是平均分布的50%左右的结果集
SELECT * FROM main SAMPLE BLOCK (50.0) -- 返回的结果是以BLOCK为颗粒度平均分布的50%左右的结果集
SELECT * FROM Orders LEFT SEMI JOIN Customers SAMPLE ROW (50) ON Orders.CustomerID=Customers.CustomerID -- 对右表进行50%的采样
```

:::info
当`SAMPLE`算子对数据集类型数据源`EVENT_SET SCAN`进行采样时，性能会有较大的提升。

以下关键字可以互换使用：
SAMPLE | TABLESAMPLE
BERNOULLI | ROW
SYSTEM | BLOCK
:::


### SELECT

使用投影(Projection)可以从结果集中筛选出关心的字段。

#### 投影列表

- 查询星号`*`，会对执行完整查询后可见的每个列生成一个输出列
- 查询表达式`expression [ [ AS ] alias ]`，表达式的计算结果生成一个输出列，其中具有可选的显式别名`alias`
- 投影中的字段名可以限定表名，当查询中只有一张表时，表名可省略，否则请限定表名
- 查询星号限定表名`fullID.*`，对执行完整查询后`fullID`表下可见的每个列生成一个输出列
- `SELECT`修饰符
   - `DISTINCT`丢弃重复行并仅返回剩余行，请参见[使用distinct多结果去重](#使用distinct多结果去重)
   - `* EXCEPT ( column_name [, column_name]* )`指定要从结果中排除的一个或多个列的名称，只能和查询星号或`COLUMNS`一起使用
   - `* REPLACE ( expr as column_name[,expar as column_name]* )`可以指定将对某个列按传入的表达式进行计算并替换，但只能和查询星号或或`COLUMNS`一起使用
   - `* EXCEPT(column_name [, column_name]* ) REPLACE ( expr as column_name[,expar as column_name]* )` 可以指定对某个列按传入的表达式进行计算并替换，并排除指定的列

:::caution

在平台中，原始数据的字段名及提取字段名都是大小写敏感的，数据集合名称大小写不敏感。
`EXCEPT`与`REPLACE`同时使用时，必须保证`EXCEPT`顺序，`REPLACE`在后。

:::

#### 样例

1. 查询所有字段
   ```sql
   SELECT * FROM main
   ```
   
1. 查询特定的method字段和host字段
   ```sql
   SELECT method, host FROM main
   ```
   
1. 给查询的字段一个别名
   ```sql
   SELECT method as method_alias, host as host_alias FROM main
   ```
   
1. 查询标量计算的字段
   ```sql
   SELECT SUBSTR(host, 3) as new_host, upper(method) as upper_method
   FROM main
   ```
   
1. 查询聚合计算的字段
   ```sql
   SELECT AVG(num) FROM main
   ```
   ```sql
   SELECT COUNT(*) FROM main
   ```
   
1. 查询所有字段，附加其他标量计算字段
   ```sql
   SELECT *, upper(method) as upper_method FROM main
   ```
   
1. 查询星号限定表名
   ```sql
   SELECT main.*, ip, upper(main.method) as new_method FROM main
   ```
   ```sql
   SELECT orders.*, customers.CustomerName 
   -- 查询orders表中所有列及customers表中CustomerName列
   FROM orders INNER JOIN customers 
   ON orders.CustomerID=customers.CustomerID
   ```
   
1. 排除指定列
   
   ```sql
   SELECT * EXCEPT (request_method) from main
   ```
   
   ```sql
   -- 排除多个指定列
   SELECT * EXCEPT (request_method, ip) from main 
   ```
   ```sql
   SELECT * EXCEPT (request_method), 
   lower(request_method) as request_method   
   -- 这里表达了用lower(request_method)替换request_method
   FROM main
   ```
   ```sql
   SELECT orders.* EXCEPT ( orders.OrderID ), 
   customers.CustomerName
   FROM Orders LEFT JOIN Customers
   ON Orders.CustomerID=Customers.CustomerID
   ```

1. 输入表达式替换指定列
    ```sql
    -- 使用 lower(request_method)替换request_method
   SELECT * REPLACE (lower(request_method) as request_method) 
   from main
   ```

   ```sql
   -- 输入多个表达式对多个列进行计算并替换
   SELECT * REPLACE (lower(request_method) as request_method,upper(request_service) as request_service) 
   from main 
   ``` 

 1. 排除指定列并输入表达式替换指定列
    ```sql
    -- 排除request_service列，并使用 lower(request_method)替换request_method
    SELECT * EXCEPT(request_service) REPLACE (lower(request_method) as request_method) 
    from main
    ```
    
### TABLE

炎凰数据平台目前支持两种引擎(ENGINE)类型的表，

一种类型是平台原生的[数据集](../../data_management/eventset/index.md)，该类型的表支持读写操作，即数据的导入和查询；

另一种类型是[以Kafka的topic为对象的存储](../../integration/export_to_kafka.md)，该类型的表仅支持写操作，即数据的导入。

表操作语法如下：
```sql
-- 创建或更新表
CREATE [ OR REPLACE ] TABLE table_name [ENGINE=engine_type [WITH (setting_1=value_1[, setting_2=value2, ...]])]

-- 删除表
DROP TABLE table_name

-- 列出所有表
SHOW [FULL] TABLES
```
- `table_name`是表的名称
- `engine_type`是表引擎的类型，目前支持`kafka`和`event_set`
- `setting_i=value_i`是表设置的键值对，支持的设置如下
	- kafka

    |设置|类型|是否必须|
    |-|-|-|
    |server_url|字符串|是|
    |server_port|字符串|是|
    |topic|字符串|是|
  
	- event_set

    |设置|类型|是否必须|
    |-|-|-|
    |max_size_mb|数值|否|
    |max_time_span_sec|数值|否|
    |max_cold_size_mb|数值|否|
    |max_cold_time_span_sec|数值|否|
    |cold_slice_enabled|布尔|否|
    |max_archive_size_mb|数值|否|
    |max_archive_time_span_sec|数值|否|
    |archive_enabled|布尔|否|
    |search_archive_data_enabled|布尔|否|
    |hot_partitions_count|数值|否|
    |max_slice_events_count|数值|否|
    |max_slice_time_span_sec|数值|否|
    |max_slice_size_mb|数值|否|
    |slice_compaction_enabled|布尔|否|
    |disabled|布尔|否|

:::info
当数据集大小大于`max_cold_size_mb`或者数据集数据分片停留时间大于`max_cold_time_span_sec`，将会把温数据转化成冷数据。

当数据集大小大于`max_archive_size_mb`或者数据集数据分片停留时间大于`max_archive_time_span_sec`，将会把温数据/冷数据转化成归档数据。

当数据集大小大于`max_size_mb`或者数据集数据分片停留时间大于`max_time_span_sec`，将会把超过限制的数据删除。
:::

样例：
1. 创建表
   ```sql
   CREATE TABLE test_event_set
   
   CREATE TABLE test_event_set ENGINE=event_set
   
   CREATE TABLE test_event_set ENGINE=event_set WITH (disabled=TRUE)
   
   CREATE TABLE test_kafka_table ENGINE=kafka WITH (server_url='1.1.1.1',server_port='9999',topic='new-events')
   ```
2. 创建或修改表
   ```sql
   CREATE OR REPLACE TABLE test_event_set ENGINE=event_set WITH (disabled=TRUE)
   ```
3. 删除表
   ```sql
   DROP TABLE test_event_set
   ```
4. 列出所有表
   ```sql
   SHOW TABLES
   
   SHOW FULL TABLES WHERE engine='event_set'
   ```

**Table 引擎视频教程**
<iframe src="//player.bilibili.com/player.html?aid=515236953&bvid=BV17g411S744&cid=821604131&page=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" width="100%" height="600px"> </iframe>


### UNION ALL

使用`UNION ALL`关键字对查询的两段结果进行拼接。`UNION ALL`关键字语法上遵守[mysql 8.0的标准](https://dev.mysql.com/doc/refman/8.0/en/union.html)
```sql
SELECT ...
UNION [ALL] SELECT ...
[UNION [ALL] SELECT ...]
```

1.对于两个查询表同时拥有相同的字段的两列进行`UNION ALL`会拼接成一列。

2.对于两个查询表同时拥有不相同的字段的列数将会用`null`填塞剩余行数。

样例：
```sql
SELECT 1 UNION ALL SELECT 'a'
+------+------+
| 1    | a    |
+------+------+
| 1    | null |
+------+------+
| null | a    |
+------+------+

# 不同类型的字段可以union在一起
SELECT 1 AS field_a UNION ALL SELECT 'a' AS field_a
+-------+
|field_a|
+-------+
| 1     |
+-------+
| a     |
+-------+
```

### VALUES

使用`VALUES`来创建`literal table`

语法
```
VALUES ( expression [, ...] ) [, ...]
```

1.在对values表进行命名时，可以使用`table_alias`也就是`t(a,b)`的方式进行命名，这里对应把表命名为`t`，第一列命名为`a`,第二列命名为`b`。在没有添加`table_alias`时，会将第一列命名为`column1`,第二列命名为`column2`,以此类推。

2.支持不同类型的`literal`在同一列里。

3.当作为子表时，里面的表的`alias`会被外面新命名的`alias`给覆盖。

4.支持使用`values`和`insert into`来导入少量数据来验证功能性。但不推荐在生产环境使用values来导入数据。
```sql
SELECT *                             
  FROM generate_series(1,10,2) as g, (VALUES(1, 'Horror'), (2, 'Sci-Fi'), (3, 'Action') AS t1 (index, kind)) as t2
  WHERE g.generate_series = t2.index
```
这里的`t1`就会被外面的`t2`给覆盖。


样例：
```sql
-- 建立一个最基础的表
VALUES (1, 'one'), (2, 'two'), (3, 'three');
-- 对表和列进行命名
VALUES (1, 'one'), (2, 'two'), (3, 'three') as t(a,b)
-- 作为子表使用
SELECT t.a, t.b FROM (VALUES (1, 'one'), (2, 'two'), (3, 'three') as t(a,b));
-- 插入特定的数据集
INSERT INTO table_a VALUES (1, 'one'), (2, 'two'), (3, 'three') as t(a,b);
-- 作为子表进行过滤或者添加条件
SELECT *                             
  FROM generate_series(1,10,2) as g, (VALUES(1, 'Horror'), (2, 'Sci-Fi'), (3, 'Action') AS t1 (index, kind)) as t2
  WHERE g.generate_series = t2.index
-- 使用cte作为lookup table添加额外条件
WITH countries (code, name) AS (
   SELECT * FROM (VALUES
     (1, 'United States'), (2, 'France'), (3, 'India')
   ) AS codes
)
SELECT * FROM generate_series(1,10,2) as g  LEFT JOIN countries ON countries.code = g.generate_series
--- 和in subquery配合使用过滤
SELECT * FROM generate_series(1,10,1) WHERE generate_series 
IN (values (1), (2), (3))
```


```sql
VALUES (1, 'one'), (2, 'two'), (3, 'three');
```
| column1 | column2    |
| ------- | ---------- | 
| 1       | 'one'      |
| 2       | 'two'      |
| 3       | 'three'    |

```sql
SELECT *                             
  FROM generate_series(1,10,2) as g, (VALUES(1, 'Horror'), (2, 'Sci-Fi'), (3, 'Action') AS t1 (index, kind)) as t2
  WHERE g.generate_series = t2.index;
```
|generate_series|index|kind|
| ---- | ----------- | ---------- |
| 1     | 1     | 'Horror'     |
| 3     | 3     | 'Action'     |

```sql
WITH countries (code, name) AS (
   SELECT * FROM (VALUES
     (1, 'United States'), (2, 'France'), (3, 'India')
   ) AS codes
)
SELECT * FROM generate_series(1,10,2) as g  LEFT JOIN countries ON countries.code = g.generate_series
```

|generate_series|code|kind|
| ---- | ----------- | ---------- |
| 1     | 1     | 'United States'     |
| 3     | 3     | 'India'     |
| 5     | 5     |      |
| 7     | 7     |      |
| 9     | 9     |      |


### WHERE

使用`WHERE`关键字可以过滤事件。

- `WHERE`关键字后面可以包含`AND`和`OR`组合的布尔表达式。
- 在平台当中，如果使用的是字符串字面常量(Literal Value)，需要使用单引号，且字面量值大小写敏感。
- 平台提供了标量函数`CONTAINS`，可以用来过滤原始事件`_message`是否包含特定字符串。

:::tip 

在 SQL 中，单引号数据代表字符串，双引号数据代表字段名。

:::

#### 过滤条件常用表达式

| 过滤条件                                    |                             用法                             |
| :------------------------------------------ | :----------------------------------------------------------: |
| `<expr> IS (NOT) NULL`                      | 判断表达式的值是否是空值，其中`expr`可以是一个字段名，也可以是一个函数表达式或者是数值运算表达式。 |
| `<expr> (NOT) IN (<expr1>, <expr2> ...)`    |   表达式的值是否等于后续列表当中的某个值，或者是某个字段。   |
| `<expr1> (NOT) LIKE <expr2>`                | 表达式1的值是否匹配表达式2，需要注意的是，LIKE表达式**大小写敏感**，比如`get`不能和`Get`相互匹配；此外，表达式2只能为单引号**字符串常量**(Literal Value)，常量中可以使用`%`和`_`作为通配符分别匹配多个和一个字符。 如果需要匹配`%_\`需要加上转义字符`\`，如`\%`可以匹配`%`字符，其他字符转义规则是 ```'\x' => 'x'```。 |
| `<expr1> (NOT) BETWEEN <expr2> AND <expr3>` |        表达式1的值是否在表达式2的值和表达式3的值之间         |
| 二元比较操作符 `<expr1> <op> <expr2>`       | 用于比较表达式1和表达式2的值。支持的比较操作符有`=` `<` `<=` `>` `>=`。但是需要注意的是，如果两个表达式的值类型不同的话，会进行值类型的隐式转换。转换成相同类型的值再进行比较。 |
| `CONTAINS(text[, tokenized])`               | 用于判断**_message**字段是否存在字符串`text`，这里`text`只能为单引号**字符串常量**(Literal Value)，且**大小写不敏感**。`tokenized`是一个布尔类型的可选参数，默认为`true`，会对`text`参数做分词 |
| `CONTAINS(<field_name>, text[, tokenized])`               | 用于判断**field_name**字段是否存在字符串`text`，这里`text`只能为单引号**字符串常量**(Literal Value)，且**大小写不敏感**。`tokenized`是一个布尔类型的可选参数，默认为`true`，会对`text`参数做分词 |
| `(NOT) EXISTS (<subquery>)`    |   子查询是否至少会返回一行结果。   |

注：
* `expr`可以是一个任何字段，常量，[标量函数表达式](../sql_function/scalar_function.mdx)
* `subquery`是一个子查询

> 当使用二元比较操作符的时候，如果是和`NULL`值比较，那么结果都是`NULL`，例如`foo = NULL`/`foo > NULL`/`NULL = NULL`的结果是`NULL`，放在`WHERE`后面作为过滤条件就是`FALSE`，返回的结果集会是空集。这和SQL的语义是一致的。

:::caution

标准SQL不允许在`WHERE`子句中引用别名，因此以下查询的结果会是空集: 

:::

```sql
   SELECT _time as t FROM main WHERE t > 0
```

#### 范围查询

范围查询可以通过比较数字字段，或者比较字符串字段，来过滤结果集。

范围查询跟二元表达式有类似的地方，语法表达为 `<field_name> <op> <scalar_value>`。
`<field_name>`是表达式的左值，是一个待比较的字段名。`<op>`是比较表达式的操作符，包括`<`,`<=`,`>`,`>=`，`<scalar_value>`是一个常量值，如果常量值是字符串类型，则字段的值会被转换成字符串比较，
如果是数值类型，则字段的值会被转换成数值类型来比较。

**字段值类型转换原则：**
:::info

范围查询中，字段转换的类型取决于操作符右边的常量值的类型，
如果常量值是字符串，则会按照字典序来比较。字符串常量必须用单引号来引用。
例如`foo`为一个索引字段，使用`SELECT * FROM main WHERE foo >= '5'`，则会找到foo中字典序大于'5'的事件(`foo='40'`这样的事件会被过滤掉)；而`SELECT * FROM main WHERE foo >= 5`，则会找到foo中浮点数值大于5的事件(`foo=40`这样的事件会被保留)。

:::

**使用索引字段加速范围查询：**
:::info

范围查询中，如果待比较的字段是索引字段，
在比较执行的时候，平台会自动使用字段的索引，对范围查询比较加速。
如果待比较字段不是索引字段，则平台会逐行执行比较操作，完成过滤。

:::


### WITH (表子查询和公用表表达式 / Common Table Expression) {#CTE}

表子查询和CTE通常用于把一个复杂查询拆分成若干步。

#### 表子查询
使用表子查询，外部查询将子查询的结果视为表。可以显示指定表别名。

样例
1. 表子查询
   ```sql
   SELECT results.account
   FROM (SELECT * FROM Players) AS results
   ```
1. 表子查询嵌套
   ```sql
   SELECT SUM(1) FROM
   (SELECT _message AS message FROM
       (SELECT _message, _datatype FROM
           (SELECT * FROM main WHERE CONTAINS('css'))
       WHERE CONTAINS('GET'))
   )
   ```

#### 公用表表达式 (Common Table Expression, CTE)

`WITH`子句包含一个或多个已命名的子查询，称之为公用表达式(Common Table Expression)。
每次后续`SELECT`语句引用它们时都会执行这些子查询。
任何子句或子查询都可以引用`WITH`子句中定义的子查询。

`WITH`子句主要用于提高可读性，并不会具体化`WITH`子句中的查询结果。使用时可以显示带上字段名别名。

:::caution

- 如果`WITH`子句包含多个子查询，则子查询名称不能重复。
- 在平台中，暂时不支持`WITH RECURSIVE`

:::

CTE语法如下:
```sql
withClause:
  WITH common_table_expression [ , common_table_expression ]*;

common_table_expression: 
  expression_name [ ( column_name [ , column_name ]* ) ] 
  AS ( CTE_query_definition )
```
- `WITH`语句后面必须直接跟使用CTE的SQL語句，否则CTE将失效
- `CTE`后面可以跟其他`CTE`，但只能使用一个`WITH`，`CTE`中间用**逗号**分隔
- `CTE`可以引用在同一`WITH`子句中预先定义的`CTE`，不允许前向引用，不可以自身引用
- 括号注意不可省略

1. 使用CTE分拆查询
```sql
WITH first_query AS (SELECT * FROM main),
      second_query AS (SELECT _message FROM first_query)
SELECT SUM(1) FROM second_query
```

1. 带字段名别名
```sql
WITH pc_query(name, id) AS (SELECT pc_name, pc_id FROM pc)
SELECT name, id FROM pc_query
```

1. 复杂CTE查询
```sql
WITH first_query  AS (SELECT * FROM main),
      second_query AS (SELECT _message, _datatype FROM first_query 
                      WHERE CONTAINS('GET')),
      third_query(message) AS (SELECT _message FROM second_query)
SELECT COUNT(DISTINCT message) FROM third_query
```
