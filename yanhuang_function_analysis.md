# 炎凰SQL标量函数和表函数分析报告

## 📋 概述

本报告基于炎凰SQL文档和PostgreSQL对比，系统分析炎凰SQL的标量函数和表函数支持情况，确定哪些可以直接复用PostgreSQL，哪些需要自定义实现。

## 🎯 分析维度

1. **直接复用PostgreSQL** - 可以直接使用PostgreSQL的函数实现
2. **需要Transform映射** - 需要在Generator中添加转换逻辑
3. **需要新增实现** - 炎凰SQL特有的函数，需要完全自定义
4. **需要限制检查** - PostgreSQL支持但炎凰SQL不支持的功能

---

## 📊 标量函数（Scalar Function）分析

### ✅ 可直接复用PostgreSQL的标量函数

#### 字符串函数
- `UPPER()` - 转大写 ✅ 直接复用
- `LOWER()` - 转小写 ✅ 直接复用  
- `SUBSTR()` - 字符串截取 ✅ 直接复用
- `LENGTH()` - 字符串长度 ✅ 直接复用
- `TRIM()` - 去除空格 ✅ 直接复用
- `LTRIM()` - 去除左空格 ✅ 直接复用
- `RTRIM()` - 去除右空格 ✅ 直接复用
- `CONCAT()` - 字符串连接 ✅ 直接复用
- `REPLACE()` - 字符串替换 ✅ 直接复用
- `SPLIT_PART()` - 字符串分割 ✅ 直接复用

#### 数学函数
- `ABS()` - 绝对值 ✅ 直接复用
- `CEIL()` - 向上取整 ✅ 直接复用
- `FLOOR()` - 向下取整 ✅ 直接复用
- `ROUND()` - 四舍五入 ✅ 直接复用
- `SQRT()` - 平方根 ✅ 直接复用
- `POWER()` - 幂运算 ✅ 直接复用
- `MOD()` - 取模 ✅ 直接复用
- `GREATEST()` - 最大值 ✅ 直接复用
- `LEAST()` - 最小值 ✅ 直接复用

#### 类型转换函数
- `CAST()` - 类型转换 ✅ 直接复用
- `COALESCE()` - 空值处理 ✅ 直接复用
- `NULLIF()` - 空值判断 ✅ 直接复用

#### 日期时间函数
- `NOW()` - 当前时间 ✅ 直接复用
- `CURRENT_TIMESTAMP` - 当前时间戳 ✅ 直接复用
- `EXTRACT()` - 提取日期部分 ✅ 直接复用
- `DATE_TRUNC()` - 日期截断 ✅ 直接复用

### 🔄 需要Transform映射的标量函数

#### 已实现的Transform
```python
# 在sqlglot/dialects/yanhuang.py中已实现
FUNCTIONS = {
    **Postgres.Parser.FUNCTIONS,
    "CONTAINS": lambda args: exp.Anonymous(this="CONTAINS", expressions=args),
    "CAST": exp.Cast.from_arg_list,
    "CONCAT": exp.Concat.from_arg_list,
    # ... 其他已实现的函数
}
```

#### 需要补充的Transform
1. **字符串函数增强**
   ```python
   # 需要添加的字符串函数
   "SUBSTRING": lambda args: exp.Substring.from_arg_list(args),
   "POSITION": lambda args: exp.StrPosition.from_arg_list(args),
   "CHAR_LENGTH": lambda args: exp.Length.from_arg_list(args),
   "CHARACTER_LENGTH": lambda args: exp.Length.from_arg_list(args),
   "LEFT": lambda args: exp.Left.from_arg_list(args),
   "RIGHT": lambda args: exp.Right.from_arg_list(args),
   "REVERSE": lambda args: exp.Anonymous(this="REVERSE", expressions=args),
   "REPEAT": lambda args: exp.Repeat.from_arg_list(args),
   "LPAD": lambda args: exp.Anonymous(this="LPAD", expressions=args),
   "RPAD": lambda args: exp.Anonymous(this="RPAD", expressions=args),
   ```

