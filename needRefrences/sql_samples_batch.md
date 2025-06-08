# 炎凰数据SQL样例集 - 第一批(1-25)

## 财务BI场景 (1-12)

### 1. 每日销售额时间分桶分析
**Description**: 帮我统计最近一个月每天的销售金额和订单数量
```sql
-- 目的: 分析每日销售趋势 | 复杂度: 简单 | 炎凰特性: 时间分桶 | 类型: SELECT查询
SELECT TIME_BUCKET('1d', _time) day_bucket, 
       SUM(amount) daily_sales,
       COUNT(*) order_count
FROM orders 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
GROUP BY day_bucket 
ORDER BY day_bucket DESC 
LIMIT 30;
```

### 2. 地区销售同比增长分析
**Description**: 我想看各个地区的销售情况与去年同期相比的增长率
```sql
-- 目的: 计算各地区同比增长率 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
WITH monthly_sales AS (
  SELECT TIME_BUCKET('1M', _time) month_bucket, region,
         SUM(amount) monthly_total
  FROM orders 
  WHERE _time >= DATE_ADD('M', -24, NOW()) AND _time < NOW()
  GROUP BY month_bucket, region
),
with_yoy AS (
  SELECT *, 
         LAG(monthly_total, 12) OVER (PARTITION BY region ORDER BY month_bucket) last_year_same_month
  FROM monthly_sales
)
SELECT month_bucket, region, monthly_total,
       (monthly_total - last_year_same_month) * 100.0 / NULLIF(last_year_same_month, 0) yoy_growth_rate
FROM with_yoy 
WHERE last_year_same_month IS NOT NULL
ORDER BY yoy_growth_rate DESC 
LIMIT 50;
```

### 3. 产品销量Top分析
**Description**: 查询最近一周最热销的产品排行榜
```sql
-- 目的: 分析热销产品排行 | 复杂度: 简单 | 炎凰特性: 聚合增强 | 类型: SELECT查询
SELECT product_id, product_name,
       COUNT(*) order_count,
       SUM(quantity) total_quantity,
       LATEST_VALUE(price) latest_price
FROM orders 
WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
GROUP BY product_id, product_name
ORDER BY total_quantity DESC 
LIMIT 20;
```

### 4. 客户价值分层分析
**Description**: 帮我按客户价值对用户进行分层分析
```sql
-- 目的: 客户价值分层统计 | 复杂度: 高级 | 炎凰特性: 窗口函数/聚合 | 类型: SELECT查询
WITH customer_metrics AS (
  SELECT customer_id,
         COUNT(*) order_count,
         SUM(amount) total_spent,
         MAX(_time) last_order_time,
         EARLIEST_VALUE(_time) first_order_time
  FROM orders 
  WHERE _time >= DATE_ADD('d', -90, NOW()) AND _time < NOW()
  GROUP BY customer_id
),
customer_tiers AS (
  SELECT *,
         NTILE(5) OVER (ORDER BY total_spent DESC) value_tier,
         DATE_DIFF('d', last_order_time, NOW()) days_since_last_order
  FROM customer_metrics
)
SELECT value_tier,
       COUNT(*) customer_count,
       AVG(total_spent) avg_spent,
       AVG(days_since_last_order) avg_days_inactive
FROM customer_tiers 
GROUP BY value_tier 
ORDER BY value_tier;
```

### 5. 小时级销售热力图
**Description**: 我想看每天24小时内各个时段的销售热力图
```sql
-- 目的: 分析销售时段热力分布 | 复杂度: 简单 | 炎凰特性: 时间分桶/时间部分提取 | 类型: SELECT查询
SELECT DATE_PART('hour', _time) hour_of_day,
       DATE_PART('dow', _time) day_of_week,
       COUNT(*) order_count,
       SUM(amount) hourly_sales
FROM orders 
WHERE _time >= DATE_ADD('d', -14, NOW()) AND _time < NOW()
GROUP BY hour_of_day, day_of_week
ORDER BY day_of_week, hour_of_day;
```

### 6. 异常订单检测
**Description**: 检测订单中的异常数据，找出可能有问题的交易
```sql
-- 目的: 检测异常高额订单 | 复杂度: 高级 | 炎凰特性: 窗口函数/统计分析 | 类型: SELECT查询
WITH order_stats AS (
  SELECT *,
         AVG(amount) OVER () avg_amount,
         STDDEV_POP(amount) OVER () stddev_amount
  FROM orders 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
)
SELECT order_id, customer_id, amount, _time,
       (amount - avg_amount) / NULLIF(stddev_amount, 0) z_score,
       CASE 
         WHEN amount > avg_amount + 3 * stddev_amount THEN 'HIGH_ANOMALY'
         WHEN amount > avg_amount + 2 * stddev_amount THEN 'MEDIUM_ANOMALY'
         ELSE 'NORMAL'
       END anomaly_level
FROM order_stats 
WHERE amount > avg_amount + 2 * stddev_amount
ORDER BY z_score DESC 
LIMIT 100;
```

### 7. 月度收入趋势预测
**Description**: 分析最近一年的月度收入趋势，并预测下个月的情况
```sql
-- 目的: 基于历史趋势预测下月收入 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
WITH monthly_revenue AS (
  SELECT TIME_BUCKET('1M', _time) month_bucket,
         SUM(amount) monthly_revenue
  FROM orders 
  WHERE _time >= DATE_ADD('M', -12, NOW()) AND _time < NOW()
  GROUP BY month_bucket
),
with_trend AS (
  SELECT *,
         LAG(monthly_revenue, 1) OVER (ORDER BY month_bucket) prev_month,
         LAG(monthly_revenue, 2) OVER (ORDER BY month_bucket) prev_2_month,
         LAG(monthly_revenue, 3) OVER (ORDER BY month_bucket) prev_3_month
  FROM monthly_revenue
)
SELECT month_bucket, monthly_revenue,
       (monthly_revenue - prev_month) mom_change,
       (prev_month + prev_2_month + prev_3_month) / 3.0 three_month_avg,
       monthly_revenue + (monthly_revenue - prev_month) predicted_next_month
FROM with_trend 
WHERE prev_3_month IS NOT NULL
ORDER BY month_bucket DESC;
```

### 8. 支付方式分析
**Description**: 统计不同支付方式的使用情况和偏好
```sql
-- 目的: 分析不同支付方式使用情况 | 复杂度: 简单 | 炎凰特性: 聚合增强 | 类型: SELECT查询
SELECT payment_method,
       COUNT(*) transaction_count,
       SUM(amount) total_amount,
       AVG(amount) avg_amount,
       FIRST_VALUE(amount) OVER (PARTITION BY payment_method ORDER BY _time) first_amount,
       LATEST_VALUE(amount) OVER (PARTITION BY payment_method ORDER BY _time) latest_amount
FROM orders 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
GROUP BY payment_method
ORDER BY total_amount DESC;
```

### 9. 退款率分析
**Description**: 分析产品退款率，找出退款率较高的产品
```sql
-- 目的: 分析产品退款率趋势 | 复杂度: 高级 | 炎凰特性: 时间分桶/条件聚合 | 类型: SELECT查询
WITH daily_orders AS (
  SELECT TIME_BUCKET('1d', _time) day_bucket, product_id,
         COUNT(*) total_orders,
         COUNT(CASE WHEN status = 'refunded' THEN 1 END) refunded_orders
  FROM orders 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
  GROUP BY day_bucket, product_id
)
SELECT day_bucket, product_id,
       total_orders,
       refunded_orders,
       refunded_orders * 100.0 / NULLIF(total_orders, 0) refund_rate,
       LAG(refunded_orders * 100.0 / NULLIF(total_orders, 0)) OVER (PARTITION BY product_id ORDER BY day_bucket) prev_refund_rate
FROM daily_orders 
WHERE total_orders >= 10
ORDER BY refund_rate DESC, day_bucket DESC 
LIMIT 100;
```

### 10. 季节性销售分析
**Description**: 查看销售数据的季节性规律和周期性变化
```sql
-- 目的: 分析季节性销售模式 | 复杂度: 简单 | 炎凰特性: 时间部分提取 | 类型: SELECT查询
SELECT DATE_PART('quarter', _time) quarter,
       DATE_PART('month', _time) month,
       category,
       COUNT(*) order_count,
       SUM(amount) quarterly_sales,
       AVG(amount) avg_order_value
FROM orders 
WHERE _time >= DATE_ADD('y', -2, NOW()) AND _time < NOW()
GROUP BY quarter, month, category
ORDER BY quarter, month, quarterly_sales DESC;
```

### 11. 新老客户对比分析
**Description**: 对比新客户和老客户的购买行为差异
```sql
-- 目的: 对比新老客户购买行为 | 复杂度: 高级 | 炎凰特性: 聚合增强/窗口函数 | 类型: SELECT查询
WITH customer_first_order AS (
  SELECT customer_id, 
         EARLIEST_VALUE(_time) first_order_time
  FROM orders 
  GROUP BY customer_id
),
customer_segments AS (
  SELECT o.*, 
         CASE 
           WHEN DATE_DIFF('d', cf.first_order_time, NOW()) <= 30 THEN 'NEW'
           WHEN DATE_DIFF('d', cf.first_order_time, NOW()) <= 180 THEN 'RETURNING'
           ELSE 'LOYAL'
         END customer_type
  FROM orders o
  JOIN customer_first_order cf ON o.customer_id = cf.customer_id
  WHERE o._time >= DATE_ADD('d', -30, NOW()) AND o._time < NOW()
)
SELECT customer_type,
       COUNT(DISTINCT customer_id) unique_customers,
       COUNT(*) total_orders,
       SUM(amount) total_revenue,
       AVG(amount) avg_order_value,
       APPROX_COUNT_DISTINCT(product_id) unique_products
FROM customer_segments 
GROUP BY customer_type
ORDER BY total_revenue DESC;
```

### 12. 库存周转率分析
**Description**: 计算各产品的库存周转率和库存健康状况
```sql
-- 目的: 分析产品库存周转情况 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
WITH weekly_sales AS (
  SELECT TIME_BUCKET('1w', _time) week_bucket, product_id,
         SUM(quantity) weekly_sold,
         COUNT(*) weekly_orders
  FROM orders 
  WHERE _time >= DATE_ADD('w', -12, NOW()) AND _time < NOW()
  GROUP BY week_bucket, product_id
),
inventory_metrics AS (
  SELECT product_id,
         AVG(weekly_sold) avg_weekly_sales,
         STDDEV_POP(weekly_sold) sales_volatility,
         COUNT(*) weeks_with_sales
  FROM weekly_sales 
  GROUP BY product_id
)
SELECT product_id,
       avg_weekly_sales,
       sales_volatility,
       weeks_with_sales,
       CASE 
         WHEN avg_weekly_sales > 50 THEN 'FAST_MOVING'
         WHEN avg_weekly_sales > 10 THEN 'MEDIUM_MOVING'
         ELSE 'SLOW_MOVING'
       END inventory_category
FROM inventory_metrics 
WHERE weeks_with_sales >= 4
ORDER BY avg_weekly_sales DESC 
LIMIT 50;
```

## 安全运营场景 (13-25)

### 13. IP地理位置威胁分析
**Description**: 分析来自不同国家IP地址的安全威胁情况
```sql
-- 目的: 分析来源IP的地理分布和威胁等级 | 复杂度: 高级 | 炎凰特性: IP分析/表函数 | 类型: SELECT查询
SELECT s.source_ip, loc.country, loc.city, loc.isp,
       COUNT(*) event_count,
       COUNT(DISTINCT s.event_type) unique_event_types,
       LATEST_VALUE(s.event_type) latest_event
FROM security_events s
OUTER APPLY ip_location(s.source_ip) AS loc
WHERE s._time >= DATE_ADD('h', -24, NOW()) AND s._time < NOW()
  AND s.event_category = 'attack'
GROUP BY s.source_ip, loc.country, loc.city, loc.isp
HAVING event_count > 10
ORDER BY event_count DESC 
LIMIT 100;
```

### 14. 恶意载荷哈希分析
**Description**: 检测恶意文件的哈希值是否在我们的威胁数据库中
```sql
-- 目的: 分析恶意载荷的哈希特征 | 复杂度: 简单 | 炎凰特性: 哈希加密/字符串增强 | 类型: SELECT查询
SELECT HASH_MD5(payload) payload_hash,
       HASH_SHA256(payload) payload_sha256,
       COUNT(*) occurrence_count,
       EARLIEST_VALUE(_time) first_seen,
       LATEST_VALUE(_time) last_seen,
       APPROX_COUNT_DISTINCT(source_ip) unique_sources
FROM security_events 
WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  AND (CONTAINS('malware') OR CONTAINS('virus') OR CONTAINS('trojan'))
GROUP BY payload_hash, payload_sha256
ORDER BY occurrence_count DESC 
LIMIT 50;
```

### 15. CIDR网段攻击统计
**Description**: 统计特定网段发起的攻击次数
```sql
-- 目的: 统计不同网段的攻击频率 | 复杂度: 高级 | 炎凰特性: IP分析/时间分桶 | 类型: SELECT查询
WITH network_attacks AS (
  SELECT TIME_BUCKET('1h', _time) hour_bucket,
         source_ip,
         CASE 
           WHEN CIDR_MATCH(source_ip, '10.0.0.0/8') THEN 'INTERNAL_10'
           WHEN CIDR_MATCH(source_ip, '192.168.0.0/16') THEN 'INTERNAL_192'
           WHEN CIDR_MATCH(source_ip, '172.16.0.0/12') THEN 'INTERNAL_172'
           ELSE 'EXTERNAL'
         END network_segment,
         COUNT(*) hourly_attacks
  FROM security_events 
  WHERE _time >= DATE_ADD('d', -1, NOW()) AND _time < NOW()
    AND event_type = 'attack'
  GROUP BY hour_bucket, source_ip, network_segment
)
SELECT network_segment,
       COUNT(DISTINCT source_ip) unique_attackers,
       SUM(hourly_attacks) total_attacks,
       AVG(hourly_attacks) avg_attacks_per_hour,
       MAX(hourly_attacks) max_attacks_per_hour
FROM network_attacks 
GROUP BY network_segment
ORDER BY total_attacks DESC;
```

### 16. 用户异常登录行为检测
**Description**: 发现用户异常登录行为，如异地登录或频繁失败
```sql
-- 目的: 检测用户异常登录模式 | 复杂度: 高级 | 炎凰特性: 窗口函数/时间分析 | 类型: SELECT查询
WITH user_login_patterns AS (
  SELECT user_id, _time, source_ip,
         COUNT(*) OVER (PARTITION BY user_id, DATE(_time)) daily_logins,
         LAG(source_ip) OVER (PARTITION BY user_id ORDER BY _time) prev_ip,
         DATE_DIFF('m', LAG(_time) OVER (PARTITION BY user_id ORDER BY _time), _time) minutes_since_last
  FROM security_events 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
    AND event_type = 'login'
),
anomaly_detection AS (
  SELECT *,
         CASE 
           WHEN daily_logins > 50 THEN 'HIGH_FREQUENCY'
           WHEN source_ip != prev_ip AND minutes_since_last < 5 THEN 'IP_HOPPING'
           WHEN minutes_since_last < 1 THEN 'RAPID_LOGIN'
           ELSE 'NORMAL'
         END anomaly_type
  FROM user_login_patterns
)
SELECT user_id, anomaly_type,
       COUNT(*) anomaly_count,
       COUNT(DISTINCT source_ip) unique_ips,
       EARLIEST_VALUE(_time) first_anomaly,
       LATEST_VALUE(_time) last_anomaly
FROM anomaly_detection 
WHERE anomaly_type != 'NORMAL'
GROUP BY user_id, anomaly_type
ORDER BY anomaly_count DESC 
LIMIT 100;
```

### 17. URL攻击模式分析
**Description**: 检测Web请求中的攻击模式和可疑URL
```sql
-- 目的: 分析URL中的攻击模式 | 复杂度: 高级 | 炎凰特性: URL解析/正则匹配 | 类型: SELECT查询
SELECT DOMAIN(request_url) domain,
       PATH(request_url) path,
       PROTOCOL(request_url) protocol,
       COUNT(*) attack_count,
       COUNT(DISTINCT source_ip) unique_attackers,
       ARRAY_LENGTH(SPLIT_PART(PATH(request_url), '/', 0)) path_depth
FROM security_events 
WHERE _time >= DATE_ADD('h', -12, NOW()) AND _time < NOW()
  AND (REGEX_LIKE(request_url, '.*(sql|xss|script|union|select).*', 'i') 
       OR CONTAINS('injection'))
GROUP BY domain, path, protocol
ORDER BY attack_count DESC 
LIMIT 50;
```

### 18. 威胁情报IOC匹配
**Description**: 将安全事件与威胁情报数据库进行匹配分析
```sql
-- 目的: 匹配威胁情报IOC指标 | 复杂度: 高级 | 炎凰特性: 哈希加密/IP分析 | 类型: SELECT查询
WITH threat_indicators AS (
  SELECT source_ip, request_url, user_agent, payload,
         HASH_MD5(payload) payload_md5,
         CRC32(user_agent) ua_crc32
  FROM security_events 
  WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
),
ioc_matches AS (
  SELECT *,
         CASE 
           WHEN IS_IPV4_LOOPBACK(source_ip) THEN 'LOOPBACK_IP'
           WHEN REGEX_LIKE(user_agent, '.*(bot|crawler|scanner).*', 'i') THEN 'SUSPICIOUS_UA'
           WHEN CONTAINS('base64') AND CONTAINS('eval') THEN 'ENCODED_PAYLOAD'
           WHEN REGEX_LIKE(request_url, '.*\\.(php|asp|jsp)\\?.*=.*', 'i') THEN 'INJECTION_ATTEMPT'
           ELSE 'CLEAN'
         END ioc_type
  FROM threat_indicators
)
SELECT ioc_type,
       COUNT(*) match_count,
       COUNT(DISTINCT source_ip) unique_sources,
       COUNT(DISTINCT payload_md5) unique_payloads
FROM ioc_matches 
WHERE ioc_type != 'CLEAN'
GROUP BY ioc_type
ORDER BY match_count DESC;
```

### 19. 端口扫描检测
**Description**: 识别针对我们系统的端口扫描行为
```sql
-- 目的: 检测端口扫描行为 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
WITH port_activities AS (
  SELECT TIME_BUCKET('5m', _time) time_bucket, source_ip, dest_port,
         COUNT(*) connection_attempts
  FROM security_events 
  WHERE _time >= DATE_ADD('h', -2, NOW()) AND _time < NOW()
    AND event_type = 'connection'
  GROUP BY time_bucket, source_ip, dest_port
),
scan_detection AS (
  SELECT time_bucket, source_ip,
         COUNT(DISTINCT dest_port) unique_ports,
         SUM(connection_attempts) total_attempts,
         COUNT(*) port_count
  FROM port_activities 
  GROUP BY time_bucket, source_ip
)
SELECT source_ip,
       MAX(unique_ports) max_ports_per_5min,
       SUM(total_attempts) total_connection_attempts,
       COUNT(DISTINCT time_bucket) active_time_buckets,
       CASE 
         WHEN MAX(unique_ports) > 100 THEN 'AGGRESSIVE_SCAN'
         WHEN MAX(unique_ports) > 20 THEN 'MODERATE_SCAN'
         WHEN MAX(unique_ports) > 5 THEN 'LIGHT_SCAN'
         ELSE 'NORMAL'
       END scan_intensity
FROM scan_detection 
WHERE unique_ports > 5
GROUP BY source_ip
ORDER BY max_ports_per_5min DESC 
LIMIT 50;
```

### 20. 文件哈希威胁检测
**Description**: 检测上传文件的哈希值是否为已知恶意文件
```sql
-- 目的: 基于文件哈希检测威胁 | 复杂度: 简单 | 炎凰特性: 哈希加密 | 类型: SELECT查询
SELECT file_path, 
       HASH_SHA1(file_content) file_sha1,
       HASH_SHA256(file_content) file_sha256,
       file_size,
       COUNT(*) detection_count,
       EARLIEST_VALUE(_time) first_detection,
       LATEST_VALUE(_time) last_detection
FROM security_events 
WHERE _time >= DATE_ADD('d', -3, NOW()) AND _time < NOW()
  AND event_type = 'file_scan'
  AND (CONTAINS('malware') OR CONTAINS('suspicious'))
GROUP BY file_path, file_sha1, file_sha256, file_size
ORDER BY detection_count DESC 
LIMIT 100;
```

