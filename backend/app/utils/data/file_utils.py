"""
文件操作工具类

提供统一的文件操作接口，包括：
- 文件读写操作
- CSV文件处理
- 文件存在性检查
- 路径处理
- 文件验证
- 错误处理

采用函数式设计，无默认值原则。
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


def file_exists(file_path: Union[str, Path]) -> bool:
    """
    检查文件是否存在

    Args:
        file_path: 文件路径

    Returns:
        bool: 文件是否存在
    """
    try:
        return Path(file_path).exists()
    except Exception as e:
        logger.log_result(f"Error checking file existence for {file_path}: {e}")
        return False


def is_file(file_path: Union[str, Path]) -> bool:
    """
    检查路径是否为文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否为文件
    """
    try:
        return Path(file_path).is_file()
    except Exception as e:
        logger.log_result(f"Error checking if path is file for {file_path}: {e}")
        return False


def is_directory(dir_path: Union[str, Path]) -> bool:
    """
    检查路径是否为目录

    Args:
        dir_path: 目录路径

    Returns:
        bool: 是否为目录
    """
    try:
        return Path(dir_path).is_dir()
    except Exception as e:
        msg = f"Error checking if path is directory for {dir_path}: {e}"
        logger.log_result(msg)
        return False


def ensure_directory(dir_path: Union[str, Path]) -> bool:
    """
    确保目录存在，如果不存在则创建

    Args:
        dir_path: 目录路径

    Returns:
        bool: 是否成功创建或目录已存在
    """
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.log_result(f"Error creating directory {dir_path}: {e}")
        return False


def read_text_file(file_path: Union[str, Path],
                   encoding: str = 'utf-8') -> Optional[str]:
    """
    读取文本文件内容

    Args:
        file_path: 文件路径
        encoding: 文件编码，默认utf-8

    Returns:
        Optional[str]: 文件内容，失败时返回None
    """
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except Exception as e:
        logger.log_result(f"Error reading text file {file_path}: {e}")
        return None


def write_text_file(file_path: Union[str, Path], content: str,
                    encoding: str = 'utf-8') -> bool:
    """
    写入文本文件

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码，默认utf-8

    Returns:
        bool: 是否写入成功
    """
    try:
        # 确保目录存在
        ensure_directory(Path(file_path).parent)

        with open(file_path, 'w', encoding=encoding) as file:
            file.write(content)
        return True
    except Exception as e:
        logger.log_result(f"Error writing text file {file_path}: {e}")
        return False


def read_json_file(file_path: Union[str, Path],
                   encoding: str = 'utf-8') -> Optional[Dict[str, Any]]:
    """
    读取JSON文件

    Args:
        file_path: 文件路径
        encoding: 文件编码，默认utf-8

    Returns:
        Optional[Dict[str, Any]]: JSON数据，失败时返回None
    """
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return json.load(file)
    except Exception as e:
        logger.log_result(f"Error reading JSON file {file_path}: {e}")
        return None


def write_json_file(file_path: Union[str, Path], data: Dict[str, Any],
                    encoding: str = 'utf-8', indent: int = 2) -> bool:
    """
    写入JSON文件

    Args:
        file_path: 文件路径
        data: JSON数据
        encoding: 文件编码，默认utf-8
        indent: JSON缩进，默认2

    Returns:
        bool: 是否写入成功
    """
    try:
        # 确保目录存在
        ensure_directory(Path(file_path).parent)

        with open(file_path, 'w', encoding=encoding) as file:
            json.dump(data, file, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logger.log_result(f"Error writing JSON file {file_path}: {e}")
        return False


def read_csv_file(file_path: Union[str, Path],
                  encoding: str = 'utf-8') -> Optional[List[Dict[str, str]]]:
    """
    读取CSV文件

    Args:
        file_path: 文件路径
        encoding: 文件编码，默认utf-8

    Returns:
        Optional[List[Dict[str, str]]]: CSV数据列表，失败时返回None
    """
    try:
        data = []
        with open(file_path, 'r', encoding=encoding, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        return data
    except Exception as e:
        logger.log_result(f"Error reading CSV file {file_path}: {e}")
        return None


def write_csv_file(file_path: Union[str, Path],
                   data: List[Dict[str, str]],
                   fieldnames: Optional[List[str]] = None,
                   encoding: str = 'utf-8') -> bool:
    """
    写入CSV文件

    Args:
        file_path: 文件路径
        data: CSV数据列表
        fieldnames: 字段名列表，如果为None则从第一行数据推断
        encoding: 文件编码，默认utf-8

    Returns:
        bool: 是否写入成功
    """
    try:
        if not data:
            logger.warning(f"No data to write to CSV file {file_path}")
            return False

        # 确保目录存在
        ensure_directory(Path(file_path).parent)

        # 如果没有指定字段名，从第一行数据推断
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        with open(file_path, 'w', encoding=encoding, newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        logger.log_result(f"Error writing CSV file {file_path}: {e}")
        return False


def append_csv_file(file_path: Union[str, Path],
                    data: List[Dict[str, str]],
                    fieldnames: Optional[List[str]] = None,
                    encoding: str = 'utf-8') -> bool:
    """
    追加数据到CSV文件

    Args:
        file_path: 文件路径
        data: CSV数据列表
        fieldnames: 字段名列表，如果为None则从第一行数据推断
        encoding: 文件编码，默认utf-8

    Returns:
        bool: 是否追加成功
    """
    try:
        if not data:
            logger.warning(f"No data to append to CSV file {file_path}")
            return False

        # 确保目录存在
        ensure_directory(Path(file_path).parent)

        # 如果没有指定字段名，从第一行数据推断
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        # 检查文件是否存在，如果不存在则写入表头
        file_exists_flag = file_exists(file_path)

        with open(file_path, 'a', encoding=encoding, newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists_flag:
                writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        logger.log_result(f"Error appending to CSV file {file_path}: {e}")
        return False


def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        Optional[int]: 文件大小，失败时返回None
    """
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        logger.log_result(f"Error getting file size for {file_path}: {e}")
        return None


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    获取文件扩展名

    Args:
        file_path: 文件路径

    Returns:
        str: 文件扩展名（包含点号）
    """
    try:
        return Path(file_path).suffix
    except Exception as e:
        logger.log_result(f"Error getting file extension for {file_path}: {e}")
        return ""


def get_file_name(file_path: Union[str, Path],
                  with_extension: bool = True) -> str:
    """
    获取文件名

    Args:
        file_path: 文件路径
        with_extension: 是否包含扩展名

    Returns:
        str: 文件名
    """
    try:
        path = Path(file_path)
        if with_extension:
            return path.name
        else:
            return path.stem
    except Exception as e:
        logger.log_result(f"Error getting file name for {file_path}: {e}")
        return ""


def list_files_in_directory(dir_path: Union[str, Path],
                            pattern: str = "*",
                            recursive: bool = False) -> List[Path]:
    """
    列出目录中的文件

    Args:
        dir_path: 目录路径
        pattern: 文件匹配模式，默认"*"
        recursive: 是否递归搜索子目录

    Returns:
        List[Path]: 文件路径列表
    """
    try:
        dir_path = Path(dir_path)
        if not dir_path.exists() or not dir_path.is_dir():
            msg = f"Directory does not exist or is not a directory: {dir_path}"
            logger.warning(msg)
            return []

        if recursive:
            return list(dir_path.rglob(pattern))
        else:
            return list(dir_path.glob(pattern))
    except Exception as e:
        logger.log_result(f"Error listing files in directory {dir_path}: {e}")
        return []


def delete_file(file_path: Union[str, Path]) -> bool:
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否删除成功
    """
    try:
        Path(file_path).unlink()
        return True
    except Exception as e:
        logger.log_result(f"Error deleting file {file_path}: {e}")
        return False


