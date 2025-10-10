"""
行为模拟工具 - 提供统一的反爬虫行为模拟策略

提供人类行为模拟、随机延迟、鼠标移动等功能。
采用函数式设计，无默认值原则。
"""

import random
import time
import asyncio
from typing import Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


def simulate_human_behavior(driver: WebDriver) -> None:
    """
    模拟人类浏览行为

    Args:
        driver: Selenium WebDriver对象
    """
    # 随机滚动
    random_scroll(driver, 100, 500)

    # 随机延迟
    random_delay(0.5, 2.0)

    # 安全的鼠标移动
    safe_mouse_move(driver)


def random_scroll(driver: WebDriver, min_amount: int, max_amount: int) -> None:
    """
    随机滚动页面

    Args:
        driver: Selenium WebDriver对象
        min_amount: 最小滚动距离
        max_amount: 最大滚动距离
    """
    # 随机滚动距离
    scroll_amount = random.randint(min_amount, max_amount)

    # 随机滚动方向（向上或向下）
    direction = random.choice([1, -1])
    scroll_amount *= direction

    # 执行滚动
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")

    # 滚动后短暂延迟
    time.sleep(random.uniform(0.1, 0.3))


def random_delay(min_seconds: float, max_seconds: float) -> None:
    """
    随机延迟

    Args:
        min_seconds: 最小延迟秒数
        max_seconds: 最大延迟秒数
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


async def async_random_delay(min_seconds: float, max_seconds: float) -> None:
    """
    异步随机延迟

    Args:
        min_seconds: 最小延迟秒数
        max_seconds: 最大延迟秒数
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


def safe_mouse_move(driver: WebDriver) -> None:
    """
    安全的鼠标移动

    Args:
        driver: Selenium WebDriver对象
    """
    try:
        # 获取页面中心点
        window_size = driver.get_window_size()
        center_x = window_size['width'] // 2
        center_y = window_size['height'] // 2

        # 添加随机偏移
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)

        target_x = center_x + offset_x
        target_y = center_y + offset_y

        # 执行鼠标移动
        actions = ActionChains(driver)
        actions.move_by_offset(target_x, target_y)
        actions.perform()

    except Exception:
        # 如果鼠标移动失败，忽略错误
        pass


def simulate_typing(driver: WebDriver, element, text: str) -> None:
    """
    模拟人类打字

    Args:
        driver: Selenium WebDriver对象
        element: 输入元素
        text: 要输入的文本
    """
    # 点击元素获得焦点
    element.click()
    random_delay(0.1, 0.3)

    # 清空现有内容
    element.clear()
    random_delay(0.1, 0.2)

    # 逐字符输入
    for char in text:
        element.send_keys(char)
        # 随机延迟模拟打字速度
        time.sleep(random.uniform(0.05, 0.15))


