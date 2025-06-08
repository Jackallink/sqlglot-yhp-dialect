#!/usr/bin/env python3
"""
炎凰数据SQL样例测试脚本
测试 sql_samples_batch1.md 中的真实炎凰SQL语句
"""

import sqlglot
import warnings
import re
from typing import List, Dict, Tuple

def extract_sql_samples(md_file: str) -> List[Dict]:
    """从Markdown文件中提取SQL样例"""
    samples = []
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式提取SQL块
        sql_pattern = r'```sql\n(.*?)\n```'
        sql_blocks = re.findall(sql_pattern, content, re.DOTALL)
        
        # 提取注释中的元数据
        comment_pattern = r'-- 目的: (.*?) \| 复杂度: (.*?) \| 炎凰特性: (.*?) \| 类型: (.*?)\n'
        
        for i, sql_block in enumerate(sql_blocks, 1):
            # 查找注释元数据
            comment_match = re.search(comment_pattern, sql_block)
            
            if comment_match:
                purpose = comment_match.group(1).strip()
                complexity = comment_match.group(2).strip()
                features = comment_match.group(3).strip()
                sql_type = comment_match.group(4).strip()
                
                # 移除注释，获取纯SQL
                sql_clean = re.sub(r'--.*?\n', '\n', sql_block).strip()
                
                samples.append({
                    'id': i,
                    'purpose': purpose,
                    'complexity': complexity,
                    'features': features,
                    'type': sql_type,
                    'sql': sql_clean
                })
                
    except Exception as e:
        print(f"❌ 读取SQL样例文件失败: {e}")
    
    return samples

def test_yanhuang_sql_sample(sample: Dict) -> Dict:
    """测试单个炎凰SQL样例"""
    result = {
        'id': sample['id'],
        'purpose': sample['purpose'],
        'complexity': sample['complexity'],
        'features': sample['features'],
        'original_sql': sample['sql'],
        'status': 'unknown',
        'parsed_ast': None,
        'formatted_sql': None,
        'warnings': [],
        'error': None,
        'feature_analysis': {},
        'performance_score': 0
    }
    
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # 1. 解析SQL为AST
            parsed = sqlglot.parse(sample['sql'], dialect='yanhuang')[0]
            result['parsed_ast'] = str(parsed)
            
            # 2. 格式化SQL
            formatted = parsed.sql(dialect='yanhuang', pretty=True)
            result['formatted_sql'] = formatted
            
            # 3. 记录警告
            if w:
                result['warnings'] = [str(warning.message) for warning in w]
            
            # 4. 分析炎凰特性使用
            result['feature_analysis'] = analyze_yanhuang_features(sample['sql'])
            
            # 5. 计算性能评分
            result['performance_score'] = calculate_performance_score(sample['sql'], sample['complexity'])
            
            result['status'] = 'success'
            
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
    
    return result

def analyze_yanhuang_features(sql: str) -> Dict:
    """分析SQL中使用的炎凰数据特性"""
    features = {
        'time_bucket': 'TIME_BUCKET(' in sql,
        'date_functions': any(func in sql for func in ['DATE_ADD(', 'DATE_DIFF(', 'DATE_PART(']),
        'window_functions': any(func in sql for func in ['ROW_NUMBER()', 'RANK(', 'LAG(', 'LEAD(', 'NTILE(']),
        'aggregation_enhanced': any(func in sql for func in ['LATEST_VALUE(', 'EARLIEST_VALUE(', 'APPROX_COUNT_DISTINCT(']),
        'string_enhanced': any(func in sql for func in ['CONTAINS(', 'CHAR_LENGTH(', 'SPLIT_PART(']),
        'hash_functions': any(func in sql for func in ['HASH_MD5(', 'HASH_SHA256(', 'HASH_SHA1(', 'CRC32(']),
        'ip_analysis': any(func in sql for func in ['CIDR_MATCH(', 'IS_IPV4_LOOPBACK(', 'IP_TO_INT(']),
        'url_functions': any(func in sql for func in ['DOMAIN(', 'PATH(', 'PROTOCOL(', 'QUERY_STRING(']),
        'table_functions': 'OUTER APPLY' in sql,
        'regex_functions': any(func in sql for func in ['REGEX_LIKE(', 'REGEXP_REPLACE(']),
        'json_functions': any(op in sql for op in ['JSON_EXTRACT_PATH(', 'JSON_EXTRACT_PATH_TEXT(']),
        'array_functions': any(func in sql for func in ['ARRAY_LENGTH(', 'SPLIT_PART(']),
        'cte_usage': 'WITH ' in sql and ' AS (' in sql,
        'complex_joins': sql.count('JOIN') >= 2,
        'subqueries': sql.count('SELECT') >= 2
    }
    
    return {k: v for k, v in features.items() if v}

