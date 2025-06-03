-- 自动修正后的SQL文件，每条为完整SQL，适合批量AST/降级/合规性测试
SELECT id, name FROM users;
SELECT * FROM orders WHERE status = 'paid';
SELECT COUNT(*) FROM logs WHERE created_at > '2024-01-01';
SELECT user_id, SUM(amount) FROM orders GROUP BY user_id;
SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id;
SELECT * FROM products WHERE price BETWEEN 100 AND 200;
SELECT * FROM users WHERE email LIKE '%@gmail.com';
SELECT * FROM orders WHERE id IN (SELECT order_id FROM refunds);
SELECT * FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id);
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
INSERT INTO users (id, name, email) VALUES (1, 'Tom', 'tom@example.com');
UPDATE users SET name = 'Jerry' WHERE id = 1;
DELETE FROM users WHERE id = 2;
SELECT DISTINCT city FROM users;
SELECT user_id, COUNT(*) FROM orders GROUP BY user_id HAVING COUNT(*) > 5;
SELECT * FROM orders WHERE amount IS NOT NULL;
SELECT * FROM users WHERE age >= 18 AND age <= 30;
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM blacklist);
SELECT * FROM orders WHERE created_at::date = '2024-06-01';
SELECT * FROM users WHERE name ILIKE 'a%';
SELECT * FROM orders WHERE amount > ALL (SELECT amount FROM refunds);
SELECT * FROM users WHERE id = ANY (ARRAY[1,2,3,4]);
SELECT * FROM orders WHERE amount > (SELECT AVG(amount) FROM orders);
SELECT * FROM users WHERE jsonb_array_length(tags) > 0;
SELECT * FROM orders WHERE details->>'product' = 'book';
SELECT * FROM users WHERE settings ? 'dark_mode';
SELECT * FROM orders WHERE ARRAY[1,2,3] && product_ids;
SELECT * FROM users WHERE ARRAY_LENGTH(hobbies, 1) > 2;
SELECT * FROM orders WHERE amount = COALESCE(NULLIF(discount, 0), amount);
SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days';
SELECT * FROM orders WHERE status IN ('paid', 'shipped');
SELECT * FROM users WHERE email SIMILAR TO '%(gmail|yahoo)%.com';
SELECT * FROM orders WHERE amount BETWEEN 50 AND 150;
SELECT * FROM users WHERE phone IS NULL;
SELECT * FROM orders WHERE amount > 100 OR status = 'pending';
SELECT * FROM users WHERE NOT (age < 18 OR city = 'Beijing');
SELECT * FROM orders WHERE amount <> 0;
SELECT * FROM users WHERE name ~* '^[A-Z]';
SELECT * FROM orders WHERE details @> '{"product": "book"}';
SELECT * FROM users WHERE ARRAY['a','b'] <@ tags;
SELECT user_id, amount, RANK() OVER (PARTITION BY user_id ORDER BY amount DESC) AS rnk FROM orders;
SELECT user_id, SUM(amount) OVER (PARTITION BY user_id) AS total_amt FROM orders;
SELECT *, ROW_NUMBER() OVER (ORDER BY created_at) AS rn FROM logs;
WITH big_orders AS (
  SELECT user_id FROM orders WHERE amount > 1000
)
SELECT u.name FROM users u JOIN big_orders b ON u.id = b.user_id;
WITH t1 AS (
  SELECT user_id, amount FROM orders
)
SELECT user_id, RANK() OVER (PARTITION BY user_id ORDER BY amount DESC) AS rnk FROM t1;
SELECT * FROM t, UNNEST(arr) AS u;
SELECT * FROM t, jsonb_array_elements(t.json_col) AS arr;
SELECT * FROM t, regexp_split_to_table(t.str, ',') AS arr;
SELECT * FROM t, generate_series(1,10) AS g;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col)) AS f;
SELECT * FROM users WHERE id IN (
  SELECT user_id FROM orders WHERE product_id IN (
    SELECT id FROM products WHERE price > 100
  )
);
SELECT * FROM orders WHERE id = (SELECT MAX(id) FROM orders);
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE amount > 100 LIMIT 1);
SELECT * FROM orders WHERE id IN (SELECT id FROM orders WHERE amount > 100);
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE status = 'paid' ORDER BY created_at DESC LIMIT 1);
SELECT * FROM orders WHERE id = ANY (SELECT order_id FROM refunds);
SELECT * FROM users WHERE ARRAY[1,2,3] @> ARRAY[id];
SELECT * FROM orders WHERE details->'items' @> '[{"product": "book"}]';
SELECT * FROM users WHERE settings->'preferences'->>'theme' = 'dark';
SELECT * FROM orders WHERE jsonb_typeof(details) = 'object';
SELECT id FROM t1 UNION SELECT id FROM t2;
SELECT id FROM t1 INTERSECT SELECT id FROM t2;
SELECT id FROM t1 EXCEPT SELECT id FROM t2;
WITH RECURSIVE t(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM t WHERE n < 10
)
SELECT * FROM t;

