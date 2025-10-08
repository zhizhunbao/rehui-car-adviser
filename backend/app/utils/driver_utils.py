"""
浏览器驱动管理工具 - 管理Chrome浏览器驱动的创建和配置

提供反检测Chrome驱动的创建、配置和管理功能。
采用函数式设计，无默认值原则。
"""

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Optional


def create_undetected_driver(profile_name: str) -> webdriver.Chrome:
    """
    创建反检测Chrome驱动

    Args:
        profile_name: 配置文件名称

    Returns:
        配置好的Chrome WebDriver对象

    Raises:
        Exception: 当驱动创建失败时
    """
    # 创建Chrome选项
    options = create_chrome_options(profile_name)

    # 创建反检测驱动
    driver = uc.Chrome(options=options)

    # 注入反检测脚本
    inject_stealth_scripts(driver)

    return driver


def create_standard_driver(profile_name: Optional[str]) -> webdriver.Chrome:
    """
    创建标准Chrome驱动

    Args:
        profile_name: 配置文件名称，可选

    Returns:
        配置好的Chrome WebDriver对象

    Raises:
        Exception: 当驱动创建失败时
    """
    options = Options()

    # 基础配置
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # 设置用户代理
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # 设置配置文件
    if profile_name:
        profile_path = get_profile_path(profile_name)
        options.add_argument(f"--user-data-dir={profile_path}")

    # 创建驱动
    driver = webdriver.Chrome(options=options)

    # 注入反检测脚本
    inject_stealth_scripts(driver)

    return driver


def create_chrome_options(profile_name: str) -> uc.ChromeOptions:
    """
    创建Chrome选项

    Args:
        profile_name: 配置文件名称

    Returns:
        配置好的ChromeOptions对象
    """
    options = uc.ChromeOptions()

    # 基础配置
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-features=VizDisplayCompositor")

    # 设置用户代理
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # 设置窗口大小
    options.add_argument("--window-size=1920,1080")

    # 设置配置文件
    profile_path = get_profile_path(profile_name)
    options.add_argument(f"--user-data-dir={profile_path}")

    # 设置实验性选项
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    return options


def inject_stealth_scripts(driver: webdriver.Chrome) -> None:
    """
    注入反检测脚本

    Args:
        driver: Chrome WebDriver对象
    """
    # 隐藏webdriver属性
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # 修改navigator属性
    driver.execute_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)

    driver.execute_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """)

    # 修改chrome属性
    driver.execute_script("""
        window.chrome = {
            runtime: {}
        };
    """)

    # 修改permissions属性
    driver.execute_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)


def get_profile_path(profile_name: str) -> str:
    """
    获取配置文件路径

    Args:
        profile_name: 配置文件名称

    Returns:
        配置文件路径
    """
    from app.utils.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    profile_path = profiles_dir / profile_name

    # 确保配置文件目录存在
    profile_path.mkdir(parents=True, exist_ok=True)

    return str(profile_path)


def set_driver_properties(driver: webdriver.Chrome) -> None:
    """
    设置驱动属性

    Args:
        driver: Chrome WebDriver对象
    """
    # 设置页面加载超时
    driver.set_page_load_timeout(30)

    # 设置隐式等待
    driver.implicitly_wait(10)

    # 设置窗口大小
    driver.set_window_size(1920, 1080)

    # 最大化窗口
    driver.maximize_window()


def cleanup_driver(driver: webdriver.Chrome) -> None:
    """
    清理驱动资源

    Args:
        driver: Chrome WebDriver对象
    """
    try:
        # 关闭所有窗口
        driver.quit()
    except Exception:
        # 如果清理失败，忽略错误
        pass


def get_driver_info(driver: webdriver.Chrome) -> dict:
    """
    获取驱动信息

    Args:
        driver: Chrome WebDriver对象

    Returns:
        驱动信息字典
    """
    try:
        return {
            "browser_name": driver.name,
            "browser_version": driver.capabilities.get("browserVersion", "Unknown"),
            "driver_version": driver.capabilities.get("chrome", {}).get("chromedriverVersion", "Unknown"),
            "user_agent": driver.execute_script("return navigator.userAgent"),
            "window_size": driver.get_window_size(),
            "current_url": driver.current_url
        }
    except Exception:
        return {"error": "无法获取驱动信息"}


def is_driver_alive(driver: webdriver.Chrome) -> bool:
    """
    检查驱动是否存活

    Args:
        driver: Chrome WebDriver对象

    Returns:
        驱动是否存活
    """
    try:
        # 尝试获取当前URL
        driver.current_url
        return True
    except Exception:
        return False


def restart_driver(driver: webdriver.Chrome, profile_name: str) -> webdriver.Chrome:
    """
    重启驱动

    Args:
        driver: 当前Chrome WebDriver对象
        profile_name: 配置文件名称

    Returns:
        新的Chrome WebDriver对象
    """
    # 清理旧驱动
    cleanup_driver(driver)

    # 创建新驱动
    new_driver = create_undetected_driver(profile_name)

    # 设置驱动属性
    set_driver_properties(new_driver)

    return new_driver


def get_driver_capabilities(driver: webdriver.Chrome) -> dict:
    """
    获取驱动能力信息

    Args:
        driver: Chrome WebDriver对象

    Returns:
        驱动能力信息字典
    """
    try:
        return driver.capabilities
    except Exception:
        return {}


def set_driver_timeouts(driver: webdriver.Chrome, page_load_timeout: int, implicit_wait: int) -> None:
    """
    设置驱动超时

    Args:
        driver: Chrome WebDriver对象
        page_load_timeout: 页面加载超时时间（秒）
        implicit_wait: 隐式等待时间（秒）
    """
    driver.set_page_load_timeout(page_load_timeout)
    driver.implicitly_wait(implicit_wait)


def enable_driver_logging(driver: webdriver.Chrome, log_level: str = "INFO") -> None:
    """
    启用驱动日志

    Args:
        driver: Chrome WebDriver对象
        log_level: 日志级别
    """
    # 设置日志级别
    driver.set_log_level(log_level)

    # 启用性能日志
    driver.execute_cdp_cmd("Performance.enable", {})
    driver.execute_cdp_cmd("Network.enable", {})
