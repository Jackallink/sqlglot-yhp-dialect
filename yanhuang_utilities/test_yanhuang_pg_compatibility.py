#!/usr/bin/env python3
"""
炎凰SQL与PostgreSQL兼容性测试
测试炎凰SQL样例在PostgreSQL方言下的转换情况
"""

import sqlglot
import warnings
from test_yanhuang_sql_samples import extract_sql_samples

def test_yanhuang_to_postgresql_conversion(sample: dict) -> dict:
    """测试炎凰SQL到PostgreSQL的转换"""
    result = {
        'id': sample['id'],
        'purpose': sample['purpose'],
        'original_yanhuang': sample['sql'],
        'converted_postgresql': None,
        'status': 'unknown',
        'warnings': [],
        'error': None,
        'compatibility_issues': [],
        'yanhuang_specific_features': []
    }
    
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # 1. 解析炎凰SQL
            parsed = sqlglot.parse(sample['sql'], dialect='yanhuang')[0]
            
            # 2. 转换为PostgreSQL
            postgresql_sql = parsed.sql(dialect='postgres', pretty=True)
            result['converted_postgresql'] = postgresql_sql
            
            # 3. 记录警告
            if w:
                result['warnings'] = [str(warning.message) for warning in w]
            
            # 4. 分析兼容性问题
            result['compatibility_issues'] = analyze_compatibility_issues(sample['sql'], postgresql_sql)
            
            # 5. 识别炎凰特有功能
            result['yanhuang_specific_features'] = identify_yanhuang_features(sample['sql'])
            
            result['status'] = 'success'
            
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
    
    return result

def analyze_compatibility_issues(yanhuang_sql: str, postgresql_sql: str) -> list:
    """分析兼容性问题"""
    issues = []
    
    # 炎凰特有函数在PostgreSQL中的问题
    yanhuang_specific = {
        'TIME_BUCKET(': 'PostgreSQL需要使用date_trunc()替代',
        'LATEST_VALUE(': 'PostgreSQL使用last_value()替代',
        'EARLIEST_VALUE(': 'PostgreSQL使用first_value()替代',
        'HASH_MD5(': 'PostgreSQL使用md5()替代',
        'HASH_SHA256(': 'PostgreSQL需要pgcrypto扩展',
        'CIDR_MATCH(': 'PostgreSQL使用网络操作符替代',
        'DOMAIN(': 'PostgreSQL需要自定义函数',
        'PATH(': 'PostgreSQL需要自定义函数',
        'PROTOCOL(': 'PostgreSQL需要自定义函数',
        'OUTER APPLY': 'PostgreSQL使用LATERAL JOIN替代',
        'CONTAINS(': 'PostgreSQL使用LIKE或position()替代',
        'APPROX_COUNT_DISTINCT(': 'PostgreSQL 9.4+支持'
    }
    
    for func, issue in yanhuang_specific.items():
        if func in yanhuang_sql:
            if func not in postgresql_sql:
                issues.append(f"{func.rstrip('(')}: {issue}")
    
    return issues

def identify_yanhuang_features(sql: str) -> list:
    """识别炎凰数据特有功能"""
    features = []
    
    yanhuang_features = {
        'TIME_BUCKET(': '时间分桶',
        'LATEST_VALUE(': '最新值聚合',
        'EARLIEST_VALUE(': '最早值聚合', 
        'HASH_MD5(': 'MD5哈希',
        'HASH_SHA256(': 'SHA256哈希',
        'CIDR_MATCH(': 'CIDR网段匹配',
        'DOMAIN(': 'URL域名提取',
        'PATH(': 'URL路径提取',
        'PROTOCOL(': 'URL协议提取',
        'OUTER APPLY': '表函数应用',
        'CONTAINS(': '字符串包含',
        'APPROX_COUNT_DISTINCT(': '近似唯一计数',
        'CRC32(': 'CRC32哈希',
        'IS_IPV4_LOOPBACK(': 'IPv4回环检测',
        'CHAR_LENGTH(': '字符长度',
        'QUERY_STRING(': 'URL查询字符串提取'
    }
    
    for func, desc in yanhuang_features.items():
        if func in sql:
            features.append(desc)
    
    return features