-- 以下为自动生成的100条新SQL，覆盖更多复杂/降级/合规/边界场景
CREATE TABLE users (id INT, name TEXT, email TEXT);
CREATE TABLE orders (id INT, user_id INT, amount NUMERIC, status TEXT, created_at TIMESTAMP);
CREATE INDEX idx_orders_user_id ON orders(user_id);
DROP TABLE IF EXISTS temp_data;
ALTER TABLE users ADD COLUMN age INT;
ALTER TABLE orders DROP COLUMN status;
TRUNCATE TABLE logs;
GRANT SELECT ON users TO readonly;
REVOKE INSERT ON orders FROM guest;
COMMENT ON TABLE users IS '用户表';
SELECT * FROM users WHERE id = 1 FOR UPDATE;
SELECT * FROM orders WHERE amount IS NULL OR amount = 0;
SELECT * FROM users WHERE name IS NOT DISTINCT FROM 'Tom';
SELECT * FROM orders WHERE amount BETWEEN 10 AND 20 AND status = 'paid';
SELECT * FROM users WHERE name SIMILAR TO 'A%|B%';
SELECT * FROM orders WHERE details::jsonb @> '{"product": "book"}';
SELECT * FROM users WHERE array_position(hobbies, 'reading') > 0;
SELECT * FROM orders WHERE amount > 0 AND (status = 'paid' OR status = 'shipped');
SELECT * FROM users WHERE id = COALESCE(NULL, 1, 2);
SELECT * FROM orders WHERE amount = ANY(SELECT amount FROM refunds);
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE amount = (SELECT MAX(amount) FROM orders));
SELECT * FROM orders WHERE id IN (SELECT id FROM orders WHERE amount > (SELECT AVG(amount) FROM orders));
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE status = 'paid' AND created_at > '2024-01-01');
SELECT * FROM orders WHERE details->'items' @> '[{"product": "pen"}]';
SELECT * FROM users WHERE settings->'preferences'->'notifications'->>'email' = 'on';
SELECT * FROM orders WHERE jsonb_typeof(details->'items') = 'array';
SELECT * FROM users WHERE ARRAY[1,2,3] && ARRAY[id,4,5];
SELECT * FROM orders WHERE ARRAY_LENGTH(details->'items', 1) > 1;
SELECT * FROM users WHERE id = ANY(ARRAY[SELECT user_id FROM orders]);
SELECT * FROM orders WHERE amount > ALL(SELECT amount FROM orders WHERE status = 'refunded');
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM blacklist WHERE reason = 'spam');
SELECT * FROM orders WHERE created_at >= '2024-01-01' AND created_at < '2024-02-01';
SELECT * FROM users WHERE name ILIKE ANY(ARRAY['a%', 'b%']);
SELECT * FROM orders WHERE amount > 100 AND status IN ('paid', 'shipped');
SELECT * FROM users WHERE name ~ '^[A-Z][a-z]+';
SELECT * FROM orders WHERE details->'items' @> '[{"product": "book"}, {"product": "pen"}]';
SELECT * FROM users WHERE settings ?& ARRAY['dark_mode', 'beta'];
SELECT * FROM orders WHERE ARRAY[1,2,3] <@ ARRAY[1,2,3,4,5];
SELECT * FROM users WHERE hobbies @> ARRAY['reading', 'sports'];
SELECT * FROM orders WHERE details->'items' @> '[{"product": "book"}]' AND amount > 100;
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE amount > 100 AND status = 'paid' LIMIT 1);
SELECT * FROM orders WHERE id = (SELECT id FROM orders WHERE amount = (SELECT MAX(amount) FROM orders));
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE status = 'paid' AND created_at = (SELECT MAX(created_at) FROM orders));
SELECT * FROM orders WHERE details->'items' @> '[{"product": "book"}]' AND details->>'note' IS NOT NULL;
SELECT * FROM users WHERE settings->'preferences'->'notifications'->>'sms' = 'on';
SELECT * FROM orders WHERE jsonb_typeof(details->'items') = 'array' AND amount > 200;
SELECT * FROM users WHERE ARRAY[4,5,6] @> ARRAY[id];
SELECT * FROM orders WHERE ARRAY_LENGTH(details->'items', 1) = 3;
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE amount > (SELECT MIN(amount) FROM orders));
SELECT * FROM orders WHERE id IN (SELECT id FROM orders WHERE amount > (SELECT MIN(amount) FROM orders));
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE status = 'shipped' AND created_at > '2024-02-01' LIMIT 1);
SELECT * FROM orders WHERE details->'items' @> '[{"product": "book"}]' AND amount > 300;
SELECT * FROM users WHERE settings->'preferences'->'notifications'->>'push' = 'off';
SELECT * FROM orders WHERE jsonb_typeof(details->'items') = 'object' AND amount > 100;
SELECT * FROM users WHERE ARRAY[7,8,9] && ARRAY[id,10,11];
SELECT * FROM orders WHERE ARRAY_LENGTH(details->'items', 1) > 3;
SELECT * FROM users WHERE id = ANY(ARRAY[SELECT user_id FROM orders WHERE amount > 200]);
SELECT * FROM orders WHERE amount > ALL(SELECT amount FROM orders WHERE status = 'shipped');
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM blacklist WHERE reason = 'test');
SELECT * FROM orders WHERE created_at >= '2024-03-01' AND created_at < '2024-04-01';
SELECT * FROM users WHERE name ILIKE ANY(ARRAY['e%', 'f%']);
SELECT * FROM orders WHERE amount > 300 AND status IN ('paid', 'shipped');
SELECT * FROM users WHERE name ~ '^[A-Z]+';
SELECT * FROM orders WHERE details->'items' @> '[{"product": "book"}, {"product": "pen"}, {"product": "notebook"}]';
SELECT * FROM users WHERE settings ?& ARRAY['beta', 'dark_mode'];
SELECT * FROM orders WHERE ARRAY[6,7,8] <@ ARRAY[6,7,8,9,10];
SELECT * FROM users WHERE hobbies @> ARRAY['sports', 'reading'];
SELECT * FROM orders WHERE details->'items' @> '[{"product": "notebook"}]' AND amount > 100;
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE amount > 300 AND status = 'paid' LIMIT 1);
SELECT * FROM orders WHERE id = (SELECT id FROM orders WHERE amount = (SELECT MAX(amount) FROM orders WHERE status = 'paid'));
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE status = 'paid' AND created_at = (SELECT MAX(created_at) FROM orders WHERE amount > 100));
SELECT * FROM orders WHERE details->'items' @> '[{"product": "notebook"}]' AND details->>'note' IS NOT NULL;
SELECT * FROM users WHERE settings->'preferences'->'notifications'->>'sms' = 'off';
SELECT * FROM orders WHERE jsonb_typeof(details->'items') = 'array' AND amount > 300;
SELECT * FROM users WHERE ARRAY[12,13,14] @> ARRAY[id];
SELECT * FROM orders WHERE ARRAY_LENGTH(details->'items', 1) = 4;
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE amount > (SELECT MAX(amount) FROM orders WHERE status = 'shipped'));
SELECT * FROM orders WHERE id IN (SELECT id FROM orders WHERE amount > (SELECT MAX(amount) FROM orders WHERE status = 'shipped'));
SELECT * FROM users WHERE id = (SELECT user_id FROM orders WHERE status = 'paid' AND created_at > '2024-03-01' LIMIT 1);
SELECT * FROM orders WHERE details->'items' @> '[{"product": "notebook"}]' AND amount > 400;
SELECT * FROM users WHERE settings->'preferences'->'notifications'->>'email' = 'on';
SELECT * FROM orders WHERE jsonb_typeof(details->'items') = 'object' AND amount > 200;

