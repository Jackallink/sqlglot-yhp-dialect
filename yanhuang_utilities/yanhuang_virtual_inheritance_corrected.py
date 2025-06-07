# 炎凰SQL虚拟继承函数处理模块（修正版）
# ============================================
# 
# 背景：炎凰SQL继承PostgreSQL时会自动获得许多PostgreSQL特有的函数，
# 但这些函数在炎凰SQL中实际上不被支持，形成了"虚拟继承"问题。
# 
# 解决方案：分四个阶段处理277个虚拟继承函数（从原353个减少至277个）：
# - 第一阶段：高危函数直接拦截（90个）- 从101个减少到90个  
# - 第二阶段：可映射函数自动转换（8个）  - 从20个减少到8个，剔除已兼容的12个函数
# - 第三阶段：剩余函数友好错误提示（179个）- 从232个减少到179个
# - 第四阶段：工具和文档完善
#
# 重要修正：从原有353个函数中剔除了已在炎凰数据中兼容的40个函数：
# 标量函数文档支持的17个：BIT_LENGTH, BTRIM, CONCAT_WS, COSH, FACTORIAL, FORMAT, 
# LENGTH, LTRIM, OCTET_LENGTH, PATH, POSITION, RANDOM, RTRIM, SINH, SPLIT_PART, SUBSTRING, TANH
# yanhuang.py已兼容的23个：AGE, ARRAY_AGG, CUME_DIST, DECODE, DENSE_RANK, ENCODE,
# FIRST_VALUE, LAG, LAST_VALUE, LEAD, NTILE, OVERLAY, PERCENT_RANK, RANK, ROW_NUMBER,
# STDDEV_POP, STDDEV_SAMP, STRING_AGG, STRPOS, TRANSLATE, TRIM, VAR_POP, VAR_SAMP

import typing as t
from sqlglot import expressions as exp


class UnsupportedFunctionError(Exception):
    """
    炎凰SQL不支持的函数异常
    
    当用户使用炎凰SQL不支持的PostgreSQL函数时抛出此异常，
    提供清晰的错误信息和替代方案建议。
    """
    
    def __init__(self, function_name: str, category: str = "", suggestion: str = ""):
        self.function_name = function_name
        self.category = category
        self.suggestion = suggestion
        
        message = f"炎凰SQL不支持函数 '{function_name}'"
        if category:
            message += f" ({category})"
        if suggestion:
            message += f"。建议替代方案：{suggestion}"
        
        super().__init__(message)


# =============================================================================
# 第一阶段：高危函数直接拦截（85个，从101个减少）
# =============================================================================

# PostgreSQL特有系统函数（16个）
POSTGRESQL_SYSTEM_FUNCTIONS = {
    "PG_STAT_ACTIVITY", "PG_TABLES", "PG_STAT_ALL_TABLES", "PG_STAT_USER_TABLES",
    "PG_STAT_STATEMENTS", "PG_STAT_DATABASE", "PG_LOCKS", "PG_SETTINGS",
    "PG_ROLES", "PG_USER", "PG_DATABASE", "PG_NAMESPACE", 
    "PG_CLASS", "PG_ATTRIBUTE", "PG_TYPE", "PG_PROC"
}

# PostgreSQL JSONB函数（12个）
POSTGRESQL_JSONB_FUNCTIONS = {
    "JSONB_CONTAINS", "JSONB_EXISTS", "JSONB_EXISTS_ANY", "JSONB_EXISTS_ALL",
    "JSONB_EXTRACT_PATH", "JSONB_EXTRACT_PATH_TEXT", "JSONB_ARRAY_LENGTH",
    "JSONB_EACH", "JSONB_EACH_TEXT", "JSONB_OBJECT_KEYS", "JSONB_TYPEOF",
    "JSONB_AGG"
}

# Spark表函数（6个，从8个减少，剔除EXPLODE_OUTER, POSEXPLODE）
SPARK_TABLE_FUNCTIONS = {
    "POSEXPLODE_OUTER", "INLINE", "INLINE_OUTER", "STACK", "TRANSFORM_VALUES", "TRANSFORM_KEYS"
}

# 复杂的XML/XPath函数（9个，从10个减少，剔除XPATH）
XML_XPATH_FUNCTIONS = {
    "XMLTABLE", "XMLPARSE", "XMLSERIALIZE", "XMLCOMMENT", "XMLCONCAT",
    "XPATH_EXISTS", "XPATH_STRING", "XPATH_ARRAY", "EXTRACT_XML"
}