### 21. 登录失败暴力破解检测
**Description**: 分析登录失败次数，检测暴力破解攻击
```sql
-- 目的: 检测暴力破解登录攻击 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
WITH failed_logins AS (
  SELECT TIME_BUCKET('1m', _time) minute_bucket,
         source_ip, username,
         COUNT(*) failed_attempts
  FROM security_events 
  WHERE _time >= DATE_ADD('h', -4, NOW()) AND _time < NOW()
    AND event_type = 'login_failed'
  GROUP BY minute_bucket, source_ip, username
),
brute_force_detection AS (
  SELECT source_ip, username,
         COUNT(*) active_minutes,
         SUM(failed_attempts) total_failures,
         MAX(failed_attempts) max_failures_per_minute,
         COUNT(DISTINCT username) target_accounts
  FROM failed_logins 
  WHERE failed_attempts >= 3
  GROUP BY source_ip, username
)
SELECT source_ip,
       COUNT(DISTINCT username) targeted_accounts,
       SUM(total_failures) total_failed_attempts,
       AVG(max_failures_per_minute) avg_max_per_minute,
       CASE 
         WHEN COUNT(DISTINCT username) > 10 THEN 'CREDENTIAL_STUFFING'
         WHEN MAX(total_failures) > 100 THEN 'INTENSIVE_BRUTE_FORCE'
         WHEN MAX(total_failures) > 20 THEN 'MODERATE_BRUTE_FORCE'
         ELSE 'LOW_INTENSITY'
       END attack_classification
FROM brute_force_detection 
GROUP BY source_ip
HAVING total_failed_attempts > 15
ORDER BY total_failed_attempts DESC 
LIMIT 50;
```

### 22. DNS异常查询分析
**Description**: 发现异常的DNS查询请求和可疑域名访问
```sql
-- 目的: 分析DNS异常查询模式 | 复杂度: 高级 | 炎凰特性: 字符串增强/时间分析 | 类型: SELECT查询
WITH dns_queries AS (
  SELECT source_ip, query_domain, query_type,
         CHAR_LENGTH(query_domain) domain_length,
         CASE 
           WHEN REGEX_LIKE(query_domain, '^[a-z0-9]{20,}\\.[a-z]{2,}$', 'i') THEN 'DGA_SUSPECTED'
           WHEN CONTAINS('.tk') OR CONTAINS('.ml') OR CONTAINS('.cf') THEN 'SUSPICIOUS_TLD'
           WHEN CHAR_LENGTH(query_domain) > 50 THEN 'LONG_DOMAIN'
           ELSE 'NORMAL'
         END domain_category,
         COUNT(*) query_count
  FROM security_events 
  WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
    AND event_type = 'dns_query'
  GROUP BY source_ip, query_domain, query_type, domain_length, domain_category
)
SELECT domain_category,
       COUNT(DISTINCT source_ip) unique_sources,
       COUNT(DISTINCT query_domain) unique_domains,
       SUM(query_count) total_queries,
       AVG(domain_length) avg_domain_length
FROM dns_queries 
WHERE domain_category != 'NORMAL'
GROUP BY domain_category
ORDER BY total_queries DESC;
```

### 23. Web Shell检测
**Description**: 检测Web Shell等后门文件的上传和访问
```sql
-- 目的: 检测Web Shell活动 | 复杂度: 高级 | 炎凰特性: URL解析/正则匹配 | 类型: SELECT查询
SELECT source_ip, 
       DOMAIN(request_url) target_domain,
       PATH(request_url) request_path,
       QUERY_STRING(request_url) query_params,
       user_agent,
       COUNT(*) shell_attempts,
       EARLIEST_VALUE(_time) first_attempt,
       LATEST_VALUE(_time) last_attempt
FROM security_events 
WHERE _time >= DATE_ADD('h', -8, NOW()) AND _time < NOW()
  AND (REGEX_LIKE(request_path, '.*(cmd|shell|eval|exec|system).*', 'i')
       OR REGEX_LIKE(query_params, '.*(base64|eval|exec).*', 'i')
       OR CONTAINS('<?php'))
GROUP BY source_ip, target_domain, request_path, query_params, user_agent
HAVING shell_attempts > 2
ORDER BY shell_attempts DESC 
LIMIT 100;
```

### 24. 内网横向移动检测
**Description**: 分析内网中的横向移动攻击行为
```sql
-- 目的: 检测内网横向移动行为 | 复杂度: 高级 | 炎凰特性: IP分析/时间分桶 | 类型: SELECT查询
WITH internal_connections AS (
  SELECT TIME_BUCKET('10m', _time) time_bucket,
         source_ip, dest_ip, service_port,
         COUNT(*) connection_count
  FROM security_events 
  WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
    AND CIDR_MATCH(source_ip, '10.0.0.0/8')
    AND CIDR_MATCH(dest_ip, '10.0.0.0/8')
    AND event_type = 'internal_connection'
  GROUP BY time_bucket, source_ip, dest_ip, service_port
),
lateral_movement AS (
  SELECT source_ip,
         COUNT(DISTINCT dest_ip) unique_targets,
         COUNT(DISTINCT service_port) unique_services,
         COUNT(DISTINCT time_bucket) active_periods,
         SUM(connection_count) total_connections
  FROM internal_connections 
  GROUP BY source_ip
)
SELECT source_ip,
       unique_targets,
       unique_services,
       active_periods,
       total_connections,
       CASE 
         WHEN unique_targets > 20 AND unique_services > 5 THEN 'HIGH_RISK_LATERAL'
         WHEN unique_targets > 10 THEN 'MODERATE_LATERAL'
         WHEN unique_targets > 5 THEN 'LOW_LATERAL'
         ELSE 'NORMAL'
       END movement_risk
FROM lateral_movement 
WHERE unique_targets > 3
ORDER BY unique_targets DESC, unique_services DESC 
LIMIT 50;
```

### 25. 数据渗透检测
**Description**: 监控数据外泄和敏感信息的异常访问
```sql
-- 目的: 检测数据渗透和泄露行为 | 复杂度: 高级 | 炎凰特性: 数据质量/窗口函数 | 类型: SELECT查询
WITH data_access AS (
  SELECT user_id, source_ip, data_type, access_size,
         _time,
         SUM(access_size) OVER (PARTITION BY user_id ORDER BY _time ROWS BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW) hourly_volume,
         COUNT(*) OVER (PARTITION BY user_id ORDER BY _time ROWS BETWEEN INTERVAL '1 hour' PRECEDING AND CURRENT ROW) hourly_accesses
  FROM security_events 
  WHERE _time >= DATE_ADD('h', -12, NOW()) AND _time < NOW()
    AND event_type = 'data_access'
    AND access_size > 0
),
exfiltration_detection AS (
  SELECT user_id, source_ip,
         MAX(hourly_volume) peak_hourly_volume,
         MAX(hourly_accesses) peak_hourly_accesses,
         COUNT(DISTINCT data_type) data_types_accessed,
         SUM(access_size) total_data_accessed
  FROM data_access 
  GROUP BY user_id, source_ip
)
SELECT user_id, source_ip,
       peak_hourly_volume / 1024 / 1024 peak_mb_per_hour,
       peak_hourly_accesses,
       data_types_accessed,
       total_data_accessed / 1024 / 1024 total_mb_accessed,
       CASE 
         WHEN peak_hourly_volume > 1073741824 THEN 'BULK_EXFILTRATION'  -- > 1GB/hour
         WHEN peak_hourly_accesses > 1000 THEN 'HIGH_FREQUENCY_ACCESS'
         WHEN data_types_accessed > 10 THEN 'BROAD_DATA_ACCESS'
         ELSE 'NORMAL'
       END exfiltration_risk
FROM exfiltration_detection 
WHERE peak_hourly_volume > 104857600  -- > 100MB/hour
ORDER BY peak_hourly_volume DESC 
LIMIT 100;
``` 

# 炎凰数据SQL样例集 - 第二批(26-50)

## 运维分析场景 (26-50)

### 26. 服务响应时间监控
**Description**: 监控各个服务的响应时间分布情况
```sql
-- 目的: 监控服务响应时间分布 | 复杂度: 高级 | 炎凰特性: 时间分桶/统计分析 | 类型: SELECT查询
SELECT TIME_BUCKET('5m', _time) time_bucket, 
       service_name,
       COUNT(*) request_count,
       AVG(response_time) avg_response,
       PERCENTILE(response_time, 0.95) p95_response,
       PERCENTILE(response_time, 0.99) p99_response
FROM app_logs 
WHERE _time >= DATE_ADD('h', -4, NOW()) AND _time < NOW()
  AND response_time > 0
GROUP BY time_bucket, service_name
ORDER BY time_bucket DESC, p99_response DESC;
```

### 27. 错误率趋势分析
**Description**: 分析应用错误率的变化趋势
```sql
-- 目的: 分析应用错误率变化趋势 | 复杂度: 高级 | 炎凰特性: 时间分桶/条件聚合 | 类型: SELECT查询
WITH error_metrics AS (
  SELECT TIME_BUCKET('10m', _time) time_bucket,
         service_name,
         COUNT(*) total_requests,
         COUNT(CASE WHEN status_code >= 400 THEN 1 END) error_requests,
         COUNT(CASE WHEN status_code >= 500 THEN 1 END) server_errors
  FROM app_logs 
  WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
  GROUP BY time_bucket, service_name
)
SELECT time_bucket, service_name,
       total_requests,
       error_requests * 100.0 / NULLIF(total_requests, 0) error_rate,
       server_errors * 100.0 / NULLIF(total_requests, 0) server_error_rate,
       LAG(error_requests * 100.0 / NULLIF(total_requests, 0)) OVER (PARTITION BY service_name ORDER BY time_bucket) prev_error_rate
FROM error_metrics 
WHERE total_requests > 10
ORDER BY error_rate DESC 
LIMIT 100;
```

### 28. 系统资源使用率监控
**Description**: 查看系统CPU和内存的使用率监控
```sql
-- 目的: 监控系统CPU、内存使用率 | 复杂度: 简单 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
SELECT TIME_BUCKET('1m', _time) time_bucket,
       hostname,
       AVG(cpu_usage) avg_cpu,
       MAX(cpu_usage) peak_cpu,
       AVG(memory_usage) avg_memory,
       MAX(memory_usage) peak_memory,
       AVG(disk_usage) avg_disk
FROM system_metrics 
WHERE _time >= DATE_ADD('h', -2, NOW()) AND _time < NOW()
GROUP BY time_bucket, hostname
HAVING MAX(cpu_usage) > 80 OR MAX(memory_usage) > 85
ORDER BY time_bucket DESC, peak_cpu DESC;
```

### 29. 慢查询分析
**Description**: 找出数据库中执行缓慢的查询语句
```sql
-- 目的: 分析数据库慢查询模式 | 复杂度: 高级 | 炎凰特性: 哈希加密/字符串处理 | 类型: SELECT查询
SELECT HASH_MD5(UPPER(REGEXP_REPLACE(query_text, '[0-9]+', 'N', 'g'))) query_pattern,
       COUNT(*) execution_count,
       AVG(execution_time) avg_execution_time,
       MAX(execution_time) max_execution_time,
       AVG(rows_examined) avg_rows_examined,
       EARLIEST_VALUE(query_text) sample_query
FROM db_slow_log 
WHERE _time >= DATE_ADD('h', -8, NOW()) AND _time < NOW()
  AND execution_time > 1000  -- milliseconds
GROUP BY query_pattern
ORDER BY avg_execution_time DESC 
LIMIT 50;
```

### 30. 网络流量异常检测
**Description**: 检测网络流量中的异常峰值
```sql
-- 目的: 检测网络流量异常 | 复杂度: 高级 | 炎凰特性: 时间分桶/统计分析 | 类型: SELECT查询
WITH traffic_stats AS (
  SELECT TIME_BUCKET('1m', _time) time_bucket,
         interface_name,
         SUM(bytes_in) total_bytes_in,
         SUM(bytes_out) total_bytes_out,
         COUNT(*) packet_count
  FROM network_metrics 
  WHERE _time >= DATE_ADD('h', -3, NOW()) AND _time < NOW()
  GROUP BY time_bucket, interface_name
),
with_baselines AS (
  SELECT *,
         AVG(total_bytes_in) OVER (PARTITION BY interface_name ORDER BY time_bucket ROWS 10 PRECEDING) baseline_bytes_in,
         STDDEV_POP(total_bytes_in) OVER (PARTITION BY interface_name ORDER BY time_bucket ROWS 10 PRECEDING) stddev_bytes_in
  FROM traffic_stats
)
SELECT time_bucket, interface_name,
       total_bytes_in / 1024 / 1024 mb_in,
       total_bytes_out / 1024 / 1024 mb_out,
       (total_bytes_in - baseline_bytes_in) / NULLIF(stddev_bytes_in, 0) z_score,
       CASE 
         WHEN ABS(total_bytes_in - baseline_bytes_in) > 3 * stddev_bytes_in THEN 'ANOMALY'
         WHEN ABS(total_bytes_in - baseline_bytes_in) > 2 * stddev_bytes_in THEN 'WARNING'
         ELSE 'NORMAL'
       END traffic_status
FROM with_baselines 
WHERE baseline_bytes_in IS NOT NULL
ORDER BY ABS(z_score) DESC 
LIMIT 100;
```

### 31. 容器资源监控
**Description**: 监控容器的资源使用情况
```sql
-- 目的: 监控容器资源使用情况 | 复杂度: 简单 | 炎凰特性: 聚合增强 | 类型: SELECT查询
SELECT container_name, image_name,
       COUNT(*) metrics_count,
       AVG(cpu_percent) avg_cpu_percent,
       MAX(cpu_percent) peak_cpu_percent,
       AVG(memory_usage_mb) avg_memory_mb,
       MAX(memory_usage_mb) peak_memory_mb,
       LATEST_VALUE(status) current_status
FROM container_metrics 
WHERE _time >= DATE_ADD('m', -30, NOW()) AND _time < NOW()
GROUP BY container_name, image_name
ORDER BY peak_cpu_percent DESC, peak_memory_mb DESC 
LIMIT 50;
```

### 32. 磁盘空间预警
**Description**: 预警磁盘空间不足的服务器
```sql
-- 目的: 监控磁盘空间使用预警 | 复杂度: 高级 | 炎凰特性: 时间分桶/趋势预测 | 类型: SELECT查询
WITH disk_trends AS (
  SELECT TIME_BUCKET('1h', _time) hour_bucket,
         hostname, mount_point,
         AVG(used_percent) avg_used_percent,
         MAX(used_percent) peak_used_percent
  FROM disk_metrics 
  WHERE _time >= DATE_ADD('d', -3, NOW()) AND _time < NOW()
  GROUP BY hour_bucket, hostname, mount_point
),
growth_analysis AS (
  SELECT hostname, mount_point,
         avg_used_percent,
         LAG(avg_used_percent, 24) OVER (PARTITION BY hostname, mount_point ORDER BY hour_bucket) usage_24h_ago,
         LAG(avg_used_percent, 72) OVER (PARTITION BY hostname, mount_point ORDER BY hour_bucket) usage_72h_ago
  FROM disk_trends
  ORDER BY hour_bucket DESC
  LIMIT 1000
)
SELECT hostname, mount_point, avg_used_percent,
       (avg_used_percent - usage_24h_ago) daily_growth,
       (avg_used_percent - usage_72h_ago) / 3.0 avg_daily_growth,
       100 - avg_used_percent remaining_space,
       CASE 
         WHEN avg_used_percent > 90 THEN 'CRITICAL'
         WHEN avg_used_percent > 80 THEN 'WARNING' 
         WHEN (avg_used_percent - usage_24h_ago) > 5 THEN 'RAPID_GROWTH'
         ELSE 'NORMAL'
       END alert_level
FROM growth_analysis 
WHERE usage_72h_ago IS NOT NULL
  AND (avg_used_percent > 75 OR (avg_used_percent - usage_24h_ago) > 2)
ORDER BY avg_used_percent DESC;
```

### 33. API接口性能分析
**Description**: 分析API接口的性能表现
```sql
-- 目的: 分析API接口性能指标 | 复杂度: 高级 | 炎凰特性: URL解析/统计分析 | 类型: SELECT查询
SELECT PATH(api_endpoint) api_path,
       http_method,
       COUNT(*) request_count,
       AVG(response_time) avg_response_time,
       PERCENTILE(response_time, 0.95) p95_response_time,
       COUNT(CASE WHEN status_code >= 400 THEN 1 END) * 100.0 / COUNT(*) error_rate,
       APPROX_COUNT_DISTINCT(client_ip) unique_clients
FROM api_logs 
WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
GROUP BY api_path, http_method
HAVING request_count > 100
ORDER BY p95_response_time DESC 
LIMIT 50;
```

### 34. 数据库连接池监控
**Description**: 监控数据库连接池的使用状况
```sql
-- 目的: 监控数据库连接池状态 | 复杂度: 简单 | 炎凰特性: 时间分桶/聚合 | 类型: SELECT查询
SELECT TIME_BUCKET('5m', _time) time_bucket,
       db_instance,
       AVG(active_connections) avg_active_conn,
       MAX(active_connections) peak_active_conn,
       AVG(idle_connections) avg_idle_conn,
       AVG(waiting_connections) avg_waiting_conn,
       MAX(waiting_connections) peak_waiting_conn
FROM db_connection_metrics 
WHERE _time >= DATE_ADD('h', -4, NOW()) AND _time < NOW()
GROUP BY time_bucket, db_instance
HAVING MAX(waiting_connections) > 0
ORDER BY time_bucket DESC, peak_waiting_conn DESC;
```

### 35. 负载均衡器健康检查
**Description**: 检查负载均衡器的健康状态
```sql
-- 目的: 监控负载均衡器后端健康状态 | 复杂度: 高级 | 炎凰特性: 时间分桶/条件聚合 | 类型: SELECT查询
WITH backend_health AS (
  SELECT TIME_BUCKET('1m', _time) time_bucket,
         lb_name, backend_server,
         COUNT(*) total_checks,
         COUNT(CASE WHEN health_status = 'healthy' THEN 1 END) healthy_checks,
         AVG(response_time) avg_health_check_time
  FROM lb_health_metrics 
  WHERE _time >= DATE_ADD('h', -2, NOW()) AND _time < NOW()
  GROUP BY time_bucket, lb_name, backend_server
)
SELECT lb_name, backend_server,
       COUNT(*) check_intervals,
       AVG(healthy_checks * 100.0 / NULLIF(total_checks, 0)) avg_health_percentage,
       MIN(healthy_checks * 100.0 / NULLIF(total_checks, 0)) min_health_percentage,
       AVG(avg_health_check_time) avg_response_time
FROM backend_health 
GROUP BY lb_name, backend_server
HAVING AVG(healthy_checks * 100.0 / NULLIF(total_checks, 0)) < 95
ORDER BY avg_health_percentage ASC;
```

### 36. 消息队列积压监控
**Description**: 监控消息队列的积压情况
```sql
-- 目的: 监控消息队列积压情况 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
SELECT TIME_BUCKET('2m', _time) time_bucket,
       queue_name, topic,
       AVG(queue_depth) avg_depth,
       MAX(queue_depth) peak_depth,
       AVG(consumer_lag) avg_lag,
       MAX(consumer_lag) max_lag,
       LAG(AVG(queue_depth)) OVER (PARTITION BY queue_name ORDER BY time_bucket) prev_avg_depth
FROM mq_metrics 
WHERE _time >= DATE_ADD('h', -3, NOW()) AND _time < NOW()
GROUP BY time_bucket, queue_name, topic
HAVING MAX(queue_depth) > 1000 OR MAX(consumer_lag) > 300
ORDER BY time_bucket DESC, peak_depth DESC;
```

### 37. 缓存命中率分析
**Description**: 分析缓存的命中率和性能
```sql
-- 目的: 分析缓存系统命中率 | 复杂度: 简单 | 炎凰特性: 时间分桶/比率计算 | 类型: SELECT查询
SELECT TIME_BUCKET('10m', _time) time_bucket,
       cache_instance, cache_type,
       SUM(cache_hits) total_hits,
       SUM(cache_misses) total_misses,
       SUM(cache_hits) * 100.0 / NULLIF(SUM(cache_hits) + SUM(cache_misses), 0) hit_rate,
       AVG(avg_response_time) avg_response_time
FROM cache_metrics 
WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
GROUP BY time_bucket, cache_instance, cache_type
HAVING SUM(cache_hits) + SUM(cache_misses) > 100
ORDER BY hit_rate ASC 
LIMIT 100;
```

### 38. SSL证书过期监控
**Description**: 检查SSL证书的过期情况
```sql
-- 目的: 监控SSL证书过期情况 | 复杂度: 简单 | 炎凰特性: 时间差计算 | 类型: SELECT查询
SELECT domain_name, certificate_issuer,
       certificate_expiry_date,
       DATE_DIFF('d', NOW(), certificate_expiry_date) days_until_expiry,
       CASE 
         WHEN DATE_DIFF('d', NOW(), certificate_expiry_date) < 7 THEN 'CRITICAL'
         WHEN DATE_DIFF('d', NOW(), certificate_expiry_date) < 30 THEN 'WARNING'
         WHEN DATE_DIFF('d', NOW(), certificate_expiry_date) < 60 THEN 'ATTENTION'
         ELSE 'OK'
       END expiry_status,
       LATEST_VALUE(_time) last_checked
FROM ssl_cert_monitor 
WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
GROUP BY domain_name, certificate_issuer, certificate_expiry_date
HAVING DATE_DIFF('d', NOW(), certificate_expiry_date) < 90
ORDER BY days_until_expiry ASC;
```

