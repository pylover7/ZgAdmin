#!/usr/bin/env python3
"""
统一版本管理脚本
"""
import os
import re
import json
import sys
from pathlib import Path

class VersionManager:
    """版本管理器 - 统一管理文件路径和操作"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.version_file = self.root_dir / "VERSION"
        self.package_file = self.root_dir / "frontend" / "package.json"
        self.pyproject_file = self.root_dir / "backend" / "pyproject.toml"
        self.readme_file = self.root_dir / "README.md"
        self.env_file = self.root_dir / "frontend" / ".env.version"
        # 缓存文件存在状态以避免重复检查
        self._file_cache = {}
    
    def ensure_version_file_exists(self):
        """确保 VERSION 文件存在"""
        if not self.version_file.exists():
            self.version_file.write_text("1.0.0\n")
            print(f"已创建 VERSION 文件，默认版本: 1.0.0")
        return True
    
    def get_current_version_cached(self):
        """获取当前版本号（带缓存）"""
        if not self.ensure_version_file_exists():
            raise IOError("无法创建 VERSION 文件")
        return self.version_file.read_text().strip()
    
    def parse_version(self, version_string):
        """解析版本号字符串为数字元组"""
        parts = version_string.split('.')
        if len(parts) != 3:
            raise ValueError(f"版本号格式不正确: {version_string}，应为 x.y.z 格式")
        
        try:
            major, minor, patch = map(int, parts)
            return major, minor, patch
        except ValueError as e:
            raise ValueError(f"版本号必须为数字: {version_string}") from e

# 全局版本管理器实例
version_manager = VersionManager()

def validate_version_format(version):
    """验证版本号格式 (x.y.z)"""
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        raise ValueError(f"版本号格式不正确: {version}，应为 x.y.z 格式")
    return version

def get_current_version():
    """获取当前版本号"""
    return version_manager.get_current_version_cached()

def increment_version(version, increment_type):
    """递增版本号"""
    try:
        # 使用统一的版本解析逻辑
        major, minor, patch = version_manager.parse_version(version)
        
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

def validate_arguments(args):
    """验证命令行参数的冲突性"""
    increment_types = [args.patch, args.minor, args.major]
    if sum(increment_types) > 1:
        raise ValueError("错误: 不能同时指定多个版本递增类型 (--patch, --minor, --major)")
    
    if args.version and any(increment_types):
        raise ValueError("错误: 不能同时指定自定义版本号和递增参数")
    
    if args.show and any([args.version, args.patch, args.minor, args.major]):
        raise ValueError("错误: --show 参数不能与其他版本操作参数同时使用")
    
    return True

def update_frontend_package_json(version):
    """更新前端 package.json 版本"""
    try:
        if not version_manager.package_file.exists():
            print(f"警告: {version_manager.package_file} 文件不存在，跳过前端版本更新")
            return
            
        with open(version_manager.package_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['version'] = version
        with open(version_manager.package_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"前端版本已更新为: {version}")
    except (json.JSONDecodeError, IOError) as e:
        print(f"更新前端版本失败: {e}")

def update_backend_pyproject(version):
    """更新后端 pyproject.toml 版本"""
    try:
        if not version_manager.pyproject_file.exists():
            print(f"警告: {version_manager.pyproject_file} 文件不存在，跳过后端版本更新")
            return
            
        content = version_manager.pyproject_file.read_text(encoding='utf-8')
        content = re.sub(r'version = ".*"', f'version = "{version}"', content)
        version_manager.pyproject_file.write_text(content, encoding='utf-8')
        print(f"后端版本已更新为: {version}")
    except (IOError, re.error) as e:
        print(f"更新后端版本失败: {e}")

def update_readme(version):
    """更新 README.md 中的版本信息"""
    try:
        if not version_manager.readme_file.exists():
            print(f"警告: {version_manager.readme_file} 文件不存在，跳过 README 版本更新")
            return
            
        content = version_manager.readme_file.read_text(encoding='utf-8')
        # 更新版本号
        content = re.sub(r'当前版本: .*', f'当前版本: {version}', content)
        version_manager.readme_file.write_text(content, encoding='utf-8')
        print(f"README 版本已更新为: {version}")
    except (IOError, re.error) as e:
        print(f"更新 README 版本失败: {e}")

def update_frontend_env(version):
    """创建前端版本环境文件"""
    try:
        # 确保前端目录存在
        version_manager.env_file.parent.mkdir(parents=True, exist_ok=True)
        version_manager.env_file.write_text(f"VITE_APP_VERSION={version}\n", encoding='utf-8')
        print(f"前端环境版本文件已更新为: {version}")
    except (IOError, OSError) as e:
        print(f"更新前端环境版本失败: {e}")

def show_version_info():
    """显示当前版本信息"""
    print("===== 当前版本信息 =====")
    
    # 获取所有文件状态信息（批量检查）
    files_info = {
        'VERSION': {
            'file': version_manager.version_file,
            'type': 'version',
            'desc': 'VERSION 文件'
        },
        'frontend': {
            'file': version_manager.package_file,
            'type': 'json',
            'desc': '前端 package.json',
            'key': 'version'
        },
        'backend': {
            'file': version_manager.pyproject_file,
            'type': 'toml',
            'desc': '后端 pyproject.toml',
            'pattern': r'version = "(.*?)"'
        },
        'env': {
            'file': version_manager.env_file,
            'type': 'env',
            'desc': '前端环境变量',
            'pattern': r'VITE_APP_VERSION=(.*)'
        }
    }
    
    for file_key, file_info in files_info.items():
        try:
            if file_key == 'VERSION':
                version_manager.ensure_version_file_exists()
                version = file_info['file'].read_text().strip()
                print(f"{file_info['desc']}: {version}")
            elif not file_info['file'].exists():
                print(f"{file_info['desc']}: 文件不存在")
            else:
                content = file_info['file'].read_text(encoding='utf-8')
                
                if file_info['type'] == 'json':
                    data = json.loads(content)
                    version = data.get(file_info['key'], 'N/A')
                    print(f"{file_info['desc']}: {version}")
                elif file_info['type'] in ['toml', 'env']:
                    match = re.search(file_info['pattern'], content)
                    if match:
                        print(f"{file_info['desc']}: {match.group(1)}")
                    else:
                        print(f"{file_info['desc']}: 未找到版本信息")
        except (IOError, json.JSONDecodeError, re.error) as e:
            print(f"{file_info['desc']}: 读取失败 - {e}")
    
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
    
    # 验证参数冲突
    try:
        validate_arguments(args)
    except ValueError as e:
        print(e)
        sys.exit(1)
    
    if args.show:
        show_version_info()
        return
    
    # 处理版本号
    new_version = None
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
        # 验证自定义版本号格式
        try:
            new_version = validate_version_format(args.version)
        except ValueError as e:
            print(f"错误: {e}")
            sys.exit(1)
    else:
        new_version = get_current_version()
    
    print(f"更新版本到: {new_version}")
    
    # 更新 VERSION 文件
    try:
        version_manager.version_file.write_text(new_version + '\n')
        print(f"VERSION 文件已更新为: {new_version}")
    except (IOError, OSError) as e:
        print(f"错误: 无法更新 VERSION 文件 - {e}")
        sys.exit(1)
    
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