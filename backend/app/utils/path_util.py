from pathlib import Path


def get_project_root() -> Path:
    """
    获取项目根目录路径
    
    Returns:
        Path: 项目根目录的Path对象
    """
    # 当前文件路径: backend/app/utils/path_util.py
    current_file = Path(__file__)
    
    # 项目根目录: 从当前文件向上3级目录
    # backend/app/utils/path_util.py -> backend/app/utils -> backend/app ->
    # backend -> 项目根目录
    project_root = current_file.parent.parent.parent.parent
    
    return project_root


def get_env_file_path() -> Path:
    """
    获取.env文件路径
    
    Returns:
        Path: .env文件的Path对象
    """
    return get_project_root() / "backend" / ".env"


def get_database_path() -> Path:
    """
    获取数据库文件路径
    
    Returns:
        Path: 数据库文件的Path对象
    """
    return get_project_root() / "backend" / "rehui_car_adviser.db"
