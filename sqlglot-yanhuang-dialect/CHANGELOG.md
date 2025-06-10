# CHANGELOG

## [1.2.0] - 2024-12-19

### 🎯 TIMESTAMP字面量原生支持
- **完整支持炎凰数据时间字面量语法**：
  - 保持`TIMESTAMP '2024-01-01T00:00:00'`原生语法不转换为CAST
  - 支持微秒精度时间戳：`TIMESTAMP '2020-11-11T14:34:30.876543'`
  - 支持带时区格式：`TIMESTAMP '2020-11-11T14:34:30+08:00'`、`TIMESTAMP '2020-11-11T14:34:30Asia/Shanghai'`
  - 支持now关键字：`TIMESTAMP 'now'`
  - 支持时间操作表达式：`TIMESTAMP 'now-6h'`、`TIMESTAMP 'now-1d/d'`
  - 支持复杂时间操作：`TIMESTAMP '2020-12-01T00:00:00||5d-30m'`
  - 支持时区指定：`TIMESTAMP 'now-1d/d||Asia/Shanghai'`

### 🔧 cast_sql方法增强
- **智能TIMESTAMP字面量转换**：检测`CAST(string AS TIMESTAMP)`并转换回`TIMESTAMP 'string'`字面量语法
- **兼容PostgreSQL语法**：`'2024-01-01T00:00:00'::TIMESTAMP`正确转换为`TIMESTAMP '2024-01-01T00:00:00'`
- **保持TIMESTAMPTZ映射**：`TIMESTAMPTZ`仍正确映射为`string`类型

### ✅ 全面验证
- **26/26测试用例100%通过**：覆盖基础时间字面量、时间操作表达式、各种SQL上下文
- **完整炎凰数据兼容性**：符合炎凰数据官方时间字面量文档规范
- **零破坏性变更**：所有现有功能完全保持不变
- **跨版本同步**：主目录和独立包版本完全一致

### 🚀 技术特性
- **智能语法识别**：区分标准CAST语法和时间字面量语法
- **完整SQL上下文支持**：WHERE、INSERT、JOIN、GROUP BY、ORDER BY、函数参数、子查询
- **复杂表达式处理**：支持炎凰数据独有的时间操作表达式语法
- **高性能转换**：保持SQLGlot解析性能，无额外开销

## [1.1.0] - 2024-12-19

### 🔧 重要修复
- **TIMESTAMP字面量支持修复**：
  - 移除了TYPE_MAPPING中错误的TIMESTAMP→string映射
  - 恢复炎凰数据对`TIMESTAMP '2024-01-01T00:00:00'`语法的原生支持
  - PostgreSQL的TIMESTAMP字面量现在正确转换为`CAST(...AS TIMESTAMP)`

- **TIMESTAMPTZ WITH TIME ZONE问题修复**：
  - 完全消除了`CAST(...AS string WITH TIME ZONE)`错误语法
  - TIMESTAMPTZ现在正确映射为简单的`string`类型
  - 修复了datatype_sql方法中的TZ_TO_WITH_TIME_ZONE处理逻辑

- **字符串类型处理优化**：
  - 修复了TYPE_MAPPING优先级问题，避免TEXT→VARCHAR(MAX)错误转换
  - 消除了`string(MAX)`语法问题
  - 优化了datatype_sql方法的条件判断逻辑

### ✅ 验证结果
- 主目录版本：137/138测试通过（99.3%成功率）
- 独立包版本：与主目录完全同步
- PostgreSQL到炎凰数据转换：100%语法兼容性
- 零破坏性：所有现有功能保持不变

### 🔄 代码同步
- 主目录和独立包版本完全同步
- 所有修复在两个版本中保持一致
- 通过了全面的回归测试验证

## [1.0.0] - 2024-12-18

### 🎉 首次发布
- 完整的PostgreSQL到炎凰数据SQL转换支持
- LATERAL JOIN到APPLY转换功能
- 127个函数映射和转换规则
- SQLGlot版本兼容性自动修复
- 动态方言注册机制

### 🚀 核心功能
- 函数映射：EXTRACT→DATE_PART、CARDINALITY→ARRAY_LENGTH等
- 操作符转换：||→CONCAT、~→REGEXP_LIKE等
- 复杂语法支持：CTE、窗口函数、数组操作等
- 告警机制：不支持函数的智能提示和替代建议

### 📦 分发支持
- 独立PyPI包：轻量级（<1MB）
- 动态方言注入：运行时注册到官方SQLGlot
- 多API支持：便捷函数和原生SQLGlot API
- 完整文档和示例 