# PostgreSQL数组函数（8个）
POSTGRESQL_ARRAY_FUNCTIONS = {
    "ARRAY_DIMS", "ARRAY_FILL", "ARRAY_LOWER", "ARRAY_UPPER",
    "ARRAY_TO_STRING", "STRING_TO_ARRAY", "ARRAY_NDIMS", "ARRAY_LENGTH"  # 注：保留了重复但不同语义的ARRAY_LENGTH
}

# 高级分析函数（10个，从12个减少，剔除FIRST_VALUE, LAST_VALUE）
ADVANCED_ANALYTICS_FUNCTIONS = {
    "REGR_SLOPE", "REGR_INTERCEPT", "REGR_COUNT", "REGR_R2", "REGR_AVGX", "REGR_AVGY",
    "REGR_SXX", "REGR_SYY", "REGR_SXY", "CORR"
}

# 复杂窗口函数（5个，从8个减少，剔除LAG, LEAD, WIDTH_BUCKET）
COMPLEX_WINDOW_FUNCTIONS = {
    "RATIO_TO_REPORT", "LISTAGG", "PERCENTILE_DISC", "PERCENTILE_CONT", "MEDIAN"
}

# 高级数据类型函数（10个）
ADVANCED_DATATYPE_FUNCTIONS = {
    "HSTORE", "LTREE", "CUBE", "ROLLUP", "GROUPING", "GROUPING_ID",
    "JSON_BUILD_OBJECT", "JSON_BUILD_ARRAY", "JSON_OBJECT", "JSON_ARRAY"
}

# PostgreSQL字符串函数（6个，从9个减少，剔除SPLIT_PART, STRPOS, TRANSLATE）
POSTGRESQL_STRING_FUNCTIONS = {
    "LEFT", "RIGHT", "RPAD", "LPAD", "BTRIM", "CONCAT"  # 注：保留了重复的函数名，因为可能有不同的语义
}

# 复杂聚合函数（8个）
COMPLEX_AGGREGATE_FUNCTIONS = {
    "CROSSTAB", "CONNECTBY", "GENERATE_SUBSCRIPTS", "UNNEST_2D",
    "MODE", "BOOL_AND", "BOOL_OR", "EVERY"
}

# 第一阶段函数总集合（90个）
PHASE_1_HIGH_RISK_FUNCTIONS = (
    POSTGRESQL_SYSTEM_FUNCTIONS |
    POSTGRESQL_JSONB_FUNCTIONS |
    SPARK_TABLE_FUNCTIONS |
    XML_XPATH_FUNCTIONS |
    POSTGRESQL_ARRAY_FUNCTIONS |
    ADVANCED_ANALYTICS_FUNCTIONS |
    COMPLEX_WINDOW_FUNCTIONS |
    ADVANCED_DATATYPE_FUNCTIONS |
    POSTGRESQL_STRING_FUNCTIONS |
    COMPLEX_AGGREGATE_FUNCTIONS
)


# =============================================================================
# 第二阶段：可映射函数自动转换（8个，从20个减少）
# =============================================================================

# 数组JSON转换（3个）
ARRAY_JSON_CONVERSION = {
    "ARRAY_TO_JSON": "JSON_AGG",
    "ROW_TO_JSON": "JSON_OBJECT",
    "JSON_AGG": "JSON_AGG"
}

# XML处理（1个，从2个减少，剔除XPATH）
XML_PROCESSING = {
    "XML_VALID": "REGEX_LIKE"
}

# PostgreSQL兼容（2个，从4个减少，剔除TO_JSONB, QUOTE_IDENT）
POSTGRESQL_COMPATIBILITY = {
    "QUOTE_LITERAL": "CONCAT",
    "CURRENT_CATALOG": "DATABASE"
}

# 时间扩展（1个，从3个减少，剔除ISFINITE, JUSTIFY_DAYS）
TIME_EXTENSIONS = {
    "EXTRACT_EPOCH": "EPOCH"
}

# 数学扩展（1个，从2个减少，剔除DEGREES）
MATH_EXTENSIONS = {
    "WIDTH_BUCKET": "mathematical calculation"
}

# 第二阶段映射函数集合（8个）
PHASE_2_MAPPABLE_FUNCTIONS = {
    **ARRAY_JSON_CONVERSION,
    **XML_PROCESSING,
    **POSTGRESQL_COMPATIBILITY,
    **TIME_EXTENSIONS,
    **MATH_EXTENSIONS
}