def print_compatibility_report(results: list):
    """打印兼容性报告"""
    total = len(results)
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'error'])
    
    print(f"📊 炎凰SQL到PostgreSQL兼容性报告")
    print("=" * 60)
    
    # 总体统计
    print(f"📈 转换统计:")
    print(f"   🎯 总样例数量: {total}")
    print(f"   ✅ 转换成功: {successful} ({successful/total*100:.1f}%)")
    print(f"   ❌ 转换失败: {failed} ({failed/total*100:.1f}%)")
    
    # 兼容性问题统计
    all_issues = []
    for r in results:
        if r['status'] == 'success':
            all_issues.extend(r['compatibility_issues'])
    
    if all_issues:
        from collections import Counter
        issue_counts = Counter(all_issues)
        
        print(f"\n⚠️  兼容性问题统计 (Top 10):")
        for issue, count in issue_counts.most_common(10):
            print(f"   • {issue}: {count}个样例")
    
    # 炎凰特有功能统计
    all_features = []
    for r in results:
        if r['status'] == 'success':
            all_features.extend(r['yanhuang_specific_features'])
    
    if all_features:
        from collections import Counter
        feature_counts = Counter(all_features)
        
        print(f"\n🚀 炎凰特有功能使用统计:")
        for feature, count in feature_counts.most_common():
            print(f"   • {feature}: {count}个样例")
    
    # 显示转换示例
    successful_results = [r for r in results if r['status'] == 'success']
    if successful_results:
        print(f"\n✅ 转换成功示例 (前3个):")
        for i, result in enumerate(successful_results[:3], 1):
            print(f"\n--- 示例 {i} ---")
            print(f"📝 目的: {result['purpose']}")
            print(f"🔧 炎凰SQL: {result['original_yanhuang'][:100]}{'...' if len(result['original_yanhuang']) > 100 else ''}")
            print(f"🔄 PostgreSQL: {result['converted_postgresql'][:100]}{'...' if len(result['converted_postgresql']) > 100 else ''}")
            
            if result['yanhuang_specific_features']:
                print(f"🚀 炎凰特性: {', '.join(result['yanhuang_specific_features'])}")
            
            if result['compatibility_issues']:
                print(f"⚠️  兼容性问题:")
                for issue in result['compatibility_issues'][:2]:
                    print(f"   • {issue}")
    
    # 显示失败示例
    failed_results = [r for r in results if r['status'] == 'error']
    if failed_results:
        print(f"\n❌ 转换失败示例:")
        for i, result in enumerate(failed_results[:3], 1):
            print(f"\n--- 失败示例 {i} ---")
            print(f"📝 目的: {result['purpose']}")
            print(f"❌ 错误: {result['error']}")

def main():
    """主函数"""
    print("🎯 炎凰SQL与PostgreSQL兼容性测试")
    print("=" * 60)
    
    # 提取SQL样例
    samples = extract_sql_samples('needRefrences/sql_samples_batch1.md')
    
    if not samples:
        print("❌ 没有找到SQL样例")
        return
    
    print(f"📁 加载了 {len(samples)} 个炎凰SQL样例")
    
    # 执行兼容性测试
    print(f"\n🔄 开始兼容性测试...")
    results = []
    
    for i, sample in enumerate(samples, 1):
        result = test_yanhuang_to_postgresql_conversion(sample)
        results.append(result)
        
        # 显示进度
        if i % 5 == 0:
            success_so_far = len([r for r in results if r['status'] == 'success'])
            print(f"   处理进度: {i}/{len(samples)} (成功率: {success_so_far/i*100:.1f}%)")
    
    # 生成报告
    print_compatibility_report(results)
    
    # 总结
    success_rate = len([r for r in results if r['status'] == 'success']) / len(results) * 100
    total_issues = sum(len(r['compatibility_issues']) for r in results if r['status'] == 'success')
    total_features = sum(len(r['yanhuang_specific_features']) for r in results if r['status'] == 'success')
    
    print(f"\n💡 兼容性总结:")
    print(f"   🔄 语法转换成功率: {success_rate:.1f}%")
    print(f"   ⚠️  识别兼容性问题: {total_issues}个")
    print(f"   🚀 炎凰特有功能: {total_features}个")
    print(f"   📊 炎凰数据在时序分析和安全场景有独特优势")
    print(f"   🔧 迁移到PostgreSQL需要相应的函数映射和扩展支持")

if __name__ == "__main__":
    main() 