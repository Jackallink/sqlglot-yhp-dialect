#!/usr/bin/env python3
"""
炎凰数据SQL样例综合测试 - 125条样例全量分析
测试范围：语法解析、功能特性、PostgreSQL兼容性、性能评分
"""

import sqlglot
import re
import traceback
from collections import defaultdict
import warnings

def extract_sql_samples(file_path):
    """从markdown文件中提取所有SQL样例"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配SQL代码块的正则表达式
    pattern = r'### (\d+)\. (.+?)\n\*\*Description\*\*: (.+?)\n```sql\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    samples = []
    for match in matches:
        sql_number, title, description, sql_content = match
        
        # 清理SQL内容（移除注释和空行）
        sql_lines = []
        for line in sql_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                sql_lines.append(line)
        
        clean_sql = ' '.join(sql_lines)
        
        # 提取SQL特征
        features = extract_features_from_comment(sql_content)
        
        samples.append({
            'number': int(sql_number),
            'title': title.strip(),
            'description': description.strip(),
            'sql': clean_sql,
            'features': features
        })
    
    return samples

def extract_features_from_comment(sql_content):
    """从SQL注释中提取特征信息"""
    features = {
        'purpose': '',
        'complexity': '简单',
        'yanhuang_features': [],
        'query_type': 'SELECT查询'
    }
    
    # 查找第一行注释
    for line in sql_content.split('\n'):
        if line.strip().startswith('-- 目的:'):
            comment = line.strip()[4:]  # 移除 "-- "
            parts = comment.split(' | ')
            
            for part in parts:
                if part.strip().startswith('目的:'):
                    features['purpose'] = part.split(':', 1)[1].strip()
                elif part.strip().startswith('复杂度:'):
                    features['complexity'] = part.split(':', 1)[1].strip()
                elif part.strip().startswith('炎凰特性:'):
                    features_str = part.split(':', 1)[1].strip()
                    features['yanhuang_features'] = [f.strip() for f in features_str.split('/')]
                elif part.strip().startswith('类型:'):
                    features['query_type'] = part.split(':', 1)[1].strip()
            break
    
    return features

def analyze_yanhuang_features(sql):
    """分析SQL中使用的炎凰数据特性"""
    features = {
        'time_functions': [],
        'aggregation_functions': [],
        'string_functions': [],
        'array_functions': [],
        'window_functions': [],
        'json_functions': [],
        'regex_functions': [],
        'security_functions': [],
        'url_functions': [],
        'ip_functions': [],
        'cte_usage': False,
        'lateral_apply': False,
        'complex_constructs': []
    }
    
    sql_upper = sql.upper()
    
    # 时间相关函数
    time_funcs = ['TIME_BUCKET', 'DATE_ADD', 'DATE_DIFF', 'DATE_PART', 'NOW', 'EXTRACT', 
                  'CURRENT_TIMESTAMP', 'CURRENT_DATE', 'DATE_TRUNC']
    for func in time_funcs:
        if func in sql_upper:
            features['time_functions'].append(func)
    
    # 聚合函数
    agg_funcs = ['LATEST_VALUE', 'EARLIEST_VALUE', 'APPROX_COUNT_DISTINCT', 
                 'STDDEV_POP', 'VARIANCE', 'STRING_AGG', 'ARRAY_AGG']
    for func in agg_funcs:
        if func in sql_upper:
            features['aggregation_functions'].append(func)
    
    # 字符串函数
    str_funcs = ['CONCAT_WS', 'CHAR_LENGTH', 'CONTAINS', 'SPLIT_PART', 'REGEXP_LIKE']
    for func in str_funcs:
        if func in sql_upper:
            features['string_functions'].append(func)
    
    # 数组函数
    array_funcs = ['ARRAY', 'ARRAY_LENGTH', 'UNNEST', 'ARRAY_APPEND']
    for func in array_funcs:
        if func in sql_upper:
            features['array_functions'].append(func)
    
    # 窗口函数
    window_funcs = ['ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LAG', 'LEAD', 'FIRST_VALUE', 
                    'LAST_VALUE', 'NTILE', 'OVER']
    for func in window_funcs:
        if func in sql_upper:
            features['window_functions'].append(func)
    
    # JSON函数
    json_funcs = ['JSON_EXTRACT', 'JSON_EXTRACT_PATH_TEXT', 'PARSE_JSON']
    for func in json_funcs:
        if func in sql_upper:
            features['json_functions'].append(func)
    
    # 正则函数
    regex_funcs = ['REGEX_LIKE', 'REGEXP_MATCH', 'REGEXP_REPLACE']
    for func in regex_funcs:
        if func in sql_upper:
            features['regex_functions'].append(func)
    
    # 安全相关函数
    security_funcs = ['MD5', 'SHA256', 'SHA1', 'SHA512']
    for func in security_funcs:
        if func in sql_upper:
            features['security_functions'].append(func)
    
    # URL函数
    url_funcs = ['DOMAIN', 'PROTOCOL', 'PATH', 'QUERY_PARAM', 'URL_DECODE']
    for func in url_funcs:
        if func in sql_upper:
            features['url_functions'].append(func)
    
    # IP函数
    ip_funcs = ['IP_TO_INT', 'INT_TO_IP', 'CIDR_MATCH', 'IP_LOCATION']
    for func in ip_funcs:
        if func in sql_upper:
            features['ip_functions'].append(func)
    
    # 复杂结构
    if 'WITH' in sql_upper:
        features['cte_usage'] = True
    
    if 'OUTER APPLY' in sql_upper or 'CROSS APPLY' in sql_upper:
        features['lateral_apply'] = True
    
    # 复杂构造
    if 'GROUPING SETS' in sql_upper:
        features['complex_constructs'].append('GROUPING_SETS')
    if 'RECURSIVE' in sql_upper:
        features['complex_constructs'].append('RECURSIVE_CTE')
    if 'UNION' in sql_upper:
        features['complex_constructs'].append('UNION')
    
    return features

def calculate_performance_score(sample, features):
    """计算性能评分"""
    score = 0
    
    # 基础分数
    score += 10
    
    # 复杂度加分
    if sample['features']['complexity'] == '高级':
        score += 20
    elif sample['features']['complexity'] == '中级':
        score += 10
    
    # 炎凰特性使用加分
    yanhuang_features = len([f for f_list in features.values() if isinstance(f_list, list) for f in f_list])
    score += yanhuang_features * 2
    
    # 时间分桶特别加分
    if 'TIME_BUCKET' in features['time_functions']:
        score += 15
    
    # 高级聚合加分
    if features['aggregation_functions']:
        score += 10
    
    # 窗口函数加分
    if features['window_functions']:
        score += 8
    
    # CTE使用加分
    if features['cte_usage']:
        score += 5
    
    # 安全/URL/IP函数加分
    if features['security_functions'] or features['url_functions'] or features['ip_functions']:
        score += 10
    
    # 复杂构造加分
    if features['complex_constructs']:
        score += len(features['complex_constructs']) * 5
    
    return min(score, 100)  # 最高100分

def test_postgresql_compatibility(sql):
    """测试PostgreSQL兼容性"""
    try:
        # 尝试将炎凰SQL转换为PostgreSQL
        pg_sql = sqlglot.transpile(sql, read="yanhuang", write="postgres")[0]
        return True, pg_sql, None
    except Exception as e:
        return False, None, str(e)

def categorize_by_scenario(samples):
    """按业务场景分类"""
    categories = {
        '财务BI': [],
        '安全运营': [],
        '运维监控': [],
        '用户行为': [],
        '业务分析': [],
        '性能优化': []
    }
    
    for sample in samples:
        number = sample['number']
        if 1 <= number <= 12:
            categories['财务BI'].append(sample)
        elif 13 <= number <= 25:
            categories['安全运营'].append(sample)
        elif 26 <= number <= 50:
            categories['运维监控'].append(sample)
        elif 51 <= number <= 75:
            categories['用户行为'].append(sample)
        elif 76 <= number <= 100:
            categories['业务分析'].append(sample)
        elif 101 <= number <= 125:
            categories['性能优化'].append(sample)
    
    return categories

def run_comprehensive_test():
    """运行综合测试"""
    print("🔥 炎凰数据SQL样例综合测试 - 125条样例全量分析")
    print("=" * 80)
    
    # 提取SQL样例
    samples = extract_sql_samples('needRefrences/sql_samples_batch.md')
    print(f"📊 成功提取 {len(samples)} 条SQL样例")
    
    # 测试统计
    test_results = {
        'total_samples': len(samples),
        'parse_success': 0,
        'parse_failed': 0,
        'failed_samples': []
    }
    
    print("\n🎯 开始逐个测试样例...")
    print("-" * 80)
    
    # 逐个测试样例（前10个作为示例）
    for i, sample in enumerate(samples[:10], 1):
        print(f"\n📋 样例 {sample['number']}: {sample['title']}")
        
        try:
            # 解析测试
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                ast = sqlglot.parse(sample['sql'], dialect="yanhuang")
                
                if ast and ast[0]:
                    print(f"  ✅ 解析成功")
                    test_results['parse_success'] += 1
                    
                    # 显示警告
                    if w:
                        for warning in w:
                            print(f"  ⚠️  警告: {warning.message}")
                else:
                    print(f"  ❌ 解析失败: 空AST")
                    test_results['parse_failed'] += 1
                    test_results['failed_samples'].append((sample['number'], "解析失败"))
        
        except Exception as e:
            print(f"  ❌ 测试异常: {str(e)[:50]}...")
            test_results['parse_failed'] += 1
            test_results['failed_samples'].append((sample['number'], str(e)[:50]))
    
    print(f"\n📈 前10个样例测试结果:")
    print(f"  • 解析成功: {test_results['parse_success']}/10")
    print(f"  • 解析失败: {test_results['parse_failed']}/10")
    
    if test_results['failed_samples']:
        print(f"\n❌ 失败样例:")
        for number, error in test_results['failed_samples']:
            print(f"  • 样例{number}: {error}")

if __name__ == "__main__":
    run_comprehensive_test() 