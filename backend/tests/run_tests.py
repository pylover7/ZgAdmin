#!/usr/bin/env python3
"""
测试运行器
提供便捷的测试运行接口
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def run_pytest(test_path=None, coverage=False, verbose=False, specific_tests=None):
    """运行pytest测试"""
    base_cmd = "python -m pytest"
    
    # 添加测试路径
    if test_path:
        test_path = Path(test_path)
        if not test_path.exists():
            print(f"测试路径不存在: {test_path}")
            return 1
        
        test_args = str(test_path)
    else:
        test_args = "tests/"
    
    # 添加覆盖率参数
    if coverage:
        coverage_args = [
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ]
        test_args += f" {' '.join(coverage_args)}"
    
    # 添加详细输出
    if verbose:
        test_args += " -v"
    
    # 添加特定测试
    if specific_tests:
        for test in specific_tests:
            test_args += f" -k {test}"
    
    # 添加其他有用的参数
    test_args += " --tb=short --strict-markers"
    
    full_cmd = f"{base_cmd} {test_args}"
    print(f"运行命令: {full_cmd}")
    
    # 切换到后端目录
    backend_dir = Path(__file__).parent.parent
    returncode, stdout, stderr = run_command(full_cmd, cwd=backend_dir)
    
    print(stdout)
    if stderr:
        print("错误输出:")
        print(stderr)
    
    return returncode


def run_specific_file(test_file):
    """运行特定测试文件"""
    if not test_file.endswith('.py'):
        test_file += '.py'
    
    test_path = Path("tests") / test_file
    if not test_path.exists():
        print(f"测试文件不存在: {test_path}")
        return 1
    
    return run_pytest(test_path=test_path, verbose=True)


def run_module_tests(module_name):
    """运行特定模块的测试"""
    test_files = {
        'password': 'test_password.py',
        'jwt': 'test_jwtt.py',
        'email': 'test_emails.py',
        'ip': 'test_ip.py',
        'localtime': 'test_localTime.py',
        'exceptions': 'test_exceptions.py',
        'models': 'test_models.py',
        'controllers': 'test_controllers.py',
        'core': 'test_core.py',
        'settings': 'test_settings.py'
    }
    
    if module_name in test_files:
        return run_specific_file(test_files[module_name])
    else:
        print(f"未知的模块名: {module_name}")
        print(f"可用模块: {', '.join(test_files.keys())}")
        return 1


def list_test_files():
    """列出所有测试文件"""
    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("test_*.py"))
    
    print("可用的测试文件:")
    for i, test_file in enumerate(test_files, 1):
        print(f"{i:2d}. {test_file.name}")
    
    return len(test_files)


def check_test_environment():
    """检查测试环境"""
    print("检查测试环境...")
    
    # 检查Python版本
    python_version = sys.version
    print(f"Python版本: {python_version}")
    
    # 检查必要的包
    required_packages = [
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'fastapi',
        'sqlmodel'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - 缺失")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺失的包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("环境检查完成!")
    return True


def generate_test_report():
    """生成测试报告"""
    print("生成测试报告...")
    
    # 运行测试并生成HTML覆盖率报告
    returncode = run_pytest(coverage=True, verbose=True)
    
    if returncode == 0:
        print("测试报告生成完成!")
        print("HTML覆盖率报告: backend/htmlcov/index.html")
    else:
        print("测试报告生成失败!")
    
    return returncode


def main():
    parser = argparse.ArgumentParser(description="测试运行器")
    parser.add_argument("command", choices=[
        'run', 'all', 'file', 'module', 'list', 'check', 'report'
    ], help="执行的命令")
    parser.add_argument("--path", help="测试路径或文件名")
    parser.add_argument("--module", help="模块名")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--tests", nargs="+", help="特定测试名称")
    
    args = parser.parse_args()
    
    # 确保在正确的目录
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    if args.command == "check":
        success = check_test_environment()
        return 0 if success else 1
    
    elif args.command == "list":
        count = list_test_files()
        return 0
    
    elif args.command == "report":
        return generate_test_report()
    
    elif args.command == "run":
        return run_pytest(
            test_path=args.path,
            coverage=args.coverage,
            verbose=args.verbose,
            specific_tests=args.tests
        )
    
    elif args.command == "all":
        return run_pytest(coverage=args.coverage, verbose=args.verbose)
    
    elif args.command == "file":
        if not args.path:
            print("错误: 请指定测试文件 (--path)")
            return 1
        return run_specific_file(args.path)
    
    elif args.command == "module":
        if not args.module:
            print("错误: 请指定模块名 (--module)")
            return 1
        return run_module_tests(args.module)
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"运行测试时出错: {e}")
        sys.exit(1)