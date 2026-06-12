"""
文件读取工具：读取文件夹内容，支持多种文件格式
"""

import os
import ast
from pathlib import Path
from typing import List, Dict


def read_folder(folder_path: str, recursive: bool = False, extensions: List[str] = None) -> str:
    """
    读取文件夹内容
    
    参数:
        folder_path: 文件夹路径
        recursive: 是否递归读取子文件夹
        extensions: 指定文件扩展名列表，如 ['.py', '.txt', '.json']
    
    返回:
        文件夹内容摘要
    """
    if not os.path.exists(folder_path):
        return f"文件夹不存在：{folder_path}"
    
    if not os.path.isdir(folder_path):
        return f"路径不是文件夹：{folder_path}"
    
    # 默认扩展名
    if extensions is None:
        extensions = ['.py', '.txt', '.json', '.md', '.csv', '.xlsx']
    
    result = []
    result.append(f"文件夹：{folder_path}")
    result.append(f"{'='*50}")
    
    # 统计信息
    file_count = 0
    dir_count = 0
    
    # 遍历文件夹
    if recursive:
        for root, dirs, files in os.walk(folder_path):
            # 跳过隐藏文件夹
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in extensions:
                    file_count += 1
                    result.append(f"\n📄 {file_path}")
                    result.append(f"{'-'*40}")
                    
                    # 读取文件内容
                    content = read_file_content(file_path, file_ext)
                    result.append(content[:2000])  # 限制长度
                    
                    if len(content) > 2000:
                        result.append(f"... (共 {len(content)} 字符，已截断)")
            dir_count += len(dirs)
    else:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                dir_count += 1
                result.append(f"\n{item}/")
            else:
                file_ext = os.path.splitext(item)[1].lower()
                if file_ext in extensions:
                    file_count += 1
                    result.append(f"\n📄 {item}")
                    result.append(f"{'-'*40}")
                    
                    content = read_file_content(item_path, file_ext)
                    result.append(content[:2000])
                    
                    if len(content) > 2000:
                        result.append(f"... (共 {len(content)} 字符，已截断)")
    
    # 统计信息
    result.append(f"\n{'='*50}")
    result.append(f"统计：")
    result.append(f"  文件数：{file_count}")
    result.append(f"  文件夹数：{dir_count}")
    
    return "\n".join(result)


def read_file_content(file_path: str, ext: str) -> str:
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Python 文件特殊处理
        if ext == '.py':
            # 可以提取函数和类
            try:
                tree = ast.parse(content)
                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                
                if functions or classes:
                    summary = f"Python 文件\n"
                    if classes:
                        summary += f"   类：{', '.join(classes)}\n"
                    if functions:
                        summary += f"   函数：{', '.join(functions)}\n"
                    summary += f"\n{content[:1500]}"
                    return summary
            except:
                pass
        
        return content
    except Exception as e:
        return f"读取失败：{str(e)}"


def list_folder_structure(folder_path: str, max_depth: int = 3) -> str:
    """
    列出文件夹结构树
    
    参数:
        folder_path: 文件夹路径
        max_depth: 最大深度
    """
    if not os.path.exists(folder_path):
        return f"文件夹不存在：{folder_path}"
    
    result = [f"{folder_path}"]
    _build_tree(folder_path, result, max_depth, prefix="")
    return "\n".join(result)


def _build_tree(path: str, result: List[str], max_depth: int, prefix: str, depth: int = 0):
    """递归构建目录树"""
    if depth >= max_depth:
        return
    
    try:
        items = sorted(os.listdir(path))
        for i, item in enumerate(items):
            if item.startswith('.'):
                continue
            
            item_path = os.path.join(path, item)
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            if os.path.isdir(item_path):
                result.append(f"{prefix}{connector},{item}/")
                extension = "    " if is_last else "│   "
                _build_tree(item_path, result, max_depth, prefix + extension, depth + 1)
            else:
                result.append(f"{prefix}{connector} {item}")
    except PermissionError:
        result.append(f"{prefix}│   ... (无权限)")