### 39. 应用启动时间分析
**Description**: 分析应用启动时间的性能
```sql
-- 目的: 分析应用启动时间趋势 | 复杂度: 高级 | 炎凰特性: 时间差计算/统计分析 | 类型: SELECT查询
WITH startup_events AS (
  SELECT application_name, instance_id,
         EARLIEST_VALUE(_time) start_time,
         LATEST_VALUE(_time) ready_time,
         DATE_DIFF('s', EARLIEST_VALUE(_time), LATEST_VALUE(_time)) startup_duration_seconds
  FROM app_lifecycle_events 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
    AND event_type IN ('start', 'ready')
  GROUP BY application_name, instance_id, DATE(_time)
  HAVING COUNT(DISTINCT event_type) = 2
)
SELECT application_name,
       COUNT(*) startup_count,
       AVG(startup_duration_seconds) avg_startup_time,
       MIN(startup_duration_seconds) min_startup_time,
       MAX(startup_duration_seconds) max_startup_time,
       STDDEV_POP(startup_duration_seconds) startup_time_variance
FROM startup_events 
WHERE startup_duration_seconds > 0 AND startup_duration_seconds < 600
GROUP BY application_name
ORDER BY avg_startup_time DESC;
```

### 40. 服务依赖健康检查
**Description**: 检查服务依赖的健康状况
```sql
-- 目的: 监控服务间依赖健康状态 | 复杂度: 高级 | 炎凰特性: 时间分桶/聚合增强 | 类型: SELECT查询
SELECT TIME_BUCKET('5m', _time) time_bucket,
       service_name, dependency_service,
       COUNT(*) total_calls,
       COUNT(CASE WHEN call_success = true THEN 1 END) successful_calls,
       COUNT(CASE WHEN call_success = true THEN 1 END) * 100.0 / COUNT(*) success_rate,
       AVG(call_duration) avg_call_duration,
       PERCENTILE(call_duration, 0.95) p95_call_duration
FROM service_dependency_metrics 
WHERE _time >= DATE_ADD('h', -4, NOW()) AND _time < NOW()
GROUP BY time_bucket, service_name, dependency_service
HAVING COUNT(*) > 10
ORDER BY success_rate ASC, time_bucket DESC 
LIMIT 100;
```

### 41. 日志错误模式识别
**Description**: 从日志中识别错误模式
```sql
-- 目的: 识别应用日志中的错误模式 | 复杂度: 高级 | 炎凰特性: 字符串增强/正则匹配 | 类型: SELECT查询
WITH error_patterns AS (
  SELECT service_name, log_level,
         CASE 
           WHEN REGEX_LIKE(message, '.*OutOfMemoryError.*', 'i') THEN 'MEMORY_ERROR'
           WHEN REGEX_LIKE(message, '.*ConnectionException.*', 'i') THEN 'CONNECTION_ERROR'
           WHEN REGEX_LIKE(message, '.*TimeoutException.*', 'i') THEN 'TIMEOUT_ERROR'
           WHEN REGEX_LIKE(message, '.*NullPointerException.*', 'i') THEN 'NULL_POINTER'
           WHEN CONTAINS('SQL') AND CONTAINS('Exception') THEN 'SQL_ERROR'
           ELSE 'OTHER_ERROR'
         END error_pattern,
         COUNT(*) error_count,
         EARLIEST_VALUE(_time) first_occurrence,
         LATEST_VALUE(_time) last_occurrence
  FROM application_logs 
  WHERE _time >= DATE_ADD('h', -8, NOW()) AND _time < NOW()
    AND log_level = 'ERROR'
  GROUP BY service_name, log_level, error_pattern
)
SELECT error_pattern, service_name,
       error_count,
       first_occurrence,
       last_occurrence,
       DATE_DIFF('m', first_occurrence, last_occurrence) duration_minutes
FROM error_patterns 
WHERE error_count > 5
ORDER BY error_count DESC 
LIMIT 50;
```

### 42. 批处理任务监控
**Description**: 监控批处理任务的执行情况
```sql
-- 目的: 监控批处理任务执行情况 | 复杂度: 高级 | 炎凰特性: 时间差计算/窗口函数 | 类型: SELECT查询
WITH job_executions AS (
  SELECT job_name, job_id,
         MIN(_time) job_start_time,
         MAX(_time) job_end_time,
         DATE_DIFF('m', MIN(_time), MAX(_time)) execution_duration_minutes,
         LATEST_VALUE(job_status) final_status,
         SUM(CASE WHEN event_type = 'error' THEN 1 ELSE 0 END) error_count
  FROM batch_job_logs 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  GROUP BY job_name, job_id
),
job_stats AS (
  SELECT job_name,
         COUNT(*) total_executions,
         COUNT(CASE WHEN final_status = 'SUCCESS' THEN 1 END) successful_executions,
         AVG(execution_duration_minutes) avg_duration,
         MAX(execution_duration_minutes) max_duration,
         SUM(error_count) total_errors
  FROM job_executions 
  GROUP BY job_name
)
SELECT job_name,
       total_executions,
       successful_executions * 100.0 / total_executions success_rate,
       avg_duration,
       max_duration,
       total_errors,
       CASE 
         WHEN successful_executions * 100.0 / total_executions < 80 THEN 'UNRELIABLE'
         WHEN avg_duration > 120 THEN 'SLOW'
         WHEN total_errors > 10 THEN 'ERROR_PRONE'
         ELSE 'HEALTHY'
       END job_health_status
FROM job_stats 
ORDER BY success_rate ASC, total_errors DESC;
```

### 43. 网络延迟监控
**Description**: 测量网络延迟和连通性
```sql
-- 目的: 监控网络节点间延迟 | 复杂度: 简单 | 炎凰特性: 时间分桶/统计分析 | 类型: SELECT查询
SELECT TIME_BUCKET('2m', _time) time_bucket,
       source_node, destination_node,
       COUNT(*) ping_count,
       AVG(latency_ms) avg_latency,
       MIN(latency_ms) min_latency,
       MAX(latency_ms) max_latency,
       PERCENTILE(latency_ms, 0.95) p95_latency,
       COUNT(CASE WHEN packet_loss > 0 THEN 1 END) packet_loss_occurrences
FROM network_latency_metrics 
WHERE _time >= DATE_ADD('h', -3, NOW()) AND _time < NOW()
GROUP BY time_bucket, source_node, destination_node
HAVING AVG(latency_ms) > 10 OR COUNT(CASE WHEN packet_loss > 0 THEN 1 END) > 0
ORDER BY avg_latency DESC;
```

### 44. 存储IOPS监控
**Description**: 监控存储系统的IOPS性能
```sql
-- 目的: 监控存储系统IOPS性能 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
WITH storage_metrics AS (
  SELECT TIME_BUCKET('1m', _time) time_bucket,
         storage_device, storage_type,
         AVG(read_iops) avg_read_iops,
         AVG(write_iops) avg_write_iops,
         AVG(read_latency) avg_read_latency,
         AVG(write_latency) avg_write_latency,
         MAX(queue_depth) max_queue_depth
  FROM storage_performance_metrics 
  WHERE _time >= DATE_ADD('h', -4, NOW()) AND _time < NOW()
  GROUP BY time_bucket, storage_device, storage_type
),
performance_analysis AS (
  SELECT *,
         avg_read_iops + avg_write_iops total_iops,
         LAG(avg_read_iops + avg_write_iops) OVER (PARTITION BY storage_device ORDER BY time_bucket) prev_total_iops
  FROM storage_metrics
)
SELECT storage_device, storage_type,
       AVG(total_iops) avg_total_iops,
       MAX(total_iops) peak_total_iops,
       AVG(avg_read_latency) avg_read_latency,
       AVG(avg_write_latency) avg_write_latency,
       MAX(max_queue_depth) peak_queue_depth,
       CASE 
         WHEN AVG(avg_read_latency) > 20 OR AVG(avg_write_latency) > 20 THEN 'HIGH_LATENCY'
         WHEN MAX(max_queue_depth) > 32 THEN 'HIGH_QUEUE_DEPTH'
         WHEN MAX(total_iops) > 10000 THEN 'HIGH_IOPS'
         ELSE 'NORMAL'
       END performance_status
FROM performance_analysis 
GROUP BY storage_device, storage_type
ORDER BY avg_total_iops DESC;
```

### 45. 服务器温度监控
**Description**: 检查服务器硬件温度状况
```sql
-- 目的: 监控服务器硬件温度 | 复杂度: 简单 | 炎凰特性: 时间分桶/聚合 | 类型: SELECT查询
SELECT TIME_BUCKET('5m', _time) time_bucket,
       server_id, sensor_location,
       AVG(temperature_celsius) avg_temp,
       MAX(temperature_celsius) peak_temp,
       COUNT(CASE WHEN temperature_celsius > 75 THEN 1 END) high_temp_readings
FROM hardware_temperature_metrics 
WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
GROUP BY time_bucket, server_id, sensor_location
HAVING MAX(temperature_celsius) > 70
ORDER BY peak_temp DESC;
```

### 46. 应用内存泄漏检测
**Description**: 检测应用内存泄漏问题
```sql
-- 目的: 检测应用内存泄漏 | 复杂度: 高级 | 炎凰特性: 时间分桶/趋势分析 | 类型: SELECT查询
WITH memory_trends AS (
  SELECT TIME_BUCKET('10m', _time) time_bucket,
         application_name, instance_id,
         AVG(heap_used_mb) avg_heap_used,
         AVG(heap_max_mb) avg_heap_max,
         AVG(non_heap_used_mb) avg_non_heap_used
  FROM jvm_memory_metrics 
  WHERE _time >= DATE_ADD('h', -12, NOW()) AND _time < NOW()
  GROUP BY time_bucket, application_name, instance_id
),
leak_detection AS (
  SELECT application_name, instance_id,
         REGR_SLOPE(avg_heap_used, EXTRACT(EPOCH FROM time_bucket)) heap_growth_rate,
         REGR_SLOPE(avg_non_heap_used, EXTRACT(EPOCH FROM time_bucket)) non_heap_growth_rate,
         COUNT(*) data_points,
         MAX(avg_heap_used) peak_heap_used,
         MAX(avg_heap_used) / MAX(avg_heap_max) * 100 peak_heap_utilization
  FROM memory_trends 
  GROUP BY application_name, instance_id
)
SELECT application_name, instance_id,
       heap_growth_rate * 3600 heap_growth_mb_per_hour,
       non_heap_growth_rate * 3600 non_heap_growth_mb_per_hour,
       peak_heap_used,
       peak_heap_utilization,
       CASE 
         WHEN heap_growth_rate * 3600 > 50 THEN 'HEAP_LEAK_SUSPECTED'
         WHEN non_heap_growth_rate * 3600 > 20 THEN 'NON_HEAP_LEAK_SUSPECTED'
         WHEN peak_heap_utilization > 90 THEN 'HIGH_MEMORY_PRESSURE'
         ELSE 'NORMAL'
       END memory_status
FROM leak_detection 
WHERE data_points >= 10
ORDER BY heap_growth_rate DESC;
```

### 47. CDN缓存效率分析
**Description**: 分析CDN缓存的效率
```sql
-- 目的: 分析CDN缓存命中效率 | 复杂度: 高级 | 炎凰特性: 时间分桶/URL解析 | 类型: SELECT查询
SELECT TIME_BUCKET('15m', _time) time_bucket,
       cdn_node, 
       DOMAIN(request_url) domain,
       SPLIT_PART(PATH(request_url), '.', -1) file_extension,
       COUNT(*) total_requests,
       COUNT(CASE WHEN cache_status = 'HIT' THEN 1 END) cache_hits,
       COUNT(CASE WHEN cache_status = 'HIT' THEN 1 END) * 100.0 / COUNT(*) hit_rate,
       SUM(response_size) total_bytes_served,
       AVG(response_time) avg_response_time
FROM cdn_access_logs 
WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
GROUP BY time_bucket, cdn_node, domain, file_extension
HAVING COUNT(*) > 50
ORDER BY hit_rate ASC, total_requests DESC 
LIMIT 100;
```

### 48. 微服务调用链分析
**Description**: 追踪微服务间的调用链路
```sql
-- 目的: 分析微服务调用链性能 | 复杂度: 高级 | 炎凰特性: 字符串处理/统计分析 | 类型: SELECT查询
WITH service_calls AS (
  SELECT trace_id, 
         caller_service, callee_service,
         operation_name,
         MIN(_time) call_start_time,
         MAX(_time) call_end_time,
         DATE_DIFF('ms', MIN(_time), MAX(_time)) call_duration_ms,
         COUNT(CASE WHEN span_status = 'ERROR' THEN 1 END) error_span_count
  FROM distributed_tracing_spans 
  WHERE _time >= DATE_ADD('h', -4, NOW()) AND _time < NOW()
  GROUP BY trace_id, caller_service, callee_service, operation_name
),
call_analytics AS (
  SELECT caller_service, callee_service, operation_name,
         COUNT(*) total_calls,
         AVG(call_duration_ms) avg_duration,
         PERCENTILE(call_duration_ms, 0.95) p95_duration,
         SUM(error_span_count) total_errors,
         COUNT(CASE WHEN error_span_count > 0 THEN 1 END) * 100.0 / COUNT(*) error_rate
  FROM service_calls 
  GROUP BY caller_service, callee_service, operation_name
)
SELECT caller_service, callee_service, operation_name,
       total_calls, avg_duration, p95_duration,
       error_rate,
       CASE 
         WHEN error_rate > 5 THEN 'HIGH_ERROR_RATE'
         WHEN p95_duration > 1000 THEN 'SLOW_RESPONSE'
         WHEN avg_duration > 500 THEN 'MODERATE_LATENCY'
         ELSE 'HEALTHY'
       END call_health_status
FROM call_analytics 
WHERE total_calls > 100
ORDER BY error_rate DESC, p95_duration DESC 
LIMIT 50;
```

### 49. 备份任务成功率监控
**Description**: 监控数据备份任务的成功率
```sql
-- 目的: 监控数据备份任务执行情况 | 复杂度: 简单 | 炎凰特性: 时间差计算/聚合 | 类型: SELECT查询
SELECT backup_type, target_system,
       COUNT(*) total_backup_jobs,
       COUNT(CASE WHEN job_status = 'SUCCESS' THEN 1 END) successful_backups,
       COUNT(CASE WHEN job_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*) success_rate,
       AVG(DATE_DIFF('m', job_start_time, job_end_time)) avg_backup_duration_minutes,
       MAX(DATE_DIFF('m', job_start_time, job_end_time)) max_backup_duration_minutes,
       LATEST_VALUE(job_end_time) last_backup_time,
       DATE_DIFF('h', LATEST_VALUE(job_end_time), NOW()) hours_since_last_backup
FROM backup_job_logs 
WHERE _time >= DATE_ADD('d', -14, NOW()) AND _time < NOW()
GROUP BY backup_type, target_system
ORDER BY success_rate ASC, hours_since_last_backup DESC;
```

### 50. 集群节点健康状态
**Description**: 检查集群节点的运行状态
```sql
-- 目的: 监控集群节点整体健康状态 | 复杂度: 高级 | 炎凰特性: 聚合增强/条件聚合 | 类型: SELECT查询
WITH node_health AS (
  SELECT node_id, node_role, availability_zone,
         LATEST_VALUE(node_status) current_status,
         LATEST_VALUE(cpu_usage) current_cpu,
         LATEST_VALUE(memory_usage) current_memory,
         LATEST_VALUE(disk_usage) current_disk,
         COUNT(CASE WHEN node_status != 'HEALTHY' THEN 1 END) unhealthy_readings,
         COUNT(*) total_readings
  FROM cluster_node_metrics 
  WHERE _time >= DATE_ADD('h', -2, NOW()) AND _time < NOW()
  GROUP BY node_id, node_role, availability_zone
)
SELECT availability_zone, node_role,
       COUNT(*) total_nodes,
       COUNT(CASE WHEN current_status = 'HEALTHY' THEN 1 END) healthy_nodes,
       COUNT(CASE WHEN current_status = 'HEALTHY' THEN 1 END) * 100.0 / COUNT(*) healthy_percentage,
       AVG(current_cpu) avg_cpu_usage,
       AVG(current_memory) avg_memory_usage,
       AVG(current_disk) avg_disk_usage,
       COUNT(CASE WHEN current_cpu > 80 OR current_memory > 85 THEN 1 END) high_resource_nodes
FROM node_health 
GROUP BY availability_zone, node_role
ORDER BY healthy_percentage ASC, high_resource_nodes DESC;
``` 

# 炎凰数据SQL样例集 - 第三批(51-75)

## 用户分析场景 (51-75)

### 51. 用户会话路径分析
**Description**: 分析用户在网站上的访问路径和行为流程
```sql
-- 目的: 分析用户访问路径 | 复杂度: 高级 | 炎凰特性: URL解析/路径分析 | 类型: SELECT查询
SELECT user_id,
       PATH(referrer_url) entry_path,
       PATH(current_url) current_path,
       SPLIT_PART(PATH(current_url), '/', 2) section,
       COUNT(*) path_frequency,
       EARLIEST_VALUE(_time) first_visit,
       LATEST_VALUE(_time) last_visit
FROM user_events 
WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  AND event_type = 'page_view'
GROUP BY user_id, entry_path, current_path, section
ORDER BY path_frequency DESC LIMIT 200;
```

### 52. 用户活跃度趋势
**Description**: 统计用户的活跃度变化趋势
```sql
-- 目的: 分析用户活跃度变化 | 复杂度: 高级 | 炎凰特性: 时间分桶/窗口函数 | 类型: SELECT查询
WITH daily_activity AS (
  SELECT TIME_BUCKET('1d', _time) day_bucket,
         user_id,
         COUNT(*) daily_events,
         COUNT(DISTINCT session_id) daily_sessions
  FROM user_events 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
  GROUP BY day_bucket, user_id
)
SELECT user_id,
       COUNT(*) active_days,
       AVG(daily_events) avg_daily_events,
       MAX(daily_events) peak_daily_events,
       AVG(daily_sessions) avg_daily_sessions,
       CASE 
         WHEN COUNT(*) >= 20 THEN 'HIGHLY_ACTIVE'
         WHEN COUNT(*) >= 10 THEN 'MODERATELY_ACTIVE'
         WHEN COUNT(*) >= 3 THEN 'OCCASIONALLY_ACTIVE'
         ELSE 'BARELY_ACTIVE'
       END activity_level
FROM daily_activity 
GROUP BY user_id
ORDER BY active_days DESC, avg_daily_events DESC LIMIT 1000;
```

### 53. 用户留存率分析
**Description**: 计算新用户的留存率情况
```sql
-- 目的: 计算用户留存率 | 复杂度: 高级 | 炎凰特性: 时间差计算/聚合增强 | 类型: SELECT查询
WITH user_first_visit AS (
  SELECT user_id, EARLIEST_VALUE(_time) first_visit_date
  FROM user_events 
  GROUP BY user_id
),
retention_cohorts AS (
  SELECT u.user_id, ufv.first_visit_date,
         DATE_DIFF('d', ufv.first_visit_date, u._time) days_since_first_visit
  FROM user_events u
  JOIN user_first_visit ufv ON u.user_id = ufv.user_id
  WHERE u._time >= DATE_ADD('d', -60, NOW()) AND u._time < NOW()
)
SELECT DATE(first_visit_date) cohort_date,
       COUNT(DISTINCT CASE WHEN days_since_first_visit = 0 THEN user_id END) day_0_users,
       COUNT(DISTINCT CASE WHEN days_since_first_visit = 1 THEN user_id END) day_1_users,
       COUNT(DISTINCT CASE WHEN days_since_first_visit = 7 THEN user_id END) day_7_users,
       COUNT(DISTINCT CASE WHEN days_since_first_visit = 30 THEN user_id END) day_30_users,
       COUNT(DISTINCT CASE WHEN days_since_first_visit = 1 THEN user_id END) * 100.0 / 
         NULLIF(COUNT(DISTINCT CASE WHEN days_since_first_visit = 0 THEN user_id END), 0) retention_1d,
       COUNT(DISTINCT CASE WHEN days_since_first_visit = 7 THEN user_id END) * 100.0 / 
         NULLIF(COUNT(DISTINCT CASE WHEN days_since_first_visit = 0 THEN user_id END), 0) retention_7d
FROM retention_cohorts 
GROUP BY DATE(first_visit_date)
ORDER BY cohort_date DESC;
```

### 54. 用户设备偏好分析
**Description**: 分析用户使用的设备类型偏好
```sql
-- 目的: 分析用户设备使用偏好 | 复杂度: 简单 | 炎凰特性: 聚合增强 | 类型: SELECT查询
SELECT device_type, browser, os_name,
       COUNT(DISTINCT user_id) unique_users,
       COUNT(*) total_sessions,
       AVG(session_duration) avg_session_duration,
       LATEST_VALUE(user_agent) latest_user_agent
FROM user_sessions 
WHERE _time >= DATE_ADD('d', -14, NOW()) AND _time < NOW()
GROUP BY device_type, browser, os_name
ORDER BY unique_users DESC LIMIT 50;
```

