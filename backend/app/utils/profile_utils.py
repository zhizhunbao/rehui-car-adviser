"""
Profile管理工具 - 管理Chrome浏览器配置文件

提供Chrome配置文件的创建、删除、清理等功能。
采用函数式设计，无默认值原则。
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


def generate_daily_profile_name(prefix: str) -> str:
    """
    生成带有日期和随机后缀的profile名

    Args:
        prefix: 前缀字符串

    Returns:
        生成的profile名称

    Example:
        >>> generate_daily_profile_name("test")
        "test_20240127_abc123"
    """
    import random
    import string

    # 获取当前日期
    date_str = datetime.now().strftime("%Y%m%d")

    # 生成随机后缀
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    return f"{prefix}_{date_str}_{random_suffix}"


def ensure_profile_exists(profile_name: str) -> str:
    """
    创建profile目录

    Args:
        profile_name: profile名称

    Returns:
        profile目录路径
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    profile_path = profiles_dir / profile_name

    # 创建profile目录
    profile_path.mkdir(parents=True, exist_ok=True)

    # 创建必要的子目录
    subdirs = ["Default", "Extensions", "Local State"]
    for subdir in subdirs:
        (profile_path / subdir).mkdir(exist_ok=True)

    return str(profile_path)


def delete_profile(profile_name: str) -> bool:
    """
    删除profile目录

    Args:
        profile_name: profile名称

    Returns:
        是否删除成功
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    profile_path = profiles_dir / profile_name

    if profile_path.exists():
        try:
            shutil.rmtree(profile_path)
            return True
        except Exception:
            return False

    return True


def cleanup_old_profiles(days_old: int) -> int:
    """
    清理旧的profile目录

    Args:
        days_old: 文件天数阈值

    Returns:
        清理的profile数量
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()

    if not profiles_dir.exists():
        return 0

    cutoff_time = datetime.now() - timedelta(days=days_old)
    cleaned_count = 0

    for profile_path in profiles_dir.iterdir():
        if profile_path.is_dir():
            # 检查profile的创建时间
            try:
                profile_time = datetime.fromtimestamp(profile_path.stat().st_mtime)
                if profile_time < cutoff_time:
                    if delete_profile(profile_path.name):
                        cleaned_count += 1
            except Exception:
                # 如果无法获取时间或删除失败，跳过
                continue

    return cleaned_count


def list_profiles() -> List[str]:
    """
    列出所有profile

    Returns:
        profile名称列表
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()

    if not profiles_dir.exists():
        return []

    profiles = []
    for profile_path in profiles_dir.iterdir():
        if profile_path.is_dir():
            profiles.append(profile_path.name)

    return sorted(profiles)


def get_profile_info(profile_name: str) -> dict:
    """
    获取profile信息

    Args:
        profile_name: profile名称

    Returns:
        profile信息字典
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    profile_path = profiles_dir / profile_name

    if not profile_path.exists():
        return {"error": "Profile不存在"}

    try:
        stat = profile_path.stat()
        return {
            "name": profile_name,
            "path": str(profile_path),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size_mb": get_profile_size_mb(profile_path)
        }
    except Exception as e:
        return {"error": f"无法获取profile信息: {str(e)}"}


def get_profile_size_mb(profile_path: Path) -> float:
    """
    获取profile大小（MB）

    Args:
        profile_path: profile路径

    Returns:
        profile大小（MB）
    """
    total_size = 0

    try:
        for file_path in profile_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except Exception:
        pass

    return total_size / (1024 * 1024)


