import random
import shutil
import string
import time
import asyncio
from typing import Optional, List, Set, Any
from contextlib import asynccontextmanager

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from app.utils.logger import logger
from app.utils.path_util import get_project_root


class BrowserUtils:
    """Chrome浏览器自动化工具类 - 优化版本"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
        ]
        
        from app.utils.path_util import get_chrome_profiles_dir, get_dead_links_file
        
        self.profile_root = get_chrome_profiles_dir()
        self.dead_links_file = get_dead_links_file()
        self._ensure_directories()
        
        # 封禁检测关键词
        self.block_keywords = [
            "cf-captcha-container",
            "captcha-bypass", 
            "captcha-delivery.com",
            "please enable js",
            "cloudflare verification",
            "checking your browser",
            "/cdn-cgi/challenge-platform",
            "/cdn-cgi/l/chk_jschl",
            "access denied",
            "looks like that one got away",
            "see similar vehicles",
            "vehicle no longer available"
        ]
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.profile_root.mkdir(parents=True, exist_ok=True)
        self.dead_links_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化死链文件
        if not self.dead_links_file.exists():
            self._write_dead_links([])
    
    def _write_dead_links(self, dead_links: List[str]):
        """写入死链列表"""
        try:
            import json
            with open(self.dead_links_file, 'w', encoding='utf-8') as f:
                json.dump(dead_links, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.log_result("写入死链文件失败", f"错误: {str(e)}")
    
    def _read_dead_links(self) -> Set[str]:
        """读取死链列表"""
        try:
            import json
            if self.dead_links_file.exists():
                with open(self.dead_links_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            return set()
        except Exception as e:
            logger.log_result("读取死链文件失败", f"错误: {str(e)}")
            return set()
    
    def generate_daily_profile_name(self, prefix: str = "user") -> str:
        """生成带有日期和随机后缀的profile名"""
        date_str = time.strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{prefix}_{date_str}_{random_suffix}"
    
    def _ensure_profile_exists(self, profile_name: str) -> str:
        """创建profile目录"""
        profile_path = self.profile_root / profile_name
        profile_path.mkdir(parents=True, exist_ok=True)
        return str(profile_path)
    
    def _delete_profile(self, profile_name: str):
        """删除profile目录"""
        try:
            profile_path = self.profile_root / profile_name
            if profile_path.exists():
                shutil.rmtree(profile_path)
                logger.log_result("删除profile", f"已删除: {profile_name}")
        except Exception as e:
            logger.log_result("删除profile失败", f"错误: {str(e)}")
    
    def _create_chrome_options(self, profile_name: str) -> uc.ChromeOptions:
        """创建Chrome选项"""
        options = uc.ChromeOptions()
        
        # 基础设置
        profile_dir = self._ensure_profile_exists(profile_name)
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument(f"--user-agent={random.choice(self.user_agents)}")
        
        # 反检测设置
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1080,720")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        
        # 性能优化
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        
        return options
    
    def _inject_stealth_scripts(self, driver: webdriver.Chrome):
        """注入反检测JavaScript"""
        stealth_scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
            "Object.defineProperty(navigator, 'chrome', {get: () => ({ runtime: {} })})",
            "delete navigator.__proto__.webdriver",
            "window.chrome = { runtime: {} }"
        ]
        
        try:
            for script in stealth_scripts:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": script
                })
            logger.log_result("反检测脚本注入", "成功注入JavaScript反检测代码")
        except Exception as e:
            logger.log_result("反检测脚本注入失败", f"错误: {str(e)}")
    
    def create_undetected_driver(self, profile_name: str) -> webdriver.Chrome:
        """创建undetected Chrome驱动"""
        try:
            options = self._create_chrome_options(profile_name)
            
            # 使用webdriver-manager自动管理ChromeDriver版本
            service = Service(ChromeDriverManager().install())
            
            # 动态检测Chrome版本，使用更兼容的配置
            driver = uc.Chrome(
                options=options,
                service=service,
                headless=False,
                use_subprocess=False,  # 改为False避免创建额外进程
                version_main=140,  # 明确指定Chrome 140版本
            )
            
            # 注入反检测脚本
            self._inject_stealth_scripts(driver)
            
            # 设置超时
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            logger.log_result("Chrome驱动创建", f"成功创建profile: {profile_name}")
            return driver
            
        except Exception as e:
            logger.log_result("Chrome驱动创建失败", f"错误: {str(e)}")
            raise
    
    def create_standard_driver(self, profile_name: Optional[str] = None) -> webdriver.Chrome:
        """创建标准Chrome驱动（备用方案）"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if profile_name:
            user_data_dir = self.profile_root / profile_name
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # 使用webdriver-manager自动管理ChromeDriver版本
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def is_blocked_page(self, page_html: str) -> bool:
        """检测页面是否被封禁"""
        page_lower = page_html.lower()
        return any(keyword in page_lower for keyword in self.block_keywords)
    
    def is_vehicle_available(self, page_html: str) -> bool:
        """检测车辆是否可用"""
        unavailable_keywords = [
            "looks like that one got away",
            "see similar vehicles", 
            "vehicle no longer available",
            "this listing is no longer available"
        ]
        
        page_lower = page_html.lower()
        return not any(keyword in page_lower for keyword in unavailable_keywords)
    
    def has_slider_captcha(self, driver) -> bool:
        """检测是否有滑块验证码"""
        try:
            # 常见的滑块验证码选择器
            slider_selectors = [
                "//div[contains(@class, 'slider')]",
                "//div[contains(@class, 'captcha')]",
                "//div[contains(@class, 'verification')]",
                "//div[contains(@class, 'puzzle')]",
                "//canvas[contains(@class, 'slider')]",
                "//div[contains(@id, 'slider')]",
                "//div[contains(@id, 'captcha')]",
                "//div[contains(text(), 'slide')]",
                "//div[contains(text(), 'verify')]",
                "//div[contains(text(), 'captcha')]"
            ]
            
            for selector in slider_selectors:
                try:
                    element = driver.find_element("xpath", selector)
                    if element.is_displayed():
                        logger.log_result("滑块检测", f"发现滑块验证码: {selector}")
                        return True
                except Exception:
                    continue
            
            # 检查页面源码中的滑块相关关键词
            page_source = driver.page_source.lower()
            slider_keywords = [
                "slider", "captcha", "verification", "puzzle", 
                "drag", "slide to verify", "complete the puzzle"
            ]
            
            for keyword in slider_keywords:
                if keyword in page_source:
                    logger.log_result("滑块检测", f"页面包含滑块关键词: {keyword}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.log_result("滑块检测", f"检测滑块时出错: {e}")
            return False
    
    async def solve_slider_captcha(self, driver, max_attempts: int = 3) -> bool:
        """自动解决滑块验证码"""
        try:
            logger.log_result("滑块处理", "开始处理滑块验证码")
            
            # 检查是否是拼图验证码
            is_puzzle = self._is_puzzle_captcha(driver)
            logger.log_result("滑块处理", f"拼图检测结果: {is_puzzle}")
            
            if is_puzzle:
                logger.log_result("滑块处理", "检测到拼图验证码，使用拼图处理逻辑")
                return await self._solve_puzzle_captcha(driver, max_attempts)
            
            # 普通滑块验证码处理
            for attempt in range(max_attempts):
                logger.log_result("滑块处理", f"尝试 {attempt + 1}/{max_attempts}")
                
                # 查找滑块元素
                slider = self._find_slider_element(driver)
                if not slider:
                    logger.log_result("滑块处理", "未找到滑块元素")
                    return False
                
                # 查找滑块轨道
                track = self._find_slider_track(driver)
                if not track:
                    logger.log_result("滑块处理", "未找到滑块轨道")
                    return False
                
                # 计算需要滑动的距离
                slide_distance = self._calculate_slider_distance(driver, slider, track)
                if slide_distance <= 0:
                    logger.log_result("滑块处理", "无法计算滑动距离")
                    return False
                
                # 执行滑动操作
                success = self._perform_slide(driver, slider, slide_distance)
                if success:
                    logger.log_result("滑块处理", "滑块验证成功")
                    await asyncio.sleep(2)  # 等待验证结果
                    return True
                
                # 等待后重试
                await asyncio.sleep(1)
            
            logger.log_result("滑块处理", "滑块验证失败，已达到最大尝试次数")
            return False
            
        except Exception as e:
            logger.log_result("滑块处理", f"处理滑块时出错: {e}")
            return False
    
    def _is_puzzle_captcha(self, driver) -> bool:
        """检测是否是拼图验证码"""
        try:
            puzzle_indicators = [
                "//div[@id='captcha__puzzle']",
                "//div[contains(@class, 'puzzle')]",
                "//canvas[contains(@class, 'block')]",
                "//div[contains(@class, 'sliderText')]",
                "//p[contains(text(), '拖动滑块完成拼图')]"
            ]
            
            for indicator in puzzle_indicators:
                try:
                    element = driver.find_element("xpath", indicator)
                    if element.is_displayed():
                        logger.log_result("拼图检测", f"检测到拼图验证码指示器: {indicator}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.log_result("拼图检测", f"检测拼图验证码时出错: {e}")
            return False
    
    async def _solve_puzzle_captcha(self, driver, max_attempts: int = 3) -> bool:
        """处理拼图验证码"""
        try:
            logger.log_result("拼图处理", "开始处理拼图验证码")
            
            for attempt in range(max_attempts):
                logger.log_result("拼图处理", f"尝试 {attempt + 1}/{max_attempts}")
                
                # 查找滑块元素
                slider = self._find_slider_element(driver)
                if not slider:
                    logger.log_result("拼图处理", "未找到滑块元素")
                    return False
                
                # 查找滑块容器
                container = self._find_slider_track(driver)
                if not container:
                    logger.log_result("拼图处理", "未找到滑块容器")
                    return False
                
                # 计算拼图滑动距离
                slide_distance = self._calculate_puzzle_distance(driver, slider, container)
                if slide_distance <= 0:
                    logger.log_result("拼图处理", "无法计算拼图滑动距离")
                    return False
                
                # 执行拼图滑动操作
                success = self._perform_puzzle_slide(driver, slider, slide_distance)
                if success:
                    logger.log_result("拼图处理", "拼图验证成功")
                    await asyncio.sleep(3)  # 等待验证结果
                    return True
                
                # 等待后重试
                await asyncio.sleep(2)
            
            logger.log_result("拼图处理", "拼图验证失败，已达到最大尝试次数")
            return False
            
        except Exception as e:
            logger.log_result("拼图处理", f"处理拼图验证码时出错: {e}")
            return False
    
    def _calculate_puzzle_distance(self, driver, slider, container) -> int:
        """计算拼图滑动距离"""
        try:
            # 获取容器宽度
            container_width = container.size['width']
            
            # 对于拼图验证码，通常需要滑动到容器的右侧
            # 减去滑块本身的宽度
            slider_width = slider.size['width']
            slide_distance = container_width - slider_width - 10  # 留10px边距
            
            logger.log_result("拼图距离", f"容器宽度: {container_width}, 滑块宽度: {slider_width}, 滑动距离: {slide_distance}")
            return max(0, slide_distance)
            
        except Exception as e:
            logger.log_result("拼图距离", f"计算拼图滑动距离时出错: {e}")
            return 0
    
    async def _perform_puzzle_slide(self, driver, slider, distance: int) -> bool:
        """执行拼图滑动操作"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 移动到滑块位置
            ActionChains(driver).move_to_element(slider).perform()
            await asyncio.sleep(0.5)
            
            # 按下鼠标
            ActionChains(driver).click_and_hold(slider).perform()
            await asyncio.sleep(0.3)
            
            # 模拟更自然的拼图滑动轨迹
            steps = random.randint(30, 50)  # 更多步骤，更平滑
            step_distance = distance // steps
            
            for i in range(steps):
                # 添加随机抖动，模拟人类操作
                jitter = random.randint(-3, 3)
                move_distance = step_distance + jitter
                
                ActionChains(driver).move_by_offset(move_distance, 0).perform()
                await asyncio.sleep(random.uniform(0.02, 0.05))  # 稍慢一些
            
            # 释放鼠标
            ActionChains(driver).release().perform()
            await asyncio.sleep(0.5)
            
            logger.log_result("拼图滑动", f"拼图滑动完成，距离: {distance}")
            return True
            
        except Exception as e:
            logger.log_result("拼图滑动", f"执行拼图滑动时出错: {e}")
            return False
    
    def _find_slider_element(self, driver) -> Optional[Any]:
        """查找滑块元素"""
        slider_selectors = [
            # 基于实际HTML结构的选择器 - 从用户提供的HTML
            "//div[@class='sliderContainer']//div[@class='slider']",
            "//div[@class='slider']",
            "//div[contains(@class, 'slider')]",
            # 备用选择器
            "//div[contains(@class, 'slider-btn')]",
            "//div[contains(@class, 'slider-button')]",
            "//div[contains(@class, 'captcha-slider')]",
            "//div[contains(@class, 'verification-slider')]",
            "//div[contains(@class, 'puzzle-slider')]",
            "//span[contains(@class, 'slider')]",
            "//button[contains(@class, 'slider')]",
            "//div[@role='slider']",
            "//div[contains(@style, 'cursor: grab')]",
            "//div[contains(@style, 'cursor: pointer')]"
        ]
        
        # 添加调试信息
        logger.log_result("滑块查找", f"开始查找滑块元素，共 {len(slider_selectors)} 个选择器")
        
        for i, selector in enumerate(slider_selectors):
            try:
                element = driver.find_element("xpath", selector)
                logger.log_result("滑块查找", f"选择器 {i+1}: {selector} - 找到元素，显示: {element.is_displayed()}, 启用: {element.is_enabled()}")
                if element.is_displayed() and element.is_enabled():
                    logger.log_result("滑块查找", f"找到滑块元素: {selector}")
                    return element
            except Exception as e:
                logger.log_result("滑块查找", f"选择器 {i+1}: {selector} - 未找到: {str(e)[:50]}")
                continue
        
        logger.log_result("滑块查找", "所有选择器都未找到滑块元素")
        return None
    
    def _find_slider_track(self, driver) -> Optional[Any]:
        """查找滑块轨道"""
        track_selectors = [
            # 基于实际HTML结构的选择器
            "//div[@class='sliderContainer']",
            "//div[contains(@class, 'sliderContainer')]",
            "//div[@class='sliderbg']",
            "//div[contains(@class, 'sliderbg')]",
            # 备用选择器
            "//div[contains(@class, 'slider-track')]",
            "//div[contains(@class, 'slider-rail')]",
            "//div[contains(@class, 'captcha-track')]",
            "//div[contains(@class, 'verification-track')]",
            "//div[contains(@class, 'puzzle-track')]",
            "//div[contains(@class, 'slider-bg')]",
            "//div[contains(@class, 'slider-container')]"
        ]
        
        for selector in track_selectors:
            try:
                element = driver.find_element("xpath", selector)
                if element.is_displayed():
                    logger.log_result("轨道查找", f"找到滑块轨道: {selector}")
                    return element
            except:
                continue
        
        return None
    
    def _find_slider_target(self, driver) -> Optional[Any]:
        """查找滑块目标位置"""
        target_selectors = [
            # 基于实际HTML结构的选择器
            "//div[@class='sliderTarget']",
            "//div[contains(@class, 'sliderTarget')]",
            "//div[@class='sliderContainer']//div[@class='sliderTarget']",
            # 备用选择器
            "//div[contains(@class, 'target')]",
            "//div[contains(@class, 'goal')]",
            "//div[contains(@class, 'destination')]"
        ]
        
        for selector in target_selectors:
            try:
                element = driver.find_element("xpath", selector)
                if element.is_displayed():
                    logger.log_result("目标查找", f"找到滑块目标: {selector}")
                    return element
            except:
                continue
        
        return None
    
    def _calculate_slider_distance(self, driver, slider, track) -> int:
        """计算滑块需要滑动的距离"""
        try:
            # 首先尝试基于目标位置计算
            target = self._find_slider_target(driver)
            if target:
                # 基于目标位置计算距离
                slider_x = slider.location['x']
                target_x = target.location['x']
                slide_distance = target_x - slider_x
                
                logger.log_result("距离计算", f"基于目标位置计算: 滑块X={slider_x}, 目标X={target_x}, 距离={slide_distance}")
                return max(0, slide_distance)
            
            # 备用方案：基于轨道宽度计算
            track_width = track.size['width']
            slider_x = slider.location['x']
            track_x = track.location['x']
            
            # 计算需要滑动的距离（通常是轨道宽度的80-90%）
            slide_distance = int(track_width * 0.85) - (slider_x - track_x)
            
            logger.log_result("距离计算", f"基于轨道宽度计算: 轨道宽度={track_width}, 滑动距离={slide_distance}")
            return max(0, slide_distance)
            
        except Exception as e:
            logger.log_result("距离计算", f"计算滑动距离时出错: {e}")
            return 0
    
    async def _perform_slide(self, driver, slider, distance: int) -> bool:
        """执行滑动操作"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # 移动到滑块位置
            ActionChains(driver).move_to_element(slider).perform()
            await asyncio.sleep(0.5)
            
            # 按下鼠标
            ActionChains(driver).click_and_hold(slider).perform()
            await asyncio.sleep(0.2)
            
            # 模拟人类滑动轨迹
            steps = random.randint(20, 30)
            step_distance = distance // steps
            
            for i in range(steps):
                # 添加随机抖动
                jitter = random.randint(-2, 2)
                move_distance = step_distance + jitter
                
                ActionChains(driver).move_by_offset(move_distance, 0).perform()
                await asyncio.sleep(random.uniform(0.01, 0.03))
            
            # 释放鼠标
            ActionChains(driver).release().perform()
            await asyncio.sleep(0.5)
            
            logger.log_result("滑动执行", f"完成滑动，距离: {distance}")
            return True
            
        except Exception as e:
            logger.log_result("滑动执行", f"执行滑动时出错: {e}")
            return False
    
    @asynccontextmanager
    async def get_driver(self, profile_name: str, use_undetected: bool = False):
        """上下文管理器，自动管理driver生命周期（不自动关闭浏览器）"""
        driver = None
        try:
            if use_undetected:
                driver = self.create_undetected_driver(profile_name)
            else:
                driver = self.create_standard_driver(profile_name)
            
            yield driver
            
        except Exception as e:
            logger.log_result("Driver操作失败", f"错误: {str(e)}")
            raise
        finally:
            # 注释掉自动关闭浏览器的代码，让浏览器保持打开状态
            # if driver:
            #     try:
            #         driver.quit()
            #     except Exception as e:
            #         logger.log_result("Driver清理失败", f"错误: {str(e)}")
            pass
    
    async def check_url_alive(self, url: str, max_retries: int = 3) -> bool:
        """检查URL是否存活（异步版本）"""
        dead_links = self._read_dead_links()
        
        if url in dead_links:
            logger.log_result("跳过死链", f"URL已在死链列表中: {url}")
            return False
        
        for attempt in range(max_retries):
            profile_name = self.generate_daily_profile_name()
            
            try:
                logger.log_result("URL检查", f"尝试 {attempt+1}/{max_retries}, profile: {profile_name}")
                
                async with self.get_driver(profile_name) as driver:
                    # 随机延迟
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # 访问URL
                    driver.get(url)
                    await asyncio.sleep(3)
                    
                    # 检查页面状态
                    page_source = driver.page_source
                    
                    if self.is_blocked_page(page_source):
                        logger.log_result("检测到封禁", "页面被检测为封禁状态")
                        self._delete_profile(profile_name)
                        continue
                    
                    if not self.is_vehicle_available(page_source):
                        logger.log_result("车辆下架", "车辆已下架")
                        dead_links.add(url)
                        self._write_dead_links(list(dead_links))
                        return False
                    
                    logger.log_result("URL检查成功", "页面可正常访问")
                    return True
                    
            except (TimeoutException, WebDriverException) as e:
                logger.log_result("URL检查失败", f"网络错误: {str(e)}")
                self._delete_profile(profile_name)
                continue
            except Exception as e:
                logger.log_result("URL检查异常", f"未知错误: {str(e)}")
                self._delete_profile(profile_name)
                continue
        
        # 所有重试都失败，标记为死链
        dead_links.add(url)
        self._write_dead_links(list(dead_links))
        return False
    
    def check_url_alive_sync(self, url: str, max_retries: int = 3) -> bool:
        """检查URL是否存活（同步版本）"""
        try:
            # 检查是否已经在事件循环中
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在事件循环中，创建新任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.check_url_alive(url, max_retries))
                    return future.result()
            else:
                # 如果没有事件循环，直接运行
                return asyncio.run(self.check_url_alive(url, max_retries))
        except RuntimeError:
            # 如果没有事件循环，创建新的
            return asyncio.run(self.check_url_alive(url, max_retries))
    
    def cleanup_old_profiles(self, days_old: int = 7):
        """清理旧的profile目录"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            for profile_path in self.profile_root.iterdir():
                if profile_path.is_dir():
                    profile_time = profile_path.stat().st_ctime
                    if profile_time < cutoff_time:
                        shutil.rmtree(profile_path)
                        logger.log_result("清理旧profile", f"已删除: {profile_path.name}")
                        
        except Exception as e:
            logger.log_result("清理旧profile失败", f"错误: {str(e)}")


# 全局实例
browser_utils = BrowserUtils()


# 便捷函数
def check_url_alive(url: str, max_retries: int = 3) -> bool:
    """检查URL是否存活的便捷函数"""
    return browser_utils.check_url_alive_sync(url, max_retries)


def is_blocked_page(page_html: str) -> bool:
    """检测页面是否被封禁的便捷函数"""
    return browser_utils.is_blocked_page(page_html)


def cleanup_old_profiles(days_old: int = 7):
    """清理旧profile的便捷函数"""
    browser_utils.cleanup_old_profiles(days_old)


if __name__ == "__main__":
    # 测试代码
    test_url = "https://www.kijijiautos.ca/cars/honda/cr-v/2020/72430034/"
    
    logger.log_result("开始测试", "测试URL存活检查功能")
    
    # 测试URL检查
    is_alive = check_url_alive(test_url)
    logger.log_result("测试结果", f"URL是否存活: {is_alive}")
    
    # 测试profile清理
    cleanup_old_profiles(1)  # 清理1天前的profile
    
    logger.log_result("测试完成", "所有测试已完成")