def calculate_performance_score(sql: str, complexity: str) -> int:
    """计算SQL性能评分"""
    score = 0
    
    # 基础分数根据复杂度
    complexity_scores = {'简单': 20, '高级': 50, '中等': 35}
    score += complexity_scores.get(complexity, 30)
    
    # 炎凰特性使用加分
    if 'TIME_BUCKET(' in sql:
        score += 15  # 时间分桶高效
    if any(func in sql for func in ['LATEST_VALUE(', 'EARLIEST_VALUE(']):
        score += 10  # 时间序列优化
    if 'APPROX_COUNT_DISTINCT(' in sql:
        score += 8   # 近似计算优化
    if any(func in sql for func in ['HASH_MD5(', 'HASH_SHA256(']):
        score += 5   # 内置哈希函数
    if 'CIDR_MATCH(' in sql:
        score += 8   # IP分析优化
    if 'OUTER APPLY' in sql:
        score += 12  # 表函数高效
    
    # 复杂度惩罚
    if sql.count('JOIN') > 3:
        score -= 5
    if sql.count('SELECT') > 4:
        score -= 3
    if len(sql) > 2000:
        score -= 5
    
    return max(score, 0)

def categorize_samples(results: List[Dict]) -> Dict:
    """按场景和复杂度分类样例"""
    categories = {
        'by_scenario': {'财务BI': [], '安全运营': []},
        'by_complexity': {'简单': [], '高级': [], '中等': []},
        'by_status': {'success': [], 'error': []},
        'by_features': {}
    }
    
    for result in results:
        # 按场景分类
        if result['id'] <= 12:
            categories['by_scenario']['财务BI'].append(result)
        else:
            categories['by_scenario']['安全运营'].append(result)
        
        # 按复杂度分类
        categories['by_complexity'][result['complexity']].append(result)
        
        # 按状态分类
        categories['by_status'][result['status']].append(result)
        
        # 按特性分类
        for feature in result['feature_analysis']:
            if feature not in categories['by_features']:
                categories['by_features'][feature] = []
            categories['by_features'][feature].append(result)
    
    return categories