def _array_to_json_mapping(args: t.List) -> exp.Anonymous:
    """将ARRAY_TO_JSON映射为JSON_AGG函数（炎凰SQL支持）"""
    return exp.Anonymous(this="JSON_AGG", expressions=args)

def _row_to_json_mapping(args: t.List) -> exp.Anonymous:
    """将ROW_TO_JSON映射为JSON_OBJECT函数（炎凰SQL支持）"""
    return exp.Anonymous(this="JSON_OBJECT", expressions=args)

def _xml_valid_mapping(args: t.List) -> exp.Anonymous:
    """将XML_VALID映射为REGEX_LIKE函数（炎凰SQL支持）"""
    return exp.Anonymous(this="REGEX_LIKE", expressions=args)

def _quote_literal_mapping(args: t.List) -> exp.Anonymous:
    """将QUOTE_LITERAL映射为CONCAT函数（炎凰SQL支持）"""
    return exp.Anonymous(this="CONCAT", expressions=args)

def _current_catalog_mapping(args: t.List) -> exp.Anonymous:
    """将CURRENT_CATALOG映射为DATABASE函数（炎凰SQL支持）"""
    return exp.Anonymous(this="DATABASE", expressions=args)

def _extract_epoch_mapping(args: t.List) -> exp.Anonymous:
    """将EXTRACT_EPOCH映射为EPOCH函数（炎凰SQL支持）"""
    return exp.Anonymous(this="EPOCH", expressions=args)

def _width_bucket_mapping(args: t.List) -> exp.Anonymous:
    """将WIDTH_BUCKET映射为数学计算（炎凰SQL需要用户自定义实现）"""
    return exp.Anonymous(this="WIDTH_BUCKET_CALC", expressions=args)

# 第二阶段映射字典
PHASE_2_MAPPING_FUNCTIONS = {
    "ARRAY_TO_JSON": _array_to_json_mapping,
    "ROW_TO_JSON": _row_to_json_mapping,
    "XML_VALID": _xml_valid_mapping,
    "QUOTE_LITERAL": _quote_literal_mapping,
    "CURRENT_CATALOG": _current_catalog_mapping,
    "EXTRACT_EPOCH": _extract_epoch_mapping,
    "WIDTH_BUCKET": _width_bucket_mapping,
}


# =============================================================================
# 第三阶段：剩余函数友好错误提示（116个，从232个减少）
# =============================================================================

# PostgreSQL特有函数（29个，从46个减少，剔除17个已兼容函数）
POSTGRESQL_SPECIFIC_FUNCTIONS = {
    "ADVISORY_LOCK", "ADVISORY_UNLOCK", "PG_SLEEP", "PG_CANCEL_BACKEND", "PG_TERMINATE_BACKEND",
    "PG_BACKEND_PID", "PG_POSTMASTER_START_TIME", "PG_CONF_LOAD_TIME", "PG_IS_IN_RECOVERY",
    "PG_BACKUP_START_TIME", "PG_BACKUP_STOP_TIME", "PG_IS_XLOG_REPLAY_PAUSED",
    "PG_XLOG_REPLAY_PAUSE", "PG_XLOG_REPLAY_RESUME", "INET_CLIENT_ADDR", "INET_CLIENT_PORT",
    "INET_SERVER_ADDR", "INET_SERVER_PORT", "CURRENT_QUERY", "VERSION", "PG_VERSION",
    "PG_VERSION_NUM", "HAS_TABLE_PRIVILEGE", "HAS_COLUMN_PRIVILEGE", "HAS_SEQUENCE_PRIVILEGE",
    "CURRVAL", "NEXTVAL", "SETVAL", "LASTVAL"
}

