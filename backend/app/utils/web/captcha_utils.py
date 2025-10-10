"""
验证码处理工具 - 处理各种类型的验证码

提供滑块验证码、拼图验证码等验证码的自动处理功能。
采用函数式设计，无默认值原则。
"""

import asyncio
import os
import random
import time
from datetime import datetime
from typing import Optional, Tuple

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.utils.core.logger import logger


def save_captcha_html(driver: WebDriver, captcha_type: str = "unknown") -> str:
    """
    保存验证码页面的HTML到tmp目录，用于调试分析

    Args:
        driver: Selenium WebDriver对象
        captcha_type: 验证码类型

    Returns:
        保存的文件路径
    """
    try:
        # 确保tmp目录存在
        tmp_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "tmp"
        )
        os.makedirs(tmp_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captcha_{captcha_type}_{timestamp}.html"
        filepath = os.path.join(tmp_dir, filename)

        # 获取页面HTML
        html_content = driver.page_source

        # 保存HTML文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"验证码HTML已保存到: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"保存验证码HTML失败: {e}")
        return ""


def has_slider_captcha(driver: WebDriver) -> bool:
    """
    检测是否有滑块验证码 - 增强版本

    Args:
        driver: Selenium WebDriver对象

    Returns:
        是否存在滑块验证码
    """
    # 扩展的滑块验证码选择器
    slider_selectors = [
        # 通用滑块选择器
        "//div[contains(@class, 'slider')]",
        "//div[contains(@class, 'captcha')]",
        "//div[contains(@class, 'verification')]",
        "//div[contains(@id, 'slider')]",
        "//div[contains(@id, 'captcha')]",
        "//canvas[contains(@class, 'slider')]",
        # 阿里云滑块验证码
        "//div[contains(@class, 'nc-container')]",
        "//div[contains(@class, 'nc_scale')]",
        "//div[contains(@class, 'nc_iconfont')]",
        "//div[contains(@class, 'nc_wrapper')]",
        # 腾讯滑块验证码
        "//div[contains(@class, 'tcaptcha')]",
        "//div[contains(@id, 'tcaptcha')]",
        "//div[contains(@class, 'tc-drag')]",
        # 极验滑块验证码
        "//div[contains(@class, 'geetest')]",
        "//div[contains(@class, 'gt_slider')]",
        "//div[contains(@class, 'gt_box')]",
        # 其他常见滑块验证码
        "//div[contains(@class, 'slider-captcha')]",
        "//div[contains(@class, 'slide-captcha')]",
        "//div[contains(@class, 'drag-captcha')]",
        "//div[contains(@class, 'slider-verify')]",
        "//div[contains(@class, 'verify-slider')]",
        # 通过文本内容检测
        "//div[contains(text(), '滑动')]",
        "//div[contains(text(), '拖动')]",
        "//div[contains(text(), 'slide')]",
        "//div[contains(text(), 'drag')]",
        # 通过属性检测
        "//*[@data-type='slider']",
        "//*[@data-captcha='slider']",
        "//*[contains(@data-testid, 'slider')]",
    ]

    for selector in slider_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if (
                    element.is_displayed()
                    and element.size["width"] > 0
                    and element.size["height"] > 0
                ):
                    logger.info(f"滑块验证码检测 - 找到滑块元素: {selector}")
                    return True
        except Exception as e:
            logger.debug(f"滑块验证码检测 - 选择器 {selector} 检测失败: {e}")
            continue

    return False


async def solve_slider_captcha(driver: WebDriver, max_attempts: int) -> bool:
    """
    自动解决滑块验证码 - 增强版本

    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决验证码
    """
    for attempt in range(max_attempts):
        try:
            # 等待页面加载
            time.sleep(random.uniform(1, 2))

            # 查找滑块元素
            slider = find_slider_element(driver)
            if not slider:
                logger.log_result(
                    "滑块验证码",
                    f"未找到滑块元素 (尝试 {attempt + 1}/{max_attempts})",
                )
                time.sleep(random.uniform(2, 4))
                continue

            # 查找滑块轨道
            track = find_slider_track(driver)
            if not track:
                logger.log_result(
                    "滑块验证码",
                    f"未找到滑块轨道 (尝试 {attempt + 1}/{max_attempts})",
                )
                time.sleep(random.uniform(2, 4))
                continue

            # 滚动到滑块可见区域
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", slider
            )
            time.sleep(random.uniform(0.5, 1))

            # 计算滑动距离 - 使用更精确的算法
            distance = calculate_enhanced_slider_distance(
                driver, slider, track
            )
            if distance <= 0:
                logger.log_result(
                    "滑块验证码",
                    f"计算滑动距离失败: {distance} (尝试 {attempt + 1}/{max_attempts})",
                )
                time.sleep(random.uniform(2, 4))
                continue

            logger.log_result(
                "滑块验证码",
                f"开始滑动，距离: {distance}px (尝试 {attempt + 1}/{max_attempts})",
            )

            # 执行滑动操作 - 使用更智能的算法
            success = await perform_enhanced_slide(driver, slider, distance)
            if success:
                # 等待验证结果
                await asyncio.sleep(random.uniform(2, 4))

                # 检查是否还有验证码
                if not has_slider_captcha(driver):
                    logger.info(
                        f"滑块验证码解决成功 (尝试 {attempt + 1}/{max_attempts})"
                    )
                    return True
                else:
                    logger.warning(
                        f"滑块验证码仍然存在，可能需要重试 (尝试 {attempt + 1}/{max_attempts})"
                    )

                    # 尝试微调滑动距离
                    if attempt < max_attempts - 1:
                        logger.info("尝试微调滑动距离")
                        fine_tune_distance = random.randint(-10, 10)
                        adjusted_distance = distance + fine_tune_distance
                        logger.info(
                            f"微调滑动距离: {distance} -> {adjusted_distance}"
                        )

                        success = await perform_enhanced_slide(
                            driver, slider, adjusted_distance
                        )
                        if success:
                            await asyncio.sleep(random.uniform(2, 4))
                            if not has_slider_captcha(driver):
                                logger.info("微调后滑块验证码解决成功")
                                return True
            else:
                logger.warning(
                    f"滑动操作失败 (尝试 {attempt + 1}/{max_attempts})"
                )

            # 如果失败，等待一段时间再重试
            time.sleep(random.uniform(3, 6))

        except Exception as e:
            logger.log_result(
                "滑块验证码",
                f"处理异常: {str(e)} (尝试 {attempt + 1}/{max_attempts})",
            )
            time.sleep(random.uniform(2, 4))
            continue

    logger.log_result("滑块验证码", f"所有尝试失败，共尝试 {max_attempts} 次")
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
        "//div[contains(@class, 'click-captcha')]",
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
        "//div[contains(@class, 'captcha-slider')]",
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
        "//div[contains(@class, 'captcha-track')]",
    ]

    for selector in track_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            continue

    return None