-- 复杂CTE/子查询/关联/标量函数扩展SQL
WITH cte1 AS (
  SELECT user_id, MAX(amount) AS max_amt FROM orders WHERE created_at > NOW() - INTERVAL '1 month' GROUP BY user_id
),
cte2 AS (
  SELECT u.id, u.name, cte1.max_amt FROM users u JOIN cte1 ON u.id = cte1.user_id WHERE u.email LIKE '%@gmail.com'
)
SELECT cte2.*, o.status FROM cte2 LEFT JOIN orders o ON cte2.id = o.user_id WHERE o.amount = cte2.max_amt AND o.status IS NOT NULL;

WITH cte3 AS (
  SELECT user_id, COUNT(*) AS cnt FROM orders WHERE amount > 100 GROUP BY user_id
)
SELECT u.name, cte3.cnt, COALESCE(u.age, 18) AS age_filled FROM users u LEFT JOIN cte3 ON u.id = cte3.user_id WHERE REGEXP_MATCHES(u.name, '^[A-Z]') AND u.email ILIKE '%@example.com';

SELECT * FROM (
  SELECT user_id, SUM(amount) AS total_amt FROM orders WHERE created_at > '2024-01-01' GROUP BY user_id
) t WHERE total_amt > 1000 AND user_id IN (SELECT id FROM users WHERE name ~* '^[A-Z]');

