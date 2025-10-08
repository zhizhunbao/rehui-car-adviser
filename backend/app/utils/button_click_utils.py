"""
按钮点击工具类

这个模块提供了通用的按钮点击功能，包括：
1. 智能按钮查找和点击
2. 多种点击策略（直接点击、JavaScript点击、ActionChains点击）
3. 点击重试机制
4. 点击状态验证
5. 异常处理和日志记录
"""

from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from app.utils.selector_utils import CarGurusSelectors, SelectorType
from app.utils.behavior_simulator_utils import random_delay, simulate_click_with_delay
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ButtonClickStrategy:
    """按钮点击策略枚举"""
    DIRECT = "direct"           # 直接点击
    JAVASCRIPT = "javascript"   # JavaScript点击
    ACTION_CHAINS = "action_chains"  # ActionChains点击
    SCROLL_AND_CLICK = "scroll_and_click"  # 滚动后点击


class ButtonClickResult:
    """按钮点击结果"""
    def __init__(self, success: bool, element: Optional[WebElement] = None,
                 strategy_used: Optional[str] = None,
                 error: Optional[str] = None):
        self.success = success
        self.element = element
        self.strategy_used = strategy_used
        self.error = error


class ButtonClickUtils:
    """按钮点击工具类"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.max_retries = 3
        self.default_timeout = 10
    
    def click_button_by_selectors(self,
                                 selectors: List[str],
                                 button_text: Optional[str] = None,
                                 strategy: str = ButtonClickStrategy.DIRECT,
                                 timeout: int = None) -> ButtonClickResult:
        """
        根据选择器列表点击按钮 - 优化版本
        
        Args:
            selectors: 选择器列表
            button_text: 按钮文本（可选，用于进一步筛选）
            strategy: 点击策略
            timeout: 超时时间
            
        Returns:
            ButtonClickResult: 点击结果
        """
        timeout = timeout or self.default_timeout
        
        for attempt in range(self.max_retries):
            try:
                # 尝试每个选择器（按优先级排序）
                for i, selector in enumerate(selectors):
                    try:
                        # 查找元素
                        elements = self.driver.find_elements(By.XPATH, selector)
                        
                        if not elements:
                            # 记录选择器失败
                            CarGurusSelectors.update_selector_success(selector, False)
                            continue
                        
                        # 如果指定了按钮文本，进一步筛选
                        if button_text:
                            elements = [elem for elem in elements
                                        if button_text.lower() in elem.text.lower()]
                        
                        if not elements:
                            CarGurusSelectors.update_selector_success(selector, False)
                            continue
                        
                        # 选择第一个可见元素
                        element = self._get_first_visible_element(elements)
                        if not element:
                            CarGurusSelectors.update_selector_success(selector, False)
                            continue
                        
                        # 执行点击
                        result = self._execute_click(element, strategy)
                        if result.success:
                            # 记录选择器成功
                            CarGurusSelectors.update_selector_success(selector, True)
                            logger.log_result(f"成功点击按钮: {selector} (第{i+1}个选择器), 策略: {strategy}")
                            return result
                        else:
                            CarGurusSelectors.update_selector_success(selector, False)
                            
                    except Exception as e:
                        CarGurusSelectors.update_selector_success(selector, False)
                        logger.log_result(f"选择器 {selector} 点击失败: {str(e)}")
                        continue
                
                # 如果所有选择器都失败，等待后重试
                if attempt < self.max_retries - 1:
                    random_delay(1, 2)
                    
            except Exception as e:
                logger.log_result(f"点击按钮第 {attempt + 1} 次尝试失败: {str(e)}")
                if attempt < self.max_retries - 1:
                    random_delay(1, 2)
        
        return ButtonClickResult(
            success=False,
            error=f"所有 {len(selectors)} 个选择器都点击失败，已重试 {self.max_retries} 次"
        )
    
    def click_button_by_text(self, 
                           button_text: str, 
                           strategy: str = ButtonClickStrategy.DIRECT,
                           timeout: int = None) -> ButtonClickResult:
        """
        根据按钮文本点击按钮
        
        Args:
            button_text: 按钮文本
            strategy: 点击策略
            timeout: 超时时间
            
        Returns:
            ButtonClickResult: 点击结果
        """
        # 构建文本匹配选择器
        text_selectors = [
            f"//button[contains(text(), '{button_text}')]",
            f"//input[@type='button' and contains(@value, '{button_text}')]",
            f"//input[@type='submit' and contains(@value, '{button_text}')]",
            f"//a[contains(text(), '{button_text}')]",
            f"//*[contains(text(), '{button_text}') and (self::button or self::input or self::a)]"
        ]
        
        return self.click_button_by_selectors(text_selectors, strategy=strategy, timeout=timeout)
    
    def click_button_by_selector_type(self, 
                                    selector_type: SelectorType,
                                    button_text: Optional[str] = None,
                                    strategy: str = ButtonClickStrategy.DIRECT,
                                    timeout: int = None) -> ButtonClickResult:
        """
        根据选择器类型点击按钮
        
        Args:
            selector_type: 选择器类型
            button_text: 按钮文本（可选）
            strategy: 点击策略
            timeout: 超时时间
            
        Returns:
            ButtonClickResult: 点击结果
        """
        selectors = CarGurusSelectors.get_selector_by_type(selector_type)
        return self.click_button_by_selectors(selectors, button_text, strategy, timeout)
    
    def click_model_button(self, 
                          button_text: Optional[str] = None,
                          strategy: str = ButtonClickStrategy.DIRECT) -> ButtonClickResult:
        """
        点击车型选择按钮
        
        Args:
            button_text: 按钮文本（可选）
            strategy: 点击策略
            
        Returns:
            ButtonClickResult: 点击结果
        """
        return self.click_button_by_selector_type(
            SelectorType.MODEL_BUTTON, 
            button_text, 
            strategy
        )
    
    def click_show_all_models_button(self, 
                                   strategy: str = ButtonClickStrategy.DIRECT) -> ButtonClickResult:
        """
        点击"显示所有车型"按钮 - 使用优化选择器
        
        Args:
            strategy: 点击策略
            
        Returns:
            ButtonClickResult: 点击结果
        """
        # 使用优化的选择器列表
        selectors = CarGurusSelectors.get_optimized_selectors("show_all_models")
        return self.click_button_by_selectors(selectors, strategy=strategy)
    
    def _get_first_visible_element(self, elements: List[WebElement]) -> Optional[WebElement]:
        """
        获取第一个可见元素
        
        Args:
            elements: 元素列表
            
        Returns:
            第一个可见元素，如果没有则返回None
        """
        for element in elements:
            try:
                if element.is_displayed() and element.is_enabled():
                    return element
            except Exception:
                continue
        return None
    
    def _execute_click(self, element: WebElement, strategy: str) -> ButtonClickResult:
        """
        执行点击操作
        
        Args:
            element: 要点击的元素
            strategy: 点击策略
            
        Returns:
            ButtonClickResult: 点击结果
        """
        try:
            if strategy == ButtonClickStrategy.DIRECT:
                return self._direct_click(element)
            elif strategy == ButtonClickStrategy.JAVASCRIPT:
                return self._javascript_click(element)
            elif strategy == ButtonClickStrategy.ACTION_CHAINS:
                return self._action_chains_click(element)
            elif strategy == ButtonClickStrategy.SCROLL_AND_CLICK:
                return self._scroll_and_click(element)
            else:
                # 默认尝试直接点击
                return self._direct_click(element)
                
        except Exception as e:
            return ButtonClickResult(
                success=False, 
                element=element, 
                strategy_used=strategy,
                error=str(e)
            )
    
    def _direct_click(self, element: WebElement) -> ButtonClickResult:
        """直接点击"""
        try:
            # 滚动到元素可见
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            random_delay(0.5, 1.0)
            
            # 执行点击
            element.click()
            random_delay(0.2, 0.5)
            
            return ButtonClickResult(
                success=True, 
                element=element, 
                strategy_used=ButtonClickStrategy.DIRECT
            )
            
        except Exception as e:
            return ButtonClickResult(
                success=False, 
                element=element, 
                strategy_used=ButtonClickStrategy.DIRECT,
                error=str(e)
            )
    
    def _javascript_click(self, element: WebElement) -> ButtonClickResult:
        """JavaScript点击"""
        try:
            # 滚动到元素可见
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            random_delay(0.5, 1.0)
            
            # JavaScript点击
            self.driver.execute_script("arguments[0].click();", element)
            random_delay(0.2, 0.5)
            
            return ButtonClickResult(
                success=True, 
                element=element, 
                strategy_used=ButtonClickStrategy.JAVASCRIPT
            )
            
        except Exception as e:
            return ButtonClickResult(
                success=False, 
                element=element, 
                strategy_used=ButtonClickStrategy.JAVASCRIPT,
                error=str(e)
            )
    
    def _action_chains_click(self, element: WebElement) -> ButtonClickResult:
        """ActionChains点击"""
        try:
            # 滚动到元素可见
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            random_delay(0.5, 1.0)
            
            # ActionChains点击
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.click(element)
            actions.perform()
            random_delay(0.2, 0.5)
            
            return ButtonClickResult(
                success=True, 
                element=element, 
                strategy_used=ButtonClickStrategy.ACTION_CHAINS
            )
            
        except Exception as e:
            return ButtonClickResult(
                success=False, 
                element=element, 
                strategy_used=ButtonClickStrategy.ACTION_CHAINS,
                error=str(e)
            )
    
    def _scroll_and_click(self, element: WebElement) -> ButtonClickResult:
        """滚动后点击"""
        try:
            # 滚动到元素中心
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, element)
            random_delay(1.0, 2.0)
            
            # 使用模拟点击
            simulate_click_with_delay(self.driver, element, 0.5, 1.0)
            
            return ButtonClickResult(
                success=True, 
                element=element, 
                strategy_used=ButtonClickStrategy.SCROLL_AND_CLICK
            )
            
        except Exception as e:
            return ButtonClickResult(
                success=False, 
                element=element, 
                strategy_used=ButtonClickStrategy.SCROLL_AND_CLICK,
                error=str(e)
            )
    
    def smart_click_button(self, 
                          selectors: List[str], 
                          button_text: Optional[str] = None,
                          timeout: int = None) -> ButtonClickResult:
        """
        智能点击按钮 - 自动尝试多种策略
        
        Args:
            selectors: 选择器列表
            button_text: 按钮文本（可选）
            timeout: 超时时间
            
        Returns:
            ButtonClickResult: 点击结果
        """
        strategies = [
            ButtonClickStrategy.DIRECT,
            ButtonClickStrategy.SCROLL_AND_CLICK,
            ButtonClickStrategy.JAVASCRIPT,
            ButtonClickStrategy.ACTION_CHAINS
        ]
        
        for strategy in strategies:
            result = self.click_button_by_selectors(selectors, button_text, strategy, timeout)
            if result.success:
                logger.log_result(f"智能点击成功，使用策略: {strategy}")
                return result
            else:
                logger.log_result(f"策略 {strategy} 失败: {result.error}")
        
        return ButtonClickResult(
            success=False, 
            error="所有点击策略都失败了"
        )
    
    def fast_click_button(self, 
                         selectors: List[str], 
                         button_text: Optional[str] = None,
                         max_selectors: int = 3) -> ButtonClickResult:
        """
        快速点击按钮 - 只尝试前几个高优先级选择器
        
        Args:
            selectors: 选择器列表
            button_text: 按钮文本（可选）
            max_selectors: 最大尝试选择器数量
            
        Returns:
            ButtonClickResult: 点击结果
        """
        # 只使用前几个选择器
        limited_selectors = selectors[:max_selectors]
        
        for i, selector in enumerate(limited_selectors):
            try:
                # 查找元素
                elements = self.driver.find_elements(By.XPATH, selector)
                
                if not elements:
                    continue
                
                # 如果指定了按钮文本，进一步筛选
                if button_text:
                    elements = [elem for elem in elements
                                if button_text.lower() in elem.text.lower()]
                
                if not elements:
                    continue
                
                # 选择第一个可见元素
                element = self._get_first_visible_element(elements)
                if not element:
                    continue
                
                # 执行点击
                result = self._execute_click(element, ButtonClickStrategy.DIRECT)
                if result.success:
                    CarGurusSelectors.update_selector_success(selector, True)
                    logger.log_result(f"快速点击成功: {selector} (第{i+1}个选择器)")
                    return result
                else:
                    CarGurusSelectors.update_selector_success(selector, False)
                    
            except Exception as e:
                CarGurusSelectors.update_selector_success(selector, False)
                logger.log_result(f"快速点击失败: {selector} - {str(e)}")
                continue
        
        return ButtonClickResult(
            success=False,
            error=f"快速点击失败，尝试了前 {max_selectors} 个选择器"
        )


# 便捷函数
def click_button_by_selectors(driver: WebDriver, 
                            selectors: List[str], 
                            button_text: Optional[str] = None,
                            strategy: str = ButtonClickStrategy.DIRECT) -> ButtonClickResult:
    """
    便捷函数：根据选择器点击按钮
    
    Args:
        driver: WebDriver实例
        selectors: 选择器列表
        button_text: 按钮文本（可选）
        strategy: 点击策略
        
    Returns:
        ButtonClickResult: 点击结果
    """
    utils = ButtonClickUtils(driver)
    return utils.click_button_by_selectors(selectors, button_text, strategy)


def click_button_by_text(driver: WebDriver, 
                        button_text: str, 
                        strategy: str = ButtonClickStrategy.DIRECT) -> ButtonClickResult:
    """
    便捷函数：根据文本点击按钮
    
    Args:
        driver: WebDriver实例
        button_text: 按钮文本
        strategy: 点击策略
        
    Returns:
        ButtonClickResult: 点击结果
    """
    utils = ButtonClickUtils(driver)
    return utils.click_button_by_text(button_text, strategy)


def smart_click_button(driver: WebDriver, 
                      selectors: List[str], 
                      button_text: Optional[str] = None) -> ButtonClickResult:
    """
    便捷函数：智能点击按钮
    
    Args:
        driver: WebDriver实例
        selectors: 选择器列表
        button_text: 按钮文本（可选）
        
    Returns:
        ButtonClickResult: 点击结果
    """
    utils = ButtonClickUtils(driver)
    return utils.smart_click_button(selectors, button_text)


def fast_click_button(driver: WebDriver, 
                     selectors: List[str], 
                     button_text: Optional[str] = None,
                     max_selectors: int = 3) -> ButtonClickResult:
    """
    便捷函数：快速点击按钮
    
    Args:
        driver: WebDriver实例
        selectors: 选择器列表
        button_text: 按钮文本（可选）
        max_selectors: 最大尝试选择器数量
        
    Returns:
        ButtonClickResult: 点击结果
    """
    utils = ButtonClickUtils(driver)
    return utils.fast_click_button(selectors, button_text, max_selectors)