def calculate_slider_distance(
    driver: WebDriver, slider: object, track: object
) -> int:
    """
    计算滑块需要滑动的距离 - 增强版本

    Args:
        driver: Selenium WebDriver对象
        slider: 滑块元素
        track: 滑块轨道元素

    Returns:
        滑动距离（像素）
    """
    try:
        # 获取轨道和滑块的尺寸
        track_width = track.size["width"]
        track_height = track.size["height"]
        slider_width = slider.size["width"]
        slider_height = slider.size["height"]

        logger.info(
            f"滑块尺寸计算 - 轨道: {track_width}x{track_height}, 滑块: {slider_width}x{slider_height}"
        )

        # 方法1: 基于轨道宽度计算
        distance_method1 = track_width - slider_width

        # 方法2: 基于滑块当前位置计算
        slider_x = slider.location["x"]
        track_x = track.location["x"]
        distance_method2 = (track_x + track_width) - (slider_x + slider_width)

        # 方法3: 基于常见的滑块验证码模式
        # 大多数滑块验证码需要滑动到轨道的80-95%位置
        distance_method3 = int(track_width * random.uniform(0.8, 0.95))

        # 选择最合理的距离
        distances = [distance_method1, distance_method2, distance_method3]
        valid_distances = [d for d in distances if d > 0]

        if valid_distances:
            # 选择中等距离，避免过大或过小
            distance = sorted(valid_distances)[len(valid_distances) // 2]
        else:
            # 如果所有方法都失败，使用默认值
            distance = 200

        # 添加一些随机性，模拟人类行为
        random_offset = random.randint(-8, 8)
        distance += random_offset

        # 确保距离在合理范围内
        distance = max(50, min(distance, track_width - 20))

        logger.info(
            f"滑块距离计算 - 方法1: {distance_method1}, 方法2: {distance_method2}, 方法3: {distance_method3}, 最终: {distance}"
        )

        return distance

    except Exception as e:
        logger.warning(f"滑块距离计算失败: {e}")
        # 如果计算失败，返回默认距离
        return 200


def calculate_enhanced_slider_distance(
    driver: WebDriver, slider: object, track: object
) -> int:
    """
    计算滑块需要滑动的距离 - 增强版本

    Args:
        driver: Selenium WebDriver对象
        slider: 滑块元素
        track: 滑块轨道元素

    Returns:
        滑动距离（像素）
    """
    try:
        # 获取轨道和滑块的详细信息
        track_rect = driver.execute_script(
            "return arguments[0].getBoundingClientRect();", track
        )
        slider_rect = driver.execute_script(
            "return arguments[0].getBoundingClientRect();", slider
        )

        # 计算轨道宽度
        track_width = track_rect["width"]

        # 计算滑块宽度
        slider_width = slider_rect["width"]

        # 计算需要滑动的距离
        distance = track_width - slider_width

        # 添加一些随机性，模拟人类操作的不精确性
        random_offset = random.randint(-3, 3)
        distance += random_offset

        # 确保距离不为负数
        distance = max(0, distance)

        # 如果距离太小，使用默认值
        if distance < 50:
            distance = random.randint(200, 300)

        return int(distance)

    except Exception as e:
        logger.log_result("滑块距离计算", f"计算失败: {str(e)}")
        # 如果计算失败，返回随机距离
        return random.randint(200, 300)


async def perform_slide(
    driver: WebDriver, slider: object, distance: int
) -> bool:
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


async def perform_enhanced_slide(
    driver: WebDriver, slider: object, distance: int
) -> bool:
    """
    执行滑动操作 - 增强版本，更接近人类行为

    Args:
        driver: Selenium WebDriver对象
        slider: 滑块元素
        distance: 滑动距离

    Returns:
        是否滑动成功
    """
    try:
        # 先移动到滑块附近，模拟鼠标移动
        actions = ActionChains(driver)

        # 获取滑块位置
        slider_location = slider.location
        slider_size = slider.size

        # 计算滑块中心点
        center_x = slider_location["x"] + slider_size["width"] // 2
        center_y = slider_location["y"] + slider_size["height"] // 2

        # 先移动到滑块附近（模拟鼠标移动）
        actions.move_by_offset(center_x - 50, center_y)
        actions.perform()
        time.sleep(random.uniform(0.1, 0.3))

        # 重新创建ActionChains
        actions = ActionChains(driver)

        # 移动到滑块并点击
        actions.move_to_element(slider)
        time.sleep(random.uniform(0.1, 0.2))
        actions.click_and_hold(slider)
        actions.perform()

        # 等待一下，模拟人类反应时间
        time.sleep(random.uniform(0.2, 0.5))

        # 重新创建ActionChains进行滑动
        actions = ActionChains(driver)
        actions.move_to_element(slider)
        actions.click_and_hold(slider)

        # 模拟人类滑动轨迹 - 使用贝塞尔曲线
        steps = random.randint(15, 25)
        current_distance = 0

        for i in range(steps):
            # 计算当前步骤应该移动的距离
            progress = (i + 1) / steps

            # 使用缓动函数模拟人类滑动（开始慢，中间快，结束慢）
            if progress < 0.3:
                # 开始阶段：慢
                ease_factor = 0.3
            elif progress < 0.7:
                # 中间阶段：快
                ease_factor = 1.0
            else:
                # 结束阶段：慢
                ease_factor = 0.3

            # 计算这一步应该移动的距离
            step_distance = (distance * ease_factor) / steps

            # 添加随机性
            step_distance += random.uniform(-2, 2)

            # 添加垂直方向的微小抖动
            offset_y = random.uniform(-1, 1)

            actions.move_by_offset(step_distance, offset_y)
            current_distance += step_distance

            # 随机延迟，模拟人类操作的不规律性
            delay = random.uniform(0.01, 0.08)
            time.sleep(delay)

        # 最后微调，确保到达目标位置
        remaining_distance = distance - current_distance
        if abs(remaining_distance) > 5:
            actions.move_by_offset(remaining_distance, 0)

        # 释放滑块
        actions.release()
        actions.perform()

        # 等待一下，模拟人类释放后的停顿
        time.sleep(random.uniform(0.1, 0.3))

        return True

    except Exception as e:
        logger.log_result("滑块滑动", f"滑动操作失败: {str(e)}")
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
        "//div[contains(@class, 'geetest_canvas')]",
    ]

    for selector in puzzle_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return element
        except NoSuchElementException:
            continue

    return None


