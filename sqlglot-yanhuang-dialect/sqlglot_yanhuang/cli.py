#!/usr/bin/env python3
"""
炎凰数据 SQL 方言命令行工具
"""
import argparse
import sys
from typing import Optional
from . import transpile_to_yanhuang, __version__

def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(
        description="炎凰数据 SQL 方言转换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  yanhuang-transpile "SELECT EXTRACT(year FROM created_at)"
  yanhuang-transpile --file input.sql --output output.sql
  echo "SELECT CURRENT_TIMESTAMP" | yanhuang-transpile --stdin
        """
    )
    
    parser.add_argument(
        "sql", 
        nargs="?", 
        help="要转换的 SQL 语句"
    )
    
    parser.add_argument(
        "--file", "-f",
        help="输入 SQL 文件路径"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认输出到标准输出）"
    )
    
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="从标准输入读取 SQL"
    )
    
    parser.add_argument(
        "--source", "-s",
        default="postgres",
        help="源方言（默认: postgres）"
    )
    
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="格式化输出"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"sqlglot-yanhuang-dialect {__version__}"
    )
    
    args = parser.parse_args()
    
    # 获取输入 SQL
    sql_input: Optional[str] = None
    
    if args.sql:
        sql_input = args.sql
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                sql_input = f.read()
        except FileNotFoundError:
            print(f"错误：文件 '{args.file}' 不存在", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"错误：读取文件 '{args.file}' 失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.stdin:
        try:
            sql_input = sys.stdin.read()
        except KeyboardInterrupt:
            print("\n操作被取消", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
    
    if not sql_input or not sql_input.strip():
        print("错误：没有提供 SQL 输入", file=sys.stderr)
        sys.exit(1)
    
    # 转换 SQL
    try:
        result = transpile_to_yanhuang(sql_input.strip(), args.source)
        
        # 输出结果
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"✅ 转换完成，结果已保存到 '{args.output}'", file=sys.stderr)
            except Exception as e:
                print(f"错误：写入文件 '{args.output}' 失败: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(result)
            
    except Exception as e:
        print(f"错误：SQL 转换失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 