def copy_file(src_path: Union[str, Path],
              dst_path: Union[str, Path]) -> bool:
    """
    复制文件

    Args:
        src_path: 源文件路径
        dst_path: 目标文件路径

    Returns:
        bool: 是否复制成功
    """
    try:
        import shutil
        # 确保目标目录存在
        ensure_directory(Path(dst_path).parent)
        shutil.copy2(src_path, dst_path)
        return True
    except Exception as e:
        logger.log_result(f"Error copying file from {src_path} to {dst_path}: {e}")
        return False


def move_file(src_path: Union[str, Path],
              dst_path: Union[str, Path]) -> bool:
    """
    移动文件

    Args:
        src_path: 源文件路径
        dst_path: 目标文件路径

    Returns:
        bool: 是否移动成功
    """
    try:
        import shutil
        # 确保目标目录存在
        ensure_directory(Path(dst_path).parent)
        shutil.move(src_path, dst_path)
        return True
    except Exception as e:
        logger.log_result(f"Error moving file from {src_path} to {dst_path}: {e}")
        return False


def validate_file_path(file_path: Union[str, Path]) -> bool:
    """
    验证文件路径是否有效

    Args:
        file_path: 文件路径

    Returns:
        bool: 路径是否有效
    """
    try:
        path = Path(file_path)
        # 检查路径是否包含非法字符
        path_str = str(path)
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in path_str for char in illegal_chars):
            return False
        return True
    except Exception as e:
        logger.log_result(f"Error validating file path {file_path}: {e}")
        return False


def get_safe_filename(filename: str) -> str:
    """
    获取安全的文件名（移除非法字符）

    Args:
        filename: 原始文件名

    Returns:
        str: 安全的文件名
    """
    import re
    # 移除或替换非法字符
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除多余的空格和点号
    safe_filename = re.sub(r'\s+', '_', safe_filename.strip())
    safe_filename = safe_filename.strip('.')
    return safe_filename