def get_puzzle_position(
    driver: WebDriver, puzzle_element: object
) -> Optional[Tuple[int, int]]:
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
        center_x = location["x"] + size["width"] // 2
        center_y = location["y"] + size["height"] // 2

        # 添加一些随机性
        center_x += random.randint(-10, 10)
        center_y += random.randint(-10, 10)

        return (center_x, center_y)

    except Exception:
        return None


async def perform_puzzle_click(
    driver: WebDriver, position: Tuple[int, int]
) -> bool:
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
    # 检查DataDome验证码
    if has_datadome_captcha(driver):
        return True

    # 检查滑块验证码
    if has_slider_captcha(driver):
        return True

    # 检查拼图验证码
    if is_puzzle_captcha(driver):
        return True

    return False


def has_datadome_captcha(driver: WebDriver) -> bool:
    """
    检测是否有DataDome验证码

    Args:
        driver: Selenium WebDriver对象

    Returns:
        是否存在DataDome验证码
    """
    datadome_selectors = [
        "//iframe[contains(@src, 'captcha-delivery.com')]",
        "//iframe[contains(@src, 'datadome')]",
        "//script[contains(@src, 'captcha-delivery.com')]",
        "//div[contains(@class, 'captcha')]",
        "//div[contains(@id, 'captcha')]",
        "//iframe[contains(@title, 'CAPTCHA')]",
    ]

    for selector in datadome_selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                return True
        except NoSuchElementException:
            continue

    # 检查页面HTML中是否包含DataDome相关关键词
    page_source = driver.page_source.lower()
    datadome_keywords = [
        "captcha-delivery.com",
        "datadome",
        "captcha",
        "verification",
        "robot check",
    ]

    for keyword in datadome_keywords:
        if keyword in page_source:
            return True

    return False


