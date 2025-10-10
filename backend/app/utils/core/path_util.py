from pathlib import Path


def get_project_root() -> Path:
    """
    获取项目根目录路径

    Returns:
        Path: 项目根目录的Path对象
    """
    # 当前文件路径: backend/app/utils/core/path_util.py
    current_file = Path(__file__)

    # 项目根目录: 从当前文件向上4级目录
    # backend/app/utils/core/path_util.py -> backend/app/utils/core -> backend/app/utils -> backend/app -> backend -> 项目根目录
    project_root = current_file.parent.parent.parent.parent.parent

    return project_root


def get_env_file_path() -> Path:
    """
    获取.env文件路径

    Returns:
        Path: .env文件的Path对象
    """
    return get_project_root() / ".env"


def get_database_path() -> Path:
    """
    获取数据库文件路径

    Returns:
        Path: 数据库文件的Path对象
    """
    return get_project_root() / "backend" / "rehui_car_adviser.db"


def get_logs_dir() -> Path:
    """
    获取日志目录路径

    Returns:
        Path: 日志目录的Path对象
    """
    logs_dir = get_project_root() / "backend" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_backend_log_path() -> Path:
    """
    获取后端日志文件路径

    Returns:
        Path: 后端日志文件的Path对象
    """
    return get_logs_dir() / "backend.log"


def get_frontend_log_path() -> Path:
    """
    获取前端日志文件路径

    Returns:
        Path: 前端日志文件的Path对象
    """
    return get_logs_dir() / "frontend.log"


def get_data_dir() -> Path:
    """
    获取数据目录路径

    Returns:
        Path: 数据目录的Path对象
    """
    data_dir = get_project_root() / "backend" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_cargurus_data_dir() -> Path:
    """
    获取CarGurus数据目录路径

    Returns:
        Path: CarGurus数据目录的Path对象
    """
    cargurus_dir = get_data_dir() / "cargurus"
    cargurus_dir.mkdir(parents=True, exist_ok=True)
    return cargurus_dir


def get_chrome_profiles_dir() -> Path:
    """
    获取Chrome配置文件目录路径

    Returns:
        Path: Chrome配置文件目录的Path对象
    """
    profiles_dir = get_project_root() / "backend" / "chrome_profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir


def get_tmp_dir() -> Path:
    """
    获取临时文件目录路径

    Returns:
        Path: 临时文件目录的Path对象
    """
    tmp_dir = get_project_root() / "backend" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def get_dead_links_file() -> Path:
    """
    获取死链记录文件路径

    Returns:
        Path: 死链记录文件的Path对象
    """
    return get_tmp_dir() / "dead_links.json"


def get_backend_dir() -> Path:
    """
    获取backend目录路径

    Returns:
        Path: backend目录的Path对象
    """
    return get_project_root() / "backend"


def get_frontend_dir() -> Path:
    """
    获取frontend目录路径

    Returns:
        Path: frontend目录的Path对象
    """
    return get_project_root() / "frontend"


# 兼容性函数 - 使用os.path的方式
def get_logs_dir_os() -> str:
    """
    获取日志目录路径 (os.path版本，用于兼容现有代码)

    Returns:
        str: 日志目录的字符串路径
    """
    return str(get_logs_dir())


def get_backend_log_path_os() -> str:
    """
    获取后端日志文件路径 (os.path版本，用于兼容现有代码)

    Returns:
        str: 后端日志文件的字符串路径
    """
    return str(get_backend_log_path())


def get_frontend_log_path_os() -> str:
    """
    获取前端日志文件路径 (os.path版本，用于兼容现有代码)

    Returns:
        str: 前端日志文件的字符串路径
    """
    return str(get_frontend_log_path())