def search_in_folder(folder_path: str, keyword: str, recursive: bool = True) -> str:
    """
    在文件夹中搜索关键词
    
    参数:
        folder_path: 文件夹路径
        keyword: 搜索关键词
        recursive: 是否递归搜索
    """
    if not os.path.exists(folder_path):
        return f"文件夹不存在：{folder_path}"
    
    results = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            if file_ext in ['.py', '.txt', '.json', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        for i, line in enumerate(lines):
                            if keyword in line:
                                results.append({
                                    "file": file_path,
                                    "line": i + 1,
                                    "content": line.strip()[:200]
                                })
                except:
                    pass
        
        if not recursive:
            break
    
    if not results:
        return f"未找到包含 '{keyword}' 的内容"
    
    output = [f"搜索 '{keyword}' 结果（共 {len(results)} 处）："]
    output.append("="*50)
    
    for r in results[:20]:  # 最多显示20条
        output.append(f"\n{r['file']}")
        output.append(f"行{r['line']}: {r['content']}")
    
    if len(results) > 20:
        output.append(f"\n... 还有 {len(results) - 20} 处结果未显示")
    
    return "\n".join(output)


def write_to_file(file_path: str, content: str, mode: str = "w") -> str:
    """
    写入内容到文件

    参数:
        file_path: 文件路径（会自动放到 output 文件夹下）
        content: 要写入的内容
        mode: 写入模式，"w"=覆盖写入，"a"=追加写入
    """
    try:
        # 确保目录存在
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        # 提取文件名
        filename = os.path.basename(file_path)
        full_path = os.path.join(output_dir, filename)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 统计信息
        lines = content.count('\n') + 1
        chars = len(content)

        return f"已写入文件：{file_path}\n 共 {lines} 行，{chars} 字符"

    except Exception as e:
        return f"写入失败：{str(e)}"


def append_to_file(file_path: str, content: str) -> str:
    """追加内容到文件末尾"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)

        return f"已追加内容到：{file_path}"

    except Exception as e:
        return f"追加失败：{str(e)}"


# ========== 工具定义 ==========

READ_FOLDER_TOOL = {
    "type": "function",
    "function": {
        "name": "read_folder",
        "description": "读取文件夹内容，支持递归读取，可指定文件类型",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "文件夹路径"},
                "recursive": {"type": "boolean", "description": "是否递归读取子文件夹"},
                "extensions": {"type": "array", "items": {"type": "string"}, "description": "文件扩展名列表，如 ['.py', '.txt']"}
            },
            "required": ["folder_path"]
        }
    }
}

LIST_FOLDER_TOOL = {
    "type": "function",
    "function": {
        "name": "list_folder_structure",
        "description": "列出文件夹结构树",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "文件夹路径"},
                "max_depth": {"type": "integer", "description": "最大深度"}
            },
            "required": ["folder_path"]
        }
    }
}

SEARCH_FOLDER_TOOL = {
    "type": "function",
    "function": {
        "name": "search_in_folder",
        "description": "在文件夹中搜索关键词",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "文件夹路径"},
                "keyword": {"type": "string", "description": "搜索关键词"},
                "recursive": {"type": "boolean", "description": "是否递归搜索"}
            },
            "required": ["folder_path", "keyword"]
        }
    }
}
WRITE_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "write_to_file",
        "description": '写入内容到文件。当用户要求"保存"、"写入"、"生成文件"时调用',
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的内容"},
                "mode": {"type": "string", "description": "写入模式：w=覆盖，a=追加"}
            },
            "required": ["file_path", "content"]
        }
    }
}

APPEND_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "append_to_file",
        "description": "追加内容到文件末尾",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要追加的内容"}
            },
            "required": ["file_path", "content"]
        }
    }
}


def handle_read_folder(folder_path: str, recursive: bool = False, extensions: list = None) -> str:
    return read_folder(folder_path, recursive, extensions)


def handle_list_folder_structure(folder_path: str, max_depth: int = 3) -> str:
    return list_folder_structure(folder_path, max_depth)


def handle_search_in_folder(folder_path: str, keyword: str, recursive: bool = True) -> str:
    return search_in_folder(folder_path, keyword, recursive)

def handle_write_to_file(file_path: str, content: str, mode: str = "w") -> str:
    return write_to_file(file_path, content, mode)


def handle_append_to_file(file_path: str, content: str) -> str:
    return append_to_file(file_path, content)

# 工具列表
FILE_READER_TOOLS = [READ_FOLDER_TOOL,LIST_FOLDER_TOOL,SEARCH_FOLDER_TOOL,WRITE_FILE_TOOL,APPEND_FILE_TOOL]
FILE_READER_HANDLERS = {
    "read_folder": handle_read_folder,
    "list_folder_structure": handle_list_folder_structure,
    "search_in_folder": handle_search_in_folder,
    "write_to_file": handle_write_to_file,
    "append_to_file": handle_append_to_file,
}