async def solve_captcha(driver: WebDriver, max_attempts: int) -> bool:
    """
    自动解决验证码 - 专注于滑动验证码

    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决验证码
    """
    logger.info("验证码处理 - 开始处理验证码，专注于滑动验证码")

    # 优先处理滑块验证码
    if has_slider_captcha(driver):
        logger.info("验证码处理 - 检测到滑块验证码")
        # 保存HTML用于调试
        save_captcha_html(driver, "slider")
        return await solve_slider_captcha(driver, max_attempts)

    # 然后尝试拼图验证码
    if is_puzzle_captcha(driver):
        logger.info("验证码处理 - 检测到拼图验证码")
        # 保存HTML用于调试
        save_captcha_html(driver, "puzzle")
        return await solve_puzzle_captcha(driver, max_attempts)

    # 处理DataDome验证码
    if has_datadome_captcha(driver):
        logger.info("验证码处理 - 检测到DataDome验证码，尝试处理")
        # 保存HTML用于调试分析
        save_captcha_html(driver, "datadome")
        # 尝试处理DataDome滑块验证码
        return await solve_datadome_slider_captcha(driver, max_attempts)

    logger.info("验证码处理 - 未检测到验证码")
    return False


async def solve_datadome_slider_captcha(
    driver: WebDriver, max_attempts: int
) -> bool:
    """
    解决DataDome滑块验证码 - 专门处理滑块拼图类型

    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决验证码
    """
    logger.info("DataDome滑块验证码 - 开始处理滑块拼图验证码")

    for attempt in range(max_attempts):
        try:
            # 等待iframe加载完成
            await asyncio.sleep(random.uniform(2, 4))

            # 切换到DataDome iframe
            iframe = None
            try:
                iframe = driver.find_element(
                    By.XPATH,
                    "//iframe[contains(@src, 'captcha-delivery.com')]",
                )
                driver.switch_to.frame(iframe)
                logger.info("DataDome滑块验证码 - 已切换到验证码iframe")
            except Exception as e:
                logger.warning(f"DataDome滑块验证码 - 无法切换到iframe: {e}")
                driver.switch_to.default_content()
                continue

            # 在iframe内查找滑块元素
            slider_element = find_datadome_slider(driver)
            if slider_element:
                logger.info("DataDome滑块验证码 - 找到滑块元素，开始拖动")

                # 执行滑块拖动
                success = await perform_datadome_slider_drag(
                    driver, slider_element
                )

                # 切换回主页面
                driver.switch_to.default_content()

                if success:
                    # 等待验证结果
                    await asyncio.sleep(random.uniform(3, 5))

                    # 检查验证码是否消失
                    if not has_datadome_captcha(driver):
                        logger.info(
                            f"DataDome滑块验证码 - 验证成功 (尝试 {attempt + 1})"
                        )
                        return True
                    else:
                        logger.warning(
                            f"DataDome滑块验证码 - 验证失败，继续尝试 (尝试 {attempt + 1})"
                        )
                else:
                    logger.warning(
                        f"DataDome滑块验证码 - 滑块拖动失败 (尝试 {attempt + 1})"
                    )
            else:
                logger.warning("DataDome滑块验证码 - 未找到滑块元素")
                driver.switch_to.default_content()

            # 如果不是最后一次尝试，等待后重试
            if attempt < max_attempts - 1:
                await asyncio.sleep(random.uniform(2, 4))

        except Exception as e:
            logger.error(f"DataDome滑块验证码 - 处理过程中出错: {e}")
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

    logger.warning("DataDome滑块验证码 - 所有尝试均失败")
    return False


