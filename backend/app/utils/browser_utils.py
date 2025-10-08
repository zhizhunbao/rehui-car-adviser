"""
Chrome浏览器自动化工具类 - 重构版本

这个模块提供了Chrome浏览器的自动化操作功能，包括：
- 浏览器驱动管理
- 用户代理管理
- 便捷函数接口

重构说明：
- 删除了与现有utils模块重复的功能
- 保留核心协调功能
- 提供便捷函数接口保持向后兼容
"""

import random
from contextlib import asynccontextmanager
from typing import List

# 导入现有的utils模块
from app.utils.driver_utils import (
    create_undetected_driver, create_standard_driver
)
from app.utils.profile_utils import (
    cleanup_old_profiles as _cleanup_old_profiles
)
from app.utils.url_checker_utils import check_url_alive_sync
from app.utils.page_detection_utils import (
    is_blocked_page as _is_blocked_page
)
from app.utils.captcha_utils import (
    has_captcha as _has_captcha, solve_captcha as _solve_captcha
)
from app.utils.logger import logger


class BrowserUtils:
    """Chrome浏览器自动化工具类 - 重构版本"""

    def __init__(self):
        """初始化浏览器工具类"""
        # User-Agent列表 - 保留原有配置
        self.user_agents = [
            ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"),
            ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
             "Safari/537.36"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 "
             "Safari/537.36"),
            ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        ]

    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)

    @asynccontextmanager
    async def get_driver(self, profile_name: str,
                         use_undetected: bool = False):
        """
        获取Chrome驱动 - 上下文管理器

        Args:
            profile_name: 配置文件名称
            use_undetected: 是否使用反检测驱动

        Yields:
            WebDriver: Chrome驱动实例
        """
        driver = None
        try:
            if use_undetected:
                driver = create_undetected_driver(profile_name)
            else:
                driver = create_standard_driver(profile_name)

            logger.log_result(
                f"创建Chrome驱动成功: profile={profile_name}, "
                f"undetected={use_undetected}"
            )
            yield driver

        except Exception as e:
            logger.log_result(f"创建Chrome驱动失败: {e}")
            raise
        finally:
            if driver:
                try:
                    driver.quit()
                    logger.log_result("Chrome驱动已关闭")
                except Exception as e:
                    logger.log_result(f"关闭Chrome驱动时出错: {e}")

    def cleanup_old_profiles(self, days_old: int = 7) -> None:
        """
        清理旧的Chrome配置文件

        Args:
            days_old: 清理多少天前的配置文件
        """
        _cleanup_old_profiles(days_old)
        logger.log_result(f"清理了{days_old}天前的Chrome配置文件")


# 创建全局实例
browser_utils = BrowserUtils()


# =============================================================================
# 便捷函数 - 保持向后兼容
# =============================================================================

def check_url_alive(url: str, max_retries: int = 3) -> bool:
    """
    检查URL是否可访问

    Args:
        url: 要检查的URL
        max_retries: 最大重试次数

    Returns:
        是否可访问
    """
    return check_url_alive_sync(url, max_retries)


def is_blocked_page(page_html: str) -> bool:
    """
    检测页面是否被阻止

    Args:
        page_html: 页面HTML内容

    Returns:
        是否被阻止
    """
    return _is_blocked_page(page_html)


def has_captcha(driver) -> bool:
    """
    检测页面是否有验证码

    Args:
        driver: WebDriver实例

    Returns:
        是否有验证码
    """
    return _has_captcha(driver)


async def solve_captcha(driver, max_attempts: int = 3) -> bool:
    """
    自动解决验证码

    Args:
        driver: WebDriver实例
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决
    """
    return await _solve_captcha(driver, max_attempts)


def cleanup_old_profiles(days_old: int = 7) -> None:
    """
    清理旧的Chrome配置文件

    Args:
        days_old: 清理多少天前的配置文件
    """
    browser_utils.cleanup_old_profiles(days_old)


def get_random_user_agent() -> str:
    """
    获取随机User-Agent

    Returns:
        随机User-Agent字符串
    """
    return browser_utils.get_random_user_agent()


# =============================================================================
# 死链管理便捷函数 - 保持向后兼容
# =============================================================================

def write_dead_links_list(dead_links: List[str]) -> None:
    """
    写入死链列表

    Args:
        dead_links: 死链列表
    """
    from app.utils.dead_link_utils import write_dead_links as _write_dead_links
    _write_dead_links(dead_links)


def read_dead_links_set() -> set:
    """
    读取死链列表

    Returns:
        死链集合
    """
    from app.utils.dead_link_utils import read_dead_links as _read_dead_links
    return _read_dead_links()


def is_dead_link(url: str) -> bool:
    """
    检查URL是否为死链

    Args:
        url: 要检查的URL

    Returns:
        是否为死链
    """
    from app.utils.dead_link_utils import is_dead_link as _is_dead_link
    return _is_dead_link(url)


def add_dead_link(url: str) -> None:
    """
    添加死链

    Args:
        url: 要添加的死链URL
    """
    from app.utils.dead_link_utils import add_dead_link as _add_dead_link
    _add_dead_link(url)