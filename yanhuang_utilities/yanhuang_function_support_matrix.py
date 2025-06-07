#!/usr/bin/env python3
"""
炎凰数据函数支持矩阵和自动核查机制
基于官方文档：needRefrences/scalar_functions.md, table_functions.md, window_functions.md
完整的炎凰数据函数支持列表，用于虚继承函数优化的核查
"""

from typing import Dict, Set, List, Tuple, Optional
from enum import Enum
import re

class FunctionCategory(Enum):
    """函数分类"""
    SCALAR = "scalar"           # 标量函数
    TABLE = "table"            # 表函数
    WINDOW = "window"          # 窗口函数
    AGGREGATE = "aggregate"    # 聚合函数

class SupportStatus(Enum):
    """支持状态"""
    SUPPORTED = "supported"           # 完全支持
    NOT_SUPPORTED = "not_supported"   # 明确不支持
    PARTIAL = "partial"              # 部分支持
    UNKNOWN = "unknown"              # 未知状态

class YanhuangFunctionMatrix:
    """炎凰数据函数支持矩阵"""
    
    def __init__(self):
        self.functions = {}
        self._load_function_matrix()
    
    def _load_function_matrix(self):
        """加载函数支持矩阵 - 基于官方文档的完整列表"""
        
        # ===== 标量函数 (基于 scalar_functions.md 完整列表) =====
        scalar_functions = {
            # 数学函数 - 支持的
            "ABS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的绝对值"),
            "ACOS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的反余弦值"),
            "ASIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的反正弦值"),
            "ATAN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的反正切值"),
            "CEIL": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x向上取整值"),
            "COS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的余弦值"),
            "COSH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的双曲余弦函数值"),
            "COT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的余切值"),
            "DEGREES": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算弧度x对应的角度值"),
            "EXP": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算 e^x"),
            "FACTORIAL": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的阶乘"),
            "FLOOR": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x向下取整值"),
            "LOG": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算自然对数或指定底数对数"),
            "LOG10": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算10为底的对数"),
            "MOD": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x对y取模的值"),
            "POW": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "幂次方运算"),
            "POWER": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同POW"),
            "RADIANS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算角度x对应的弧度值"),
            "RAND": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "生成随机数"),
            "RANDOM": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同RAND"),
            "ROUND": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "四舍五入"),
            "SIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的正弦值"),
            "SINH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的双曲正弦函数值"),
            "SQRT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的平方根"),
            "TAN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的正切值"),
            "TANH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的双曲正切函数值"),
            "TRUNC": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算x的舍位值"),
            "TRUNCATE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同TRUNC"),
            "CBRT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算立方根"),
            "BROUND": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "HALF_EVEN规则取整"),
            "PMOD": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "正取余值"),
            
            # 数学函数 - 不支持的(常见PostgreSQL函数但炎凰不支持)
            "ATAN2": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "双参数反正切函数"),
            "ATAN2D": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "双参数反正切函数(度数)"),
            "ATANH": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "反双曲正切函数"),
            "PI": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "圆周率常量"),
            "ATAND": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "反正切函数(度数)"),
            "CEILING": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "使用CEIL替代"),
            
            # 字符串函数 - 支持的
            "ASCII": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回ASCII编码值"),
            "BIT_LENGTH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算比特位数"),
            "BTRIM": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "去除两端空格或字符"),
            "CHAR_LENGTH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回字符串长度"),
            "CHARACTER_LENGTH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同CHAR_LENGTH"),
            "CHR": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回ASCII字符"),
            "CONCAT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "字符串连接"),
            "CONCAT_WS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "带分隔符连接"),
            "CONTAINS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "检查是否包含关键字"),
            "ENDS_WITH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "检测是否以指定字符串结尾"),
            "INITCAP": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "首字母大写"),
            "IS_ASCII": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "判断是否ASCII编码"),
            "IS_SUBSTR": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "检测是否包含子字符串"),
            "LEFT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回左边字符"),
            "LENGTH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同CHAR_LENGTH"),
            "LOCATE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "查找子字符串位置"),
            "LOWER": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "转换为小写"),
            "LPAD": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "左侧填充"),
            "LTRIM": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "去除左侧空格"),
            "MASK_FIRST_N": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "掩码前N个字符"),
            "MASK_LAST_N": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "掩码后N个字符"),
            "OCTET_LENGTH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回字节长度"),
            "POSITION": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同LOCATE"),
            "QUOTE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "添加单引号"),
            "REMOVE_CHARS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "移除指定字符"),
            "REPEAT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "重复字符串"),
            "REPLACE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "替换字符串"),
            "REVERSE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "反转字符串"),
            "RIGHT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回右边字符"),
            "RPAD": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "右侧填充"),
            "RTRIM": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "去除右侧空格"),
            "SOUNDEX": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回SOUNDEX值"),
            "SPACE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回空白符"),
            "SPLIT_PART": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "分割字符串取指定部分"),
            "STARTS_WITH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "检测是否以指定字符串开头"),
            "SUBSTR": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取子字符串"),
            "SUBSTRING": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同SUBSTR"),
            "UPPER": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "转换为大写"),
            
            # 数组函数 - 支持的
            "ARRAY_AT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "获取数组指定索引值"),
            "ARRAY_APPEND": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "向数组尾部追加元素"),
            "ARRAY_APPEND_AT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "在指定位置插入元素"),
            "ARRAY_CAT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "合并两个数组"),
            "ARRAY_CONTAINS": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "检查数组是否包含元素"),
            "ARRAY_DISTINCT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组去重"),
            "ARRAY_GENERATE_RANGE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "生成数字范围数组"),
            "ARRAY_JOIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组连接为字符串"),
            "ARRAY_LENGTH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算数组长度"),
            "ARRAY_MAX": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组最大值"),
            "ARRAY_MIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组最小值"),
            "ARRAY_POSITION": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "元素在数组中的位置"),
            "ARRAY_PREPEND": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "向数组头部追加元素"),
            "ARRAY_REGEX_LIKE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组正则匹配"),
            "ARRAY_REMOVE_AT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "移除指定位置元素"),
            "ARRAY_SLICE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组切片"),
            "ARRAY_SORT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组排序"),
            "ARRAY_SPLIT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "字符串分割为数组"),
            "ARRAY_INTERSECT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组交集"),
            "ARRAY_EXCEPT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "数组差集"),
            
            # 哈希函数 - 支持的(炎凰特有命名)
            "CRC32": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算CRC32值"),
            "HASH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算32位哈希值"),
            "HASH32": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "同HASH"),
            "HASH64": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算64位哈希值"),
            "HASH_MD5": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算MD5哈希值"),
            "HASH_SHA1": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算SHA1哈希值"),
            "HASH_SHA256": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算SHA256哈希值"),
            
            # 哈希函数 - 不支持的(PostgreSQL命名)
            "MD5": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "MD5函数(应使用HASH_MD5)"),
            "SHA1": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "SHA1函数(应使用HASH_SHA1)"),
            "SHA256": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "SHA256函数(应使用HASH_SHA256)"),
            "SHA2": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "SHA2函数(应使用HASH_SHA256)"),
            "SHA": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "SHA函数(应使用HASH_SHA1)"),
            
            # 编码函数 - 支持的
            "UNBASE64_STRING": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "BASE64解码"),
            "URL_DECODE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "URL解码"),
            
            # 编码函数 - 不支持的
            "BASE64_ENCODE": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "BASE64编码"),
            "ENCODE": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "通用编码"),
            "URL_ENCODE": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "URL编码"),
            "DECODE": (FunctionCategory.SCALAR, SupportStatus.PARTIAL, "部分支持(仅非BASE64)"),
            
            # 位运算函数 - 支持的
            "BIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算二进制字符串"),
            "BITWISE_AND": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "按位与"),
            "BITWISE_NOT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "按位取反"),
            "BITWISE_OR": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "按位或"),
            "BITWISE_XOR": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "按位异或"),
            "CONV": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "进制转换"),
            "HEX": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "计算16进制值"),
            
            # IP地址函数 - 支持的
            "CIDR_MATCH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "CIDR匹配"),
            "INT_TO_IP": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "整数转IP地址"),
            "IP_TO_INT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "IP地址转整数"),
            "IPV4_TO_IPV6": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "IPv4转IPv6"),
            "IS_IPV4": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "判断是否IPv4"),
            "IS_IPV4_LOOPBACK": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "判断是否IPv4回环"),
            "IS_IPV6": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "判断是否IPv6"),
            "IS_IPV6_LOOPBACK": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "判断是否IPv6回环"),
            
            # URL处理函数 - 支持的
            "CUT_QUERY_STRING": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "删除URL查询字符串"),
            "CUT_QUERY_STRING_AND_FRAGMENT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "删除URL查询字符串和片段"),
            "CUT_WWW": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "删除域名开头的www"),
            "DOMAIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取域名"),
            "DOMAIN_WITHOUT_WWW": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取域名(不含www)"),
            "FRAGMENT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回片段标识符"),
            "IS_VALID_URL": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "判断URL是否有效"),
            "NETLOC": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取网络位置信息"),
            "NETLOC_USERNAME": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取用户名"),
            "NETLOC_PASSWORD": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取密码"),
            "PATH": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回路径"),
            "PATH_FULL": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回完整路径"),
            "PORT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回端口"),
            "PROTOCOL": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取协议"),
            "QUERY_STRING": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回查询字符串"),
            "TOP_LEVEL_DOMAIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取顶级域"),
            
            # 距离/相似度函数 - 支持的
            "DAMERAU_LEVENSHTEIN_DISTANCE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "Damerau-Levenshtein距离"),
            "HAMMING_DISTANCE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "汉明距离"),
            "JARO_SIMILARITY": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "Jaro相似度"),
            "JARO_WINKLER_SIMILARITY": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "Jaro-Winkler相似度"),
            "LEVENSHTEIN": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "Levenshtein距离"),
            "NORMALIZED_DAMERAU_LEVENSHTEIN_DISTANCE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "归一化Damerau-Levenshtein距离"),
            "NORMALIZED_LEVENSHTEIN_DISTANCE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "归一化Levenshtein距离"),
            "OSA_DISTANCE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "OSA距离"),
            "SORENSEN_DICE_SIMILARITY": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "Sørensen-Dice相似度"),
            
            # 时间函数 - 支持的
            "DATE_ADD": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "日期加法"),
            "DATE_DIFF": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "日期差值"),
            "DATE_PART": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "提取日期部分"),
            "DATE_TRUNC": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "日期截断"),
            "NOW": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "当前时间"),
            "STRFTIME": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "时间格式化"),
            "STRPTIME": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "时间解析"),
            "TIME_BUCKET": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "时间分桶"),
            
            # 时间函数 - 不支持的(PostgreSQL风格)
            "CURRENT_TIME": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "当前时间(使用NOW)"),
            "CURRENT_TIMESTAMP": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "当前时间戳(使用NOW)"),
            "LOCALTIME": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "本地时间(使用NOW)"),
            "LOCALTIMESTAMP": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "本地时间戳(使用NOW)"),
            
            # 条件函数 - 支持的
            "COALESCE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回第一个非空值"),
            "GREATEST": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回最大值"),
            "LEAST": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回最小值"),
            "NULLIF": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "条件返回NULL"),
            
            # 格式化函数 - 支持的
            "BAR": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "建立条形图"),
            "ELT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回指定位置字符串"),
            "FORMAT": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "字符串格式化"),
            
            # 正则表达式函数 - 支持的
            "ILIKE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "不区分大小写模式匹配"),
            "REGEX_LIKE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "正则表达式匹配"),
            "REGEXP_REPLACE": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "正则表达式替换"),
            
            # JSON函数 - 支持的
            "JSON_POINTER": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "JSON指针解析"),
            "JSON_POINTER_MV": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "JSON指针解析(多值)"),
            "VALID_JSON": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "判断JSON是否合法"),
            
            # 类型转换函数 - 支持的
            "CAST": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "类型转换"),
            "TRY_CAST": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "安全类型转换(非炎凰原生)"),
            "SAFE_CAST": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "安全类型转换(非炎凰原生)"),
            "CONVERT": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "SQL Server类型转换"),
            "TRY_CONVERT": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "SQL Server安全转换"),
            
            # 字符串函数 - 补充(基于官方文档验证)
            "TRIM": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "不在官方文档中(使用BTRIM/LTRIM/RTRIM)"),
            "OVERLAY": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "字符串覆盖(不在官方文档中)"),
            "NORMALIZE": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "Unicode规范化(不在官方文档中)"),
            
            # JSON函数 - 不支持的
            "JSON_OBJECT": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "JSON对象构造"),
            "JSON_OBJECTAGG": (FunctionCategory.AGGREGATE, SupportStatus.NOT_SUPPORTED, "JSON对象聚合"),
            "JSONB_EXISTS": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "JSONB存在检查"),
            
            # XML函数 - 不支持的
            "XMLELEMENT": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "XML元素构造"),
            "XMLTABLE": (FunctionCategory.TABLE, SupportStatus.NOT_SUPPORTED, "XML表函数"),
            
            # 分析函数 - 不支持的(不在官方文档中)
            "ARG_MAX": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "分析函数(不在官方文档中)"),
            "ARG_MIN": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "分析函数(不在官方文档中)"),
            "ARGMAX": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "分析函数(不在官方文档中)"),
            "ARGMIN": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "分析函数(不在官方文档中)"),
            "MAX_BY": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "分析函数(不在官方文档中)"),
            "MIN_BY": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "分析函数(不在官方文档中)"),
            
            # 时间序列函数 - 不支持的
            "GAP_FILL": (FunctionCategory.SCALAR, SupportStatus.NOT_SUPPORTED, "时间序列填充(不在官方文档中)"),
            
            # 机器学习函数 - 未知
            "PREDICT": (FunctionCategory.SCALAR, SupportStatus.UNKNOWN, "机器学习预测"),
            
            # 搜索函数 - 未知
            "MATCH": (FunctionCategory.SCALAR, SupportStatus.UNKNOWN, "全文搜索匹配"),
            
            # Microsoft SQL函数 - 不支持的
            "OPENJSON": (FunctionCategory.TABLE, SupportStatus.NOT_SUPPORTED, "SQL Server JSON表函数"),
            "JSON_TABLE": (FunctionCategory.TABLE, SupportStatus.NOT_SUPPORTED, "SQL Server JSON表函数"),
            
            # 其他函数 - 支持的
            "TYPEOF": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "返回数据类型"),
            "UUID": (FunctionCategory.SCALAR, SupportStatus.SUPPORTED, "生成UUID"),
        }
        
        # ===== 窗口函数 (基于 window_functions.md) =====
        window_functions = {
            # 支持的窗口函数
            "ROW_NUMBER": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "行号"),
            "FIRST_VALUE": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "第一个值"),
            "LAST_VALUE": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "最后一个值"),
            "LAG": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "向上偏移取值"),
            "LEAD": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "向下偏移取值"),
            
            # 聚合函数在窗口中的使用 - 支持的
            "COUNT": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "计数(窗口)"),
            "SUM": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "求和(窗口)"),
            "AVG": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "平均值(窗口)"),
            "MAX": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "最大值(窗口)"),
            "MIN": (FunctionCategory.WINDOW, SupportStatus.SUPPORTED, "最小值(窗口)"),
            
            # 不支持的窗口函数
            "RANK": (FunctionCategory.WINDOW, SupportStatus.NOT_SUPPORTED, "排名函数"),
            "DENSE_RANK": (FunctionCategory.WINDOW, SupportStatus.NOT_SUPPORTED, "密集排名函数"),
            "PERCENT_RANK": (FunctionCategory.WINDOW, SupportStatus.NOT_SUPPORTED, "百分比排名函数"),
            "CUME_DIST": (FunctionCategory.WINDOW, SupportStatus.NOT_SUPPORTED, "累积分布函数"),
            "NTILE": (FunctionCategory.WINDOW, SupportStatus.NOT_SUPPORTED, "分桶函数"),
        }
        
        # ===== 表函数 (基于 table_functions.md) =====
        table_functions = {
            # 内置表函数 - 支持的
            "GENERATE_SERIES": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "生成数字序列"),
            "IP_LOCATION": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "IP地理位置查询"),
            "FLATTEN": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "多值字段展平"),
            
            # 解析函数 - 支持的
            "PARSE_JSON": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "JSON解析"),
            "PARSE_CSV": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "CSV解析"),
            "PARSE_REGEX": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "正则解析"),
            "PARSE_KV": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "键值对解析"),
            "PARSE_XML": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "XML解析"),
            "PARSE_URL": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "URL解析"),
            "PARSE_USER_AGENT": (FunctionCategory.TABLE, SupportStatus.SUPPORTED, "User Agent解析"),
            
            # 不支持的表函数
            "UNNEST": (FunctionCategory.TABLE, SupportStatus.NOT_SUPPORTED, "数组展开(应使用FLATTEN)"),
            "EXPLODE": (FunctionCategory.TABLE, SupportStatus.NOT_SUPPORTED, "数组展开(应使用FLATTEN)"),
        }
        
        # ===== 聚合函数 (推断支持的) =====
        aggregate_functions = {
            # 基础聚合函数 - 支持的
            "COUNT": (FunctionCategory.AGGREGATE, SupportStatus.SUPPORTED, "计数"),
            "SUM": (FunctionCategory.AGGREGATE, SupportStatus.SUPPORTED, "求和"),
            "AVG": (FunctionCategory.AGGREGATE, SupportStatus.SUPPORTED, "平均值"),
            "MAX": (FunctionCategory.AGGREGATE, SupportStatus.SUPPORTED, "最大值"),
            "MIN": (FunctionCategory.AGGREGATE, SupportStatus.SUPPORTED, "最小值"),
            "STDDEV": (FunctionCategory.AGGREGATE, SupportStatus.SUPPORTED, "标准差"),
            "VARIANCE": (FunctionCategory.AGGREGATE, SupportStatus.SUPPORTED, "方差"),
            
            # 不支持的聚合函数
            "BOOL_AND": (FunctionCategory.AGGREGATE, SupportStatus.NOT_SUPPORTED, "布尔与聚合"),
            "BOOL_OR": (FunctionCategory.AGGREGATE, SupportStatus.NOT_SUPPORTED, "布尔或聚合"),
            "STRING_AGG": (FunctionCategory.AGGREGATE, SupportStatus.NOT_SUPPORTED, "字符串聚合"),
            "ARRAY_AGG": (FunctionCategory.AGGREGATE, SupportStatus.NOT_SUPPORTED, "数组聚合"),
        }
        
        # 合并所有函数
        self.functions.update(scalar_functions)
        self.functions.update(window_functions)
        self.functions.update(table_functions)
        self.functions.update(aggregate_functions)
    
    def is_supported(self, function_name: str) -> bool:
        """检查函数是否被支持"""
        function_name = function_name.upper()
        if function_name not in self.functions:
            return False
        _, status, _ = self.functions[function_name]
        return status == SupportStatus.SUPPORTED
    
    def is_not_supported(self, function_name: str) -> bool:
        """检查函数是否明确不被支持"""
        function_name = function_name.upper()
        if function_name not in self.functions:
            return False
        _, status, _ = self.functions[function_name]
        return status == SupportStatus.NOT_SUPPORTED
    
    def is_partial_supported(self, function_name: str) -> bool:
        """检查函数是否部分支持"""
        function_name = function_name.upper()
        if function_name not in self.functions:
            return False
        _, status, _ = self.functions[function_name]
        return status == SupportStatus.PARTIAL
    
    def get_function_info(self, function_name: str) -> Optional[Tuple[FunctionCategory, SupportStatus, str]]:
        """获取函数信息"""
        function_name = function_name.upper()
        return self.functions.get(function_name)
    
    def get_supported_functions(self, category: Optional[FunctionCategory] = None) -> List[str]:
        """获取支持的函数列表"""
        result = []
        for func_name, (cat, status, desc) in self.functions.items():
            if status == SupportStatus.SUPPORTED:
                if category is None or cat == category:
                    result.append(func_name)
        return sorted(result)
    
    def get_unsupported_functions(self, category: Optional[FunctionCategory] = None) -> List[str]:
        """获取不支持的函数列表"""
        result = []
        for func_name, (cat, status, desc) in self.functions.items():
            if status == SupportStatus.NOT_SUPPORTED:
                if category is None or cat == category:
                    result.append(func_name)
        return sorted(result)
    
    def validate_virtual_inheritance_optimization(self, function_list: List[str]) -> Dict[str, str]:
        """验证虚继承函数优化的合理性"""
        results = {}
        
        for func_name in function_list:
            func_name_upper = func_name.upper()
            info = self.get_function_info(func_name_upper)
            
            if info is None:
                results[func_name] = "UNKNOWN - 函数不在支持矩阵中，需要手动验证"
            else:
                category, status, description = info
                if status == SupportStatus.SUPPORTED:
                    results[func_name] = f"SUPPORTED - {description} (可以优化虚继承)"
                elif status == SupportStatus.NOT_SUPPORTED:
                    results[func_name] = f"NOT_SUPPORTED - {description} (需要错误处理或映射)"
                elif status == SupportStatus.PARTIAL:
                    results[func_name] = f"PARTIAL - {description} (需要条件处理)"
                else:
                    results[func_name] = f"UNKNOWN - {description} (需要进一步验证)"
        
        return results
    
    def generate_optimization_recommendations(self, virtual_functions: List[str]) -> Dict[str, List[str]]:
        """生成优化建议"""
        recommendations = {
            "can_inherit": [],           # 可以直接继承
            "need_mapping": [],          # 需要映射转换
            "need_error_handling": [],   # 需要错误处理
            "need_verification": []      # 需要手动验证
        }
        
        for func_name in virtual_functions:
            func_name_upper = func_name.upper()
            info = self.get_function_info(func_name_upper)
            
            if info is None:
                recommendations["need_verification"].append(func_name)
            else:
                category, status, description = info
                if status == SupportStatus.SUPPORTED:
                    recommendations["can_inherit"].append(func_name)
                elif status == SupportStatus.NOT_SUPPORTED:
                    recommendations["need_error_handling"].append(func_name)
                elif status == SupportStatus.PARTIAL:
                    recommendations["need_mapping"].append(func_name)
                else:
                    recommendations["need_verification"].append(func_name)
        
        return recommendations
    
    def print_matrix_summary(self):
        """打印矩阵摘要"""
        print("🔍 炎凰数据函数支持矩阵摘要")
        print("=" * 60)
        
        # 按类别统计
        category_stats = {}
        status_stats = {}
        
        for func_name, (category, status, desc) in self.functions.items():
            # 类别统计
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
            
            # 状态统计
            if status not in status_stats:
                status_stats[status] = 0
            status_stats[status] += 1
        
        print("📊 按类别统计:")
        for category, count in category_stats.items():
            print(f"   {category.value}: {count} 个函数")
        
        print("\n📊 按支持状态统计:")
        for status, count in status_stats.items():
            print(f"   {status.value}: {count} 个函数")
        
        print(f"\n📊 总计: {len(self.functions)} 个函数")
        
        # 详细列表
        print("\n📋 支持的标量函数列表:")
        supported_scalar = self.get_supported_functions(FunctionCategory.SCALAR)
        for i, func in enumerate(supported_scalar):
            if i % 10 == 0:
                print()
            print(f"{func:15}", end="")
        
        print("\n\n❌ 不支持的函数列表:")
        unsupported = self.get_unsupported_functions()
        for i, func in enumerate(unsupported):
            if i % 8 == 0:
                print()
            print(f"{func:18}", end="")
        print()


def main():
    """主函数 - 演示用法"""
    matrix = YanhuangFunctionMatrix()
    
    # 打印矩阵摘要
    matrix.print_matrix_summary()
    
    # 测试一些函数
    test_functions = ["ABS", "MD5", "ENCODE", "DECODE", "ATAN2", "NOW", "UNKNOWN_FUNC"]
    
    print("\n🔍 函数支持状态测试")
    print("=" * 60)
    
    for func in test_functions:
        info = matrix.get_function_info(func)
        if info:
            category, status, description = info
            print(f"{func:15}: {status.value:15} ({category.value}) - {description}")
        else:
            print(f"{func:15}: UNKNOWN - 不在支持矩阵中")
    
    # 生成优化建议示例
    virtual_functions = ["ABS", "MD5", "ENCODE", "ATAN2", "ROW_NUMBER", "CEILING"]
    recommendations = matrix.generate_optimization_recommendations(virtual_functions)
    
    print("\n🎯 优化建议示例")
    print("=" * 60)
    for category, functions in recommendations.items():
        if functions:
            print(f"{category:20}: {', '.join(functions)}")


if __name__ == "__main__":
    main()