def find_datadome_slider(driver: WebDriver) -> Optional[object]:
    """
    在DataDome iframe中查找滑块元素

    Args:
        driver: Selenium WebDriver对象

    Returns:
        滑块元素，如果未找到则返回None
    """
    slider_selectors = [
        # DataDome滑块验证码常见选择器
        "//div[contains(@class, 'slider')]",
        "//div[contains(@class, 'slider-button')]",
        "//div[contains(@class, 'slider-handle')]",
        "//div[contains(@class, 'captcha-slider')]",
        "//div[contains(@class, 'puzzle-slider')]",
        "//div[contains(@class, 'drag-handle')]",
        "//span[contains(@class, 'slider')]",
        "//button[contains(@class, 'slider')]",
        # 通过文本内容检测
        "//div[contains(text(), '拖动')]",
        "//div[contains(text(), '滑动')]",
        "//div[contains(text(), 'slide')]",
        "//div[contains(text(), 'drag')]",
        # 通过属性检测
        "//*[@draggable='true']",
        "//*[contains(@style, 'cursor: grab')]",
        "//*[contains(@style, 'cursor: pointer')]",
    ]

    for selector in slider_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if (
                    element.is_displayed()
                    and element.size["width"] > 0
                    and element.size["height"] > 0
                ):
                    logger.info(
                        f"DataDome滑块验证码 - 找到滑块元素: {selector}"
                    )
                    return element
        except Exception as e:
            logger.debug(
                f"DataDome滑块验证码 - 选择器 {selector} 检测失败: {e}"
            )
            continue

    return None