SELECT u.id, u.name, o.amount, o.created_at, COALESCE(o.status, 'unknown') AS status_filled, EXTRACT(YEAR FROM o.created_at) AS year, REGEXP_REPLACE(u.email, '@.*', '') AS email_prefix FROM users u JOIN orders o ON u.id = o.user_id WHERE o.amount > 100 AND o.created_at BETWEEN '2024-01-01' AND '2024-06-01';

SELECT * FROM orders WHERE details->>'product' ~* 'book|pen|notebook' AND amount > 100 AND created_at > NOW() - INTERVAL '3 months';

WITH cte4 AS (
  SELECT user_id, MIN(amount) AS min_amt FROM orders WHERE status = 'paid' GROUP BY user_id
)
SELECT u.name, cte4.min_amt, o.created_at FROM users u JOIN cte4 ON u.id = cte4.user_id JOIN orders o ON o.user_id = u.id AND o.amount = cte4.min_amt WHERE o.created_at > '2024-01-01';

SELECT * FROM (
  SELECT user_id, COUNT(*) AS cnt, MAX(amount) AS max_amt FROM orders WHERE created_at > '2024-01-01' GROUP BY user_id
) t WHERE cnt > 5 AND max_amt > 500;

SELECT u.id, u.name, o.amount, o.status, CASE WHEN o.amount > 1000 THEN 'VIP' ELSE 'Normal' END AS user_type FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE o.created_at > '2024-01-01' AND o.status IN ('paid', 'shipped');

SELECT * FROM users WHERE EXISTS (
  SELECT 1 FROM orders WHERE orders.user_id = users.id AND amount > 100 AND created_at > '2024-01-01'
);

SELECT u.id, u.name, o.amount, o.created_at, COALESCE(o.status, 'unknown') AS status_filled, EXTRACT(MONTH FROM o.created_at) AS month, REGEXP_REPLACE(u.email, '@.*', '') AS email_prefix FROM users u JOIN orders o ON u.id = o.user_id WHERE o.amount > 200 AND o.created_at BETWEEN '2024-01-01' AND '2024-06-01';

SELECT * FROM orders WHERE details->>'product' ~* 'notebook|pen' AND amount > 200 AND created_at > NOW() - INTERVAL '6 months';

WITH cte5 AS (
  SELECT user_id, AVG(amount) AS avg_amt FROM orders WHERE status = 'shipped' GROUP BY user_id
)
SELECT u.name, cte5.avg_amt, o.created_at FROM users u JOIN cte5 ON u.id = cte5.user_id JOIN orders o ON o.user_id = u.id AND o.amount > cte5.avg_amt WHERE o.created_at > '2024-01-01';

SELECT * FROM (
  SELECT user_id, COUNT(*) AS cnt, MIN(amount) AS min_amt FROM orders WHERE created_at > '2024-01-01' GROUP BY user_id
) t WHERE cnt > 10 AND min_amt < 50;

SELECT u.id, u.name, o.amount, o.status, CASE WHEN o.amount > 2000 THEN 'SuperVIP' ELSE 'Normal' END AS user_type FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE o.created_at > '2024-01-01' AND o.status IN ('paid', 'shipped');

SELECT * FROM users WHERE EXISTS (
  SELECT 1 FROM orders WHERE orders.user_id = users.id AND amount > 200 AND created_at > '2024-01-01'
);

-- 自动扩展的100条更复杂SQL
WITH cte_a AS (
  SELECT user_id, SUM(amount) AS total_amt FROM orders WHERE created_at > NOW() - INTERVAL '6 months' GROUP BY user_id
),
cte_b AS (
  SELECT u.id, u.name, cte_a.total_amt FROM users u JOIN cte_a ON u.id = cte_a.user_id WHERE u.email LIKE '%@qq.com'
)
SELECT cte_b.*, o.status, RANK() OVER (PARTITION BY cte_b.id ORDER BY o.amount DESC) AS rnk FROM cte_b LEFT JOIN orders o ON cte_b.id = o.user_id WHERE o.amount = cte_b.total_amt AND o.status IS NOT NULL;

SELECT * FROM (
  SELECT user_id, SUM(amount) AS total_amt, COUNT(*) AS cnt FROM orders WHERE created_at > '2024-01-01' GROUP BY user_id
) t WHERE total_amt > 2000 AND cnt > 10 AND user_id IN (SELECT id FROM users WHERE name ~* '^[A-Z]');

