"""
浏览器驱动管理工具 - 管理Chrome浏览器驱动的创建和配置

提供反检测Chrome驱动的创建、配置和管理功能。
采用函数式设计，无默认值原则。
"""

import re
import subprocess
from typing import Optional

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_chrome_version() -> str:
    """
    获取当前安装的Chrome版本

    Returns:
        Chrome版本号，如 "140.0.7339.208"
    """
    try:
        # Windows系统通过注册表获取Chrome版本
        result = subprocess.run(
            [
                "reg",
                "query",
                "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon",
                "/v",
                "version",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # 解析版本号
        match = re.search(
            r"version\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)", result.stdout
        )
        if match:
            return match.group(1)
    except Exception:
        pass

    try:
        # 备用方法：通过Chrome可执行文件获取版本
        result = subprocess.run(
            [
                "reg",
                "query",
                "HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome",
                "/v",
                "DisplayVersion",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        match = re.search(
            r"DisplayVersion\s+REG_SZ\s+(\d+\.\d+\.\d+\.\d+)", result.stdout
        )
        if match:
            return match.group(1)
    except Exception:
        pass

    # 如果无法获取，返回默认版本
    return "140.0.0.0"


def get_matching_user_agent(chrome_version: str = None) -> str:
    """
    获取匹配Chrome版本的User-Agent

    Args:
        chrome_version: Chrome版本号，如果为None则自动检测

    Returns:
        匹配的User-Agent字符串
    """
    if chrome_version is None:
        chrome_version = get_chrome_version()

    # 提取主版本号
    major_version = chrome_version.split(".")[0]

    return (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{major_version}.0.0.0 Safari/537.36"
    )


def create_undetected_driver(profile_name: str) -> webdriver.Chrome:
    """
    创建反检测Chrome驱动 - Chrome 140兼容版本

    Args:
        profile_name: 配置文件名称

    Returns:
        配置好的Chrome WebDriver对象

    Raises:
        Exception: 当驱动创建失败时
    """
    try:
        # 创建Chrome选项
        options = create_chrome_options(profile_name)

        # 创建反检测驱动 - 强制使用Chrome 140兼容版本
        driver = uc.Chrome(options=options, version_main=140)

        # 注入反检测脚本
        inject_stealth_scripts(driver)

        return driver
    except Exception as e:
        # 如果undetected-chromedriver失败，尝试使用标准驱动
        print(f"undetected-chromedriver失败，尝试标准驱动: {e}")
        return create_standard_driver(profile_name)


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
    # 设置实验性选项 - Chrome 140+兼容
    try:
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)
    except Exception:
        # Chrome 140+可能不支持某些选项，忽略错误
        pass

    # 设置用户代理 - 动态匹配当前Chrome版本
    user_agent = get_matching_user_agent()
    options.add_argument(f"--user-agent={user_agent}")

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
    创建Chrome选项 - Chrome 140兼容版本

    Args:
        profile_name: 配置文件名称

    Returns:
        配置好的ChromeOptions对象
    """
    options = uc.ChromeOptions()

    # 基础配置 - Chrome 140兼容
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")

    # 反检测配置
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")

    # 设置用户代理 - 动态匹配当前Chrome版本
    user_agent = get_matching_user_agent()
    options.add_argument(f"--user-agent={user_agent}")

    # 设置窗口大小
    options.add_argument("--window-size=1920,1080")

    # 设置配置文件
    profile_path = get_profile_path(profile_name)
    options.add_argument(f"--user-data-dir={profile_path}")

    # 简化的实验性选项 - Chrome 140兼容
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,
            "geolocation": 2,
            "media_stream": 2,
        },
        "profile.managed_default_content_settings": {"images": 1},
    }
    options.add_experimental_option("prefs", prefs)

    return options


def inject_stealth_scripts(driver: webdriver.Chrome) -> None:
    """
    注入反检测脚本 - 增强版本

    Args:
        driver: Chrome WebDriver对象
    """
    # 获取当前Chrome版本
    chrome_version = get_chrome_version()
    major_version = chrome_version.split(".")[0]
    # 隐藏webdriver属性 - 使用更安全的方式
    try:
        driver.execute_script(
            """
            if (navigator.webdriver !== undefined) {
                delete navigator.webdriver;
            }
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
        """
        )
    except Exception:
        # 如果重定义失败，尝试删除属性
        try:
            driver.execute_script("delete navigator.webdriver;")
        except Exception:
            pass  # 忽略错误，继续执行

    # 修改navigator属性
    driver.execute_script(
        """
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """
    )

    driver.execute_script(
        """
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
    """
    )

    # 修改chrome属性 - 安全版本
    try:
        driver.execute_script(
            """
            if (window.chrome === undefined) {
                window.chrome = {
                    runtime: {}
                };
            }
        """
        )
    except Exception:
        # 如果chrome属性已存在，忽略错误
        pass

    # 修改permissions属性
    driver.execute_script(
        """
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """
    )

    # 增强反检测脚本
    stealth_script = f"""
        // 隐藏自动化相关属性
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
        }});
        
        // 修改navigator.platform
        Object.defineProperty(navigator, 'platform', {{
            get: () => 'Win32',
        }});
        
        // 修改navigator.vendor
        Object.defineProperty(navigator, 'vendor', {{
            get: () => 'Google Inc.',
        }});
        
        // 修改navigator.appVersion - 动态匹配Chrome版本
        const chromeVersion = '{major_version}.0.0.0';
        Object.defineProperty(navigator, 'appVersion', {{
            get: () => `5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${{chromeVersion}} Safari/537.36`,
        }});
        
        // 隐藏selenium相关属性
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        // 修改chrome对象 - 安全版本
        if (window.chrome === undefined) {{
            Object.defineProperty(window, 'chrome', {{
                get: () => ({{
                    runtime: {{}},
                    loadTimes: function() {{}},
                    csi: function() {{}},
                    app: {{}}
                }}),
            }});
        }}
        
        // 修改screen属性
        Object.defineProperty(screen, 'availHeight', {{
            get: () => 1040,
        }});
        Object.defineProperty(screen, 'availWidth', {{
            get: () => 1920,
        }});
        Object.defineProperty(screen, 'colorDepth', {{
            get: () => 24,
        }});
        Object.defineProperty(screen, 'height', {{
            get: () => 1080,
        }});
        Object.defineProperty(screen, 'width', {{
            get: () => 1920,
        }});
        
        // 修改Date对象 - 安全版本
        try {{
            const originalDate = Date;
            Date = class extends originalDate {{
                constructor(...args) {{
                    if (args.length === 0) {{
                        super();
                    }} else {{
                        super(...args);
                    }}
                }}
            }};
            Object.setPrototypeOf(Date, originalDate);
        }} catch (e) {{
            // 如果Date对象修改失败，忽略错误
        }}
        
        // 修改getTimezoneOffset
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        Date.prototype.getTimezoneOffset = function() {{
            return -480; // 中国时区
        }};
    """

    driver.execute_script(stealth_script)


def get_profile_path(profile_name: str) -> str:
    """
    获取配置文件路径

    Args:
        profile_name: 配置文件名称

    Returns:
        配置文件路径
    """
    import time

    from app.utils.core.path_util import get_chrome_profiles_dir

    profiles_dir = get_chrome_profiles_dir()
    # 添加时间戳确保唯一性
    unique_profile_name = f"{profile_name}_{int(time.time())}"
    profile_path = profiles_dir / unique_profile_name

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
            "browser_version": driver.capabilities.get(
                "browserVersion", "Unknown"
            ),
            "driver_version": driver.capabilities.get("chrome", {}).get(
                "chromedriverVersion", "Unknown"
            ),
            "user_agent": driver.execute_script("return navigator.userAgent"),
            "window_size": driver.get_window_size(),
            "current_url": driver.current_url,
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


def restart_driver(
    driver: webdriver.Chrome, profile_name: str
) -> webdriver.Chrome:
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


def set_driver_timeouts(
    driver: webdriver.Chrome, page_load_timeout: int, implicit_wait: int
) -> None:
    """
    设置驱动超时

    Args:
        driver: Chrome WebDriver对象
        page_load_timeout: 页面加载超时时间（秒）
        implicit_wait: 隐式等待时间（秒）
    """
    driver.set_page_load_timeout(page_load_timeout)
    driver.implicitly_wait(implicit_wait)


def enable_driver_logging(
    driver: webdriver.Chrome, log_level: str = "INFO"
) -> None:
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
