"""
验证码处理工具 - 处理各种类型的验证码

提供滑块验证码、拼图验证码等验证码的自动处理功能。
采用函数式设计，无默认值原则。
"""

import time
import random
from typing import Optional, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def has_slider_captcha(driver: WebDriver) -> bool:
    """
    检测是否有滑块验证码

    Args:
        driver: Selenium WebDriver对象

    Returns:
        是否存在滑块验证码
    """
    slider_selectors = [
        "//div[contains(@class, 'slider')]",
        "//div[contains(@class, 'captcha')]",
        "//div[contains(@class, 'verification')]",
        "//div[contains(@id, 'slider')]",
        "//div[contains(@id, 'captcha')]",
        "//canvas[contains(@class, 'slider')]",
        "//div[contains(@class, 'nc-container')]",
        "//div[contains(@class, 'nc_scale')]"
    ]

    for selector in slider_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return True
        except NoSuchElementException:
            continue

    return False


async def solve_slider_captcha(driver: WebDriver, max_attempts: int) -> bool:
    """
    自动解决滑块验证码

    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决验证码
    """
    for attempt in range(max_attempts):
        try:
            # 查找滑块元素
            slider = find_slider_element(driver)
            if not slider:
                return False

            # 查找滑块轨道
            track = find_slider_track(driver)
            if not track:
                return False

            # 计算滑动距离
            distance = calculate_slider_distance(driver, slider, track)
            if distance <= 0:
                return False

            # 执行滑动操作
            success = await perform_slide(driver, slider, distance)
            if success:
                # 等待验证结果
                time.sleep(2)
                if not has_slider_captcha(driver):
                    return True

            # 如果失败，等待一段时间再重试
            time.sleep(random.uniform(1, 3))

        except Exception:
            # 如果出现异常，等待后重试
            time.sleep(random.uniform(1, 2))
            continue

    return False


def is_puzzle_captcha(driver: WebDriver) -> bool:
    """
    检测是否是拼图验证码

    Args:
        driver: Selenium WebDriver对象

    Returns:
        是否是拼图验证码
    """
    puzzle_selectors = [
        "//div[contains(@class, 'puzzle')]",
        "//div[contains(@class, 'jigsaw')]",
        "//canvas[contains(@class, 'puzzle')]",
        "//div[contains(@class, 'geetest')]",
        "//div[contains(@class, 'click-captcha')]"
    ]

    for selector in puzzle_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return True
        except NoSuchElementException:
            continue

    return False


async def solve_puzzle_captcha(driver: WebDriver, max_attempts: int) -> bool:
    """
    处理拼图验证码

    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决验证码
    """
    for attempt in range(max_attempts):
        try:
            # 查找拼图元素
            puzzle_element = find_puzzle_element(driver)
            if not puzzle_element:
                return False

            # 获取拼图位置
            puzzle_pos = get_puzzle_position(driver, puzzle_element)
            if not puzzle_pos:
                return False

            # 执行点击操作
            success = await perform_puzzle_click(driver, puzzle_pos)
            if success:
                # 等待验证结果
                time.sleep(2)
                if not is_puzzle_captcha(driver):
                    return True

            # 如果失败，等待一段时间再重试
            time.sleep(random.uniform(1, 3))

        except Exception:
            # 如果出现异常，等待后重试
            time.sleep(random.uniform(1, 2))
            continue

    return False


def find_slider_element(driver: WebDriver) -> Optional[object]:
    """
    查找滑块元素

    Args:
        driver: Selenium WebDriver对象

    Returns:
        滑块元素，如果未找到则返回None
    """
    slider_selectors = [
        "//div[contains(@class, 'slider-button')]",
        "//div[contains(@class, 'slider-handle')]",
        "//div[contains(@class, 'nc_iconfont')]",
        "//span[contains(@class, 'slider')]",
        "//div[contains(@class, 'captcha-slider')]"
    ]

    for selector in slider_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            continue

    return None


def find_slider_track(driver: WebDriver) -> Optional[object]:
    """
    查找滑块轨道

    Args:
        driver: Selenium WebDriver对象

    Returns:
        滑块轨道元素，如果未找到则返回None
    """
    track_selectors = [
        "//div[contains(@class, 'slider-track')]",
        "//div[contains(@class, 'nc_scale')]",
        "//div[contains(@class, 'slider-bg')]",
        "//div[contains(@class, 'captcha-track')]"
    ]

    for selector in track_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            continue

    return None


def calculate_slider_distance(driver: WebDriver, slider: object, track: object) -> int:
    """
    计算滑块需要滑动的距离

    Args:
        driver: Selenium WebDriver对象
        slider: 滑块元素
        track: 滑块轨道元素

    Returns:
        滑动距离（像素）
    """
    try:
        # 获取轨道宽度
        track_width = track.size['width']

        # 获取滑块当前位置
        slider_location = slider.location['x']

        # 计算需要滑动的距离（通常是轨道宽度减去滑块宽度）
        slider_width = slider.size['width']
        distance = track_width - slider_width

        # 添加一些随机性
        distance += random.randint(-5, 5)

        return max(0, distance)

    except Exception:
        # 如果计算失败，返回默认距离
        return 200