async def perform_datadome_slider_drag(
    driver: WebDriver, slider_element: object
) -> bool:
    """
    执行DataDome滑块拖动操作

    Args:
        driver: Selenium WebDriver对象
        slider_element: 滑块元素

    Returns:
        是否拖动成功
    """
    try:
        # 计算拖动距离（通常是轨道宽度减去滑块宽度）
        # 对于拼图验证码，通常需要拖动到特定位置
        drag_distance = random.randint(200, 400)  # 根据实际情况调整

        logger.info(f"DataDome滑块验证码 - 开始拖动，距离: {drag_distance}px")

        # 创建动作链
        actions = ActionChains(driver)

        # 移动到滑块中心
        actions.move_to_element(slider_element)
        actions.pause(random.uniform(0.5, 1.0))

        # 按下鼠标
        actions.click_and_hold(slider_element)
        actions.pause(random.uniform(0.2, 0.5))

        # 模拟人类拖动轨迹
        steps = random.randint(8, 15)
        for i in range(steps):
            # 计算当前步骤的偏移
            progress = (i + 1) / steps
            current_distance = drag_distance * progress

            # 添加随机抖动，模拟人类不完美的拖动
            jitter_x = random.randint(-3, 3)
            jitter_y = random.randint(-2, 2)

            actions.move_by_offset(
                current_distance - (drag_distance * (i / steps)) + jitter_x,
                jitter_y,
            )
            actions.pause(random.uniform(0.05, 0.15))

        # 释放鼠标
        actions.release()
        actions.perform()

        logger.info("DataDome滑块验证码 - 滑块拖动完成")
        return True

    except Exception as e:
        logger.error(f"DataDome滑块验证码 - 拖动操作失败: {e}")
        return False


async def solve_datadome_captcha(driver: WebDriver, max_attempts: int) -> bool:
    """
    解决DataDome验证码 - 增强版本，模拟人类行为

    Args:
        driver: Selenium WebDriver对象
        max_attempts: 最大尝试次数

    Returns:
        是否成功解决验证码
    """
    logger.log_result(
        "DataDome验证码", "检测到DataDome验证码，开始模拟人类行为"
    )

    # 保存HTML用于调试分析
    save_captcha_html(driver, "datadome")

    for attempt in range(max_attempts):
        try:
            # 模拟人类浏览行为
            await simulate_human_browsing_behavior(driver)

            # 等待验证码自动解决（DataDome通常会自动解决）
            await asyncio.sleep(random.uniform(8, 15))

            # 检查验证码是否已消失
            if not has_datadome_captcha(driver):
                logger.log_result(
                    "DataDome验证码",
                    f"验证码自动解决成功 (尝试 {attempt + 1})",
                )
                return True

            # 尝试刷新页面并模拟人类行为
            if attempt < max_attempts - 1:
                logger.log_result(
                    "DataDome验证码",
                    f"验证码未解决，刷新页面并模拟人类行为 (尝试 {attempt + 1})",
                )
                await simulate_page_refresh_behavior(driver)

        except Exception as e:
            logger.log_result("DataDome验证码", f"解决验证码时出错: {e}")

    logger.log_result("DataDome验证码", "验证码解决失败")
    return False


async def simulate_human_browsing_behavior(driver: WebDriver) -> None:
    """
    模拟人类浏览行为，提高通过DataDome检测的概率

    Args:
        driver: Selenium WebDriver对象
    """
    try:
        # 1. 模拟鼠标移动
        await simulate_mouse_movement(driver)

        # 2. 模拟页面滚动
        await simulate_page_scrolling(driver)

        # 3. 模拟键盘活动
        await simulate_keyboard_activity(driver)

        # 4. 模拟点击行为
        await simulate_click_behavior(driver)

    except Exception as e:
        logger.log_result("人类行为模拟", f"模拟行为时出错: {e}")


