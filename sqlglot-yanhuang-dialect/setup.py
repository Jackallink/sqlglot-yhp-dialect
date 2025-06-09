#!/usr/bin/env python3
from setuptools import setup, find_packages

# 读取 README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取版本
with open("sqlglot_yanhuang/__init__.py", "r", encoding="utf-8") as fh:
    for line in fh:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

setup(
    name="sqlglot-yanhuang-dialect",
    version=version,
    author="炎凰数据团队",
    author_email="support@yanhuangdata.com",
    description="炎凰数据 SQL 方言包 - SQLGlot 扩展",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yanhuangdata/sqlglot-yanhuang-dialect",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "sqlglot>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "yanhuang-transpile=sqlglot_yanhuang.cli:main",
        ],
    },
    keywords="sql, database, yanhuang, transpile, dialect, sqlglot",
    project_urls={
        "Bug Reports": "https://github.com/yanhuangdata/sqlglot-yanhuang-dialect/issues",
        "Source": "https://github.com/yanhuangdata/sqlglot-yanhuang-dialect",
        "Documentation": "https://docs.yanhuangdata.com/sqlglot-dialect",
    },
)