async def perform_slide(driver: WebDriver, slider: object, distance: int) -> bool:
    """
    执行滑动操作

    Args:
        driver: Selenium WebDriver对象
        slider: 滑块元素
        distance: 滑动距离

    Returns:
        是否滑动成功
    """
    try:
        actions = ActionChains(driver)

        # 移动到滑块
        actions.move_to_element(slider)
        actions.click_and_hold(slider)

        # 模拟人类滑动轨迹
        steps = random.randint(10, 20)
        step_distance = distance / steps

        for i in range(steps):
            # 添加随机偏移
            offset_x = step_distance + random.uniform(-2, 2)
            offset_y = random.uniform(-1, 1)

            actions.move_by_offset(offset_x, offset_y)

            # 随机延迟
            time.sleep(random.uniform(0.01, 0.05))

        # 释放滑块
        actions.release()
        actions.perform()

        return True

    except Exception:
        return False


def find_puzzle_element(driver: WebDriver) -> Optional[object]:
    """
    查找拼图元素

    Args:
        driver: Selenium WebDriver对象

    Returns:
        拼图元素，如果未找到则返回None
    """
    puzzle_selectors = [
        "//div[contains(@class, 'puzzle-piece')]",
        "//div[contains(@class, 'jigsaw-piece')]",
        "//canvas[contains(@class, 'puzzle')]",
        "//div[contains(@class, 'geetest_canvas')]"
    ]

    for selector in puzzle_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            continue

    return None


def get_puzzle_position(driver: WebDriver, puzzle_element: object) -> Optional[Tuple[int, int]]:
    """
    获取拼图位置

    Args:
        driver: Selenium WebDriver对象
        puzzle_element: 拼图元素

    Returns:
        拼图位置坐标 (x, y)，如果未找到则返回None
    """
    try:
        # 获取元素位置和大小
        location = puzzle_element.location
        size = puzzle_element.size

        # 计算中心点
        center_x = location['x'] + size['width'] // 2
        center_y = location['y'] + size['height'] // 2

        # 添加一些随机性
        center_x += random.randint(-10, 10)
        center_y += random.randint(-10, 10)

        return (center_x, center_y)

    except Exception:
        return None


async def perform_puzzle_click(driver: WebDriver, position: Tuple[int, int]) -> bool:
    """
    执行拼图点击操作

    Args:
        driver: Selenium WebDriver对象
        position: 点击位置坐标

    Returns:
        是否点击成功
    """
    try:
        actions = ActionChains(driver)

        # 移动到指定位置
        actions.move_by_offset(position[0], position[1])

        # 点击
        actions.click()
        actions.perform()

        return True

    except Exception:
        return False


def has_captcha(driver: WebDriver) -> bool:
    """
    检测页面是否有验证码

    Args:
        driver: Selenium WebDriver对象

    Returns:
        是否有验证码
    """
    return has_slider_captcha(driver) or is_puzzle_captcha(driver)


async def solve_captcha(driver: WebDriver, max_attempts: int) -> bool:
    """
    自动解决验证码

    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决验证码
    """
    # 首先尝试滑块验证码
    if has_slider_captcha(driver):
        return await solve_slider_captcha(driver, max_attempts)

    # 然后尝试拼图验证码
    if is_puzzle_captcha(driver):
        return await solve_puzzle_captcha(driver, max_attempts)

    return False


def wait_for_captcha_to_disappear(driver: WebDriver, timeout: int = 10) -> bool:
    """
    等待验证码消失

    Args:
        driver: Selenium WebDriver对象
        timeout: 超时时间（秒）

    Returns:
        验证码是否消失
    """
    try:
        wait = WebDriverWait(driver, timeout)

        # 等待验证码元素消失
        wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'captcha')]")))
        return True

    except TimeoutException:
        return False


def get_captcha_type(driver: WebDriver) -> str:
    """
    获取验证码类型

    Args:
        driver: Selenium WebDriver对象

    Returns:
        验证码类型
    """
    if has_slider_captcha(driver):
        return "slider"
    elif is_puzzle_captcha(driver):
        return "puzzle"
    else:
        return "unknown"


def skip_captcha(driver: WebDriver) -> bool:
    """
    跳过验证码（如果可能）

    Args:
        driver: Selenium WebDriver对象

    Returns:
        是否成功跳过
    """
    try:
        # 查找跳过按钮
        skip_selectors = [
            "//button[contains(text(), 'Skip')]",
            "//button[contains(text(), '跳过')]",
            "//a[contains(text(), 'Skip')]",
            "//a[contains(text(), '跳过')]",
            "//div[contains(@class, 'skip')]"
        ]

        for selector in skip_selectors:
            try:
                element = driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    element.click()
                    time.sleep(1)
                    return True
            except NoSuchElementException:
                continue

        return False

    except Exception:
        return False