### 55. 用户地理分布分析
**Description**: 查看用户的地理分布情况
```sql
-- 目的: 分析用户地理分布 | 复杂度: 高级 | 炎凰特性: IP分析/表函数 | 类型: SELECT查询
SELECT loc.country, loc.region, loc.city,
       COUNT(DISTINCT u.user_id) unique_users,
       COUNT(*) total_events,
       AVG(u.session_duration) avg_session_duration,
       APPROX_COUNT_DISTINCT(u.user_id) approx_unique_users
FROM user_events u
OUTER APPLY ip_location(u.client_ip) AS loc
WHERE u._time >= DATE_ADD('d', -30, NOW()) AND u._time < NOW()
GROUP BY loc.country, loc.region, loc.city
HAVING COUNT(DISTINCT u.user_id) > 10
ORDER BY unique_users DESC LIMIT 100;
```

### 56. 页面访问热力图
**Description**: 生成网站页面访问的热力图数据
```sql
-- 目的: 生成页面访问热力图数据 | 复杂度: 简单 | 炎凰特性: URL解析/时间分析 | 类型: SELECT查询
SELECT DOMAIN(page_url) domain,
       PATH(page_url) page_path,
       DATE_PART('hour', _time) hour_of_day,
       DATE_PART('dow', _time) day_of_week,
       COUNT(*) page_views,
       COUNT(DISTINCT user_id) unique_visitors,
       AVG(time_on_page) avg_time_on_page
FROM page_analytics 
WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
GROUP BY domain, page_path, hour_of_day, day_of_week
ORDER BY page_views DESC LIMIT 500;
```

### 57. 用户转化漏斗分析
**Description**: 分析用户从浏览到购买的转化漏斗
```sql
-- 目的: 分析用户转化漏斗 | 复杂度: 高级 | 炎凰特性: 窗口函数/条件聚合 | 类型: SELECT查询
WITH funnel_events AS (
  SELECT user_id, event_type, _time,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY _time) event_sequence
  FROM user_events 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND event_type IN ('page_view', 'add_to_cart', 'checkout', 'purchase')
),
funnel_stages AS (
  SELECT user_id,
         COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) > 0 has_page_view,
         COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) > 0 has_add_to_cart,
         COUNT(CASE WHEN event_type = 'checkout' THEN 1 END) > 0 has_checkout,
         COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) > 0 has_purchase
  FROM funnel_events 
  GROUP BY user_id
)
SELECT 
  COUNT(*) total_users,
  COUNT(CASE WHEN has_page_view THEN 1 END) page_view_users,
  COUNT(CASE WHEN has_add_to_cart THEN 1 END) add_to_cart_users,
  COUNT(CASE WHEN has_checkout THEN 1 END) checkout_users,
  COUNT(CASE WHEN has_purchase THEN 1 END) purchase_users,
  COUNT(CASE WHEN has_add_to_cart THEN 1 END) * 100.0 / NULLIF(COUNT(CASE WHEN has_page_view THEN 1 END), 0) view_to_cart_rate,
  COUNT(CASE WHEN has_purchase THEN 1 END) * 100.0 / NULLIF(COUNT(CASE WHEN has_checkout THEN 1 END), 0) checkout_to_purchase_rate
FROM funnel_stages;
```

### 58. 用户标签画像分析
**Description**: 根据用户标签进行画像分析
```sql
-- 目的: 分析用户标签画像 | 复杂度: 高级 | 炎凰特性: 数组处理 | 类型: SELECT查询
SELECT user_id, user_tags,
       ARRAY_LENGTH(user_tags) tag_count,
       CASE 
         WHEN ARRAY_CONTAINS(user_tags, 'VIP') THEN 'VIP_USER'
         WHEN ARRAY_CONTAINS(user_tags, 'premium') THEN 'PREMIUM_USER'
         WHEN ARRAY_CONTAINS(user_tags, 'loyal') THEN 'LOYAL_USER'
         ELSE 'REGULAR_USER'
       END user_segment,
       total_spent, last_login_time,
       DATE_DIFF('d', last_login_time, NOW()) days_since_last_login
FROM user_profiles 
WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
  AND ARRAY_LENGTH(user_tags) > 0
ORDER BY total_spent DESC LIMIT 500;
```

### 59. 用户搜索行为分析
**Description**: 分析用户的搜索行为和关键词
```sql
-- 目的: 分析用户搜索行为模式 | 复杂度: 高级 | 炎凰特性: 字符串处理 | 类型: SELECT查询
SELECT search_query,
       COUNT(*) search_count,
       COUNT(DISTINCT user_id) unique_searchers,
       AVG(results_count) avg_results_returned,
       COUNT(CASE WHEN click_through = true THEN 1 END) * 100.0 / COUNT(*) click_through_rate,
       CHAR_LENGTH(search_query) query_length,
       CASE 
         WHEN CHAR_LENGTH(search_query) <= 10 THEN 'SHORT_QUERY'
         WHEN CHAR_LENGTH(search_query) <= 30 THEN 'MEDIUM_QUERY'
         ELSE 'LONG_QUERY'
       END query_type
FROM search_logs 
WHERE _time >= DATE_ADD('d', -14, NOW()) AND _time < NOW()
GROUP BY search_query
HAVING COUNT(*) > 5
ORDER BY search_count DESC LIMIT 200;
```

### 60. 用户互动行为分析
**Description**: 统计用户的互动行为数据
```sql
-- 目的: 分析用户互动行为 | 复杂度: 简单 | 炎凰特性: 聚合增强 | 类型: SELECT查询
SELECT user_id, interaction_type,
       COUNT(*) interaction_count,
       EARLIEST_VALUE(_time) first_interaction,
       LATEST_VALUE(_time) last_interaction,
       COUNT(DISTINCT target_id) unique_targets,
       AVG(interaction_value) avg_interaction_value
FROM user_interactions 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
GROUP BY user_id, interaction_type
ORDER BY interaction_count DESC LIMIT 1000;
```

### 61. 用户生命周期价值
**Description**: 计算用户的生命周期价值
```sql
-- 目的: 计算用户生命周期价值 | 复杂度: 高级 | 炎凰特性: 时间差计算/窗口函数 | 类型: SELECT查询
WITH user_metrics AS (
  SELECT user_id,
         EARLIEST_VALUE(_time) first_purchase_date,
         LATEST_VALUE(_time) last_purchase_date,
         COUNT(*) total_orders,
         SUM(order_amount) total_spent,
         AVG(order_amount) avg_order_value
  FROM purchase_events 
  WHERE _time >= DATE_ADD('y', -2, NOW()) AND _time < NOW()
  GROUP BY user_id
),
ltv_calculation AS (
  SELECT *,
         DATE_DIFF('d', first_purchase_date, last_purchase_date) customer_lifespan_days,
         total_spent / NULLIF(DATE_DIFF('d', first_purchase_date, last_purchase_date), 0) * 365 projected_annual_value
  FROM user_metrics 
  WHERE total_orders > 1
)
SELECT user_id, total_orders, total_spent, avg_order_value,
       customer_lifespan_days,
       projected_annual_value,
       NTILE(5) OVER (ORDER BY projected_annual_value DESC) ltv_quintile
FROM ltv_calculation 
WHERE customer_lifespan_days > 30
ORDER BY projected_annual_value DESC LIMIT 500;
```

### 62. 用户流失预警模型
**Description**: 建立用户流失预警模型
```sql
-- 目的: 构建用户流失预警模型 | 复杂度: 高级 | 炎凰特性: 时间分析/窗口函数 | 类型: SELECT查询
WITH user_activity AS (
  SELECT user_id,
         COUNT(*) total_events_30d,
         MAX(_time) last_activity,
         COUNT(DISTINCT DATE(_time)) active_days_30d,
         AVG(session_duration) avg_session_duration
  FROM user_events 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
  GROUP BY user_id
),
churn_indicators AS (
  SELECT *,
         DATE_DIFF('d', last_activity, NOW()) days_since_last_activity,
         CASE 
           WHEN DATE_DIFF('d', last_activity, NOW()) > 14 THEN 5
           WHEN DATE_DIFF('d', last_activity, NOW()) > 7 THEN 3
           WHEN active_days_30d < 5 THEN 2
           WHEN total_events_30d < 10 THEN 2
           ELSE 0
         END churn_risk_score
  FROM user_activity
)
SELECT user_id, days_since_last_activity, active_days_30d, 
       total_events_30d, churn_risk_score,
       CASE 
         WHEN churn_risk_score >= 5 THEN 'HIGH_CHURN_RISK'
         WHEN churn_risk_score >= 3 THEN 'MEDIUM_CHURN_RISK'
         WHEN churn_risk_score >= 1 THEN 'LOW_CHURN_RISK'
         ELSE 'ACTIVE'
       END churn_risk_level
FROM churn_indicators 
WHERE churn_risk_score > 0
ORDER BY churn_risk_score DESC LIMIT 1000;
```

### 63. 用户个性化推荐
**Description**: 为用户生成个性化推荐
```sql
-- 目的: 生成用户个性化推荐 | 复杂度: 高级 | 炎凰特性: 数组处理/窗口函数 | 类型: SELECT查询
WITH user_preferences AS (
  SELECT user_id,
         ARRAY_AGG(DISTINCT category) preferred_categories,
         ARRAY_AGG(DISTINCT brand) preferred_brands,
         AVG(rating) avg_rating,
         COUNT(*) interaction_count
  FROM user_product_interactions 
  WHERE _time >= DATE_ADD('d', -60, NOW()) AND _time < NOW()
  GROUP BY user_id
),
similar_users AS (
  SELECT u1.user_id, u2.user_id similar_user_id,
         COUNT(*) common_preferences
  FROM user_preferences u1
  JOIN user_preferences u2 ON u1.user_id != u2.user_id
  WHERE ARRAY_INTERSECT(u1.preferred_categories, u2.preferred_categories) IS NOT NULL
  GROUP BY u1.user_id, u2.user_id
  HAVING COUNT(*) > 2
)
SELECT user_id, preferred_categories, preferred_brands,
       avg_rating, interaction_count,
       CASE 
         WHEN avg_rating > 4.5 THEN 'HIGH_SATISFACTION'
         WHEN avg_rating > 3.5 THEN 'MEDIUM_SATISFACTION'
         ELSE 'LOW_SATISFACTION'
       END satisfaction_level
FROM user_preferences 
ORDER BY interaction_count DESC LIMIT 500;
```

### 64. 用户异常行为检测
**Description**: 检测用户的异常行为模式
```sql
-- 目的: 检测用户异常行为 | 复杂度: 高级 | 炎凰特性: 统计分析/窗口函数 | 类型: SELECT查询
WITH user_behavior_baseline AS (
  SELECT user_id,
         AVG(daily_events) avg_daily_events,
         STDDEV_POP(daily_events) stddev_daily_events,
         AVG(session_duration) avg_session_duration,
         STDDEV_POP(session_duration) stddev_session_duration
  FROM (
    SELECT user_id, DATE(_time) date,
           COUNT(*) daily_events,
           AVG(session_duration) session_duration
    FROM user_events 
    WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    GROUP BY user_id, DATE(_time)
  ) daily_stats
  GROUP BY user_id
),
recent_behavior AS (
  SELECT user_id, DATE(_time) date,
         COUNT(*) daily_events,
         AVG(session_duration) session_duration
  FROM user_events 
  WHERE _time >= DATE_ADD('d', -3, NOW()) AND _time < NOW()
  GROUP BY user_id, DATE(_time)
)
SELECT rb.user_id, rb.date, rb.daily_events, rb.session_duration,
       (rb.daily_events - ubb.avg_daily_events) / NULLIF(ubb.stddev_daily_events, 0) events_z_score,
       (rb.session_duration - ubb.avg_session_duration) / NULLIF(ubb.stddev_session_duration, 0) duration_z_score,
       CASE 
         WHEN ABS((rb.daily_events - ubb.avg_daily_events) / NULLIF(ubb.stddev_daily_events, 0)) > 3 THEN 'ANOMALY'
         WHEN ABS((rb.session_duration - ubb.avg_session_duration) / NULLIF(ubb.stddev_session_duration, 0)) > 3 THEN 'ANOMALY'
         ELSE 'NORMAL'
       END behavior_status
FROM recent_behavior rb
JOIN user_behavior_baseline ubb ON rb.user_id = ubb.user_id
WHERE ABS((rb.daily_events - ubb.avg_daily_events) / NULLIF(ubb.stddev_daily_events, 0)) > 2
ORDER BY ABS(events_z_score) DESC LIMIT 200;
```

### 65. 用户群体细分分析
**Description**: 对用户进行群体细分分析
```sql
-- 目的: 用户群体细分和特征分析 | 复杂度: 高级 | 炎凰特性: 聚合增强/分层 | 类型: SELECT查询
WITH user_segments AS (
  SELECT user_id,
         total_spent,
         total_orders,
         registration_days,
         last_login_days,
         CASE 
           WHEN total_spent > 1000 AND total_orders > 10 THEN 'HIGH_VALUE'
           WHEN total_spent > 500 AND total_orders > 5 THEN 'MEDIUM_VALUE'
           WHEN registration_days < 30 THEN 'NEW_USER'
           WHEN last_login_days > 90 THEN 'DORMANT_USER'
           ELSE 'REGULAR_USER'
         END user_segment
  FROM user_summary 
  WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
)
SELECT user_segment,
       COUNT(*) segment_size,
       AVG(total_spent) avg_spent,
       AVG(total_orders) avg_orders,
       AVG(registration_days) avg_registration_days,
       AVG(last_login_days) avg_last_login_days,
       COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () segment_percentage
FROM user_segments 
GROUP BY user_segment
ORDER BY segment_size DESC;
```

### 66. 营销活动效果分析
**Description**: 分析营销活动的转化效果
```sql
-- 目的: 分析营销活动转化效果 | 复杂度: 高级 | 炎凰特性: 时间分桶/转化分析 | 类型: SELECT查询
WITH campaign_exposure AS (
  SELECT user_id, campaign_id, campaign_type,
         EARLIEST_VALUE(_time) first_exposure,
         COUNT(*) exposure_count
  FROM marketing_events 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND event_type = 'campaign_exposure'
  GROUP BY user_id, campaign_id, campaign_type
),
conversions AS (
  SELECT user_id, campaign_id,
         COUNT(*) conversion_count,
         SUM(conversion_value) total_conversion_value
  FROM marketing_events 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND event_type = 'conversion'
  GROUP BY user_id, campaign_id
)
SELECT ce.campaign_id, ce.campaign_type,
       COUNT(DISTINCT ce.user_id) exposed_users,
       COUNT(DISTINCT c.user_id) converted_users,
       COUNT(DISTINCT c.user_id) * 100.0 / COUNT(DISTINCT ce.user_id) conversion_rate,
       COALESCE(SUM(c.total_conversion_value), 0) total_revenue,
       COALESCE(SUM(c.total_conversion_value), 0) / COUNT(DISTINCT ce.user_id) revenue_per_user
FROM campaign_exposure ce
LEFT JOIN conversions c ON ce.user_id = c.user_id AND ce.campaign_id = c.campaign_id
GROUP BY ce.campaign_id, ce.campaign_type
ORDER BY conversion_rate DESC LIMIT 50;
```

### 67. 用户邮件打开率分析
**Description**: 统计邮件营销的打开率
```sql
-- 目的: 分析邮件营销打开率 | 复杂度: 简单 | 炎凰特性: 时间分桶/比率计算 | 类型: SELECT查询
SELECT TIME_BUCKET('1d', _time) day_bucket,
       email_campaign, email_subject,
       COUNT(CASE WHEN event_type = 'email_sent' THEN 1 END) emails_sent,
       COUNT(CASE WHEN event_type = 'email_opened' THEN 1 END) emails_opened,
       COUNT(CASE WHEN event_type = 'email_clicked' THEN 1 END) emails_clicked,
       COUNT(CASE WHEN event_type = 'email_opened' THEN 1 END) * 100.0 / 
         NULLIF(COUNT(CASE WHEN event_type = 'email_sent' THEN 1 END), 0) open_rate,
       COUNT(CASE WHEN event_type = 'email_clicked' THEN 1 END) * 100.0 / 
         NULLIF(COUNT(CASE WHEN event_type = 'email_opened' THEN 1 END), 0) click_through_rate
FROM email_marketing_events 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
GROUP BY day_bucket, email_campaign, email_subject
HAVING COUNT(CASE WHEN event_type = 'email_sent' THEN 1 END) > 100
ORDER BY open_rate DESC LIMIT 100;
```

### 68. 用户优惠券使用分析
**Description**: 分析优惠券的使用情况
```sql
-- 目的: 分析用户优惠券使用行为 | 复杂度: 高级 | 炎凰特性: 时间差计算/聚合 | 类型: SELECT查询
WITH coupon_lifecycle AS (
  SELECT user_id, coupon_id, coupon_type, discount_amount,
         EARLIEST_VALUE(_time) coupon_issued,
         LATEST_VALUE(_time) coupon_used,
         COUNT(CASE WHEN event_type = 'coupon_used' THEN 1 END) > 0 was_used
  FROM coupon_events 
  WHERE _time >= DATE_ADD('d', -60, NOW()) AND _time < NOW()
  GROUP BY user_id, coupon_id, coupon_type, discount_amount
)
SELECT coupon_type,
       COUNT(*) total_coupons_issued,
       COUNT(CASE WHEN was_used THEN 1 END) coupons_used,
       COUNT(CASE WHEN was_used THEN 1 END) * 100.0 / COUNT(*) usage_rate,
       AVG(discount_amount) avg_discount_amount,
       AVG(CASE WHEN was_used THEN DATE_DIFF('h', coupon_issued, coupon_used) END) avg_usage_delay_hours
FROM coupon_lifecycle 
GROUP BY coupon_type
ORDER BY usage_rate DESC;
```

### 69. 用户推荐成功率分析
**Description**: 评估推荐系统的成功率
```sql
-- 目的: 分析推荐系统成功率 | 复杂度: 高级 | 炎凰特性: 窗口函数/成功率 | 类型: SELECT查询
WITH recommendations AS (
  SELECT user_id, recommendation_id, recommended_item,
         recommendation_algorithm, _time recommendation_time
  FROM recommendation_events 
  WHERE _time >= DATE_ADD('d', -14, NOW()) AND _time < NOW()
    AND event_type = 'recommendation_shown'
),
interactions AS (
  SELECT user_id, item_id, interaction_type, _time interaction_time
  FROM user_item_interactions 
  WHERE _time >= DATE_ADD('d', -14, NOW()) AND _time < NOW()
    AND interaction_type IN ('click', 'purchase', 'like')
)
SELECT r.recommendation_algorithm,
       COUNT(*) total_recommendations,
       COUNT(DISTINCT r.user_id) unique_users,
       COUNT(i.user_id) successful_recommendations,
       COUNT(i.user_id) * 100.0 / COUNT(*) success_rate,
       AVG(DATE_DIFF('m', r.recommendation_time, i.interaction_time)) avg_time_to_interaction_minutes
FROM recommendations r
LEFT JOIN interactions i ON r.user_id = i.user_id 
  AND r.recommended_item = i.item_id
  AND i.interaction_time > r.recommendation_time
  AND i.interaction_time <= DATE_ADD('h', 24, r.recommendation_time)
GROUP BY r.recommendation_algorithm
ORDER BY success_rate DESC;
```

### 70. 用户App推送效果分析
**Description**: 分析App推送消息的效果
```sql
-- 目的: 分析App推送消息效果 | 复杂度: 高级 | 炎凰特性: 时间分桶/效果分析 | 类型: SELECT查询
SELECT TIME_BUCKET('1h', _time) hour_bucket,
       push_campaign, push_type,
       COUNT(CASE WHEN event_type = 'push_sent' THEN 1 END) pushes_sent,
       COUNT(CASE WHEN event_type = 'push_delivered' THEN 1 END) pushes_delivered,
       COUNT(CASE WHEN event_type = 'push_opened' THEN 1 END) pushes_opened,
       COUNT(CASE WHEN event_type = 'push_clicked' THEN 1 END) pushes_clicked,
       COUNT(CASE WHEN event_type = 'push_delivered' THEN 1 END) * 100.0 / 
         NULLIF(COUNT(CASE WHEN event_type = 'push_sent' THEN 1 END), 0) delivery_rate,
       COUNT(CASE WHEN event_type = 'push_opened' THEN 1 END) * 100.0 / 
         NULLIF(COUNT(CASE WHEN event_type = 'push_delivered' THEN 1 END), 0) open_rate
FROM push_notification_events 
WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
GROUP BY hour_bucket, push_campaign, push_type
HAVING COUNT(CASE WHEN event_type = 'push_sent' THEN 1 END) > 50
ORDER BY open_rate DESC LIMIT 200;
```

### 71. 用户社交分享分析
**Description**: 统计用户的社交分享行为
```sql
-- 目的: 分析用户社交分享行为 | 复杂度: 简单 | 炎凰特性: URL解析/聚合 | 类型: SELECT查询
SELECT DOMAIN(shared_url) shared_domain,
       social_platform, content_type,
       COUNT(*) total_shares,
       COUNT(DISTINCT user_id) unique_sharers,
       COUNT(DISTINCT shared_url) unique_urls_shared,
       AVG(engagement_score) avg_engagement
FROM social_sharing_events 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
GROUP BY shared_domain, social_platform, content_type
ORDER BY total_shares DESC LIMIT 100;
```