def print_test_report(results: List[Dict], categories: Dict):
    """打印测试报告"""
    total = len(results)
    successful = len(categories['by_status']['success'])
    failed = len(categories['by_status']['error'])
    
    print(f"📊 炎凰数据SQL样例测试报告")
    print("=" * 60)
    
    # 总体统计
    print(f"📈 总体测试统计:")
    print(f"   🎯 总样例数量: {total}")
    print(f"   ✅ 测试通过: {successful} ({successful/total*100:.1f}%)")
    print(f"   ❌ 测试失败: {failed} ({failed/total*100:.1f}%)")
    
    # 场景分类统计
    print(f"\n📋 场景分类统计:")
    for scenario, samples in categories['by_scenario'].items():
        success_count = len([s for s in samples if s['status'] == 'success'])
        print(f"   📝 {scenario}: {len(samples)}个样例 ({success_count}/{len(samples)} 通过)")
    
    # 复杂度分类统计
    print(f"\n🔧 复杂度分类统计:")
    for complexity, samples in categories['by_complexity'].items():
        success_count = len([s for s in samples if s['status'] == 'success'])
        avg_score = sum(s['performance_score'] for s in samples) / len(samples) if samples else 0
        print(f"   📊 {complexity}: {len(samples)}个样例 ({success_count}/{len(samples)} 通过, 平均性能评分: {avg_score:.1f})")
    
    # 炎凰特性使用统计
    print(f"\n🚀 炎凰特性使用统计:")
    for feature, samples in sorted(categories['by_features'].items(), key=lambda x: len(x[1]), reverse=True):
        feature_name = {
            'time_bucket': '时间分桶',
            'date_functions': '日期函数',
            'window_functions': '窗口函数',
            'aggregation_enhanced': '增强聚合',
            'string_enhanced': '字符串增强',
            'hash_functions': '哈希函数',
            'ip_analysis': 'IP分析',
            'url_functions': 'URL函数',
            'table_functions': '表函数',
            'regex_functions': '正则函数',
            'json_functions': 'JSON函数',
            'array_functions': '数组函数',
            'cte_usage': 'CTE查询',
            'complex_joins': '复杂关联',
            'subqueries': '子查询'
        }.get(feature, feature)
        
        print(f"   🔹 {feature_name}: {len(samples)}个样例")
    
    # 显示高性能样例
    high_performance = sorted([r for r in results if r['status'] == 'success'], 
                             key=lambda x: x['performance_score'], reverse=True)
    
    print(f"\n🌟 高性能样例 (Top 5):")
    for i, sample in enumerate(high_performance[:5], 1):
        print(f"\n--- 样例 {i} (评分: {sample['performance_score']}) ---")
        print(f"📝 目的: {sample['purpose']}")
        print(f"🔧 复杂度: {sample['complexity']}")
        print(f"🚀 炎凰特性: {', '.join(sample['feature_analysis'].keys())}")
        print(f"💾 SQL: {sample['original_sql'][:100]}{'...' if len(sample['original_sql']) > 100 else ''}")
    
    # 显示失败样例
    if failed > 0:
        error_samples = categories['by_status']['error']
        print(f"\n❌ 失败样例:")
        for i, sample in enumerate(error_samples[:3], 1):
            print(f"\n--- 失败样例 {i} ---")
            print(f"📝 目的: {sample['purpose']}")
            print(f"❌ 错误: {sample['error']}")
            print(f"💾 SQL: {sample['original_sql'][:100]}{'...' if len(sample['original_sql']) > 100 else ''}")
    
    # 显示警告样例
    warning_samples = [r for r in results if r['warnings']]
    if warning_samples:
        print(f"\n⚠️  警告样例:")
        for i, sample in enumerate(warning_samples[:3], 1):
            print(f"\n--- 警告样例 {i} ---")
            print(f"📝 目的: {sample['purpose']}")
            for warning in sample['warnings']:
                print(f"⚠️  警告: {warning}")

def main():
    """主函数"""
    print("🎯 炎凰数据SQL样例综合测试")
    print("=" * 60)
    
    # 提取SQL样例
    samples = extract_sql_samples('needRefrences/sql_samples_batch1.md')
    
    if not samples:
        print("❌ 没有找到SQL样例")
        return
    
    print(f"📁 从样例文件中提取了 {len(samples)} 个SQL样例")
    
    # 执行测试
    print(f"\n🔄 开始测试SQL样例...")
    results = []
    
    for i, sample in enumerate(samples, 1):
        result = test_yanhuang_sql_sample(sample)
        results.append(result)
        
        # 显示进度
        if i % 5 == 0:
            success_so_far = len([r for r in results if r['status'] == 'success'])
            print(f"   处理进度: {i}/{len(samples)} (成功率: {success_so_far/i*100:.1f}%)")
    
    # 分类结果
    categories = categorize_samples(results)
    
    # 生成报告
    print_test_report(results, categories)
    
    # 总结
    success_rate = len(categories['by_status']['success']) / len(results) * 100
    avg_performance = sum(r['performance_score'] for r in results if r['status'] == 'success') / len(categories['by_status']['success'])
    
    print(f"\n💡 测试总结:")
    print(f"   🌟 炎凰数据SQL样例成功率: {success_rate:.1f}%")
    print(f"   ⚡ 平均性能评分: {avg_performance:.1f}")
    print(f"   🚀 涵盖了{len(categories['by_features'])}种炎凰数据特性")
    print(f"   📊 支持财务BI和安全运营两大核心场景")
    print(f"   🔧 从简单到高级的完整复杂度覆盖")

if __name__ == "__main__":
    main() 