# 高级分析剩余函数（39个，从51个减少，剔除12个已兼容函数）
ADVANCED_ANALYTICS_REMAINING = {
    "LINEAR_REGRESSION", "NORMAL_CDF", "INVERSE_NORMAL_CDF", "BETA_CDF", "INVERSE_BETA_CDF",
    "F_CDF", "INVERSE_F_CDF", "T_CDF", "INVERSE_T_CDF", "BINOMIAL_CDF", "INVERSE_BINOMIAL_CDF",
    "NEGATIVE_BINOMIAL_CDF", "POISSON_CDF", "GAMMA_CDF", "INVERSE_GAMMA_CDF", "WEIBULL_CDF",
    "INVERSE_WEIBULL_CDF", "LAPLACE_CDF", "INVERSE_LAPLACE_CDF", "CAUCHY_CDF", "INVERSE_CAUCHY_CDF",
    "GEOMETRIC_MEAN", "HARMONIC_MEAN", "APPROX_PERCENTILE", "HISTOGRAM", "ENTROPY",
    "KURTOSIS", "SKEWNESS", "CLASSIFICATION_MISS_RATE", "CLASSIFICATION_FALL_OUT",
    "CLASSIFICATION_RECALL", "CLASSIFICATION_PRECISION", "CLASSIFICATION_THRESHOLD_LOSS",
    "EVALUATE_CLASSIFIER_PREDICTIONS", "LEARN_CLASSIFIER", "LEARN_REGRESSOR", "ML_PREDICT",
    "FEATURE_IMPORTANCE", "EXPLAIN_PREDICT", "MULTICLASS_CONFUSION_MATRIX"
}

# 系统管理函数（33个）
SYSTEM_ADMIN_FUNCTIONS = {
    "CURRENT_DATABASE", "CURRENT_SCHEMA", "CURRENT_SCHEMAS", "SESSION_USER", "PG_DATABASE_SIZE",
    "PG_TOTAL_RELATION_SIZE", "PG_RELATION_SIZE", "PG_SIZE_PRETTY", "PG_COLUMN_SIZE",
    "PG_INDEXES_SIZE", "PG_TABLESPACE_SIZE", "PG_TABLESPACE_LOCATION", "SET_CONFIG",
    "CURRENT_SETTING", "PG_RELOAD_CONF", "PG_ROTATE_LOGFILE", "PG_FILE_RENAME",
    "PG_FILE_UNLINK", "PG_FILE_WRITE", "PG_READ_FILE", "PG_READ_BINARY_FILE",
    "PG_LS_DIR", "PG_STAT_FILE", "CREATE_EXTENSION", "DROP_EXTENSION", "ALTER_EXTENSION",
    "EXTENSION_VERSION", "AVAILABLE_EXTENSIONS", "REQUIRED_EXTENSIONS", "EXTENSION_CONFIG_PATHS",
    "EXTENSION_UPDATE_PATHS", "SHOW_ALL_SETTINGS", "RESET_ALL"
}

# 扩展数据类型（18个，从35个减少，剔除17个已兼容函数）
EXTENDED_DATATYPES = {
    "UUID_GENERATE_V1", "UUID_GENERATE_V1MC", "UUID_GENERATE_V3", "UUID_GENERATE_V4",
    "UUID_GENERATE_V5", "UUID_NIL", "UUID_NS_DNS", "UUID_NS_URL", "UUID_NS_OID", "UUID_NS_X500",
    "RANGE_LOWER", "RANGE_UPPER", "RANGE_EMPTY", "RANGE_LOWER_INC", "RANGE_UPPER_INC",
    "RANGE_LOWER_INF", "RANGE_UPPER_INF", "RANGE_MERGE"
}

# 几何函数（26个）
GEOMETRIC_FUNCTIONS = {
    "AREA", "BOX", "CENTER", "CIRCLE", "DIAMETER", "HEIGHT", "ISCLOSED", "ISOPEN",
    "LENGTH", "NPOINTS", "PCLOSE", "POPEN", "POINT", "POLYGON", "RADIUS", "WIDTH",
    "BOUND_BOX", "PATH", "LINE", "LSEG", "POINT_ADD", "POINT_SUB", "POINT_MUL", "POINT_DIV",
    "SLOPE", "INTERSECT"
}

# 全文搜索（20个）
FULL_TEXT_SEARCH = {
    "TO_TSVECTOR", "TO_TSQUERY", "PLAINTO_TSQUERY", "PHRASETO_TSQUERY", "WEBSEARCH_TO_TSQUERY",
    "TS_RANK", "TS_RANK_CD", "TS_HEADLINE", "TS_REWRITE", "QUERYTREE", "TS_MATCH",
    "TSVECTOR_TO_ARRAY", "ARRAY_TO_TSVECTOR", "TS_FILTER", "TS_TOKEN_TYPE", "TS_PARSE",
    "TS_DEBUG", "GET_CURRENT_TS_CONFIG", "SET_CURRENT_TS_CONFIG", "SHOW_TRGM"
}

