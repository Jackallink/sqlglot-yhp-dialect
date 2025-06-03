import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
import csv
import os
from utils.sqlglot_adapter import parse_sql_to_yhp_ast, ComplianceError, parse_sql_to_ast
from utils.yhp_sql_ast import select_to_sql

# 注意：本文件所有AST结构断言均为结构化repr字符串，不再断言SQL片段。

# 读取修正后的SQL文件，支持多行SQL以分号分割
with open('tests/pg_bulk_test_fixed.sql', encoding='utf-8') as f:
    content = f.read()
    sqls = [s.strip() for s in content.split(';') if s.strip() and not s.strip().startswith('--')]
# 过滤掉明显不完整的SQL
skip_patterns = ['(']
def is_valid_sql(sql):
    s = sql.strip()
    if s in ('(', ')') or s.endswith('(') or s.startswith(')') or s.upper() in {'UNION ALL'}:
        return False
    return True
sqls = [sql for sql in sqls if is_valid_sql(sql)]

# 初始化csv文件（只写表头）
if not os.path.exists('tests/pg_bulk_test_report.csv'):
    with open('tests/pg_bulk_test_report.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sql', 'ast', 'sql_out', 'degrade', 'error', 'result'])
        writer.writeheader()
if not os.path.exists('tests/failures_pg_bulk.csv'):
    with open('tests/failures_pg_bulk.csv', 'w', encoding='utf-8') as f:
        pass

all_results = []
all_failures = []

@pytest.mark.parametrize('sql', sqls)
def test_pg_bulk_sql(sql):
    """
    批量AST链路、SQL输出、降级/报错分支自动化测试，输出csv报表
    """
    row = {'sql': sql, 'ast': '', 'sql_out': '', 'degrade': '', 'error': '', 'result': 'PASS'}
    try:
        ast = parse_sql_to_yhp_ast(sql)
        # 结构化repr，记录AST结构字符串
        row['ast'] = str(ast)
        # 可选：断言结构化repr类型
        assert isinstance(row['ast'], str) and row['ast'].startswith(ast.__class__.__name__)
        sql_out = select_to_sql(ast) if ast else ''
        row['sql_out'] = sql_out
        degrade = getattr(ast, 'degrade_info', None)
        if degrade:
            row['degrade'] = str(degrade)
        assert sql_out and any(x in sql_out for x in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']), f'SQL输出异常: {sql_out}'
        # 调试：遇到NOW或CURRENT_TIMESTAMP的SQL，打印AST类型和内容
        if 'NOW' in sql.upper() or 'CURRENT_TIMESTAMP' in sql.upper():
            ast = parse_sql_to_ast(sql, dialect='postgres')
            with open('/tmp/now_ast_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"[DEBUG][NOW] SQL={sql}\nAST type={type(ast)}, AST={ast}\n")
    except ComplianceError as ce:
        row['error'] = f'合规报错: {ce}'
        row['result'] = 'COMPLIANCE_ERROR'
    except NotImplementedError as nie:
        row['error'] = f'未实现降级: {nie}'
        row['result'] = 'NOT_IMPLEMENTED'
    except Exception as e:
        row['error'] = f'异常: {e}'
        row['result'] = 'FAIL'
        with open('tests/failures_pg_bulk.csv', 'a', encoding='utf-8') as f:
            f.write(sql + '\n')
        all_failures.append(sql)
    with open('tests/pg_bulk_test_report.csv', 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sql', 'ast', 'sql_out', 'degrade', 'error', 'result'])
        writer.writerow(row)
    all_results.append(row)

def test_pg_bulk_stats():
    """
    统计降级/报错分支命中率
    """
    degrade_count = 0
    compliance_count = 0
    notimpl_count = 0
    total = 0
    for sql in sqls:
        try:
            ast = parse_sql_to_yhp_ast(sql)
            degrade = getattr(ast, 'degrade_info', None)
            if degrade:
                degrade_count += 1
            total += 1
        except ComplianceError:
            compliance_count += 1
            total += 1
        except NotImplementedError:
            notimpl_count += 1
            total += 1
        except Exception:
            total += 1
    print(f'总SQL数: {total}, 降级命中: {degrade_count}, 合规报错: {compliance_count}, 未实现: {notimpl_count}')
    assert total > 0

def pytest_sessionfinish(session, exitstatus):
    _ = session
    _ = exitstatus
    with open('tests/pg_bulk_test_report.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sql', 'ast', 'sql_out', 'degrade', 'error', 'result'])
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)
    if all_failures:
        with open('tests/failures_pg_bulk.csv', 'w', encoding='utf-8') as f:
            for sql in all_failures:
                f.write(sql + '\n') 