### 72. 用户购买意向预测
**Description**: 预测用户的购买意向
```sql
-- 目的: 预测用户购买意向 | 复杂度: 高级 | 炎凰特性: 窗口函数/意向评分 | 类型: SELECT查询
WITH user_behavior_signals AS (
  SELECT user_id,
         COUNT(CASE WHEN event_type = 'product_view' THEN 1 END) product_views,
         COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) cart_additions,
         COUNT(CASE WHEN event_type = 'wishlist_add' THEN 1 END) wishlist_additions,
         COUNT(CASE WHEN event_type = 'price_check' THEN 1 END) price_checks,
         COUNT(CASE WHEN event_type = 'review_read' THEN 1 END) reviews_read,
         MAX(_time) last_activity
  FROM user_behavior_events 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  GROUP BY user_id
),
purchase_intent_score AS (
  SELECT *,
         (product_views * 1 + cart_additions * 5 + wishlist_additions * 3 + 
          price_checks * 2 + reviews_read * 2) purchase_intent_score,
         CASE 
           WHEN DATE_DIFF('h', last_activity, NOW()) <= 2 THEN 'IMMEDIATE'
           WHEN DATE_DIFF('h', last_activity, NOW()) <= 24 THEN 'SHORT_TERM'
           ELSE 'LONG_TERM'
         END urgency_level
  FROM user_behavior_signals
)
SELECT user_id, purchase_intent_score, urgency_level,
       product_views, cart_additions, wishlist_additions,
       NTILE(10) OVER (ORDER BY purchase_intent_score DESC) intent_decile,
       CASE 
         WHEN purchase_intent_score > 20 THEN 'HIGH_INTENT'
         WHEN purchase_intent_score > 10 THEN 'MEDIUM_INTENT'
         WHEN purchase_intent_score > 5 THEN 'LOW_INTENT'
         ELSE 'NO_INTENT'
       END intent_level
FROM purchase_intent_score 
WHERE purchase_intent_score > 0
ORDER BY purchase_intent_score DESC LIMIT 1000;
```

### 73. 用户客服咨询分析
**Description**: 分析用户的客服咨询模式
```sql
-- 目的: 分析用户客服咨询模式 | 复杂度: 高级 | 炎凰特性: 字符串处理/分类 | 类型: SELECT查询
WITH support_tickets AS (
  SELECT user_id, ticket_id, category, priority,
         DATE_DIFF('m', created_time, resolved_time) resolution_time_minutes,
         satisfaction_rating,
         CASE 
           WHEN CONTAINS(LOWER(description), 'refund') THEN 'REFUND_REQUEST'
           WHEN CONTAINS(LOWER(description), 'bug') OR CONTAINS(LOWER(description), 'error') THEN 'TECHNICAL_ISSUE'
           WHEN CONTAINS(LOWER(description), 'account') THEN 'ACCOUNT_ISSUE'
           WHEN CONTAINS(LOWER(description), 'billing') THEN 'BILLING_ISSUE'
           ELSE 'GENERAL_INQUIRY'
         END issue_type
  FROM customer_support_tickets 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND status = 'resolved'
)
SELECT issue_type, category,
       COUNT(*) ticket_count,
       COUNT(DISTINCT user_id) unique_users,
       AVG(resolution_time_minutes) avg_resolution_time,
       AVG(satisfaction_rating) avg_satisfaction,
       COUNT(CASE WHEN satisfaction_rating >= 4 THEN 1 END) * 100.0 / 
         NULLIF(COUNT(CASE WHEN satisfaction_rating IS NOT NULL THEN 1 END), 0) satisfaction_rate
FROM support_tickets 
GROUP BY issue_type, category
ORDER BY ticket_count DESC;
```

### 74. 用户反馈情感分析
**Description**: 分析用户反馈的情感倾向
```sql
-- 目的: 分析用户反馈情感倾向 | 复杂度: 高级 | 炎凰特性: 字符串分析/情感分类 | 类型: SELECT查询
WITH feedback_sentiment AS (
  SELECT user_id, feedback_text, rating, product_id,
         CHAR_LENGTH(feedback_text) feedback_length,
         CASE 
           WHEN REGEX_LIKE(feedback_text, '.*(excellent|amazing|perfect|love|great).*', 'i') THEN 'VERY_POSITIVE'
           WHEN REGEX_LIKE(feedback_text, '.*(good|nice|satisfied|happy).*', 'i') THEN 'POSITIVE'
           WHEN REGEX_LIKE(feedback_text, '.*(okay|average|fine).*', 'i') THEN 'NEUTRAL'
           WHEN REGEX_LIKE(feedback_text, '.*(bad|poor|disappointed|hate).*', 'i') THEN 'NEGATIVE'
           WHEN REGEX_LIKE(feedback_text, '.*(terrible|awful|worst|horrible).*', 'i') THEN 'VERY_NEGATIVE'
           ELSE 'UNKNOWN'
         END sentiment_category
  FROM user_feedback 
  WHERE _time >= DATE_ADD('d', -60, NOW()) AND _time < NOW()
    AND feedback_text IS NOT NULL
)
SELECT sentiment_category,
       COUNT(*) feedback_count,
       COUNT(DISTINCT user_id) unique_users,
       AVG(rating) avg_numeric_rating,
       AVG(feedback_length) avg_feedback_length,
       COUNT(DISTINCT product_id) products_mentioned,
       COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () sentiment_percentage
FROM feedback_sentiment 
WHERE sentiment_category != 'UNKNOWN'
GROUP BY sentiment_category
ORDER BY feedback_count DESC;
```

### 75. 用户忠诚度评分
**Description**: 计算用户的忠诚度评分
```sql
-- 目的: 计算用户忠诚度评分 | 复杂度: 高级 | 炎凰特性: 综合评分算法 | 类型: SELECT查询
WITH loyalty_metrics AS (
  SELECT u.user_id,
         DATE_DIFF('d', u.registration_date, NOW()) tenure_days,
         u.total_orders,
         u.total_spent,
         u.last_login_days,
         r.avg_rating,
         r.total_reviews,
         s.social_shares,
         ref.referrals_made
  FROM user_profiles u
  LEFT JOIN (
    SELECT user_id, AVG(rating) avg_rating, COUNT(*) total_reviews
    FROM product_reviews 
    WHERE _time >= DATE_ADD('d', -365, NOW()) AND _time < NOW()
    GROUP BY user_id
  ) r ON u.user_id = r.user_id
  LEFT JOIN (
    SELECT user_id, COUNT(*) social_shares
    FROM social_sharing_events 
    WHERE _time >= DATE_ADD('d', -365, NOW()) AND _time < NOW()
    GROUP BY user_id
  ) s ON u.user_id = s.user_id
  LEFT JOIN (
    SELECT referrer_user_id, COUNT(*) referrals_made
    FROM user_referrals 
    WHERE _time >= DATE_ADD('d', -365, NOW()) AND _time < NOW()
    GROUP BY referrer_user_id
  ) ref ON u.user_id = ref.referrer_user_id
  WHERE u._time >= DATE_ADD('h', -24, NOW()) AND u._time < NOW()
),
loyalty_scoring AS (
  SELECT *,
         LEAST(tenure_days / 365.0 * 20, 20) tenure_score,
         LEAST(total_orders / 10.0 * 25, 25) frequency_score,
         LEAST(total_spent / 1000.0 * 25, 25) monetary_score,
         CASE WHEN last_login_days <= 7 THEN 15 WHEN last_login_days <= 30 THEN 10 ELSE 0 END recency_score,
         COALESCE(avg_rating - 3, 0) * 5 satisfaction_score,
         LEAST(COALESCE(social_shares, 0) * 2, 10) advocacy_score,
         LEAST(COALESCE(referrals_made, 0) * 5, 15) referral_score
  FROM loyalty_metrics
)
SELECT user_id,
       tenure_score + frequency_score + monetary_score + recency_score + 
       satisfaction_score + advocacy_score + referral_score loyalty_score,
       CASE 
         WHEN tenure_score + frequency_score + monetary_score + recency_score + 
              satisfaction_score + advocacy_score + referral_score >= 80 THEN 'CHAMPION'
         WHEN tenure_score + frequency_score + monetary_score + recency_score + 
              satisfaction_score + advocacy_score + referral_score >= 60 THEN 'LOYAL'
         WHEN tenure_score + frequency_score + monetary_score + recency_score + 
              satisfaction_score + advocacy_score + referral_score >= 40 THEN 'POTENTIAL'
         ELSE 'CASUAL'
       END loyalty_tier
FROM loyalty_scoring 
ORDER BY loyalty_score DESC LIMIT 1000;
``` 

# 炎凰数据SQL样例集 - 第四批(76-100)

## 综合分析场景 (76-100)

### 76. 业务指标关联分析
**Description**: 分析多个业务指标之间的关联性
```sql
-- 目的: 分析多维业务指标关联性 | 复杂度: 高级 | 炎凰特性: 时间分桶/多维关联 | 类型: SELECT查询
WITH daily_metrics AS (
  SELECT TIME_BUCKET('1d', _time) day_bucket,
         SUM(CASE WHEN event_type = 'order' THEN amount ELSE 0 END) daily_revenue,
         COUNT(CASE WHEN event_type = 'order' THEN 1 END) daily_orders,
         COUNT(CASE WHEN event_type = 'user_signup' THEN 1 END) daily_signups,
         COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) daily_pageviews
  FROM business_events 
  WHERE _time >= DATE_ADD('d', -90, NOW()) AND _time < NOW()
  GROUP BY day_bucket
)
SELECT day_bucket,
       daily_revenue, daily_orders, daily_signups, daily_pageviews,
       daily_revenue / NULLIF(daily_orders, 0) avg_order_value,
       daily_orders / NULLIF(daily_signups, 0) signup_to_order_conversion,
       LAG(daily_revenue) OVER (ORDER BY day_bucket) prev_day_revenue,
       (daily_revenue - LAG(daily_revenue) OVER (ORDER BY day_bucket)) * 100.0 / 
         NULLIF(LAG(daily_revenue) OVER (ORDER BY day_bucket), 0) revenue_growth_rate
FROM daily_metrics 
ORDER BY day_bucket DESC LIMIT 90;
```

### 77. 实时告警规则分析
**Description**: 统计告警规则的触发情况
```sql
-- 目的: 分析实时告警规则触发情况 | 复杂度: 高级 | 炎凰特性: 时间分桶/告警分析 | 类型: SELECT查询
SELECT TIME_BUCKET('10m', _time) time_bucket,
       alert_rule_name, severity_level,
       COUNT(*) alert_count,
       COUNT(DISTINCT affected_resource) affected_resources,
       AVG(DATE_DIFF('m', trigger_time, resolution_time)) avg_resolution_minutes,
       COUNT(CASE WHEN auto_resolved = true THEN 1 END) auto_resolved_count,
       LATEST_VALUE(alert_message) latest_alert_message
FROM alert_events 
WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
GROUP BY time_bucket, alert_rule_name, severity_level
ORDER BY alert_count DESC LIMIT 200;
```

### 78. 数据质量监控分析
**Description**: 监控数据质量指标
```sql
-- 目的: 监控数据质量指标 | 复杂度: 高级 | 炎凰特性: 数据质量/统计分析 | 类型: SELECT查询
WITH data_quality_checks AS (
  SELECT table_name, column_name,
         COUNT(*) total_records,
         COUNT(CASE WHEN field_value IS NULL THEN 1 END) null_count,
         COUNT(CASE WHEN field_value = '' THEN 1 END) empty_count,
         COUNT(DISTINCT field_value) unique_values,
         AVG(CHAR_LENGTH(CAST(field_value AS STRING))) avg_length
  FROM data_quality_metrics 
  WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
  GROUP BY table_name, column_name
)
SELECT table_name, column_name,
       total_records,
       null_count * 100.0 / total_records null_percentage,
       empty_count * 100.0 / total_records empty_percentage,
       unique_values * 100.0 / total_records uniqueness_ratio,
       avg_length,
       CASE 
         WHEN null_count * 100.0 / total_records > 20 THEN 'HIGH_NULL_RATE'
         WHEN unique_values * 100.0 / total_records < 50 THEN 'LOW_UNIQUENESS'
         WHEN avg_length < 3 THEN 'SHORT_VALUES'
         ELSE 'GOOD_QUALITY'
       END quality_status
FROM data_quality_checks 
WHERE total_records > 1000
ORDER BY null_percentage DESC, empty_percentage DESC;
```

### 79. 成本效益分析
**Description**: 分析各项投入的成本效益
```sql
-- 目的: 分析各项投入的成本效益 | 复杂度: 高级 | 炎凰特性: 时间分桶/ROI计算 | 类型: SELECT查询
WITH cost_revenue_data AS (
  SELECT TIME_BUCKET('1M', _time) month_bucket,
         cost_category, cost_subcategory,
         SUM(cost_amount) total_cost,
         SUM(attributed_revenue) attributed_revenue
  FROM cost_tracking_events 
  WHERE _time >= DATE_ADD('M', -12, NOW()) AND _time < NOW()
  GROUP BY month_bucket, cost_category, cost_subcategory
)
SELECT cost_category, cost_subcategory,
       SUM(total_cost) total_investment,
       SUM(attributed_revenue) total_return,
       (SUM(attributed_revenue) - SUM(total_cost)) * 100.0 / NULLIF(SUM(total_cost), 0) roi_percentage,
       SUM(attributed_revenue) / NULLIF(SUM(total_cost), 0) roi_ratio,
       AVG(total_cost) avg_monthly_cost,
       CASE 
         WHEN (SUM(attributed_revenue) - SUM(total_cost)) * 100.0 / NULLIF(SUM(total_cost), 0) > 100 THEN 'HIGH_ROI'
         WHEN (SUM(attributed_revenue) - SUM(total_cost)) * 100.0 / NULLIF(SUM(total_cost), 0) > 20 THEN 'POSITIVE_ROI'
         ELSE 'NEGATIVE_ROI'
       END roi_category
FROM cost_revenue_data 
GROUP BY cost_category, cost_subcategory
ORDER BY roi_percentage DESC;
```

### 80. 合规性检查分析
**Description**: 检查系统的合规性状况
```sql
-- 目的: 分析系统合规性检查结果 | 复杂度: 高级 | 炎凰特性: 条件聚合/合规监控 | 类型: SELECT查询
SELECT compliance_framework, check_category, check_name,
       COUNT(*) total_checks,
       COUNT(CASE WHEN check_status = 'PASS' THEN 1 END) passed_checks,
       COUNT(CASE WHEN check_status = 'FAIL' THEN 1 END) failed_checks,
       COUNT(CASE WHEN check_status = 'WARNING' THEN 1 END) warning_checks,
       COUNT(CASE WHEN check_status = 'PASS' THEN 1 END) * 100.0 / COUNT(*) compliance_rate,
       LATEST_VALUE(check_details) latest_check_details,
       LATEST_VALUE(_time) last_check_time
FROM compliance_audit_logs 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
GROUP BY compliance_framework, check_category, check_name
HAVING COUNT(CASE WHEN check_status = 'FAIL' THEN 1 END) > 0
ORDER BY compliance_rate ASC, failed_checks DESC;
```

### 81. 风险评估综合分析
**Description**: 进行综合风险评估
```sql
-- 目的: 综合评估系统风险等级 | 复杂度: 高级 | 炎凰特性: 风险评分/多维分析 | 类型: SELECT查询
WITH risk_factors AS (
  SELECT risk_category, risk_source,
         AVG(risk_score) avg_risk_score,
         MAX(risk_score) max_risk_score,
         COUNT(*) risk_event_count,
         COUNT(CASE WHEN mitigation_status = 'RESOLVED' THEN 1 END) resolved_count
  FROM risk_assessment_events 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  GROUP BY risk_category, risk_source
),
weighted_risk AS (
  SELECT *,
         CASE risk_category
           WHEN 'SECURITY' THEN avg_risk_score * 1.5
           WHEN 'OPERATIONAL' THEN avg_risk_score * 1.2
           WHEN 'FINANCIAL' THEN avg_risk_score * 1.3
           ELSE avg_risk_score
         END weighted_score,
         resolved_count * 100.0 / risk_event_count resolution_rate
  FROM risk_factors
)
SELECT risk_category, risk_source,
       avg_risk_score, max_risk_score, weighted_score,
       risk_event_count, resolution_rate,
       CASE 
         WHEN weighted_score > 8 AND resolution_rate < 50 THEN 'CRITICAL'
         WHEN weighted_score > 6 AND resolution_rate < 70 THEN 'HIGH'
         WHEN weighted_score > 4 THEN 'MEDIUM'
         ELSE 'LOW'
       END overall_risk_level
FROM weighted_risk 
ORDER BY weighted_score DESC, resolution_rate ASC;
```

### 82. 性能基线建立分析
**Description**: 建立系统性能基线
```sql
-- 目的: 建立系统性能基线 | 复杂度: 高级 | 炎凰特性: 统计分析/基线计算 | 类型: SELECT查询
WITH performance_history AS (
  SELECT TIME_BUCKET('1h', _time) hour_bucket,
         service_name, metric_name,
         AVG(metric_value) avg_value,
         MIN(metric_value) min_value,
         MAX(metric_value) max_value,
         PERCENTILE(metric_value, 0.95) p95_value
  FROM performance_metrics 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND metric_name IN ('response_time', 'cpu_usage', 'memory_usage', 'error_rate')
  GROUP BY hour_bucket, service_name, metric_name
),
baseline_calculation AS (
  SELECT service_name, metric_name,
         AVG(avg_value) baseline_avg,
         STDDEV_POP(avg_value) baseline_stddev,
         AVG(p95_value) baseline_p95,
         COUNT(*) data_points
  FROM performance_history 
  GROUP BY service_name, metric_name
)
SELECT service_name, metric_name,
       baseline_avg,
       baseline_avg - 2 * baseline_stddev lower_threshold,
       baseline_avg + 2 * baseline_stddev upper_threshold,
       baseline_p95,
       baseline_stddev,
       data_points,
       CASE 
         WHEN baseline_stddev / baseline_avg > 0.5 THEN 'HIGH_VARIANCE'
         WHEN baseline_stddev / baseline_avg > 0.2 THEN 'MEDIUM_VARIANCE'
         ELSE 'LOW_VARIANCE'
       END stability_rating
FROM baseline_calculation 
WHERE data_points > 100
ORDER BY service_name, metric_name;
```

### 83. 容量规划预测分析
**Description**: 预测系统容量需求
```sql
-- 目的: 预测系统容量需求 | 复杂度: 高级 | 炎凰特性: 趋势预测/容量分析 | 类型: SELECT查询
WITH resource_trends AS (
  SELECT TIME_BUCKET('1d', _time) day_bucket,
         resource_type, resource_name,
         AVG(usage_percentage) avg_usage,
         MAX(usage_percentage) peak_usage
  FROM resource_utilization_metrics 
  WHERE _time >= DATE_ADD('d', -60, NOW()) AND _time < NOW()
  GROUP BY day_bucket, resource_type, resource_name
),
growth_analysis AS (
  SELECT resource_type, resource_name,
         REGR_SLOPE(avg_usage, EXTRACT(EPOCH FROM day_bucket)) daily_growth_rate,
         AVG(avg_usage) current_avg_usage,
         MAX(peak_usage) max_peak_usage,
         COUNT(*) data_points
  FROM resource_trends 
  GROUP BY resource_type, resource_name
)
SELECT resource_type, resource_name,
       current_avg_usage,
       max_peak_usage,
       daily_growth_rate * 30 monthly_growth_estimate,
       current_avg_usage + (daily_growth_rate * 90) projected_90d_usage,
       CASE 
         WHEN current_avg_usage + (daily_growth_rate * 90) > 80 THEN 'CAPACITY_UPGRADE_NEEDED'
         WHEN current_avg_usage + (daily_growth_rate * 90) > 70 THEN 'MONITOR_CLOSELY'
         WHEN daily_growth_rate > 1 THEN 'GROWING_DEMAND'
         ELSE 'STABLE'
       END capacity_status,
       CASE 
         WHEN daily_growth_rate > 0 THEN 
           CEILING((80 - current_avg_usage) / NULLIF(daily_growth_rate, 0))
         ELSE NULL
       END days_to_80_percent
FROM growth_analysis 
WHERE data_points > 30
ORDER BY projected_90d_usage DESC;
```

### 84. 业务连续性分析
**Description**: 分析业务连续性状况
```sql
-- 目的: 分析业务连续性状况 | 复杂度: 高级 | 炎凰特性: 时间分析/可用性计算 | 类型: SELECT查询
WITH service_availability AS (
  SELECT TIME_BUCKET('5m', _time) time_bucket,
         service_name, environment,
         AVG(CASE WHEN service_status = 'UP' THEN 1 ELSE 0 END) availability_ratio,
         COUNT(CASE WHEN service_status = 'DOWN' THEN 1 END) downtime_events
  FROM service_health_checks 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  GROUP BY time_bucket, service_name, environment
),
availability_summary AS (
  SELECT service_name, environment,
         AVG(availability_ratio) * 100 avg_availability_percentage,
         MIN(availability_ratio) * 100 min_availability_percentage,
         SUM(downtime_events) total_downtime_events,
         COUNT(*) total_check_periods
  FROM service_availability 
  GROUP BY service_name, environment
)
SELECT service_name, environment,
       avg_availability_percentage,
       min_availability_percentage,
       total_downtime_events,
       total_check_periods,
       CASE 
         WHEN avg_availability_percentage >= 99.9 THEN 'EXCELLENT'
         WHEN avg_availability_percentage >= 99.5 THEN 'GOOD'
         WHEN avg_availability_percentage >= 99.0 THEN 'ACCEPTABLE'
         ELSE 'POOR'
       END availability_rating,
       100 - avg_availability_percentage downtime_percentage,
       (100 - avg_availability_percentage) / 100 * 7 * 24 * 60 estimated_downtime_minutes_per_week
FROM availability_summary 
ORDER BY avg_availability_percentage ASC;
```