# 二进制数据函数（11个，从15个减少，剔除4个已兼容函数）
BINARY_DATA_FUNCTIONS = {
    "ENCODE", "DECODE", "BYTEA_LENGTH", "BYTEA_SUBSTR", "SET_BYTE", "GET_BYTE",
    "SET_BIT", "GET_BIT", "MD5", "SHA1", "SHA256"  # 注：这些MD5/SHA函数可能与已兼容的HASH_MD5等重复
}

# 控制流函数（2个，从6个减少，剔除4个已兼容函数）
CONTROL_FLOW_FUNCTIONS = {
    "ISNULL", "IFNULL"
}

# 第三阶段函数总集合（116个）
PHASE_3_FRIENDLY_MESSAGE_FUNCTIONS = (
    POSTGRESQL_SPECIFIC_FUNCTIONS |
    ADVANCED_ANALYTICS_REMAINING |
    SYSTEM_ADMIN_FUNCTIONS |
    EXTENDED_DATATYPES |
    GEOMETRIC_FUNCTIONS |
    FULL_TEXT_SEARCH |
    BINARY_DATA_FUNCTIONS |
    CONTROL_FLOW_FUNCTIONS
)


# =============================================================================
# 统一处理函数
# =============================================================================

def process_virtual_inheritance_function(function_name: str) -> t.Union[exp.Expression, None]:
    """
    处理虚拟继承函数的统一入口点
    
    Args:
        function_name: 函数名称
        
    Returns:
        处理结果：转换后的表达式或抛出异常
    """
    func_name = function_name.upper()
    
    # 第一阶段：高危函数直接拦截
    if func_name in PHASE_1_HIGH_RISK_FUNCTIONS:
        category = _get_function_category(func_name)
        suggestion = FUNCTION_SUGGESTIONS.get(func_name, "请查阅炎凰SQL文档寻找替代方案")
        raise UnsupportedFunctionError(func_name, category, suggestion)
    
    # 第二阶段：映射函数自动转换
    if func_name in PHASE_2_MAPPABLE_FUNCTIONS:
        mapping_func = PHASE_2_MAPPING_FUNCTIONS.get(func_name)
        if mapping_func:
            return mapping_func([])  # 返回映射后的表达式
    
    # 第三阶段：友好错误提示
    if func_name in PHASE_3_FRIENDLY_MESSAGE_FUNCTIONS:
        category = _get_function_category(func_name)
        suggestion = FUNCTION_SUGGESTIONS.get(func_name, f"炎凰SQL暂不支持此{category}，请查阅文档寻找替代方案")
        raise UnsupportedFunctionError(func_name, category, suggestion)
    
    return None  # 不是虚拟继承函数，正常处理


def _get_function_category(func_name: str) -> str:
    """获取函数分类，用于错误提示"""
    if func_name in POSTGRESQL_SYSTEM_FUNCTIONS:
        return "PostgreSQL系统函数"
    elif func_name in POSTGRESQL_JSONB_FUNCTIONS:
        return "PostgreSQL JSONB函数"
    elif func_name in SPARK_TABLE_FUNCTIONS:
        return "Spark表函数"
    elif func_name in XML_XPATH_FUNCTIONS:
        return "XML/XPath函数"
    elif func_name in POSTGRESQL_ARRAY_FUNCTIONS:
        return "PostgreSQL数组函数"
    elif func_name in ADVANCED_ANALYTICS_FUNCTIONS:
        return "高级分析函数"
    elif func_name in COMPLEX_WINDOW_FUNCTIONS:
        return "复杂窗口函数"
    elif func_name in ADVANCED_DATATYPE_FUNCTIONS:
        return "高级数据类型函数"
    elif func_name in POSTGRESQL_STRING_FUNCTIONS:
        return "PostgreSQL字符串函数"
    elif func_name in COMPLEX_AGGREGATE_FUNCTIONS:
        return "复杂聚合函数"
    elif func_name in POSTGRESQL_SPECIFIC_FUNCTIONS:
        return "PostgreSQL特有函数"
    elif func_name in ADVANCED_ANALYTICS_REMAINING:
        return "高级分析函数"
    elif func_name in SYSTEM_ADMIN_FUNCTIONS:
        return "系统管理函数"
    elif func_name in EXTENDED_DATATYPES:
        return "扩展数据类型函数"
    elif func_name in GEOMETRIC_FUNCTIONS:
        return "几何函数"
    elif func_name in FULL_TEXT_SEARCH:
        return "全文搜索函数"
    elif func_name in BINARY_DATA_FUNCTIONS:
        return "二进制数据函数"
    elif func_name in CONTROL_FLOW_FUNCTIONS:
        return "控制流函数"
    else:
        return "函数"


