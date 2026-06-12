"""
代码查看工具 - 查看 Python 文件代码和结构
"""

import os
import ast
from typing import List


def view_code(file_path: str, show_summary: bool = False) -> str:
    """
    查看 Python 代码

    参数:
        file_path: 文件路径
        show_summary: 是否显示文件摘要
    """
    if not os.path.exists(file_path):
        return f"文件不存在：{file_path}"

    if not file_path.endswith('.py'):
        return f"仅支持 .py 文件，当前文件：{file_path}"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        total_lines = len(content.split('\n'))

        # 如果需要摘要
        if show_summary:
            return _get_code_summary(file_path, content)

        # 默认显示全部内容，超过5000行截断
        lines = content.split('\n')
        max_lines = 200

        result = []
        result.append(f"{file_path}")
        result.append(f"总行数：{total_lines}")
        result.append("=" * 60)

        if total_lines > max_lines:
            # 显示前200行
            for i in range(min(max_lines, total_lines)):
                result.append(f"{i+1:4d} | {lines[i]}")
            result.append(f"\n... 还有 {total_lines - max_lines} 行未显示")
            result.append(f"使用 view_code_summary 查看摘要")
        else:
            for i, line in enumerate(lines):
                result.append(f"{i+1:4d} | {line}")

        return "\n".join(result)

    except Exception as e:
        return f"读取失败：{str(e)}"


def view_code_summary(file_path: str) -> str:
    """查看代码摘要（导入、类、函数）"""
    if not os.path.exists(file_path):
        return f"文件不存在：{file_path}"

    if not file_path.endswith('.py'):
        return f"仅支持 .py 文件"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return _get_code_summary(file_path, content)
    except Exception as e:
        return f"读取失败：{str(e)}"


def _get_code_summary(file_path: str, content: str) -> str:
    """获取代码摘要"""
    try:
        tree = ast.parse(content)
        lines = content.split('\n')

        imports = []
        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "methods": methods[:5],
                    "line": node.lineno
                })
            elif isinstance(node, ast.FunctionDef):
                if not hasattr(node, 'parent') or not isinstance(node.parent, ast.ClassDef):
                    args = [arg.arg for arg in node.args.args]
                    functions.append({
                        "name": node.name,
                        "args": args,
                        "line": node.lineno
                    })

        result = [f"📄 {file_path}"]
        result.append("=" * 50)
        result.append(f"统计：{len(lines)} 行，{len(imports)} 个导入，{len(classes)} 个类，{len(functions)} 个函数")
        result.append("")

        if imports:
            result.append("导入：")
            for imp in imports[:20]:
                result.append(f"   {imp}")
            if len(imports) > 20:
                result.append(f"   ... 共 {len(imports)} 个")
            result.append("")

        if classes:
            result.append("类：")
            for cls in classes[:15]:
                methods_str = f"({', '.join(cls['methods'])})" if cls['methods'] else ""
                result.append(f"   {cls['name']} {methods_str} (行 {cls['line']})")
            if len(classes) > 15:
                result.append(f"   ... 共 {len(classes)} 个类")
            result.append("")

        if functions:
            result.append("函数：")
            for func in functions[:20]:
                args_str = f"({', '.join(func['args'])})" if func['args'] else "()"
                result.append(f"   {func['name']}{args_str} (行 {func['line']})")
            if len(functions) > 20:
                result.append(f"   ... 共 {len(functions)} 个函数")

        return "\n".join(result)

    except SyntaxError as e:
        return f"语法错误：{e}"
    except Exception as e:
        return f"解析失败：{str(e)}"


def list_functions(file_path: str) -> str:
    """列出文件中的所有函数和类"""
    if not os.path.exists(file_path):
        return f"文件不存在：{file_path}"

    if not file_path.endswith('.py'):
        return f"仅支持 .py 文件"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        items = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                items.append(f"类: {node.name} (行 {node.lineno})")
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        items.append(f"   └── 方法: {child.name} (行 {child.lineno})")
            elif isinstance(node, ast.FunctionDef):
                if not hasattr(node, 'parent') or not isinstance(node.parent, ast.ClassDef):
                    items.append(f"函数: {node.name} (行 {node.lineno})")

        if not items:
            return f"{file_path}\n未找到任何函数或类"

        result = [f"{file_path}", "=" * 40]
        result.extend(items)
        return "\n".join(result)

    except Exception as e:
        return f"解析失败：{str(e)}"


def read_all_py_files(folder_path: str, recursive: bool = True) -> str:
    """读取文件夹下所有 py 文件的内容并返回"""
    if not os.path.exists(folder_path):
        return f"文件夹不存在：{folder_path}"

    py_files = []
    if recursive:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(folder_path):
            if file.endswith('.py'):
                py_files.append(os.path.join(folder_path, file))

    if not py_files:
        return f"{folder_path} 中没有找到 .py 文件"

    result = []
    result.append(f"找到 {len(py_files)} 个 Python 文件")
    result.append("=" * 60)

    for file_path in py_files:
        result.append(f"\n📄 {file_path}")
        result.append("-" * 40)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                result.append(f.read())
        except Exception as e:
            result.append(f"读取失败：{e}")

    return "\n".join(result)

# ========== 工具定义 ==========

VIEW_CODE_TOOL = {
    "type": "function",
    "function": {
        "name": "view_code",
        "description": "查看 Python 文件代码内容",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Python 文件路径"},
                "show_summary": {"type": "boolean", "description": "是否只显示摘要"}
            },
            "required": ["file_path"]
        }
    }
}

VIEW_CODE_SUMMARY_TOOL = {
    "type": "function",
    "function": {
        "name": "view_code_summary",
        "description": "查看 Python 文件摘要（导入、类、函数列表）",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Python 文件路径"}
            },
            "required": ["file_path"]
        }
    }
}

LIST_FUNCTIONS_TOOL = {
    "type": "function",
    "function": {
        "name": "list_functions",
        "description": "列出 Python 文件中的所有函数和类",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Python 文件路径"}
            },
            "required": ["file_path"]
        }
    }
}

READ_ALL_PY_TOOL = {
    "type": "function",
    "function": {
        "name": "read_all_py_files",
        "description": "读取文件夹下所有 Python 文件的内容并返回。当用户说'读取'、'查看'、'显示'文件夹下所有py文件时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "文件夹路径"},
                "recursive": {"type": "boolean", "description": "是否递归子文件夹"}
            },
            "required": ["folder_path"]
        }
    }
}

def handle_view_code(file_path: str, show_summary: bool = False) -> str:
    return view_code(file_path, show_summary)


def handle_view_code_summary(file_path: str) -> str:
    return view_code_summary(file_path)


def handle_list_functions(file_path: str) -> str:
    return list_functions(file_path)


def handle_read_all_py_files(folder_path: str, recursive: bool = True) -> str:
    return read_all_py_files(folder_path, recursive)


CODE_VIEWER_TOOLS = [VIEW_CODE_TOOL, VIEW_CODE_SUMMARY_TOOL, LIST_FUNCTIONS_TOOL,
                     READ_ALL_PY_TOOL]
CODE_VIEWER_HANDLERS = {
    "view_code": handle_view_code,
    "view_code_summary": handle_view_code_summary,
    "list_functions": handle_list_functions,
    "read_all_py_files": handle_read_all_py_files,
}