async def simulate_mouse_movement(driver: WebDriver) -> None:
    """模拟鼠标移动"""
    try:
        actions = ActionChains(driver)

        # 获取页面尺寸
        window_size = driver.get_window_size()
        width = window_size["width"]
        height = window_size["height"]

        # 模拟自然的鼠标移动轨迹
        for _ in range(random.randint(3, 6)):
            # 随机移动鼠标
            x_offset = random.randint(-width // 4, width // 4)
            y_offset = random.randint(-height // 4, height // 4)

            actions.move_by_offset(x_offset, y_offset)
            actions.perform()

            # 随机延迟
            await asyncio.sleep(random.uniform(0.1, 0.3))

    except Exception as e:
        logger.log_result("鼠标移动模拟", f"鼠标移动模拟失败: {e}")


async def simulate_page_scrolling(driver: WebDriver) -> None:
    """模拟页面滚动"""
    try:
        # 获取页面高度
        page_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        # 模拟滚动行为
        scroll_steps = random.randint(2, 4)
        for i in range(scroll_steps):
            # 计算滚动位置
            scroll_position = (page_height * (i + 1)) // scroll_steps

            # 平滑滚动
            driver.execute_script(
                f"window.scrollTo({{top: {scroll_position}, behavior: 'smooth'}})"
            )

            # 随机延迟
            await asyncio.sleep(random.uniform(0.5, 1.5))

        # 滚动回顶部
        driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'})")
        await asyncio.sleep(random.uniform(0.5, 1.0))

    except Exception as e:
        logger.log_result("页面滚动模拟", f"页面滚动模拟失败: {e}")


async def simulate_keyboard_activity(driver: WebDriver) -> None:
    """模拟键盘活动"""
    try:
        actions = ActionChains(driver)

        # 模拟一些键盘操作
        keyboard_actions = [
            lambda: actions.key_down(Keys.CONTROL)
            .key_down("a")
            .key_up("a")
            .key_up(Keys.CONTROL),  # Ctrl+A
            lambda: actions.key_down(Keys.TAB),  # Tab键
            lambda: actions.key_down(Keys.ESCAPE),  # Escape键
        ]

        # 随机执行一些键盘操作
        for _ in range(random.randint(1, 3)):
            action = random.choice(keyboard_actions)
            action()
            actions.perform()
            await asyncio.sleep(random.uniform(0.1, 0.3))

    except Exception as e:
        logger.log_result("键盘活动模拟", f"键盘活动模拟失败: {e}")


async def simulate_click_behavior(driver: WebDriver) -> None:
    """模拟点击行为"""
    try:
        # 尝试找到一些可点击的元素
        clickable_elements = driver.find_elements(By.TAG_NAME, "button")
        clickable_elements.extend(driver.find_elements(By.TAG_NAME, "a"))
        clickable_elements.extend(
            driver.find_elements(By.CSS_SELECTOR, "[onclick]")
        )

        if clickable_elements:
            # 随机选择一个元素进行悬停（不实际点击）
            element = random.choice(clickable_elements)
            actions = ActionChains(driver)
            actions.move_to_element(element)
            actions.perform()
            await asyncio.sleep(random.uniform(0.2, 0.5))

    except Exception as e:
        logger.log_result("点击行为模拟", f"点击行为模拟失败: {e}")


async def simulate_page_refresh_behavior(driver: WebDriver) -> None:
    """模拟人类刷新页面的行为"""
    try:
        # 1. 先模拟一些浏览行为
        await simulate_human_browsing_behavior(driver)

        # 2. 等待一段时间
        await asyncio.sleep(random.uniform(2, 4))

        # 3. 刷新页面
        driver.refresh()

        # 4. 等待页面加载
        await asyncio.sleep(random.uniform(3, 6))

        # 5. 再次模拟浏览行为
        await simulate_human_browsing_behavior(driver)

    except Exception as e:
        logger.log_result("页面刷新模拟", f"页面刷新模拟失败: {e}")


def wait_for_captcha_to_disappear(
    driver: WebDriver, timeout: int = 10
) -> bool:
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
        wait.until_not(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'captcha')]")
            )
        )
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
            "//div[contains(@class, 'skip')]",
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


def handle_captcha_blocked(driver: WebDriver, reason: str = "unknown") -> str:
    """
    处理验证码封控情况，保存HTML用于分析

    Args:
        driver: Selenium WebDriver对象
        reason: 封控原因

    Returns:
        保存的HTML文件路径
    """
    logger.warning(f"检测到验证码封控，原因: {reason}")

    # 保存HTML用于调试分析
    filepath = save_captcha_html(driver, f"blocked_{reason}")

    if filepath:
        logger.info(f"验证码封控HTML已保存到: {filepath}")
        logger.info("建议检查保存的HTML文件，分析封控原因和绕过方法")

    return filepath


def save_page_screenshot(
    driver: WebDriver, captcha_type: str = "unknown"
) -> str:
    """
    保存验证码页面的截图到tmp目录

    Args:
        driver: Selenium WebDriver对象
        captcha_type: 验证码类型

    Returns:
        保存的文件路径
    """
    try:
        # 确保tmp目录存在
        tmp_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "tmp"
        )
        os.makedirs(tmp_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captcha_{captcha_type}_{timestamp}.png"
        filepath = os.path.join(tmp_dir, filename)

        # 保存截图
        driver.save_screenshot(filepath)

        logger.info(f"验证码截图已保存到: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"保存验证码截图失败: {e}")
        return ""