2. **数学函数增强**
   ```python
   # 需要添加的数学函数
   "SIN": lambda args: exp.Anonymous(this="SIN", expressions=args),
   "COS": lambda args: exp.Anonymous(this="COS", expressions=args),
   "TAN": lambda args: exp.Anonymous(this="TAN", expressions=args),
   "ASIN": lambda args: exp.Anonymous(this="ASIN", expressions=args),
   "ACOS": lambda args: exp.Anonymous(this="ACOS", expressions=args),
   "ATAN": lambda args: exp.Anonymous(this="ATAN", expressions=args),
   "LOG": lambda args: exp.Log.from_arg_list(args),
   "LOG10": lambda args: exp.Log10.from_arg_list(args),
   "EXP": lambda args: exp.Exp.from_arg_list(args),
   "SIGN": lambda args: exp.Anonymous(this="SIGN", expressions=args),
   "TRUNC": lambda args: exp.Anonymous(this="TRUNC", expressions=args),
   ```

3. **条件函数**
   ```python
   # 条件判断函数
   "IF": lambda args: exp.If.from_arg_list(args),
   "CASE": lambda args: exp.Case.from_arg_list(args),
   "DECODE": lambda args: exp.Anonymous(this="DECODE", expressions=args),
   ```

### 🆕 需要新增实现的炎凰SQL特有标量函数

#### 1. CONTAINS函数（已实现）
```python
# 已在yanhuang.py中实现
"CONTAINS": lambda args: exp.Anonymous(this="CONTAINS", expressions=args),
```

#### 2. 需要新增的炎凰SQL特有函数
```python
# 炎凰SQL特有的函数，需要新增
"IP_TO_COUNTRY": lambda args: exp.Anonymous(this="IP_TO_COUNTRY", expressions=args),
"IP_TO_REGION": lambda args: exp.Anonymous(this="IP_TO_REGION", expressions=args),
"IP_TO_CITY": lambda args: exp.Anonymous(this="IP_TO_CITY", expressions=args),
"GEOHASH": lambda args: exp.Anonymous(this="GEOHASH", expressions=args),
"TIME_BUCKET": lambda args: exp.Anonymous(this="TIME_BUCKET", expressions=args),
"REGEX_EXTRACT": lambda args: exp.Anonymous(this="REGEX_EXTRACT", expressions=args),
"REGEX_MATCH": lambda args: exp.Anonymous(this="REGEX_MATCH", expressions=args),
"JSON_EXTRACT_SCALAR": lambda args: exp.JSONExtractScalar.from_arg_list(args),
"JSON_EXTRACT": lambda args: exp.JSONExtract.from_arg_list(args),
```

### ⚠️ 需要限制检查的PostgreSQL函数

#### 1. 复杂类型函数（应报错）
- `ARRAY_*` 系列函数 - 炎凰SQL不支持数组类型
- `JSONB_*` 系列函数 - 炎凰SQL不支持JSONB类型
- `HSTORE_*` 系列函数 - 炎凰SQL不支持HSTORE类型

#### 2. 高级数学函数（部分支持）
- 三角函数：基础支持，复杂的不支持
- 统计函数：基础支持，高级的不支持

---

## 📊 表函数（Table Function）分析

### ✅ 可直接复用PostgreSQL的表函数

#### 基础表函数
- `GENERATE_SERIES()` - 生成数字序列 ✅ 直接复用
- `UNNEST()` - 数组展开 ⚠️ 有限支持（炎凰SQL数组支持有限）

### 🔄 需要Transform映射的表函数

#### 已实现的Transform
```python
# 在yanhuang.py中已有部分实现
TRANSFORMS = {
    **Postgres.Generator.TRANSFORMS,
    exp.Explode: lambda self, e: self.explode_sql(e),
    # ... 其他已实现的转换
}
```

#### 需要补充的Transform
```python
# 需要添加的表函数转换
exp.GenerateSeries: lambda self, e: self.func("GENERATE_SERIES", *e.expressions),
exp.Unnest: lambda self, e: self.func("UNNEST", e.this),
```

### 🆕 需要新增实现的炎凰SQL特有表函数

