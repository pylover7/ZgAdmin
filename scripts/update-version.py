#!/usr/bin/env python3
"""
统一版本管理脚本
"""
import os
import re
import json
import sys
from pathlib import Path

def get_current_version():
    """获取当前版本号"""
    version_file = Path(__file__).parent.parent / "VERSION"
    return version_file.read_text().strip()

def increment_version(version, increment_type):
    """递增版本号"""
    try:
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError("版本号格式不正确，应为 x.y.z")
        
        major, minor, patch = map(int, parts)
        
        if increment_type == "patch":
            patch += 1
        elif increment_type == "minor":
            minor += 1
            patch = 0
        elif increment_type == "major":
            major += 1
            minor = 0
            patch = 0
        else:
            raise ValueError("递增类型必须是 patch, minor, 或 major")
            
        return f"{major}.{minor}.{patch}"
    except ValueError as e:
        print(f"错误: {e}")
        return None

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

def show_version_info():
    """显示当前版本信息"""
    version_file = Path(__file__).parent.parent / "VERSION"
    package_file = Path(__file__).parent.parent / "frontend" / "package.json"
    pyproject_file = Path(__file__).parent.parent / "backend" / "pyproject.toml"
    
    print("===== 当前版本信息 =====")
    print(f"VERSION 文件: {version_file.read_text().strip()}")
    
    try:
        with open(package_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"前端 package.json: {data.get('version', 'N/A')}")
    except:
        print("前端 package.json: 读取失败")
    
    try:
        content = pyproject_file.read_text(encoding='utf-8')
        match = re.search(r'version = "(.*?)"', content)
        if match:
            print(f"后端 pyproject.toml: {match.group(1)}")
        else:
            print("后端 pyproject.toml: 未找到版本信息")
    except:
        print("后端 pyproject.toml: 读取失败")
    print("========================")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='统一更新项目版本')
    parser.add_argument('version', nargs='?', help='新版本号（如 1.2.3）')
    parser.add_argument('--frontend-only', action='store_true', help='只更新前端版本')
    parser.add_argument('--backend-only', action='store_true', help='只更新后端版本')
    parser.add_argument('--patch', action='store_true', help='递增补丁版本号')
    parser.add_argument('--minor', action='store_true', help='递增次版本号')
    parser.add_argument('--major', action='store_true', help='递增主版本号')
    parser.add_argument('--show', action='store_true', help='显示当前版本信息')
    parser.add_argument('--no-build', action='store_true', help='跳过构建项目')
    
    args = parser.parse_args()
    
    if args.show:
        show_version_info()
        return
    
    # 处理版本号
    if args.patch or args.minor or args.major:
        current_version = get_current_version()
        if args.patch:
            new_version = increment_version(current_version, "patch")
        elif args.minor:
            new_version = increment_version(current_version, "minor")
        elif args.major:
            new_version = increment_version(current_version, "major")
        
        if not new_version:
            print("版本号递增失败")
            sys.exit(1)
    elif args.version:
        new_version = args.version
    else:
        new_version = get_current_version()
    
    print(f"更新版本到: {new_version}")
    
    # 更新 VERSION 文件
    version_file = Path(__file__).parent.parent / "VERSION"
    version_file.write_text(new_version + '\n')
    
    # 更新其他文件
    if args.frontend_only:
        update_frontend_package_json(new_version)
        update_frontend_env(new_version)
    elif args.backend_only:
        update_backend_pyproject(new_version)
    else:
        update_frontend_package_json(new_version)
        update_backend_pyproject(new_version)
        update_readme(new_version)
        update_frontend_env(new_version)
    
    print(f"版本更新完成！当前版本: {new_version}")
    
    # 询问是否构建
    if not args.no_build and not (args.frontend_only or args.backend_only):
        print("\n是否要构建项目？(y/n)")
        response = input().strip().lower()
        if response in ['y', 'yes', '是']:
            print("开始构建项目...")
            os.system("chmod +x build.sh && ./build.sh")

if __name__ == "__main__":
    main()