### 85. 多租户资源分析
**Description**: 分析多租户的资源使用
```sql
-- 目的: 分析多租户资源使用情况 | 复杂度: 高级 | 炎凰特性: 租户隔离/资源分析 | 类型: SELECT查询
SELECT tenant_id, tenant_name, subscription_tier,
       SUM(cpu_usage_hours) total_cpu_hours,
       SUM(memory_usage_gb_hours) total_memory_gb_hours,
       SUM(storage_usage_gb) total_storage_gb,
       SUM(network_usage_gb) total_network_gb,
       COUNT(DISTINCT user_id) active_users,
       SUM(api_requests) total_api_requests,
       SUM(cpu_usage_hours) / NULLIF(COUNT(DISTINCT user_id), 0) cpu_hours_per_user,
       CASE subscription_tier
         WHEN 'BASIC' THEN SUM(cpu_usage_hours) - 100
         WHEN 'PRO' THEN SUM(cpu_usage_hours) - 500
         WHEN 'ENTERPRISE' THEN SUM(cpu_usage_hours) - 2000
       END cpu_overage_hours
FROM tenant_resource_usage 
WHERE _time >= DATE_ADD('M', -1, NOW()) AND _time < NOW()
GROUP BY tenant_id, tenant_name, subscription_tier
ORDER BY total_cpu_hours DESC LIMIT 100;
```

### 86. 数据备份恢复分析
**Description**: 评估数据备份恢复效率
```sql
-- 目的: 分析数据备份恢复效率 | 复杂度: 高级 | 炎凰特性: 时间差计算/成功率分析 | 类型: SELECT查询
WITH backup_operations AS (
  SELECT backup_id, backup_type, data_source,
         backup_size_gb,
         DATE_DIFF('m', backup_start_time, backup_end_time) backup_duration_minutes,
         backup_status,
         _time
  FROM backup_logs 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND operation_type = 'BACKUP'
),
restore_operations AS (
  SELECT restore_id, backup_id, restore_type,
         DATE_DIFF('m', restore_start_time, restore_end_time) restore_duration_minutes,
         restore_status,
         _time
  FROM backup_logs 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND operation_type = 'RESTORE'
)
SELECT b.backup_type, b.data_source,
       COUNT(b.backup_id) total_backups,
       COUNT(CASE WHEN b.backup_status = 'SUCCESS' THEN 1 END) successful_backups,
       COUNT(CASE WHEN b.backup_status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(b.backup_id) backup_success_rate,
       AVG(b.backup_duration_minutes) avg_backup_duration,
       AVG(b.backup_size_gb) avg_backup_size,
       COUNT(r.restore_id) total_restores,
       COUNT(CASE WHEN r.restore_status = 'SUCCESS' THEN 1 END) successful_restores,
       AVG(r.restore_duration_minutes) avg_restore_duration
FROM backup_operations b
LEFT JOIN restore_operations r ON b.backup_id = r.backup_id
GROUP BY b.backup_type, b.data_source
ORDER BY backup_success_rate ASC;
```

### 87. 系统健康度评分
**Description**: 计算系统整体健康度
```sql
-- 目的: 计算系统整体健康度评分 | 复杂度: 高级 | 炎凰特性: 综合评分/多维度分析 | 类型: SELECT查询
WITH health_metrics AS (
  SELECT system_component,
         AVG(CASE WHEN metric_name = 'availability' THEN metric_value END) availability_score,
         AVG(CASE WHEN metric_name = 'performance' THEN metric_value END) performance_score,
         AVG(CASE WHEN metric_name = 'error_rate' THEN 100 - metric_value END) error_score,
         AVG(CASE WHEN metric_name = 'resource_usage' THEN 100 - metric_value END) resource_score,
         COUNT(DISTINCT DATE(_time)) monitoring_days
  FROM system_health_metrics 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  GROUP BY system_component
),
weighted_health AS (
  SELECT *,
         (availability_score * 0.3 + performance_score * 0.25 + 
          error_score * 0.25 + resource_score * 0.2) overall_health_score
  FROM health_metrics 
  WHERE monitoring_days >= 5
)
SELECT system_component,
       ROUND(availability_score, 2) availability,
       ROUND(performance_score, 2) performance,
       ROUND(error_score, 2) error_management,
       ROUND(resource_score, 2) resource_efficiency,
       ROUND(overall_health_score, 2) health_score,
       CASE 
         WHEN overall_health_score >= 90 THEN 'EXCELLENT'
         WHEN overall_health_score >= 80 THEN 'GOOD'
         WHEN overall_health_score >= 70 THEN 'FAIR'
         WHEN overall_health_score >= 60 THEN 'POOR'
         ELSE 'CRITICAL'
       END health_grade
FROM weighted_health 
ORDER BY overall_health_score DESC;
```

### 88. 运营效率分析
**Description**: 分析运营效率指标
```sql
-- 目的: 分析运营效率指标 | 复杂度: 高级 | 炎凰特性: 效率计算/时间分析 | 类型: SELECT查询
WITH operational_metrics AS (
  SELECT department, process_name,
         COUNT(*) total_tasks,
         COUNT(CASE WHEN task_status = 'COMPLETED' THEN 1 END) completed_tasks,
         AVG(DATE_DIFF('h', task_start_time, task_end_time)) avg_completion_hours,
         SUM(resource_cost) total_cost,
         COUNT(CASE WHEN requires_manual_intervention = true THEN 1 END) manual_interventions
  FROM operational_tasks 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
  GROUP BY department, process_name
)
SELECT department, process_name,
       total_tasks, completed_tasks,
       completed_tasks * 100.0 / total_tasks completion_rate,
       avg_completion_hours,
       total_cost / NULLIF(completed_tasks, 0) cost_per_completed_task,
       manual_interventions * 100.0 / total_tasks manual_intervention_rate,
       CASE 
         WHEN completion_rate >= 95 AND manual_intervention_rate <= 10 THEN 'HIGHLY_EFFICIENT'
         WHEN completion_rate >= 85 AND manual_intervention_rate <= 25 THEN 'EFFICIENT'
         WHEN completion_rate >= 70 THEN 'MODERATELY_EFFICIENT'
         ELSE 'INEFFICIENT'
       END efficiency_rating
FROM operational_metrics 
WHERE total_tasks > 10
ORDER BY efficiency_rating DESC, completion_rate DESC;
```

### 89. 智能运维分析
**Description**: 进行智能运维分析
```sql
-- 目的: AIOps智能运维分析 | 复杂度: 高级 | 炎凰特性: 预测分析/智能告警 | 类型: SELECT查询
WITH anomaly_patterns AS (
  SELECT service_name, anomaly_type,
         COUNT(*) anomaly_count,
         AVG(anomaly_score) avg_anomaly_score,
         COUNT(CASE WHEN prediction_accuracy > 0.8 THEN 1 END) accurate_predictions,
         AVG(time_to_resolution_minutes) avg_resolution_time
  FROM aiops_anomaly_detection 
  WHERE _time >= DATE_ADD('d', -14, NOW()) AND _time < NOW()
  GROUP BY service_name, anomaly_type
),
prediction_effectiveness AS (
  SELECT *,
         accurate_predictions * 100.0 / anomaly_count prediction_accuracy_rate,
         CASE 
           WHEN avg_anomaly_score > 0.8 AND accurate_predictions * 100.0 / anomaly_count > 80 THEN 'HIGH_CONFIDENCE'
           WHEN avg_anomaly_score > 0.6 AND accurate_predictions * 100.0 / anomaly_count > 60 THEN 'MEDIUM_CONFIDENCE'
           ELSE 'LOW_CONFIDENCE'
         END prediction_confidence
  FROM anomaly_patterns
)
SELECT service_name, anomaly_type,
       anomaly_count, avg_anomaly_score,
       prediction_accuracy_rate, avg_resolution_time,
       prediction_confidence,
       CASE 
         WHEN prediction_confidence = 'HIGH_CONFIDENCE' AND avg_resolution_time < 30 THEN 'EXCELLENT_AIOPS'
         WHEN prediction_confidence = 'MEDIUM_CONFIDENCE' AND avg_resolution_time < 60 THEN 'GOOD_AIOPS'
         ELSE 'NEEDS_IMPROVEMENT'
       END aiops_effectiveness
FROM prediction_effectiveness 
ORDER BY prediction_accuracy_rate DESC, avg_anomaly_score DESC;
```

### 90. 数字化转型指标
**Description**: 评估数字化转型进展
```sql
-- 目的: 评估数字化转型进展 | 复杂度: 高级 | 炎凰特性: 转型指标/综合评估 | 类型: SELECT查询
WITH transformation_metrics AS (
  SELECT metric_category, metric_name,
         current_value, target_value, baseline_value,
         measurement_unit,
         LATEST_VALUE(_time) last_updated
  FROM digital_transformation_kpis 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
),
progress_calculation AS (
  SELECT *,
         CASE 
           WHEN target_value > baseline_value THEN 
             (current_value - baseline_value) * 100.0 / NULLIF(target_value - baseline_value, 0)
           WHEN target_value < baseline_value THEN 
             (baseline_value - current_value) * 100.0 / NULLIF(baseline_value - target_value, 0)
           ELSE 100
         END progress_percentage
  FROM transformation_metrics
)
SELECT metric_category, metric_name,
       current_value, target_value, baseline_value,
       ROUND(progress_percentage, 2) progress_percentage,
       CASE 
         WHEN progress_percentage >= 100 THEN 'TARGET_ACHIEVED'
         WHEN progress_percentage >= 80 THEN 'ON_TRACK'
         WHEN progress_percentage >= 50 THEN 'MODERATE_PROGRESS'
         WHEN progress_percentage >= 20 THEN 'SLOW_PROGRESS'
         ELSE 'BEHIND_SCHEDULE'
       END progress_status,
       measurement_unit,
       last_updated
FROM progress_calculation 
ORDER BY metric_category, progress_percentage DESC;
```

### 91. 数组数据处理分析
**Description**: 处理和分析数组类型的数据
```sql
-- 目的: 展示数组处理功能 | 复杂度: 高级 | 炎凰特性: 数组函数族 | 类型: SELECT查询
SELECT user_id, user_tags, user_interests,
       ARRAY_LENGTH(user_tags) tag_count,
       ARRAY_LENGTH(user_interests) interest_count,
       ARRAY_CONTAINS(user_tags, 'premium') is_premium,
       ARRAY_CONTAINS(user_interests, 'technology') likes_tech,
       ARRAY_INTERSECT(user_tags, ARRAY['vip', 'premium', 'gold']) premium_tags,
       ARRAY_APPEND(user_interests, 'data_analysis') enhanced_interests,
       ARRAY_DISTINCT(ARRAY_CAT(user_tags, user_interests)) combined_attributes,
       ARRAY_AT(user_tags, 0) primary_tag,
       ARRAY_POSITION(user_interests, 'sports') sports_position
FROM user_profiles 
WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
  AND ARRAY_LENGTH(user_tags) > 0
  AND ARRAY_LENGTH(user_interests) > 0
ORDER BY tag_count DESC, interest_count DESC LIMIT 500;
```

### 92. 正则表达式模式匹配
**Description**: 使用正则表达式进行模式匹配
```sql
-- 目的: 展示正则表达式功能 | 复杂度: 高级 | 炎凰特性: 正则匹配 | 类型: SELECT查询
SELECT log_message, log_level, service_name,
       CASE 
         WHEN REGEX_LIKE(log_message, '^ERROR.*SQLException.*', 'i') THEN 'DATABASE_ERROR'
         WHEN REGEX_LIKE(log_message, '^WARN.*timeout.*', 'i') THEN 'TIMEOUT_WARNING'
         WHEN REGEX_LIKE(log_message, '^INFO.*started.*in.*ms', 'i') THEN 'STARTUP_INFO'
         WHEN REGEX_LIKE(log_message, '.*[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}.*') THEN 'CONTAINS_IP'
         WHEN REGEX_LIKE(log_message, '.*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}.*') THEN 'CONTAINS_EMAIL'
         ELSE 'GENERAL_LOG'
       END log_pattern,
       COUNT(*) pattern_count,
       EARLIEST_VALUE(_time) first_occurrence,
       LATEST_VALUE(_time) last_occurrence
FROM application_logs 
WHERE _time >= DATE_ADD('h', -12, NOW()) AND _time < NOW()
GROUP BY log_message, log_level, service_name, log_pattern
HAVING pattern_count > 5
ORDER BY pattern_count DESC LIMIT 200;
```

### 93. 地理信息分析
**Description**: 分析地理位置相关信息
```sql
-- 目的: 展示地理信息功能 | 复杂度: 高级 | 炎凰特性: IP地理分析 | 类型: SELECT查询
WITH geo_analytics AS (
  SELECT s.event_id, s.user_id, s.source_ip,
         loc.country, loc.region, loc.city, loc.isp,
         loc.latitude, loc.longitude,
         s.event_type, s.event_value
  FROM user_events s
  OUTER APPLY ip_location(s.source_ip, true) AS loc
  WHERE s._time >= DATE_ADD('d', -7, NOW()) AND s._time < NOW()
    AND IS_IPV4(s.source_ip) = true
)
SELECT country, region, city,
       COUNT(*) total_events,
       COUNT(DISTINCT user_id) unique_users,
       COUNT(DISTINCT source_ip) unique_ips,
       AVG(event_value) avg_event_value,
       CASE 
         WHEN country IN ('United States', 'Canada', 'United Kingdom') THEN 'TIER_1'
         WHEN country IN ('Germany', 'France', 'Japan', 'Australia') THEN 'TIER_2'
         ELSE 'TIER_3'
       END country_tier,
       FIRST_VALUE(latitude) OVER (PARTITION BY country ORDER BY total_events DESC) country_lat,
       FIRST_VALUE(longitude) OVER (PARTITION BY country ORDER BY total_events DESC) country_lng
FROM geo_analytics 
WHERE country IS NOT NULL
GROUP BY country, region, city
HAVING total_events > 100
ORDER BY total_events DESC LIMIT 200;
```

### 94. 时间序列预测分析
**Description**: 进行时间序列预测分析
```sql
-- 目的: 时间序列预测分析 | 复杂度: 高级 | 炎凰特性: 时间序列/趋势预测 | 类型: SELECT查询
WITH time_series_data AS (
  SELECT TIME_BUCKET('1h', _time) hour_bucket,
         metric_name,
         AVG(metric_value) avg_value
  FROM time_series_metrics 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND metric_name IN ('cpu_usage', 'memory_usage', 'request_rate')
  GROUP BY hour_bucket, metric_name
),
trend_analysis AS (
  SELECT metric_name,
         hour_bucket,
         avg_value,
         LAG(avg_value, 1) OVER (PARTITION BY metric_name ORDER BY hour_bucket) prev_1h,
         LAG(avg_value, 24) OVER (PARTITION BY metric_name ORDER BY hour_bucket) prev_24h,
         LAG(avg_value, 168) OVER (PARTITION BY metric_name ORDER BY hour_bucket) prev_1w,
         AVG(avg_value) OVER (PARTITION BY metric_name ORDER BY hour_bucket ROWS 23 PRECEDING) ma_24h
  FROM time_series_data
),
forecasting AS (
  SELECT *,
         (avg_value - prev_1h) hourly_change,
         (avg_value - prev_24h) daily_change,
         (avg_value - prev_1w) weekly_change,
         avg_value + (avg_value - ma_24h) * 0.8 next_hour_prediction
  FROM trend_analysis 
  WHERE prev_1w IS NOT NULL
)
SELECT metric_name,
       COUNT(*) data_points,
       AVG(hourly_change) avg_hourly_change,
       AVG(daily_change) avg_daily_change,
       AVG(weekly_change) avg_weekly_change,
       LATEST_VALUE(avg_value) current_value,
       LATEST_VALUE(next_hour_prediction) predicted_next_hour,
       CASE 
         WHEN AVG(weekly_change) > 10 THEN 'GROWING_TREND'
         WHEN AVG(weekly_change) < -10 THEN 'DECLINING_TREND'
         ELSE 'STABLE_TREND'
       END trend_direction
FROM forecasting 
GROUP BY metric_name
ORDER BY ABS(avg_weekly_change) DESC;
```

### 95. 概率统计分析
**Description**: 进行概率统计分析
```sql
-- 目的: 概率统计分析 | 复杂度: 高级 | 炎凰特性: 统计函数 | 类型: SELECT查询
WITH statistical_data AS (
  SELECT experiment_group, user_id, conversion_value,
         CASE WHEN conversion_value > 0 THEN 1 ELSE 0 END converted
  FROM ab_test_results 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND experiment_name = 'checkout_optimization'
),
group_statistics AS (
  SELECT experiment_group,
         COUNT(*) sample_size,
         COUNT(CASE WHEN converted = 1 THEN 1 END) conversions,
         AVG(converted) conversion_rate,
         AVG(conversion_value) avg_conversion_value,
         STDDEV_POP(conversion_value) stddev_conversion_value,
         PERCENTILE(conversion_value, 0.5) median_conversion_value,
         PERCENTILE(conversion_value, 0.95) p95_conversion_value
  FROM statistical_data 
  GROUP BY experiment_group
)
SELECT experiment_group,
       sample_size, conversions, 
       ROUND(conversion_rate * 100, 2) conversion_rate_percent,
       ROUND(avg_conversion_value, 2) avg_value,
       ROUND(stddev_conversion_value, 2) value_stddev,
       median_conversion_value, p95_conversion_value,
       ROUND(stddev_conversion_value / NULLIF(avg_conversion_value, 0), 2) coefficient_of_variation,
       CASE 
         WHEN conversion_rate > 0.05 AND sample_size > 1000 THEN 'STATISTICALLY_SIGNIFICANT'
         WHEN sample_size > 500 THEN 'MODERATELY_SIGNIFICANT'
         ELSE 'INSUFFICIENT_DATA'
       END significance_level
FROM group_statistics 
ORDER BY conversion_rate DESC;
```

### 96. 数据生成测试分析
**Description**: 生成测试数据进行分析
```sql
-- 目的: 使用generate_series生成测试数据 | 复杂度: 简单 | 炎凰特性: 数据生成 | 类型: SELECT查询
WITH generated_dates AS (
  SELECT DATE_ADD('d', generate_series, TIMESTAMP '2024-01-01 00:00:00') test_date
  FROM generate_series(0, 90, 1)
),
simulated_metrics AS (
  SELECT test_date,
         EXTRACT(dow FROM test_date) day_of_week,
         RAND(HASH(test_date)) * 1000 + 500 simulated_revenue,
         RAND(HASH(test_date) + 1) * 100 + 50 simulated_users,
         CASE 
           WHEN EXTRACT(dow FROM test_date) IN (0, 6) THEN 'WEEKEND'
           ELSE 'WEEKDAY'
         END day_type
  FROM generated_dates
)
SELECT day_type,
       COUNT(*) total_days,
       AVG(simulated_revenue) avg_revenue,
       AVG(simulated_users) avg_users,
       MIN(simulated_revenue) min_revenue,
       MAX(simulated_revenue) max_revenue,
       STDDEV_POP(simulated_revenue) revenue_stddev
FROM simulated_metrics 
GROUP BY day_type
ORDER BY avg_revenue DESC;
```

### 97. 多值字段展开分析
**Description**: 展开多值字段进行分析
```sql
-- 目的: 使用flatten展开多值字段 | 复杂度: 高级 | 炎凰特性: 数组展开 | 类型: SELECT查询
WITH user_skill_data AS (
  SELECT user_id, user_name, skill_array
  FROM user_profiles 
  WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
    AND ARRAY_LENGTH(skill_array) > 0
),
flattened_skills AS (
  SELECT usd.user_id, usd.user_name, fs.skill_name
  FROM user_skill_data usd
  CROSS APPLY flatten(usd.skill_array) AS fs(skill_name)
)
SELECT skill_name,
       COUNT(*) skill_count,
       COUNT(DISTINCT user_id) users_with_skill,
       COLLECT_LIST(user_name) sample_users,
       skill_count * 100.0 / (SELECT COUNT(DISTINCT user_id) FROM flattened_skills) skill_percentage
FROM flattened_skills 
GROUP BY skill_name
HAVING skill_count > 5
ORDER BY skill_count DESC LIMIT 50;
```