#### 1. 数据解析表函数
```python
# 炎凰SQL特有的表函数
"PARSE_JSON": lambda args: exp.Anonymous(this="PARSE_JSON", expressions=args),
"PARSE_CSV": lambda args: exp.Anonymous(this="PARSE_CSV", expressions=args),
"PARSE_REGEX": lambda args: exp.Anonymous(this="PARSE_REGEX", expressions=args),
"PARSE_KV": lambda args: exp.Anonymous(this="PARSE_KV", expressions=args),
"PARSE_XML": lambda args: exp.Anonymous(this="PARSE_XML", expressions=args),
```

#### 2. 地理位置表函数
```python
"IP_LOCATION": lambda args: exp.Anonymous(this="IP_LOCATION", expressions=args),
"GEO_DISTANCE": lambda args: exp.Anonymous(this="GEO_DISTANCE", expressions=args),
```

#### 3. 数据加载表函数
```python
"LOAD_CSV": lambda args: exp.Anonymous(this="LOAD_CSV", expressions=args),
"LOAD_JSON": lambda args: exp.Anonymous(this="LOAD_JSON", expressions=args),
"LOAD_PARQUET": lambda args: exp.Anonymous(this="LOAD_PARQUET", expressions=args),
```

### ⚠️ 需要限制检查的PostgreSQL表函数

#### 1. 复杂表函数（应报错）
- `LATERAL` 子查询 - 炎凰SQL不支持
- `JSONB_*` 表函数 - 炎凰SQL不支持JSONB
- `CROSSTAB()` - 炎凰SQL不支持
- 自定义PL/pgSQL表函数 - 炎凰SQL不支持

---

## 🛠️ 实现建议

### 1. 立即实施（高优先级）

#### A. 补充常用标量函数
```python
# 在sqlglot/dialects/yanhuang.py的FUNCTIONS中添加
FUNCTIONS = {
    **Postgres.Parser.FUNCTIONS,
    
    # 字符串函数补充
    "SUBSTRING": lambda args: exp.Substring.from_arg_list(args),
    "POSITION": lambda args: exp.StrPosition.from_arg_list(args),
    "LEFT": lambda args: exp.Left.from_arg_list(args),
    "RIGHT": lambda args: exp.Right.from_arg_list(args),
    "REVERSE": lambda args: exp.Anonymous(this="REVERSE", expressions=args),
    "LPAD": lambda args: exp.Anonymous(this="LPAD", expressions=args),
    "RPAD": lambda args: exp.Anonymous(this="RPAD", expressions=args),
    
    # 数学函数补充
    "SIN": lambda args: exp.Anonymous(this="SIN", expressions=args),
    "COS": lambda args: exp.Anonymous(this="COS", expressions=args),
    "TAN": lambda args: exp.Anonymous(this="TAN", expressions=args),
    "LOG": lambda args: exp.Log.from_arg_list(args),
    "LOG10": lambda args: exp.Log10.from_arg_list(args),
    "EXP": lambda args: exp.Exp.from_arg_list(args),
    
    # 条件函数
    "IF": lambda args: exp.If.from_arg_list(args),
    
    # 炎凰SQL特有函数
    "TIME_BUCKET": lambda args: exp.Anonymous(this="TIME_BUCKET", expressions=args),
    "REGEX_EXTRACT": lambda args: exp.Anonymous(this="REGEX_EXTRACT", expressions=args),
    "REGEX_MATCH": lambda args: exp.Anonymous(this="REGEX_MATCH", expressions=args),
}
```

#### B. 添加表函数支持
```python
# 表函数支持
"GENERATE_SERIES": _build_generate_series,  # 复用PostgreSQL实现
"PARSE_JSON": lambda args: exp.Anonymous(this="PARSE_JSON", expressions=args),
"PARSE_CSV": lambda args: exp.Anonymous(this="PARSE_CSV", expressions=args),
"IP_LOCATION": lambda args: exp.Anonymous(this="IP_LOCATION", expressions=args),
```

### 2. 中期实施（中优先级）

