"""PyTool CLI — 代码生成与项目管理工具
用法: uv run python -m app.cli <命令>
"""
import sys
from .generate import generate_module

HELP = """PyTool CLI

命令:
  generate-module <name> --fields <定义> [--menu <菜单名>]
      生成完整的 CRUD 模块（model + controller + api 路由）

      示例:
        uv run python -m app.cli generate-module product \\
          --fields "name:str, price:float, category:str" \\
          --menu "商品管理"

  help  显示帮助
"""


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help", "-h"):
        print(HELP)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "generate-module":
        if len(args) < 1:
            print("用法: generate-module <模块名> --fields <定义> [--menu <菜单名>]")
            return

        name = args[0]
        fields = ""
        menu = ""

        i = 1
        while i < len(args):
            if args[i] == "--fields" and i + 1 < len(args):
                fields = args[i + 1]
                i += 2
            elif args[i] == "--menu" and i + 1 < len(args):
                menu = args[i + 1]
                i += 2
            else:
                i += 1

        if not fields:
            print("错误: 需要 --fields 参数")
            return

        print(f"生成模块: {name}")
        print(f"  字段: {fields}")
        if menu:
            print(f"  菜单: {menu}")
        print()

        created = generate_module(name, fields, menu)
        for path in created:
            print(f"  ✅ {path.relative_to(path.parents[3])}")
        print()
        print("下一步:")
        print(f"  1. 在 backend/app/models/__init__.py 添加: from .{name} import *")
        print("  2. 在 backend/app/api/v1/__init__.py 注册路由")
        print("  3. 在 seed/data/menus.py 添加菜单项")
        print("  4. 重启服务")

    else:
        print(f"未知命令: {cmd}")
        print(HELP)


if __name__ == "__main__":
    main()