def random_user_agent() -> str:
    """
    获取随机User-Agent

    Returns:
        随机的User-Agent字符串
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]

    return random.choice(user_agents)


def simulate_page_reading(driver: WebDriver, min_time: float = 2.0, max_time: float = 8.0) -> None:
    """
    模拟页面阅读行为

    Args:
        driver: Selenium WebDriver对象
        min_time: 最小阅读时间
        max_time: 最大阅读时间
    """
    reading_time = random.uniform(min_time, max_time)

    # 模拟阅读过程中的滚动
    scroll_count = random.randint(2, 5)
    scroll_interval = reading_time / scroll_count

    for _ in range(scroll_count):
        random_scroll(driver, 200, 800)
        time.sleep(scroll_interval)


def simulate_element_hover(driver: WebDriver, element) -> None:
    """
    模拟鼠标悬停元素

    Args:
        driver: Selenium WebDriver对象
        element: 要悬停的元素
    """
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element)
        actions.perform()

        # 悬停后短暂延迟
        random_delay(0.5, 1.5)

    except Exception:
        # 如果悬停失败，忽略错误
        pass


def simulate_form_filling(driver: WebDriver, form_data: dict) -> None:
    """
    模拟表单填写行为

    Args:
        driver: Selenium WebDriver对象
        form_data: 表单数据字典
    """
    for field_name, value in form_data.items():
        try:
            # 查找输入字段
            element = driver.find_element(By.NAME, field_name)

            # 模拟人类填写行为
            simulate_typing(driver, element, str(value))

            # 字段间随机延迟
            random_delay(0.3, 1.0)

        except Exception:
            # 如果字段不存在，继续下一个
            continue


def simulate_search_behavior(driver: WebDriver, search_term: str) -> None:
    """
    模拟搜索行为

    Args:
        driver: Selenium WebDriver对象
        search_term: 搜索词
    """
    try:
        # 查找搜索框
        search_box = driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[name*='search'], input[placeholder*='search']")

        # 模拟输入搜索词
        simulate_typing(driver, search_box, search_term)

        # 搜索前短暂延迟
        random_delay(0.5, 1.0)

        # 模拟按回车键
        search_box.send_keys("\n")

    except Exception:
        # 如果搜索框不存在，忽略错误
        pass


def simulate_click_with_delay(driver: WebDriver, element, min_delay: float = 0.5, max_delay: float = 2.0) -> None:
    """
    模拟带延迟的点击行为

    Args:
        driver: Selenium WebDriver对象
        element: 要点击的元素
        min_delay: 最小延迟
        max_delay: 最大延迟
    """
    # 点击前延迟
    random_delay(min_delay, max_delay)

    # 执行点击
    element.click()

    # 点击后延迟
    random_delay(0.2, 0.8)


def simulate_mouse_trajectory(driver: WebDriver, start_point: Tuple[int, int], end_point: Tuple[int, int]) -> None:
    """
    模拟鼠标轨迹移动

    Args:
        driver: Selenium WebDriver对象
        start_point: 起始点坐标 (x, y)
        end_point: 结束点坐标 (x, y)
    """
    try:
        actions = ActionChains(driver)

        # 移动到起始点
        actions.move_by_offset(start_point[0], start_point[1])

        # 计算中间点
        mid_x = (start_point[0] + end_point[0]) // 2
        mid_y = (start_point[1] + end_point[1]) // 2

        # 添加随机偏移
        mid_x += random.randint(-20, 20)
        mid_y += random.randint(-20, 20)

        # 移动到中间点
        actions.move_by_offset(mid_x - start_point[0], mid_y - start_point[1])

        # 移动到结束点
        actions.move_by_offset(end_point[0] - mid_x, end_point[1] - mid_y)

        actions.perform()

    except Exception:
        # 如果轨迹移动失败，忽略错误
        pass


def simulate_zoom_behavior(driver: WebDriver) -> None:
    """
    模拟缩放行为

    Args:
        driver: Selenium WebDriver对象
    """
    try:
        # 随机选择缩放操作
        zoom_actions = [
            lambda: driver.execute_script("document.body.style.zoom='1.1'"),
            lambda: driver.execute_script("document.body.style.zoom='0.9'"),
            lambda: driver.execute_script("document.body.style.zoom='1.0'")
        ]

        # 执行随机缩放
        random.choice(zoom_actions)()

        # 缩放后延迟
        random_delay(0.5, 1.5)

        # 恢复原始缩放
        driver.execute_script("document.body.style.zoom='1.0'")

    except Exception:
        # 如果缩放失败，忽略错误
        pass


def simulate_tab_switching(driver: WebDriver) -> None:
    """
    模拟标签页切换行为

    Args:
        driver: Selenium WebDriver对象
    """
    try:
        # 获取所有窗口句柄
        window_handles = driver.window_handles

        if len(window_handles) > 1:
            # 随机切换到另一个标签页
            target_handle = random.choice(window_handles)
            driver.switch_to.window(target_handle)

            # 切换后短暂停留
            random_delay(1.0, 3.0)

            # 切换回原标签页
            original_handle = window_handles[0]
            driver.switch_to.window(original_handle)

    except Exception:
        # 如果标签页切换失败，忽略错误
        pass


def simulate_resize_window(driver: WebDriver) -> None:
    """
    模拟窗口大小调整

    Args:
        driver: Selenium WebDriver对象
    """
    try:
        # 获取当前窗口大小
        current_size = driver.get_window_size()

        # 随机调整窗口大小
        width_variation = random.randint(-100, 100)
        height_variation = random.randint(-100, 100)

        new_width = max(800, current_size['width'] + width_variation)
        new_height = max(600, current_size['height'] + height_variation)

        driver.set_window_size(new_width, new_height)

        # 调整后延迟
        random_delay(0.5, 1.5)

    except Exception:
        # 如果窗口调整失败，忽略错误
        pass


def get_random_viewport_size() -> Tuple[int, int]:
    """
    获取随机视口大小

    Returns:
        随机的视口大小 (width, height)
    """
    viewport_sizes = [
        (1920, 1080),  # Full HD
        (1366, 768),   # Common laptop
        (1440, 900),   # MacBook Air
        (1536, 864),   # Surface
        (1280, 720),   # HD
        (1600, 900),   # HD+
        (2560, 1440),  # 2K
        (3840, 2160)   # 4K
    ]

    return random.choice(viewport_sizes)
