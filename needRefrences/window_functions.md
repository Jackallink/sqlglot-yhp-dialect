PARTITION BY (窗口函数)
窗口函数可以对数据进行分组计算，与GROUP BY不同的是， 窗口函数可以为每组数据返回多个值，目前支持的功能如下：

功能	样例	支持程度
在SELECT中使用基本窗口函数	SELECT COUNT(*) OVER (PARTITION BY id ORDER BY time DESC)	支持
在ORDER BY中使用窗口函数	SELECT * ORDER BY COUNT(*) OVER (PARTITION BY id)	不支持
对窗口函数进行运算	(COUNT(*) OVER ()) + 1	不支持，可以使用子查询替代
窗口分区子句PARTITION BY	COUNT(*) OVER (PARTITION BY id)	支持
窗口排序子句ORDER BY	COUNT(*) OVER (ORDER BY id)	部分支持，由于暂不支持RANGE子句，若未指定框架子句，则会加上默认窗口子句ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
窗口框架(Frame)子句	ROWS RANGE INTERVAL GROUPS	支持ROWS
WINDOW子句	WINDOW w AS	不支持
聚合函数	COUNT SUM AVG MAX MIN	支持前述函数
非聚合函数	RANK ROW_NUMBER等	支持以下函数
ROW_NUMBER()
FIRST_VALUE(<EXPRESSION>)
LAST_VALUE(<EXPRESSION>)
LAG(<EXPRESSION>)
LEAD(<EXPRESSION>)
样例：

查询nginx accesslog，统计每类agent的size总和
SELECT  
   sum(size) OVER(PARTITION BY agent)
FROM main 
WHERE _datatype='nginx.access_log'

查询nginx accesslog，得到每类agent按照method排序后关于size的累加和
SELECT  
   sum(size) OVER(PARTITION BY agent ORDER BY method ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
FROM main 
WHERE _datatype='nginx.access_log'


窗口框架(Window Frame)
窗口框架用于在窗口分区内对行进一步限制。 语法：

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

目前frame_units仅支持ROWS

示例：

ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING

在没有指定窗口框架子句(frame_clause)的情况下，默认的frame和是否有ORDER BY有关

有ORDER BY，默认的frame包含从当前分区开始到当前行，等价于：
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

没有ORDER BY，默认的frame包含当前分区的所有行，等价于：
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING

非聚合窗口函数
Function	Window Frame
FIRST_VALUE	Yes
LAST_VALUE	Yes
ROW_NUMBER	No
LAG	No
LEAD	No
FIRST_VALUE
FIRST_VALUE返回有序数据集中的第一个值，如果指定ignore_null=true，则会返回第一个非null的值。

语法：

FIRST_VALUE (column_expr, ignore_null=false) OVER ( [ partition_by_clause ] order_by_clause [ frame_clause ] )


column_expr是需要取值的列名；
ignore_null指定是否需要忽略null值，默认是false；
frame_clause目前仅支持ROWS窗口框架(Window Frame)子句；
例如数据集products中有如下数据：

id	name	price	group_id
1	iPhone	5000	1
2	Mi	3000	1
3	Huawei	4000	1
4	Lenovo	8000	2
5	Dell	6000	2
使用如下查询语句：

SELECT
   name, price, FIRST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC)
FROM products   

可以得到如下结果:

name	price	first_price
iPhone	5000	5000
Huawei	4000	5000
Mi	3000	5000
Lenovo	8000	8000
Dell	6000	8000
LAST_VALUE
LAST_VALUE返回有序数据集中的最后一个值。

语法：

LAST_VALUE (column_expr) OVER ( [ partition_by_clause ] order_by_clause [ frame_clause ] )

column_expr是需要取值的列名；
frame_clause目前仅支持ROWS窗口框架(Window Frame)子句；
对于上述数据集products，使用如下查询语句：

SELECT
   name, price, LAST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) last_price
FROM products   


可以得到如下结果:

name	price	last_price
iPhone	5000	3000
Huawei	4000	3000
Mi	3000	3000
Lenovo	8000	6000
Dell	6000	6000
ROW_NUMBER
ROW_NUMBER用来给分区结果集加上从1开始的序列号。 语法：

ROW_NUMBER() OVER ([ partition_by_clause ] order_by_clause )

对于上述数据集products如下查询语句：

SELECT 
    name, price, ROW_NUMBER() OVER ( PARTITION BY group_id ORDER BY price DESC) row_id 
FROM products

可以得到如下结果:

name	price	row_id
iPhone	5000	1
Huawei	4000	2
Mi	3000	3
Lenovo	8000	1
Dell	6000	2
LAG
LAG窗口函数用于返回窗口分区内位于当前行上方第offset行的值。在SELECT语句中使用此分析函数可将当前行中的值与先前行中的值进行比较。 语法:

LAG (column_expr [,offset] [,default]) OVER ( [ partition_by_clause ] order_by_clause )  

column_expr是需要取值的列名；
offset是取值时相对当前行向上的偏移量，默认是1, 必须是一个非负整数；
default是偏移量超出分区范围时返回的字面量值，默认是NULL。如果给定的默认值类型和column_expr的类型不一致，会尝试转换成对应的类型，如果转换失败则会使用默认值NULL。目前支持的类型包括INT64/STRING/DOUBLE/BOOL；
例如在我们的数据集sale中有如下的数据：

id	seller_name	sale_value
3	Bob	7000
1	Alice	12000
2	Lily	25000
用包含LAG的如下的查询语句：

SELECT seller_name, sale_value,
  LAG(sale_value) OVER(ORDER BY sale_value) as previous_sale_value
FROM sale;

可以得到如下结果：

seller_name	sale_value	previous_sale_value
Bob	7000	NULL
Alice	12000	7000
Lily	25000	12000
LEAD
LEAD窗口函数用于返回窗口分区内位于当前行下方第offset行的值。在SELECT语句中使用此分析函数可将当前行中的值与后续行中的值进行比较。 语法:

LEAD (column_expr [,offset] [,default]) OVER ( [partition_by_clause ] order_by_clause )  

column_expr是需要取值的列名；
offset是取值时相对当前行向下的偏移量，默认是1, 必须是一个非负整数；
default是偏移量超出分区范围时返回的字面量值，默认是NULL。如果给定的默认值类型和column_expr的类型不一致，会尝试转换成对应的类型，如果转换失败则会使用默认值NULL。目前支持的类型包括INT64/STRING/DOUBLE/BOOL；
对于上述同样的一个数据集sale，采用如下包含LEAD的查询语句：

SELECT seller_name, sale_value,
  LEAD(sale_value) OVER(ORDER BY sale_value) as next_sale_value
FROM sale;

可以得到如下结果：

seller_name	sale_value	next_sale_value
Bob	7000	12000
Alice	12000	25000
Lily	25000	NULL