### 98. 加密哈希安全分析
**Description**: 使用哈希加密进行安全分析
```sql
-- 目的: 展示加密哈希功能 | 复杂度: 高级 | 炎凰特性: 哈希加密 | 类型: SELECT查询
SELECT file_path, file_name,
       HASH_MD5(file_content) md5_hash,
       HASH_SHA1(file_content) sha1_hash,
       HASH_SHA256(file_content) sha256_hash,
       CRC32(file_content) crc32_checksum,
       HASH(file_path) path_hash,
       file_size,
       COUNT(*) OVER (PARTITION BY HASH_SHA256(file_content)) duplicate_count,
       CASE 
         WHEN COUNT(*) OVER (PARTITION BY HASH_SHA256(file_content)) > 1 THEN 'DUPLICATE_DETECTED'
         WHEN file_size = 0 THEN 'EMPTY_FILE'
         WHEN REGEX_LIKE(file_name, '.*\\.(exe|dll|bat)$', 'i') THEN 'EXECUTABLE_FILE'
         ELSE 'NORMAL_FILE'
       END file_classification
FROM file_security_scan 
WHERE _time >= DATE_ADD('h', -12, NOW()) AND _time < NOW()
ORDER BY file_size DESC, duplicate_count DESC LIMIT 500;
```

### 99. URL完整解析分析
**Description**: 完整解析URL地址信息
```sql
-- 目的: 展示URL解析功能族 | 复杂度: 高级 | 炎凰特性: URL函数族 | 类型: SELECT查询
SELECT request_url,
       PROTOCOL(request_url) url_protocol,
       NETLOC(request_url) network_location,
       DOMAIN(request_url) domain_name,
       TOP_LEVEL_DOMAIN(request_url) tld,
       PORT(request_url) port_number,
       PATH(request_url) url_path,
       QUERY_STRING(request_url) query_parameters,
       FRAGMENT(request_url) url_fragment,
       CUT_WWW(DOMAIN(request_url)) domain_without_www,
       CUT_QUERY_STRING(request_url) url_without_params,
       IS_VALID_URL(request_url) is_valid,
       COUNT(*) request_count
FROM web_access_logs 
WHERE _time >= DATE_ADD('d', -3, NOW()) AND _time < NOW()
  AND request_url IS NOT NULL
GROUP BY request_url, url_protocol, network_location, domain_name, tld, 
         port_number, url_path, query_parameters, url_fragment, 
         domain_without_www, url_without_params, is_valid
HAVING request_count > 10
ORDER BY request_count DESC LIMIT 200;
```

### 100. 综合查询性能优化
**Description**: 优化查询性能
```sql
-- 目的: 展示查询性能优化技巧 | 复杂度: 高级 | 炎凰特性: 性能优化 | 类型: SELECT查询
WITH optimized_base_query AS (
  SELECT TIME_BUCKET('10m', _time) time_bucket,
         service_name, user_tier,
         COUNT(*) request_count,
         APPROX_COUNT_DISTINCT(user_id) approx_unique_users,
         PERCENTILE(response_time, 0.95) p95_response_time,
         LATEST_VALUE(server_region) current_region
  FROM performance_logs 
  WHERE _time >= DATE_ADD('h', -6, NOW()) AND _time < NOW()
    AND service_name IN ('api-gateway', 'user-service', 'payment-service')
    AND response_time > 0
  GROUP BY time_bucket, service_name, user_tier
),
performance_analysis AS (
  SELECT *,
         LAG(request_count) OVER (PARTITION BY service_name ORDER BY time_bucket) prev_request_count,
         AVG(p95_response_time) OVER (PARTITION BY service_name ORDER BY time_bucket ROWS 5 PRECEDING) ma_response_time
  FROM optimized_base_query
),
final_metrics AS (
  SELECT service_name, user_tier,
         SUM(request_count) total_requests,
         AVG(approx_unique_users) avg_unique_users,
         MAX(p95_response_time) peak_response_time,
         AVG(ma_response_time) avg_ma_response_time,
         FIRST_VALUE(current_region) OVER (PARTITION BY service_name ORDER BY time_bucket DESC) latest_region
  FROM performance_analysis 
  WHERE prev_request_count IS NOT NULL
  GROUP BY service_name, user_tier
)
SELECT service_name, user_tier, latest_region,
       total_requests, avg_unique_users,
       ROUND(peak_response_time, 2) peak_response_ms,
       ROUND(avg_ma_response_time, 2) avg_response_ms,
       total_requests / NULLIF(avg_unique_users, 0) requests_per_user,
       CASE 
         WHEN peak_response_time > 2000 THEN 'PERFORMANCE_ISSUE'
         WHEN avg_ma_response_time > 1000 THEN 'SLOW_RESPONSE'
         WHEN total_requests / NULLIF(avg_unique_users, 0) > 100 THEN 'HIGH_ACTIVITY'
         ELSE 'NORMAL'
       END performance_status
FROM final_metrics 
ORDER BY total_requests DESC, peak_response_time DESC 
LIMIT 100;
``` 

# 炎凰数据SQL样例集 - 第五批(101-125)

## 语言变体与优化场景 (101-125)

### 101. 同义词查询变体 - 销售数据分析
**Description**: 帮我查看销售数据，包括营收、收入、销售额等信息
```sql
-- 目的: 展示同一查询的不同自然语言表达 | 复杂度: 简单 | 炎凰特性: 时间分桶 | 类型: SELECT查询
-- 用户可能的表达：营收/收入/销售额/成交金额/订单总额
SELECT TIME_BUCKET('1d', _time) day_bucket,
       SUM(amount) total_revenue,
       COUNT(*) order_volume,
       AVG(amount) average_order_value
FROM orders 
WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  AND amount > 0
GROUP BY day_bucket
ORDER BY day_bucket DESC;
```

### 102. 时间表达变体 - 用户活跃度
**Description**: 我想看最近一周、过去7天、近期的用户活跃情况
```sql
-- 目的: 处理多种时间表达方式 | 复杂度: 简单 | 炎凰特性: 时间处理 | 类型: SELECT查询
-- 用户可能的表达：最近一周/过去7天/近7日/上周至今/7天内
SELECT DATE(_time) activity_date,
       COUNT(DISTINCT user_id) daily_active_users,
       COUNT(*) total_events
FROM user_events 
WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  AND event_type IN ('login', 'page_view', 'action')
GROUP BY DATE(_time)
ORDER BY activity_date DESC;
```

### 103. 空结果集处理 - 新产品销售
**Description**: 查询新产品的销售情况，如果没有数据也要显示
```sql
-- 目的: 处理可能无数据的查询场景 | 复杂度: 高级 | 炎凰特性: 条件聚合/默认值 | 类型: SELECT查询
SELECT product_category,
       COALESCE(SUM(sales_amount), 0) total_sales,
       COALESCE(COUNT(*), 0) order_count,
       COALESCE(AVG(sales_amount), 0) avg_order_value,
       CASE 
         WHEN COUNT(*) = 0 THEN 'NO_SALES'
         WHEN COUNT(*) < 5 THEN 'LOW_VOLUME'
         ELSE 'NORMAL'
       END sales_status
FROM product_sales 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
  AND product_launch_date >= DATE_ADD('d', -30, NOW())
GROUP BY product_category
ORDER BY total_sales DESC;
```

### 104. 数据类型边界处理 - 极值分析
**Description**: 分析数据中的极值和边界情况
```sql
-- 目的: 处理数据类型边界和极值 | 复杂度: 高级 | 炎凰特性: 统计分析/边界检查 | 类型: SELECT查询
WITH value_bounds AS (
  SELECT metric_name,
         MIN(metric_value) min_value,
         MAX(metric_value) max_value,
         AVG(metric_value) avg_value,
         STDDEV_POP(metric_value) stddev_value,
         COUNT(*) sample_count
  FROM system_metrics 
  WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
    AND metric_value IS NOT NULL
    AND metric_value >= 0  -- 排除负值异常
    AND metric_value < 999999999  -- 排除超大异常值
  GROUP BY metric_name
)
SELECT metric_name,
       min_value, max_value, avg_value,
       CASE 
         WHEN max_value > (avg_value + 5 * stddev_value) THEN 'EXTREME_HIGH'
         WHEN min_value < (avg_value - 5 * stddev_value) THEN 'EXTREME_LOW'
         WHEN stddev_value / NULLIF(avg_value, 0) > 2 THEN 'HIGH_VARIANCE'
         ELSE 'NORMAL_RANGE'
       END value_status,
       sample_count
FROM value_bounds 
WHERE sample_count > 10
ORDER BY stddev_value / NULLIF(avg_value, 0) DESC;
```

### 105. 时间格式容错处理 - 日志查询
**Description**: 查询日志信息，兼容不同的时间格式
```sql
-- 目的: 展示时间格式兼容性处理 | 复杂度: 高级 | 炎凰特性: 时间转换 | 类型: SELECT查询
SELECT log_level,
       TIME_BUCKET('1h', _time) hour_bucket,
       COUNT(*) log_count,
       COUNT(DISTINCT source_service) unique_services,
       LATEST_VALUE(log_message) latest_message
FROM application_logs 
WHERE _time >= CASE 
  WHEN CHAR_LENGTH('2024-01-01') = 10 THEN TIMESTAMP '2024-01-01 00:00:00'
  ELSE DATE_ADD('d', -1, NOW())
END 
AND _time < NOW()
AND log_level IS NOT NULL
GROUP BY log_level, hour_bucket
ORDER BY hour_bucket DESC, log_count DESC
LIMIT 100;
```

### 106. JOIN条件优化 - 用户订单关联
**Description**: 优化用户和订单的关联查询性能
```sql
-- 目的: 展示高效JOIN写法 | 复杂度: 高级 | 炎凰特性: 优化查询/聚合增强 | 类型: SELECT查询
SELECT u.user_tier, u.registration_region,
       COUNT(o.order_id) total_orders,
       COALESCE(SUM(o.order_amount), 0) total_spent,
       COALESCE(AVG(o.order_amount), 0) avg_order_value,
       EARLIEST_VALUE(o._time) first_order_time,
       LATEST_VALUE(o._time) latest_order_time
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id 
  AND o._time >= DATE_ADD('d', -90, NOW()) 
  AND o._time < NOW()
  AND o.order_status = 'completed'
WHERE u.registration_date >= DATE_ADD('d', -365, NOW())
  AND u.account_status = 'active'
GROUP BY u.user_tier, u.registration_region
HAVING COUNT(o.order_id) > 0  -- 只显示有订单的用户
ORDER BY total_spent DESC
LIMIT 50;
```

### 107. 复杂条件组合 - 安全事件关联
**Description**: 结合多种安全分析功能进行威胁检测
```sql
-- 目的: 多个炎凰特色功能组合使用 | 复杂度: 高级 | 炎凰特性: IP分析/URL解析/哈希 | 类型: SELECT查询
WITH threat_analysis AS (
  SELECT event_id, source_ip, request_url, user_agent,
         HASH_MD5(user_agent) ua_hash,
         DOMAIN(request_url) target_domain,
         PATH(request_url) request_path,
         ip_loc.country source_country,
         ip_loc.isp source_isp
  FROM security_events se
  OUTER APPLY ip_location(se.source_ip) AS ip_loc
  WHERE se._time >= DATE_ADD('h', -6, NOW()) AND se._time < NOW()
    AND IS_IPV4(se.source_ip) = true
    AND se.event_type = 'web_request'
),
risk_scoring AS (
  SELECT *,
         CASE 
           WHEN source_country IN ('CN', 'RU', 'IR') THEN 3
           WHEN source_country IS NULL THEN 2
           ELSE 0
         END country_risk_score,
         CASE 
           WHEN REGEX_LIKE(request_path, '.*(admin|config|wp-admin).*', 'i') THEN 5
           WHEN REGEX_LIKE(request_path, '.*(sql|script|eval).*', 'i') THEN 4
           ELSE 0
         END path_risk_score,
         CASE 
           WHEN CONTAINS(LOWER(user_agent), 'bot') OR CONTAINS(LOWER(user_agent), 'crawler') THEN 2
           WHEN CHAR_LENGTH(user_agent) < 10 THEN 3
           ELSE 0
         END ua_risk_score
  FROM threat_analysis
)
SELECT source_ip, target_domain, source_country,
       COUNT(*) request_count,
       COUNT(DISTINCT request_path) unique_paths,
       MAX(country_risk_score + path_risk_score + ua_risk_score) max_risk_score,
       AVG(country_risk_score + path_risk_score + ua_risk_score) avg_risk_score,
       COLLECT_LIST(DISTINCT request_path) sample_paths
FROM risk_scoring 
GROUP BY source_ip, target_domain, source_country
HAVING COUNT(*) > 5 OR MAX(country_risk_score + path_risk_score + ua_risk_score) > 5
ORDER BY max_risk_score DESC, request_count DESC
LIMIT 100;
```

### 108. 大数据量分页优化 - 历史订单查询
**Description**: 高效查询大量历史订单数据并分页显示
```sql
-- 目的: 展示分页查询最佳实践 | 复杂度: 高级 | 炎凰特性: 性能优化 | 类型: SELECT查询
WITH ordered_data AS (
  SELECT order_id, user_id, order_amount, order_date,
         ROW_NUMBER() OVER (ORDER BY order_date DESC, order_id DESC) row_num
  FROM orders 
  WHERE _time >= DATE_ADD('M', -6, NOW()) AND _time < NOW()
    AND order_status = 'completed'
    AND order_amount > 0
)
SELECT order_id, user_id, order_amount, order_date
FROM ordered_data 
WHERE row_num BETWEEN 1001 AND 1050  -- 第21页，每页50条
ORDER BY order_date DESC, order_id DESC;
```

### 109. 索引友好查询 - 用户行为分析
**Description**: 设计对索引友好的用户行为查询
```sql
-- 目的: 展示索引友好的查询写法 | 复杂度: 高级 | 炎凰特性: 查询优化 | 类型: SELECT查询
SELECT DATE(_time) event_date,
       event_type, user_segment,
       COUNT(*) event_count,
       COUNT(DISTINCT user_id) unique_users,
       APPROX_COUNT_DISTINCT(session_id) approx_sessions
FROM user_events 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()  -- 时间索引优先
  AND user_segment IN ('premium', 'vip', 'enterprise')  -- 枚举值过滤
  AND event_type IS NOT NULL  -- 避免NULL值处理
GROUP BY DATE(_time), event_type, user_segment
ORDER BY event_date DESC, event_count DESC
LIMIT 500;
```

### 110. 内存优化子查询 - 产品推荐分析
**Description**: 优化产品推荐分析的内存使用
```sql
-- 目的: 优化内存使用的子查询设计 | 复杂度: 高级 | 炎凰特性: 子查询优化 | 类型: SELECT查询
WITH top_products AS (
  SELECT product_id, SUM(quantity) total_sales
  FROM order_items 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
  GROUP BY product_id
  ORDER BY total_sales DESC
  LIMIT 100  -- 限制子查询结果集大小
),
user_preferences AS (
  SELECT oi.user_id, tp.product_id, SUM(oi.quantity) user_product_quantity
  FROM order_items oi
  INNER JOIN top_products tp ON oi.product_id = tp.product_id  -- 只关联热门产品
  WHERE oi._time >= DATE_ADD('d', -30, NOW()) AND oi._time < NOW()
  GROUP BY oi.user_id, tp.product_id
  HAVING SUM(oi.quantity) > 0
)
SELECT user_id,
       COUNT(DISTINCT product_id) purchased_hot_products,
       SUM(user_product_quantity) total_hot_product_quantity,
       AVG(user_product_quantity) avg_quantity_per_product
FROM user_preferences 
GROUP BY user_id
HAVING COUNT(DISTINCT product_id) >= 3  -- 至少购买3种热门产品
ORDER BY purchased_hot_products DESC
LIMIT 200;
```

### 111. 错误模式修正 - 时间范围查询
**Description**: 正确处理时间范围查询，避免性能问题
```sql
-- 目的: 展示常见错误的正确写法 | 复杂度: 简单 | 炎凰特性: 时间处理正确性 | 类型: SELECT查询
-- 错误模式：WHERE DATE(_time) = '2024-01-01'  (低效)
-- 正确模式：使用时间范围查询
SELECT service_name, operation_type,
       COUNT(*) operation_count,
       AVG(execution_time) avg_execution_time,
       MAX(execution_time) max_execution_time
FROM service_operations 
WHERE _time >= TIMESTAMP '2024-01-01 00:00:00' 
  AND _time < TIMESTAMP '2024-01-02 00:00:00'  -- 正确的时间范围
  AND execution_time > 0
GROUP BY service_name, operation_type
ORDER BY avg_execution_time DESC;
```

### 112. NULL值处理最佳实践 - 用户档案分析
**Description**: 安全处理用户档案中的空值情况
```sql
-- 目的: 展示NULL值处理最佳实践 | 复杂度: 高级 | 炎凰特性: 条件处理/默认值 | 类型: SELECT查询
SELECT user_id,
       COALESCE(user_name, 'UNKNOWN_USER') display_name,
       COALESCE(user_tier, 'BASIC') user_tier,
       COALESCE(registration_source, 'ORGANIC') acquisition_channel,
       CASE 
         WHEN last_login_time IS NULL THEN 'NEVER_LOGGED_IN'
         WHEN last_login_time < DATE_ADD('d', -30, NOW()) THEN 'INACTIVE'
         WHEN last_login_time < DATE_ADD('d', -7, NOW()) THEN 'DORMANT'
         ELSE 'ACTIVE'
       END user_status,
       COALESCE(total_orders, 0) order_count,
       COALESCE(total_spent, 0.00) lifetime_value,
       CASE 
         WHEN user_tags IS NULL OR ARRAY_LENGTH(user_tags) = 0 THEN false
         ELSE ARRAY_CONTAINS(user_tags, 'high_value')
       END is_high_value
FROM user_profiles 
WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
  AND (account_status IS NULL OR account_status = 'active')  -- 包含NULL作为有效状态
ORDER BY lifetime_value DESC NULLS LAST  -- NULL值排在最后
LIMIT 1000;
```

### 113. 数组操作边界处理 - 用户技能分析
**Description**: 安全处理用户技能数组数据的边界情况
```sql
-- 目的: 数组操作的安全边界处理 | 复杂度: 高级 | 炎凰特性: 数组安全操作 | 类型: SELECT查询
SELECT user_id,
       CASE 
         WHEN user_skills IS NULL THEN 0
         ELSE ARRAY_LENGTH(user_skills)
       END skill_count,
       CASE 
         WHEN user_skills IS NULL OR ARRAY_LENGTH(user_skills) = 0 THEN 'NO_SKILLS'
         WHEN ARRAY_LENGTH(user_skills) <= 3 THEN 'BEGINNER'
         WHEN ARRAY_LENGTH(user_skills) <= 7 THEN 'INTERMEDIATE'
         ELSE 'EXPERT'
       END skill_level,
       CASE 
         WHEN user_skills IS NOT NULL AND ARRAY_LENGTH(user_skills) > 0 THEN
           ARRAY_AT(user_skills, 0)  -- 安全访问第一个元素
         ELSE NULL
       END primary_skill,
       CASE 
         WHEN user_skills IS NOT NULL AND ARRAY_CONTAINS(user_skills, 'python') THEN true
         ELSE false
       END has_python_skill,
       COALESCE(skill_verification_date, DATE_ADD('y', -10, NOW())) last_verification
FROM user_skill_profiles 
WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
ORDER BY skill_count DESC, last_verification DESC
LIMIT 500;
```

### 114. 字符串处理边界 - 日志消息分析
**Description**: 安全处理日志消息的字符串边界情况
```sql
-- 目的: 字符串处理边界和容错 | 复杂度: 高级 | 炎凰特性: 字符串安全处理 | 类型: SELECT查询
SELECT log_level,
       CASE 
         WHEN log_message IS NULL THEN 'EMPTY_MESSAGE'
         WHEN CHAR_LENGTH(log_message) = 0 THEN 'EMPTY_MESSAGE'
         WHEN CHAR_LENGTH(log_message) > 1000 THEN 
           CONCAT(SUBSTRING(log_message, 1, 997), '...')  -- 截断长消息
         ELSE log_message
       END processed_message,
       CASE 
         WHEN log_message IS NOT NULL AND CHAR_LENGTH(log_message) > 0 THEN
           CHAR_LENGTH(log_message)
         ELSE 0
       END message_length,
       CASE 
         WHEN log_message IS NOT NULL AND CONTAINS(UPPER(log_message), 'ERROR') THEN 'ERROR'
         WHEN log_message IS NOT NULL AND CONTAINS(UPPER(log_message), 'WARN') THEN 'WARNING'
         WHEN log_message IS NOT NULL AND CONTAINS(UPPER(log_message), 'INFO') THEN 'INFO'
         ELSE 'UNKNOWN'
       END message_type,
       COUNT(*) message_count
FROM application_logs 
WHERE _time >= DATE_ADD('h', -12, NOW()) AND _time < NOW()
GROUP BY log_level, processed_message, message_length, message_type
HAVING COUNT(*) > 1  -- 过滤单次出现的消息
ORDER BY message_count DESC
LIMIT 200;
```