#### A. 添加函数限制检查
```python
def _check_function_support(self, expression: exp.Anonymous) -> None:
    """检查函数是否被炎凰SQL支持"""
    unsupported_functions = {
        "ARRAY_AGG", "ARRAY_LENGTH", "ARRAY_APPEND",
        "JSONB_AGG", "JSONB_OBJECT_AGG", "JSONB_BUILD_OBJECT",
        "HSTORE", "AKEYS", "AVALS",
        "CROSSTAB", "CONNECTBY",
    }
    
    if expression.this.upper() in unsupported_functions:
        self.unsupported(f"Function {expression.this} is not supported in YanhuangSQL")
```

#### B. 完善Generator转换
```python
TRANSFORMS = {
    **Postgres.Generator.TRANSFORMS,
    
    # 表函数转换
    exp.GenerateSeries: lambda self, e: self.func("GENERATE_SERIES", *e.expressions),
    
    # 炎凰SQL特有函数的生成
    exp.Anonymous: lambda self, e: self._anonymous_sql(e),
}

def _anonymous_sql(self, expression: exp.Anonymous) -> str:
    """处理炎凰SQL特有的匿名函数"""
    func_name = expression.this
    if func_name in ("CONTAINS", "TIME_BUCKET", "REGEX_EXTRACT", "PARSE_JSON"):
        return self.func(func_name, *expression.expressions)
    return self.function_fallback_sql(expression)
```

### 3. 长期规划（低优先级）

#### A. 完整的函数兼容性检查
- 建立函数白名单机制
- 添加函数参数类型检查
- 实现函数重载限制检查

#### B. 高级表函数支持
- 实现更多炎凰SQL特有的表函数
- 添加表函数参数验证
- 支持表函数的默认参数

---

## 📝 测试建议

### 1. 标量函数测试
```python
def test_scalar_functions(self):
    """测试标量函数支持"""
    
    # 基础字符串函数
    self.validate_identity("SELECT UPPER(name), LOWER(name) FROM main")
    self.validate_identity("SELECT SUBSTR(name, 1, 5), LENGTH(name) FROM main")
    
    # 数学函数
    self.validate_identity("SELECT ABS(value), ROUND(value, 2) FROM main")
    self.validate_identity("SELECT SIN(angle), COS(angle) FROM main")
    
    # 炎凰SQL特有函数
    self.validate_identity("SELECT CONTAINS('keyword') FROM main")
    self.validate_identity("SELECT TIME_BUCKET('1h', timestamp) FROM main")
    
    # 不支持的函数应报错
    with self.assertRaises(Exception):
        self.parse_one("SELECT ARRAY_AGG(value) FROM main", dialect="yanhuang")
```

### 2. 表函数测试
```python
def test_table_functions(self):
    """测试表函数支持"""
    
    # PostgreSQL兼容的表函数
    self.validate_identity("SELECT * FROM GENERATE_SERIES(1, 10)")
    
    # 炎凰SQL特有表函数
    self.validate_identity("SELECT * FROM PARSE_JSON(data)")
    self.validate_identity("SELECT * FROM IP_LOCATION(ip_address)")
    
    # 不支持的表函数应报错
    with self.assertRaises(Exception):
        self.parse_one("SELECT * FROM CROSSTAB(...)", dialect="yanhuang")
```

---

## 📊 总结

### 当前状态
- ✅ **基础支持完备**: 核心的字符串、数学、类型转换函数已支持
- ✅ **炎凰SQL特色**: CONTAINS等特有函数已实现
- ⚠️ **部分缺失**: 一些常用函数需要补充
- ❌ **限制检查不足**: 对不支持的函数缺乏明确的错误提示

### 优先级建议
1. **高优先级**: 补充常用标量函数（字符串、数学、条件函数）
2. **中优先级**: 添加表函数支持和限制检查
3. **低优先级**: 完善高级功能和边界情况处理

### 预期效果
完成上述实现后，炎凰SQL方言将：
- 支持90%以上的常用标量函数
- 支持主要的表函数功能
- 提供清晰的错误提示
- 保持与PostgreSQL的最大兼容性 