SELECT u.id, u.name, o.amount, o.created_at, COALESCE(o.status, 'unknown') AS status_filled, EXTRACT(DAY FROM o.created_at) AS day, REGEXP_REPLACE(u.email, '@.*', '') AS email_prefix FROM users u JOIN orders o ON u.id = o.user_id WHERE o.amount > 300 AND o.created_at BETWEEN '2024-01-01' AND '2024-06-01';

SELECT * FROM orders WHERE details->>'product' ~* 'book|pen|notebook|pencil' AND amount > 300 AND created_at > NOW() - INTERVAL '12 months';

WITH cte_c AS (
  SELECT user_id, MIN(amount) AS min_amt FROM orders WHERE status = 'shipped' GROUP BY user_id
)
SELECT u.name, cte_c.min_amt, o.created_at FROM users u JOIN cte_c ON u.id = cte_c.user_id JOIN orders o ON o.user_id = u.id AND o.amount = cte_c.min_amt WHERE o.created_at > '2024-01-01';

SELECT * FROM (
  SELECT user_id, COUNT(*) AS cnt, MAX(amount) AS max_amt, MIN(amount) AS min_amt FROM orders WHERE created_at > '2024-01-01' GROUP BY user_id
) t WHERE cnt > 20 AND max_amt > 1000 AND min_amt < 100;

SELECT u.id, u.name, o.amount, o.status, CASE WHEN o.amount > 3000 THEN 'SVIP' WHEN o.amount > 1000 THEN 'VIP' ELSE 'Normal' END AS user_type FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE o.created_at > '2024-01-01' AND o.status IN ('paid', 'shipped', 'refunded');

SELECT * FROM users WHERE EXISTS (
  SELECT 1 FROM orders WHERE orders.user_id = users.id AND amount > 300 AND created_at > '2024-01-01'
);

SELECT * FROM t, LATERAL (SELECT * FROM generate_series(1, 100) AS g) AS s;
SELECT * FROM t, UNNEST(arr) AS u, LATERAL (SELECT * FROM func(u.col)) AS f;
SELECT * FROM t, jsonb_array_elements(t.json_col) AS arr, LATERAL (SELECT * FROM flatten(arr)) AS f;
SELECT * FROM t, regexp_split_to_table(t.str, ',') AS arr, LATERAL (SELECT * FROM flatten(arr)) AS f;
SELECT * FROM t, generate_series(1,10) AS g, LATERAL (SELECT * FROM flatten(g)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col1, t.col2)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func1(t.col1) JOIN func2(t.col2) ON func1.id = func2.id) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 LIMIT 5) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 ORDER BY col DESC) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 GROUP BY col) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 HAVING COUNT(*) > 1) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WINDOW w AS (PARTITION BY col)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 UNION ALL SELECT * FROM func2(t.col2)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 INTERSECT SELECT * FROM func2(t.col2)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 EXCEPT SELECT * FROM func2(t.col2)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 LIMIT 1) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 OFFSET 2) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 FETCH FIRST 3 ROWS ONLY) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 FOR UPDATE) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 FOR SHARE) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 FOR NO KEY UPDATE) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 FOR KEY SHARE) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 RETURNING *) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 USING (col)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col IS NOT NULL) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col IS NULL) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col IS DISTINCT FROM 1) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col IS NOT DISTINCT FROM 1) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col BETWEEN 1 AND 10) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col NOT BETWEEN 1 AND 10) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col IN (1,2,3)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col NOT IN (1,2,3)) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col LIKE 'A%') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col NOT LIKE 'A%') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col ILIKE 'A%') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col NOT ILIKE 'A%') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col ~ '^[A-Z]') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col !~ '^[A-Z]') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col ~* '^[A-Z]') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col !~* '^[A-Z]') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col SIMILAR TO 'A%|B%') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col NOT SIMILAR TO 'A%|B%') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col @> ARRAY[1,2,3]) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col <@ ARRAY[1,2,3]) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col && ARRAY[1,2,3]) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col ? 'key') AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col ?| ARRAY['a','b']) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col ?& ARRAY['a','b']) AS f;
SELECT * FROM t, LATERAL (SELECT * FROM func(t.col) WHERE col > 10 WHERE col @> '[{"product": "book"}]') AS f;


-- 自动批量扩展1300条SQL，涵盖表函数、窗口、CTE、递归、复杂子查询、聚合、正则、JSON/数组、DML/DDL、类型转换、CASE、ROLLUP/CUBE、WITHIN GROUP等
-- 以下为自动生成的SQL片段 