### 115. 窗口函数性能优化 - 销售排名
**Description**: 优化销售排名的窗口函数性能
```sql
-- 目的: 窗口函数的性能优化技巧 | 复杂度: 高级 | 炎凰特性: 窗口函数优化 | 类型: SELECT查询
WITH daily_sales AS (
  SELECT DATE(_time) sale_date, salesperson_id, region,
         SUM(sale_amount) daily_total
  FROM sales_records 
  WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
    AND sale_amount > 0
    AND salesperson_id IS NOT NULL
  GROUP BY DATE(_time), salesperson_id, region
),
ranked_sales AS (
  SELECT sale_date, salesperson_id, region, daily_total,
         ROW_NUMBER() OVER (PARTITION BY sale_date, region ORDER BY daily_total DESC) daily_rank,
         ROW_NUMBER() OVER (PARTITION BY region ORDER BY daily_total DESC) overall_rank,
         AVG(daily_total) OVER (PARTITION BY salesperson_id ORDER BY sale_date ROWS 6 PRECEDING) ma_7day
  FROM daily_sales
)
SELECT salesperson_id, region,
       COUNT(*) active_days,
       AVG(daily_total) avg_daily_sales,
       AVG(daily_rank) avg_daily_rank,
       MIN(overall_rank) best_overall_rank,
       AVG(ma_7day) avg_7day_moving_average
FROM ranked_sales 
WHERE daily_rank <= 10  -- 只统计每日前10名的表现
GROUP BY salesperson_id, region
HAVING COUNT(*) >= 15  -- 至少活跃15天
ORDER BY avg_daily_sales DESC
LIMIT 50;
```

### 116. CTE嵌套优化 - 客户价值分析
**Description**: 优化客户价值分析的CTE嵌套结构
```sql
-- 目的: 展示合理的CTE嵌套深度 | 复杂度: 高级 | 炎凰特性: CTE结构优化 | 类型: SELECT查询
WITH base_orders AS (
  SELECT user_id, order_amount, order_date, product_category
  FROM orders 
  WHERE _time >= DATE_ADD('y', -1, NOW()) AND _time < NOW()
    AND order_status = 'completed'
    AND order_amount > 0
),
user_metrics AS (
  SELECT user_id,
         COUNT(*) total_orders,
         SUM(order_amount) total_spent,
         AVG(order_amount) avg_order_value,
         COUNT(DISTINCT product_category) category_diversity,
         EARLIEST_VALUE(order_date) first_order,
         LATEST_VALUE(order_date) last_order
  FROM base_orders 
  GROUP BY user_id
),
user_segments AS (
  SELECT *,
         DATE_DIFF('d', first_order, last_order) customer_lifespan,
         CASE 
           WHEN total_spent > 10000 THEN 'VIP'
           WHEN total_spent > 5000 THEN 'HIGH_VALUE'
           WHEN total_spent > 1000 THEN 'MEDIUM_VALUE'
           ELSE 'LOW_VALUE'
         END value_segment,
         CASE 
           WHEN DATE_DIFF('d', last_order, NOW()) <= 30 THEN 'ACTIVE'
           WHEN DATE_DIFF('d', last_order, NOW()) <= 90 THEN 'AT_RISK'
           ELSE 'CHURNED'
         END activity_segment
  FROM user_metrics
)
SELECT value_segment, activity_segment,
       COUNT(*) customer_count,
       AVG(total_spent) avg_customer_value,
       AVG(total_orders) avg_order_frequency,
       AVG(category_diversity) avg_category_diversity,
       COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () segment_percentage
FROM user_segments 
GROUP BY value_segment, activity_segment
ORDER BY avg_customer_value DESC;
```

### 117. IP地址处理优化 - 网络安全分析
**Description**: 优化网络安全分析中的IP地址处理性能
```sql
-- 目的: IP地址处理的性能优化 | 复杂度: 高级 | 炎凰特性: IP处理优化 | 类型: SELECT查询
WITH ip_analysis AS (
  SELECT source_ip,
         IP_TO_INT(source_ip) ip_numeric,  -- 预转换为数值便于比较
         COUNT(*) request_count,
         COUNT(DISTINCT target_port) unique_ports,
         COUNT(DISTINCT HOUR(_time)) active_hours
  FROM network_logs 
  WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
    AND IS_IPV4(source_ip) = true  -- 预过滤有效IP
    AND source_ip NOT IN ('127.0.0.1', '0.0.0.0')  -- 排除无效IP
  GROUP BY source_ip, IP_TO_INT(source_ip)
  HAVING COUNT(*) > 100  -- 预过滤低频IP
),
ip_geo_info AS (
  SELECT ia.*, 
         loc.country, loc.region, loc.city,
         CASE 
           WHEN ia.ip_numeric >= IP_TO_INT('10.0.0.0') AND ia.ip_numeric <= IP_TO_INT('10.255.255.255') THEN 'PRIVATE'
           WHEN ia.ip_numeric >= IP_TO_INT('172.16.0.0') AND ia.ip_numeric <= IP_TO_INT('172.31.255.255') THEN 'PRIVATE'
           WHEN ia.ip_numeric >= IP_TO_INT('192.168.0.0') AND ia.ip_numeric <= IP_TO_INT('192.168.255.255') THEN 'PRIVATE'
           ELSE 'PUBLIC'
         END ip_type
  FROM ip_analysis ia
  OUTER APPLY ip_location(ia.source_ip) AS loc
)
SELECT ip_type, country,
       COUNT(*) ip_count,
       SUM(request_count) total_requests,
       AVG(request_count) avg_requests_per_ip,
       AVG(unique_ports) avg_ports_per_ip,
       AVG(active_hours) avg_active_hours
FROM ip_geo_info 
WHERE ip_type = 'PUBLIC'  -- 关注公网IP
GROUP BY ip_type, country
ORDER BY total_requests DESC
LIMIT 50;
```

### 118. URL解析性能优化 - Web访问分析
**Description**: 优化Web访问分析中的URL解析性能
```sql
-- 目的: URL解析功能的高效使用 | 复杂度: 高级 | 炎凰特性: URL解析优化 | 类型: SELECT查询
WITH url_analysis AS (
  SELECT request_url,
         DOMAIN(request_url) domain,
         PATH(request_url) path,
         CASE 
           WHEN QUERY_STRING(request_url) IS NOT NULL AND CHAR_LENGTH(QUERY_STRING(request_url)) > 0 THEN true
           ELSE false
         END has_parameters,
         COUNT(*) access_count,
         COUNT(DISTINCT user_id) unique_visitors,
         AVG(response_time) avg_response_time
  FROM web_access_logs 
  WHERE _time >= DATE_ADD('h', -12, NOW()) AND _time < NOW()
    AND response_code < 500  -- 排除服务器错误
    AND request_url IS NOT NULL
    AND CHAR_LENGTH(request_url) > 0
    AND IS_VALID_URL(request_url) = true  -- 预过滤有效URL
  GROUP BY request_url, DOMAIN(request_url), PATH(request_url), has_parameters
  HAVING COUNT(*) > 10  -- 过滤低频URL
),
domain_stats AS (
  SELECT domain,
         COUNT(*) unique_urls,
         SUM(access_count) total_accesses,
         SUM(unique_visitors) total_visitors,
         AVG(avg_response_time) avg_domain_response_time,
         COUNT(CASE WHEN has_parameters THEN 1 END) * 100.0 / COUNT(*) param_usage_rate
  FROM url_analysis 
  GROUP BY domain
)
SELECT domain,
       unique_urls, total_accesses, total_visitors,
       ROUND(avg_domain_response_time, 2) avg_response_ms,
       ROUND(param_usage_rate, 2) parameter_usage_percent,
       total_accesses / NULLIF(unique_urls, 0) avg_accesses_per_url
FROM domain_stats 
WHERE total_accesses > 1000
ORDER BY total_accesses DESC
LIMIT 30;
```

### 119. 哈希函数应用优化 - 数据去重分析
**Description**: 优化数据去重分析中的哈希函数应用
```sql
-- 目的: 哈希函数的高效应用 | 复杂度: 高级 | 炎凰特性: 哈希函数优化 | 类型: SELECT查询
WITH content_hashing AS (
  SELECT content_id, content_text,
         HASH_MD5(content_text) content_md5,
         HASH_SHA256(content_text) content_sha256,
         CRC32(content_text) content_crc32,
         CHAR_LENGTH(content_text) content_length,
         upload_user_id, upload_time
  FROM user_content 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
    AND content_text IS NOT NULL
    AND CHAR_LENGTH(content_text) > 10  -- 过滤太短的内容
),
duplicate_analysis AS (
  SELECT content_md5,
         COUNT(*) duplicate_count,
         MIN(upload_time) first_upload,
         MAX(upload_time) last_upload,
         COUNT(DISTINCT upload_user_id) unique_uploaders,
         AVG(content_length) avg_length,
         FIRST_VALUE(content_id) OVER (PARTITION BY content_md5 ORDER BY upload_time) original_content_id
  FROM content_hashing 
  GROUP BY content_md5
  HAVING COUNT(*) > 1  -- 只分析重复内容
)
SELECT original_content_id,
       duplicate_count,
       unique_uploaders,
       DATE_DIFF('h', first_upload, last_upload) spread_duration_hours,
       avg_length,
       CASE 
         WHEN duplicate_count > 100 THEN 'VIRAL_CONTENT'
         WHEN duplicate_count > 10 THEN 'POPULAR_CONTENT'
         ELSE 'DUPLICATE_CONTENT'
       END content_type,
       CASE 
         WHEN unique_uploaders = 1 THEN 'SAME_USER'
         WHEN unique_uploaders * 1.0 / duplicate_count < 0.1 THEN 'FEW_USERS'
         ELSE 'MANY_USERS'
       END distribution_pattern
FROM duplicate_analysis 
ORDER BY duplicate_count DESC, spread_duration_hours ASC
LIMIT 100;
```

### 120. 聚合函数组合优化 - 业务指标计算
**Description**: 优化业务指标计算中的聚合函数组合
```sql
-- 目的: 聚合函数的高效组合使用 | 复杂度: 高级 | 炎凰特性: 聚合函数优化 | 类型: SELECT查询
WITH business_metrics AS (
  SELECT TIME_BUCKET('1h', _time) hour_bucket,
         business_unit, metric_category,
         SUM(metric_value) hourly_total,
         COUNT(*) data_points,
         AVG(metric_value) hourly_avg,
         MIN(metric_value) hourly_min,
         MAX(metric_value) hourly_max,
         STDDEV_POP(metric_value) hourly_stddev,
         PERCENTILE(metric_value, 0.5) hourly_median,
         PERCENTILE(metric_value, 0.95) hourly_p95,
         APPROX_COUNT_DISTINCT(source_system) unique_sources
  FROM business_metrics_raw 
  WHERE _time >= DATE_ADD('d', -3, NOW()) AND _time < NOW()
    AND metric_value IS NOT NULL
    AND metric_value >= 0
  GROUP BY hour_bucket, business_unit, metric_category
  HAVING COUNT(*) >= 10  -- 确保足够的数据点
),
metric_quality AS (
  SELECT *,
         CASE 
           WHEN hourly_stddev / NULLIF(hourly_avg, 0) > 2 THEN 'HIGH_VARIANCE'
           WHEN hourly_stddev / NULLIF(hourly_avg, 0) > 0.5 THEN 'MEDIUM_VARIANCE'
           ELSE 'LOW_VARIANCE'
         END variance_level,
         CASE 
           WHEN data_points < 20 THEN 'SPARSE'
           WHEN data_points < 100 THEN 'MODERATE'
           ELSE 'DENSE'
         END data_density
  FROM business_metrics
)
SELECT business_unit, metric_category,
       COUNT(*) reporting_hours,
       AVG(hourly_total) avg_hourly_total,
       MAX(hourly_max) peak_value,
       AVG(hourly_p95) avg_p95_value,
       AVG(data_points) avg_data_points_per_hour,
       MODE() WITHIN GROUP (ORDER BY variance_level) most_common_variance,
       AVG(unique_sources) avg_data_sources
FROM metric_quality 
GROUP BY business_unit, metric_category
ORDER BY avg_hourly_total DESC
LIMIT 50;
```

### 121. 时间序列性能优化 - 趋势分析
**Description**: 优化趋势分析中的时间序列查询性能
```sql
-- 目的: 时间序列查询的性能优化 | 复杂度: 高级 | 炎凰特性: 时间序列优化 | 类型: SELECT查询
WITH time_series_base AS (
  SELECT TIME_BUCKET('15m', _time) time_bucket,
         sensor_id, location,
         AVG(temperature) avg_temp,
         AVG(humidity) avg_humidity,
         COUNT(*) reading_count
  FROM sensor_readings 
  WHERE _time >= DATE_ADD('d', -7, NOW()) AND _time < NOW()
    AND sensor_id IS NOT NULL
    AND temperature BETWEEN -50 AND 100  -- 合理温度范围
    AND humidity BETWEEN 0 AND 100  -- 合理湿度范围
  GROUP BY time_bucket, sensor_id, location
  HAVING COUNT(*) >= 5  -- 确保足够的采样点
),
trend_calculation AS (
  SELECT sensor_id, location,
         time_bucket, avg_temp, avg_humidity,
         LAG(avg_temp, 1) OVER (PARTITION BY sensor_id ORDER BY time_bucket) prev_temp,
         LAG(avg_temp, 4) OVER (PARTITION BY sensor_id ORDER BY time_bucket) temp_1h_ago,
         AVG(avg_temp) OVER (PARTITION BY sensor_id ORDER BY time_bucket ROWS 11 PRECEDING) ma_3h_temp,
         (avg_temp - LAG(avg_temp, 1) OVER (PARTITION BY sensor_id ORDER BY time_bucket)) temp_change_15m
  FROM time_series_base
),
anomaly_detection AS (
  SELECT *,
         CASE 
           WHEN ABS(temp_change_15m) > 5 THEN 'RAPID_CHANGE'
           WHEN avg_temp > (ma_3h_temp + 10) THEN 'HIGH_ANOMALY'
           WHEN avg_temp < (ma_3h_temp - 10) THEN 'LOW_ANOMALY'
           ELSE 'NORMAL'
         END temp_status
  FROM trend_calculation 
  WHERE prev_temp IS NOT NULL  -- 排除第一个数据点
)
SELECT sensor_id, location,
       COUNT(*) total_readings,
       AVG(avg_temp) avg_temperature,
       MAX(avg_temp) max_temperature,
       MIN(avg_temp) min_temperature,
       COUNT(CASE WHEN temp_status != 'NORMAL' THEN 1 END) anomaly_count,
       COUNT(CASE WHEN temp_status != 'NORMAL' THEN 1 END) * 100.0 / COUNT(*) anomaly_rate,
       LATEST_VALUE(temp_status) current_status
FROM anomaly_detection 
GROUP BY sensor_id, location
HAVING COUNT(*) > 100  -- 足够的历史数据
ORDER BY anomaly_rate DESC
LIMIT 50;
```

### 122. 多维度分组优化 - 销售分析
**Description**: 优化销售分析的多维度分组查询
```sql
-- 目的: 多维度分组的性能优化 | 复杂度: 高级 | 炎凰特性: 分组查询优化 | 类型: SELECT查询
-- 使用GROUPING SETS提高多维度分析效率
SELECT 
  CASE WHEN GROUPING(region) = 1 THEN 'ALL_REGIONS' ELSE region END region_group,
  CASE WHEN GROUPING(product_category) = 1 THEN 'ALL_CATEGORIES' ELSE product_category END category_group,
  CASE WHEN GROUPING(sales_channel) = 1 THEN 'ALL_CHANNELS' ELSE sales_channel END channel_group,
  COUNT(*) order_count,
  SUM(sale_amount) total_sales,
  AVG(sale_amount) avg_order_value,
  COUNT(DISTINCT customer_id) unique_customers
FROM sales_transactions 
WHERE _time >= DATE_ADD('d', -30, NOW()) AND _time < NOW()
  AND sale_amount > 0
  AND region IS NOT NULL
  AND product_category IS NOT NULL
  AND sales_channel IS NOT NULL
GROUP BY GROUPING SETS (
  (region, product_category, sales_channel),  -- 完整维度
  (region, product_category),                 -- 区域+品类
  (region, sales_channel),                    -- 区域+渠道
  (product_category, sales_channel),          -- 品类+渠道
  (region),                                   -- 仅区域
  (product_category),                         -- 仅品类
  (sales_channel),                           -- 仅渠道
  ()                                         -- 总计
)
ORDER BY 
  CASE WHEN region_group = 'ALL_REGIONS' THEN 1 ELSE 0 END,
  CASE WHEN category_group = 'ALL_CATEGORIES' THEN 1 ELSE 0 END,
  CASE WHEN channel_group = 'ALL_CHANNELS' THEN 1 ELSE 0 END,
  total_sales DESC;
```

### 123. 递归查询优化 - 组织架构分析
**Description**: 优化组织架构的递归查询性能
```sql
-- 目的: 递归查询的性能控制 | 复杂度: 高级 | 炎凰特性: 递归查询控制 | 类型: SELECT查询
WITH RECURSIVE org_hierarchy AS (
  -- 基础查询：顶级管理者
  SELECT employee_id, manager_id, employee_name, department, 
         1 as level, 
         employee_name as path,
         ARRAY[employee_id] as id_path
  FROM employees 
  WHERE _time >= DATE_ADD('h', -24, NOW()) AND _time < NOW()
    AND manager_id IS NULL
    AND employment_status = 'active'
  
  UNION ALL
  
  -- 递归查询：下级员工
  SELECT e.employee_id, e.manager_id, e.employee_name, e.department,
         oh.level + 1,
         oh.path || ' -> ' || e.employee_name,
         oh.id_path || e.employee_id
  FROM employees e
  INNER JOIN org_hierarchy oh ON e.manager_id = oh.employee_id
  WHERE e._time >= DATE_ADD('h', -24, NOW()) AND e._time < NOW()
    AND e.employment_status = 'active'
    AND oh.level < 6  -- 限制递归深度，防止性能问题
    AND NOT (e.employee_id = ANY(oh.id_path))  -- 防止循环引用
)
SELECT department,
       level,
       COUNT(*) employee_count,
       AVG(level) avg_level_in_dept,
       MAX(level) max_depth,
       COUNT(DISTINCT CASE WHEN level = 1 THEN employee_id END) top_level_count
FROM org_hierarchy 
GROUP BY department, level
ORDER BY department, level;
```

### 124. 内存效率优化 - 大表关联
**Description**: 优化大表关联的内存效率
```sql
-- 目的: 大表关联的内存效率优化 | 复杂度: 高级 | 炎凰特性: 内存优化策略 | 类型: SELECT查询
WITH recent_orders AS (
  -- 预过滤减少数据量
  SELECT order_id, customer_id, order_amount, order_date
  FROM orders 
  WHERE _time >= DATE_ADD('d', -90, NOW()) AND _time < NOW()
    AND order_status IN ('completed', 'shipped')
    AND order_amount > 0
),
active_customers AS (
  -- 预过滤活跃客户
  SELECT customer_id, customer_tier, registration_date
  FROM customers 
  WHERE last_activity_date >= DATE_ADD('d', -180, NOW())
    AND customer_status = 'active'
),
order_summary AS (
  -- 先聚合再关联，减少关联数据量
  SELECT customer_id,
         COUNT(*) order_count,
         SUM(order_amount) total_spent,
         AVG(order_amount) avg_order_value,
         EARLIEST_VALUE(order_date) first_order,
         LATEST_VALUE(order_date) last_order
  FROM recent_orders 
  GROUP BY customer_id
)
SELECT ac.customer_tier,
       COUNT(*) customer_count,
       AVG(os.order_count) avg_orders_per_customer,
       AVG(os.total_spent) avg_customer_value,
       AVG(os.avg_order_value) avg_order_size,
       SUM(os.total_spent) tier_total_revenue
FROM active_customers ac
INNER JOIN order_summary os ON ac.customer_id = os.customer_id  -- 内连接，只关联有订单的客户
GROUP BY ac.customer_tier
ORDER BY tier_total_revenue DESC;
```

### 125. 查询计划友好设计 - 复合索引利用
**Description**: 设计对查询计划友好的索引利用方案
```sql
-- 目的: 设计查询计划友好的SQL | 复杂度: 高级 | 炎凰特性: 索引优化设计 | 类型: SELECT查询
-- 假设存在复合索引：(_time, event_type, user_id, session_id)
SELECT event_type, 
       DATE(_time) event_date,
       COUNT(*) event_count,
       COUNT(DISTINCT user_id) unique_users,
       COUNT(DISTINCT session_id) unique_sessions,
       AVG(event_duration) avg_duration
FROM user_events 
WHERE _time >= DATE_ADD('d', -7, NOW())   -- 第1个索引列
  AND _time < NOW()                       -- 范围查询
  AND event_type IN ('login', 'purchase', 'logout')  -- 第2个索引列，使用IN
  AND user_id IS NOT NULL                 -- 第3个索引列，过滤NULL
  AND session_id IS NOT NULL              -- 第4个索引列，过滤NULL
  AND event_duration > 0                  -- 业务逻辑过滤
GROUP BY event_type, DATE(_time)          -- 分组字段与索引对齐
HAVING COUNT(*) > 10                      -- 聚合后过滤
ORDER BY event_date DESC, event_type     -- 排序利用索引
LIMIT 100;                               -- 限制结果集
``` 
