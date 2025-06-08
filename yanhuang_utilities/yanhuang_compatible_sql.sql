-- 炎凰数据兼容版本的SQL
-- 基于官方文档修正：问题是语法错误，不是UNBOUNDED不支持

WITH 
last_month_data AS (
  SELECT user_id, 
         SUM(amount) total_spent,
         MAX(_time) latest_activity_time
  FROM orders 
  WHERE _time >= DATE_ADD('d', -30, NOW())
    AND _time < NOW()
  GROUP BY user_id
),
user_segments AS (
  SELECT ld.user_id,
         ld.total_spent,
         CASE WHEN ld.latest_activity_time IS NOT NULL THEN 'ACTIVE' ELSE 'INACTIVE' END activity_status,
         
         -- 🎯 推荐方案：使用默认窗口框架（语义等价，性能更好）
         FIRST_VALUE(ld.total_spent) OVER (PARTITION BY ld.user_id ORDER BY _time DESC) monthly_spent
         
         -- 🔧 如果确实需要特定窗口范围，可以使用以下语法：
         -- FIRST_VALUE(ld.total_spent) OVER (PARTITION BY ld.user_id ORDER BY _time DESC ROWS BETWEEN 6 PRECEDING AND UNBOUNDED FOLLOWING) monthly_spent
         
  FROM last_month_data ld
),
group_ratios AS (
  SELECT s.activity_status, 
         CASE WHEN s.monthly_spent IS NULL THEN 'NO_PURCHASE' 
              WHEN s.monthly_spent >= 1000 THEN 'HIGH_VALUE'
              WHEN s.monthly_spent >= 500 AND s.monthly_spent < 1000 THEN 'MEDIUM_VALUE'
              ELSE 'LOW_VALUE' END value_segment,
         COUNT(*) total_count
  FROM user_segments s
  GROUP BY activity_status, value_segment
)
SELECT value_segment AS 客户价值等级,
       activity_status AS 活跃状态,
       ROUND((total_count * 100.0) / NULLIF(SUM(total_count) OVER(), 0), 2) || '%' AS 群体比例
FROM group_ratios 
ORDER BY (SELECT value_segment || '_' || activity_status) ASC; 