def copy_profile(source_profile: str, target_profile: str) -> bool:
    """
    复制profile

    Args:
        source_profile: 源profile名称
        target_profile: 目标profile名称

    Returns:
        是否复制成功
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    source_path = profiles_dir / source_profile
    target_path = profiles_dir / target_profile

    if not source_path.exists():
        return False

    try:
        # 删除目标profile（如果存在）
        if target_path.exists():
            shutil.rmtree(target_path)

        # 复制profile
        shutil.copytree(source_path, target_path)
        return True
    except Exception:
        return False


def backup_profile(profile_name: str, backup_dir: Optional[Path] = None) -> Optional[Path]:
    """
    备份profile

    Args:
        profile_name: profile名称
        backup_dir: 备份目录，如果为None则使用默认目录

    Returns:
        备份文件路径，如果失败则返回None
    """
    from app.utils.path_util import get_chrome_profiles_dir, get_tmp_dir

    profiles_dir = get_chrome_profiles_dir()
    profile_path = profiles_dir / profile_name

    if not profile_path.exists():
        return None

    # 使用默认备份目录
    if backup_dir is None:
        backup_dir = get_tmp_dir() / "profile_backups"

    backup_dir.mkdir(parents=True, exist_ok=True)

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{profile_name}_{timestamp}.zip"
    backup_path = backup_dir / backup_filename

    try:
        # 创建ZIP备份
        shutil.make_archive(
            str(backup_path.with_suffix('')),
            'zip',
            str(profile_path.parent),
            profile_name
        )
        return backup_path
    except Exception:
        return None


def restore_profile(backup_path: Path, profile_name: str) -> bool:
    """
    恢复profile

    Args:
        backup_path: 备份文件路径
        profile_name: 目标profile名称

    Returns:
        是否恢复成功
    """
    from app.utils.path_util import get_chrome_profiles_dir

    if not backup_path.exists():
        return False

    profiles_dir = get_chrome_profiles_dir()
    target_path = profiles_dir / profile_name

    try:
        # 删除现有profile
        if target_path.exists():
            shutil.rmtree(target_path)

        # 解压备份
        shutil.unpack_archive(backup_path, str(profiles_dir))

        # 重命名解压的目录
        extracted_name = backup_path.stem.split('_')[0]  # 获取原始profile名
        extracted_path = profiles_dir / extracted_name

        if extracted_path.exists() and extracted_path != target_path:
            extracted_path.rename(target_path)

        return True
    except Exception:
        return False


def clean_profile_data(profile_name: str) -> bool:
    """
    清理profile数据（保留配置，删除缓存等）

    Args:
        profile_name: profile名称

    Returns:
        是否清理成功
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    profile_path = profiles_dir / profile_name

    if not profile_path.exists():
        return False

    # 要清理的目录和文件
    cleanup_items = [
        "Default/Cache",
        "Default/Code Cache",
        "Default/GPUCache",
        "Default/Service Worker",
        "Default/IndexedDB",
        "Default/Local Storage",
        "Default/Session Storage",
        "Default/WebStorage",
        "Default/Application Cache",
        "Default/File System",
        "Default/Pepper Data"
    ]

    try:
        for item in cleanup_items:
            item_path = profile_path / item
            if item_path.exists():
                if item_path.is_file():
                    item_path.unlink()
                else:
                    shutil.rmtree(item_path)

        return True
    except Exception:
        return False


def is_profile_in_use(profile_name: str) -> bool:
    """
    检查profile是否正在使用

    Args:
        profile_name: profile名称

    Returns:
        是否正在使用
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    profile_path = profiles_dir / profile_name

    if not profile_path.exists():
        return False

    # 检查是否有锁文件
    lock_files = [
        "Default/SingletonLock",
        "Default/LockFile",
        "SingletonLock"
    ]

    for lock_file in lock_files:
        lock_path = profile_path / lock_file
        if lock_path.exists():
            return True

    return False


def get_profile_statistics() -> dict:
    """
    获取profile统计信息

    Returns:
        统计信息字典
    """
    profiles = list_profiles()

    total_profiles = len(profiles)
    total_size = 0
    oldest_profile = None
    newest_profile = None

    for profile_name in profiles:
        info = get_profile_info(profile_name)
        if "error" not in info:
            total_size += info.get("size_mb", 0)

            created = info.get("created", "")
            if created:
                if oldest_profile is None or created < oldest_profile:
                    oldest_profile = created
                if newest_profile is None or created > newest_profile:
                    newest_profile = created

    return {
        "total_profiles": total_profiles,
        "total_size_mb": round(total_size, 2),
        "oldest_profile": oldest_profile,
        "newest_profile": newest_profile,
        "average_size_mb": round(total_size / total_profiles, 2) if total_profiles > 0 else 0
    }