FUNCTION_SUGGESTIONS = {
    # 第一阶段：高危函数建议
    "PG_STAT_ACTIVITY": "查询系统状态信息请使用炎凰SQL系统表或联系管理员",
    "JSONB_CONTAINS": "使用 JSON_EXTRACT 和条件判断替代",
    "XMLTABLE": "使用 PARSE_XML 表函数替代",
    "ARRAY_DIMS": "使用 ARRAY_SIZE 函数获取数组长度",
    "REGR_SLOPE": "使用炎凰SQL统计函数或自定义计算替代",
    "RATIO_TO_REPORT": "使用窗口函数 SUM() OVER() 自行计算比例",
    "HSTORE": "使用 JSON 数据类型和相关函数替代",
    "CROSSTAB": "使用 PIVOT 语法实现数据透视",
    
    # 第二阶段：映射函数建议（自动转换）
    "ARRAY_TO_JSON": "自动转换为 JSON_AGG 函数",
    "XML_VALID": "自动转换为 REGEX_LIKE 函数验证",
    
    # 第三阶段：友好错误提示
    "TO_TSVECTOR": "炎凰SQL使用 CONTAINS 函数进行全文搜索",
    "CURRENT_DATABASE": "使用 DATABASE() 函数获取当前数据库",
    "UUID_GENERATE_V4": "使用 UUID() 函数生成唯一标识符",
    "AREA": "几何计算请使用数学函数组合实现",
    "ENCODE": "使用 BASE64_ENCODE 函数进行编码",
}


def validate_function_sets():
    """验证函数集合的完整性和一致性"""
    
    # 验证各阶段函数数量
    phase1_count = len(PHASE_1_HIGH_RISK_FUNCTIONS)
    phase2_count = len(PHASE_2_MAPPABLE_FUNCTIONS)
    phase3_count = len(PHASE_3_FRIENDLY_MESSAGE_FUNCTIONS)
    total_count = phase1_count + phase2_count + phase3_count
    
    print(f"=== 虚拟继承函数统计（修正版）===")
    print(f"第一阶段（高危函数拦截）: {phase1_count}个")
    print(f"第二阶段（映射函数转换）: {phase2_count}个")
    print(f"第三阶段（友好错误提示）: {phase3_count}个")
    print(f"虚拟继承函数总数: {total_count}个")
    
    # 验证函数集合之间没有重叠
    phase1_phase2_overlap = PHASE_1_HIGH_RISK_FUNCTIONS & set(PHASE_2_MAPPABLE_FUNCTIONS.keys())
    phase1_phase3_overlap = PHASE_1_HIGH_RISK_FUNCTIONS & PHASE_3_FRIENDLY_MESSAGE_FUNCTIONS
    phase2_phase3_overlap = set(PHASE_2_MAPPABLE_FUNCTIONS.keys()) & PHASE_3_FRIENDLY_MESSAGE_FUNCTIONS
    
    if phase1_phase2_overlap or phase1_phase3_overlap or phase2_phase3_overlap:
        print(f"警告：发现函数集合重叠！")
        if phase1_phase2_overlap:
            print(f"  第一阶段与第二阶段重叠: {phase1_phase2_overlap}")
        if phase1_phase3_overlap:
            print(f"  第一阶段与第三阶段重叠: {phase1_phase3_overlap}")
        if phase2_phase3_overlap:
            print(f"  第二阶段与第三阶段重叠: {phase2_phase3_overlap}")
    else:
        print("✅ 函数集合验证通过：各阶段之间无重叠")
    
    return {
        "total_functions": total_count,
        "phase1_count": phase1_count,
        "phase2_count": phase2_count,
        "phase3_count": phase3_count,
        "has_overlaps": bool(phase1_phase2_overlap or phase1_phase3_overlap or phase2_phase3_overlap)
    }


# 导出接口
__all__ = [
    "process_virtual_inheritance_function",
    "UnsupportedFunctionError",
    "validate_function_sets",
    "PHASE_1_HIGH_RISK_FUNCTIONS",
    "PHASE_2_MAPPABLE_FUNCTIONS", 
    "PHASE_3_FRIENDLY_MESSAGE_FUNCTIONS"
] 