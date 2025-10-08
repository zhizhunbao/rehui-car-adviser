"""
死链管理工具 - 管理死链记录和清理

提供死链的添加、删除、查询、持久化存储等功能。
采用函数式设计，无默认值原则。
"""

import json
from pathlib import Path
from typing import List, Set, Dict, Any
from datetime import datetime
from app.utils.path_util import get_data_dir


def write_dead_links(dead_links: List[str]) -> None:
    """
    写入死链列表

    Args:
        dead_links: 死链列表
    """
    data_dir = get_data_dir()
    dead_links_file = data_dir / "dead_links.json"

    # 确保数据目录存在
    data_dir.mkdir(parents=True, exist_ok=True)

    # 构建保存数据
    save_data = {
        "timestamp": datetime.now().isoformat(),
        "count": len(dead_links),
        "dead_links": dead_links
    }

    # 写入文件
    with open(dead_links_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)


def read_dead_links() -> Set[str]:
    """
    读取死链列表

    Returns:
        死链集合
    """
    data_dir = get_data_dir()
    dead_links_file = data_dir / "dead_links.json"

    if not dead_links_file.exists():
        return set()

    try:
        with open(dead_links_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get("dead_links", []))
    except (json.JSONDecodeError, KeyError, FileNotFoundError):
        return set()


def add_dead_link(url: str) -> None:
    """
    添加死链

    Args:
        url: 要添加的死链
    """
    if not url:
        return

    # 读取现有死链
    dead_links = read_dead_links()

    # 添加新死链
    dead_links.add(url)

    # 写回文件
    write_dead_links(list(dead_links))


def remove_dead_link(url: str) -> None:
    """
    移除死链

    Args:
        url: 要移除的死链
    """
    if not url:
        return

    # 读取现有死链
    dead_links = read_dead_links()

    # 移除死链
    dead_links.discard(url)

    # 写回文件
    write_dead_links(list(dead_links))


def is_dead_link(url: str) -> bool:
    """
    检查是否为死链

    Args:
        url: 要检查的URL

    Returns:
        是否为死链
    """
    if not url:
        return True

    dead_links = read_dead_links()
    return url in dead_links


def add_dead_links_batch(urls: List[str]) -> None:
    """
    批量添加死链

    Args:
        urls: 要添加的死链列表
    """
    if not urls:
        return

    # 读取现有死链
    dead_links = read_dead_links()

    # 添加新死链
    for url in urls:
        if url:
            dead_links.add(url)

    # 写回文件
    write_dead_links(list(dead_links))


def remove_dead_links_batch(urls: List[str]) -> None:
    """
    批量移除死链

    Args:
        urls: 要移除的死链列表
    """
    if not urls:
        return

    # 读取现有死链
    dead_links = read_dead_links()

    # 移除死链
    for url in urls:
        if url:
            dead_links.discard(url)

    # 写回文件
    write_dead_links(list(dead_links))


def get_dead_links_count() -> int:
    """
    获取死链数量

    Returns:
        死链数量
    """
    dead_links = read_dead_links()
    return len(dead_links)


def get_dead_links_list() -> List[str]:
    """
    获取死链列表

    Returns:
        死链列表
    """
    dead_links = read_dead_links()
    return sorted(list(dead_links))


def clear_dead_links() -> None:
    """
    清空死链列表
    """
    write_dead_links([])


def filter_dead_links_from_list(urls: List[str]) -> List[str]:
    """
    从URL列表中过滤掉死链

    Args:
        urls: URL列表

    Returns:
        过滤后的URL列表
    """
    if not urls:
        return []

    dead_links = read_dead_links()
    return [url for url in urls if url and url not in dead_links]


def get_dead_links_by_domain(domain: str) -> List[str]:
    """
    获取指定域名的死链

    Args:
        domain: 域名

    Returns:
        该域名的死链列表
    """
    if not domain:
        return []

    dead_links = read_dead_links()
    domain_dead_links = []

    for url in dead_links:
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            if parsed_url.netloc == domain:
                domain_dead_links.append(url)
        except Exception:
            continue

    return sorted(domain_dead_links)


def get_dead_links_statistics() -> Dict[str, Any]:
    """
    获取死链统计信息

    Returns:
        死链统计信息字典
    """
    dead_links = read_dead_links()

    # 统计域名
    domain_count = {}
    for url in dead_links:
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            domain_count[domain] = domain_count.get(domain, 0) + 1
        except Exception:
            continue

    # 获取文件信息
    data_dir = get_data_dir()
    dead_links_file = data_dir / "dead_links.json"

    file_size = 0
    last_modified = None

    if dead_links_file.exists():
        try:
            stat = dead_links_file.stat()
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except Exception:
            pass

    return {
        "total_count": len(dead_links),
        "domain_count": len(domain_count),
        "top_domains": sorted(domain_count.items(), key=lambda x: x[1], reverse=True)[:10],
        "file_size_bytes": file_size,
        "last_modified": last_modified
    }


def export_dead_links(output_file: Path) -> bool:
    """
    导出死链到文件

    Args:
        output_file: 输出文件路径

    Returns:
        是否导出成功
    """
    try:
        dead_links = read_dead_links()

        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 构建导出数据
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_count": len(dead_links),
            "dead_links": sorted(list(dead_links))
        }

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return True

    except Exception:
        return False


def import_dead_links(input_file: Path) -> bool:
    """
    从文件导入死链

    Args:
        input_file: 输入文件路径

    Returns:
        是否导入成功
    """
    try:
        if not input_file.exists():
            return False

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        dead_links = data.get("dead_links", [])
        if dead_links:
            add_dead_links_batch(dead_links)

        return True

    except Exception:
        return False


def cleanup_old_dead_links(days_old: int) -> int:
    """
    清理旧的死链记录

    Args:
        days_old: 天数阈值

    Returns:
        清理的死链数量
    """
    # 注意：当前实现没有时间戳，所以这个函数暂时返回0
    # 如果需要实现，需要在死链记录中添加时间戳
    return 0


def is_url_in_dead_links(url: str) -> bool:
    """
    检查URL是否在死链列表中

    Args:
        url: 要检查的URL

    Returns:
        是否在死链列表中
    """
    return is_dead_link(url)


def get_dead_links_by_pattern(pattern: str) -> List[str]:
    """
    根据模式获取死链

    Args:
        pattern: 匹配模式

    Returns:
        匹配的死链列表
    """
    if not pattern:
        return []

    dead_links = read_dead_links()
    matching_links = []

    for url in dead_links:
        if pattern.lower() in url.lower():
            matching_links.append(url)

    return sorted(matching_links)


def remove_dead_links_by_pattern(pattern: str) -> int:
    """
    根据模式移除死链

    Args:
        pattern: 匹配模式

    Returns:
        移除的死链数量
    """
    if not pattern:
        return 0

    dead_links = read_dead_links()
    links_to_remove = []

    for url in dead_links:
        if pattern.lower() in url.lower():
            links_to_remove.append(url)

    if links_to_remove:
        remove_dead_links_batch(links_to_remove)

    return len(links_to_remove)


def backup_dead_links(backup_file: Path) -> bool:
    """
    备份死链数据

    Args:
        backup_file: 备份文件路径

    Returns:
        是否备份成功
    """
    return export_dead_links(backup_file)


def restore_dead_links(backup_file: Path) -> bool:
    """
    恢复死链数据

    Args:
        backup_file: 备份文件路径

    Returns:
        是否恢复成功
    """
    return import_dead_links(backup_file)
