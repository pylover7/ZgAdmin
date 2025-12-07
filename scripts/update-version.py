#!/usr/bin/env python3
"""
统一版本管理脚本
"""
import os
import re
import json
from pathlib import Path

def get_current_version():
    """获取当前版本号"""
    version_file = Path(__file__).parent.parent / "VERSION"
    return version_file.read_text().strip()

def update_frontend_package_json(version):
    """更新前端 package.json 版本"""
    package_file = Path(__file__).parent.parent / "frontend" / "package.json"
    with open(package_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['version'] = version
    with open(package_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"前端版本已更新为: {version}")

def update_backend_pyproject(version):
    """更新后端 pyproject.toml 版本"""
    pyproject_file = Path(__file__).parent.parent / "backend" / "pyproject.toml"
    content = pyproject_file.read_text(encoding='utf-8')
    content = re.sub(r'version = ".*"', f'version = "{version}"', content)
    pyproject_file.write_text(content, encoding='utf-8')
    print(f"后端版本已更新为: {version}")

def update_readme(version):
    """更新 README.md 中的版本信息"""
    readme_file = Path(__file__).parent.parent / "README.md"
    content = readme_file.read_text(encoding='utf-8')
    
    # 更新版本号
    content = re.sub(r'当前版本: .*', f'当前版本: {version}', content)
    
    readme_file.write_text(content, encoding='utf-8')
    print(f"README 版本已更新为: {version}")

def update_frontend_env(version):
    """创建前端版本环境文件"""
    env_file = Path(__file__).parent.parent / "frontend" / ".env.version"
    env_file.write_text(f"VITE_APP_VERSION={version}\n", encoding='utf-8')
    print(f"前端环境版本文件已更新为: {version}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='统一更新项目版本')
    parser.add_argument('version', nargs='?', help='新版本号（如不提供则使用 VERSION 文件中的版本）')
    parser.add_argument('--frontend-only', action='store_true', help='只更新前端版本')
    parser.add_argument('--backend-only', action='store_true', help='只更新后端版本')
    
    args = parser.parse_args()
    
    if args.version:
        version = args.version
        # 更新 VERSION 文件
        version_file = Path(__file__).parent.parent / "VERSION"
        version_file.write_text(version + '\n')
    else:
        version = get_current_version()
    
    print(f"更新版本到: {version}")
    
    if args.frontend_only:
        update_frontend_package_json(version)
        update_frontend_env(version)
    elif args.backend_only:
        update_backend_pyproject(version)
    else:
        # 更新所有
        update_frontend_package_json(version)
        update_backend_pyproject(version)
        update_readme(version)
        update_frontend_env(version)
    
    print(f"版本更新完成！当前版本: {version}")

if __name__ == "__main__":
    main()