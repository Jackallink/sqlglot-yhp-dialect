聚合函数
可以使用如下聚合函数进行聚合分析:

算子名	功能	语法
COUNT	统计行数，不包括NULL值，COUNT(*)包括NULL值	COUNT(expression)
SUM	统计和	SUM(expression)
AVG	统计平均值	AVG(expression)
MAX	统计最大值	MAX(expression)
MIN	统计最小值	MIN(expression)
MAX_STR	按照字符串规则统计最大值	MAX(expression)
MIN_STR	按照字符串规则统计最小值	MIN(expression)
STDDEV_POP	计算总体标准差	STDDEV_POP(expression)
STDDEV_SAMP	计算样本标准差	STDDEV_SAMP(expression)
VAR_POP	计算总体方差	VAR_POP(expression)
VAR_SAMP	计算样本方差	VAR_SAMP(expression)
STRING_AGG	实验性功能：拼接每行表达式expression的值，并在其间放置分隔符separator	STRING_AGG(expression, separator)
QUANTILE_T_DIGEST	实验性功能：使用T-Digest算法计算数值数据的近似分位数	QUANTILE_T_DIGEST(expression, fraction)，其中fraction为分位数水平，允许值范围为[0,1]
PERCENTILE	实验性功能：等价于QUANTILE_T_DIGEST	PERCENTILE(expression, fraction)
APPROX_COUNT_DISTINCT	近似值计算函数，使用概率数据结构来估算唯一值的数值，适用于大数据量下在可接受的误差范围内快速返回结果	APPROX_COUNT_DISTINCT(expression)
APPROX_MEDIAN	使用T-Digest算法计算数值数组的近似中位数	APPROX_MEDIAN(expression)
PRODUCT	用于计算给定列的数值的乘积	PRODUCT(expression)
FIRST_VALUE	默认返回组内的第一个非空值	FIRST_VALUE(expression)
LAST_VALUE	默认返回组内的第一个非空值	LAST_VALUE(expression)
LATEST_VALUE	返回组内时间属性_time最大的值所在行的对应字段值，若存在多个_time最大值，则返回字段值的结果不确定	LATEST_VALUE(expression)
EARLIEST_VALUE	返回组内时间属性_time最小的值所在行的对应字段值，若存在多个_time最小值，则返回字段值的结果不确定	EARLIEST_VALUE(expression)

GROUP BY
使用group by配合以下聚合运算算子，可以对数据进行聚合分析。需要注意

group by后的列只能是int或者string类型的，对于浮点类型的列，是不支持的，需要使用cast功能转换成别的类型。
不支持不明确的非聚合列的查询。例如，以下查询是不支持的，因为select中的非聚合列method未出现在group by语句中。
SELECT method, agent, SUM(size) FROM main GROUP BY agent;

支持的聚合算子如下：包括 COUNT SUM AVG MAX MIN
算子名	功能	语法
COUNT	统计行数，不包括NULL值，COUNT(*)包括NULL值	COUNT(expression)
SUM	统计和	SUM(expression)
AVG	统计平均值	AVG(expression)
MAX	统计最大值	MAX(expression)
MIN	统计最小值	MIN(expression)
MAX_STR	按照字符串规则统计最大值	MAX(expression)
MIN_STR	按照字符串规则统计最小值	MIN(expression)
STDDEV_POP	计算总体标准差	STDDEV_POP(expression)
STDDEV_SAMP	计算样本标准差	STDDEV_SAMP(expression)
VAR_POP	计算总体方差	VAR_POP(expression)
VAR_SAMP	计算样本方差	VAR_SAMP(expression)
STRING_AGG	实验性功能：拼接每行表达式expression的值，并在其间放置分隔符separator	STRING_AGG(expression, separator)
QUANTILE_T_DIGEST	实验性功能：使用T-Digest算法计算数值数据的近似分位数	QUANTILE_T_DIGEST(expression, fraction)，其中fraction为分位数水平，允许值范围为[0,1]
PERCENTILE	实验性功能：等价于QUANTILE_T_DIGEST	PERCENTILE(expression, fraction)
APPROX_MEDIAN	使用T-Digest算法计算数值数组的近似中位数	APPROX_MEDIAN(expression)
PRODUCT	用于计算给定列的数值的乘积	PRODUCT(expression)
FIRST_VALUE	默认返回组内的第一个非空值	FIRST_VALUE(expression)
LAST_VALUE	默认返回组内的第一个非空值	LAST_VALUE(expression)
LATEST_VALUE	返回组内时间属性_time最大的值所在行的对应字段值，若存在多个_time最大值，则返回字段值的结果不确定	LATEST_VALUE(expression)
EARLIEST_VALUE	返回组内时间属性_time最小的值所在行的对应字段值，若存在多个_time最小值，则返回字段值的结果不确定	EARLIEST_VALUE(expression)