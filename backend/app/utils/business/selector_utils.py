"""
CarGurus 选择器工具类

这个模块包含了所有用于 CarGurus 网站元素定位的 XPath 选择器。
集中管理选择器有助于：
1. 统一维护和更新
2. 提高代码可读性
3. 便于调试和测试
4. 支持选择器的版本管理
"""

from typing import List, Dict, Any
from enum import Enum


class SelectorType(Enum):
    """选择器类型枚举"""
    MODEL_SELECT = "model_select"  # 车型选择器
    MODEL_BUTTON = "model_button"  # 车型按钮
    MODEL_LINK = "model_link"      # 车型链接
    CAR_LISTING = "car_listing"    # 车源列表
    BUTTON_CLICK = "button_click"  # 按钮点击
    LABEL_TEXT = "label_text"      # 标签文本


class CarGurusSelectors:
    """CarGurus 网站选择器集合 - 优化版本"""
    
    # 选择器缓存
    _selector_cache = {}
    
    # 选择器成功率统计
    _selector_success_rate = {}
    
    # =============================================================================
    # 车型选择器 - 用于收集品牌车型数据
    # =============================================================================
    
    @staticmethod
    def get_model_selectors() -> List[str]:
        """获取车型选择器列表 - 精简版，按成功率排序"""
        return [
            # 高成功率选择器（基于实际测试）
            "//div[@id='MakeAndModel-accordion-content']//button[contains(@value, '/')]",
            "//select[@name='makeModelTrimPaths']//option[contains(@value, '/')]",
            
            # 备用选择器
            "//div[contains(@class, '_accordionContent_')]//button[contains(@value, '/')]",
            "//a[contains(@href, 'makeModelTrimPaths') and contains(@href, '/')]"
        ]
    
    @staticmethod
    def get_model_button_selectors() -> List[str]:
        """获取车型按钮选择器列表 - 精简版"""
        return [
            # 高成功率选择器
            "//button[@id='MakeAndModel-accordion-trigger']",
            "//button[contains(@class, '_accordionTrigger_')]",
            
            # 备用选择器
            "//button[@aria-controls='MakeAndModel-accordion-content']",
            "//button[contains(text(), 'Make & model')]"
        ]
    
    @staticmethod
    def get_show_all_models_button_selectors() -> List[str]:
        """获取"显示所有车型"按钮选择器列表 - 精简版"""
        return [
            # 高成功率选择器
            "//button[contains(@class, '_toggleShowAllButton_')]",
            "//button[contains(@class, 'lOGaE')]",
            
            # 备用选择器
            "//button[contains(text(), 'Show all models')]",
            "//button[contains(text(), 'Show all')]"
        ]
    
    # =============================================================================
    # 车源选择器 - 用于搜索和提取车源信息
    # =============================================================================
    
    @staticmethod
    def get_car_listing_selectors() -> List[str]:
        """获取车源列表选择器"""
        return [
            "//a[@data-testid='car-blade-link']",
            "//a[contains(@href, '/cars/')]",
            "//div[contains(@class, 'listing')]//a",
            "//div[contains(@data-testid, 'listing')]//a"
        ]
    
    @staticmethod
    def get_car_detail_selectors() -> Dict[str, str]:
        """获取车源详情选择器"""
        return {
            'title': ".//h4",
            'price': ".//h4[contains(@class,'_priceText')]",
            'mileage': ".//p[contains(@data-testid,'mileage')]",
            'location': ".//p[@data-testid='srp-tile-bucket-text']",
            'deal_rating': ".//span[contains(text(),'Deal')]",
            'url': "href"  # 属性选择器
        }
    
    # =============================================================================
    # 通用选择器 - 用于各种通用操作
    # =============================================================================
    
    @staticmethod
    def get_button_selectors() -> List[str]:
        """获取通用按钮选择器"""
        return [
            "//button",
            "//input[@type='button']",
            "//input[@type='submit']",
            "//a[contains(@class, 'button')]"
        ]
    
    @staticmethod
    def get_form_selectors() -> List[str]:
        """获取表单选择器"""
        return [
            "//form",
            "//div[contains(@class, 'form')]",
            "//div[contains(@class, 'search')]"
        ]
    
    # =============================================================================
    # 选择器工具方法
    # =============================================================================
    
    @staticmethod
    def get_selector_by_type(selector_type: SelectorType) -> List[str]:
        """根据类型获取选择器列表"""
        selector_map = {
            SelectorType.MODEL_SELECT: CarGurusSelectors.get_model_selectors(),
            SelectorType.MODEL_BUTTON: CarGurusSelectors.get_model_button_selectors(),
            SelectorType.MODEL_LINK: CarGurusSelectors.get_model_selectors(),  # 复用
            SelectorType.CAR_LISTING: CarGurusSelectors.get_car_listing_selectors(),
            SelectorType.BUTTON_CLICK: CarGurusSelectors.get_button_selectors(),
        }
        return selector_map.get(selector_type, [])
    
    @staticmethod
    def get_selector_info() -> Dict[str, Any]:
        """获取选择器信息统计"""
        return {
            'model_selectors_count': len(CarGurusSelectors.get_model_selectors()),
            'model_button_selectors_count': len(CarGurusSelectors.get_model_button_selectors()),
            'show_all_button_selectors_count': len(CarGurusSelectors.get_show_all_models_button_selectors()),
            'car_listing_selectors_count': len(CarGurusSelectors.get_car_listing_selectors()),
            'car_detail_selectors_count': len(CarGurusSelectors.get_car_detail_selectors()),
            'total_selector_types': len(SelectorType)
        }
    
    @staticmethod
    def validate_selector(selector: str) -> bool:
        """验证选择器格式是否正确"""
        try:
            # 基本的 XPath 格式验证
            if not selector.startswith('//') and not selector.startswith('.//'):
                return False
            
            # 检查是否包含必要的 XPath 语法
            if '[' not in selector or ']' not in selector:
                return False
                
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_selector_priority(selector: str) -> int:
        """获取选择器优先级（数字越小优先级越高）"""
        priority_map = {
            # 高优先级 - 精确匹配
            "//select[@name='makeModelTrimPaths']": 1,
            "//a[@data-testid='car-blade-link']": 1,
            "//button[@id='MakeAndModel-accordion-trigger']": 1,
            "//button[contains(@class, '_toggleShowAllButton_')]": 1,
            
            # 中优先级 - 部分匹配
            "//select[contains(@name, 'model')]": 2,
            "//button[contains(@data-testid, 'FILTER.MAKE_MODEL')]": 2,
            "//button[contains(@class, '_accordionTrigger_')]": 2,
            
            # 低优先级 - 通用匹配
            "//button[contains(@value, '/')]": 3,
            "//a[contains(@href, '/cars/')]": 3,
        }
        
        for pattern, priority in priority_map.items():
            if pattern in selector:
                return priority
        
        return 5  # 默认优先级
    
    @classmethod
    def get_optimized_selectors(cls, selector_type: str) -> List[str]:
        """获取优化的选择器列表 - 基于成功率排序"""
        if selector_type in cls._selector_cache:
            return cls._selector_cache[selector_type]
        
        # 获取原始选择器列表
        if selector_type == "model":
            selectors = cls.get_model_selectors()
        elif selector_type == "model_button":
            selectors = cls.get_model_button_selectors()
        elif selector_type == "show_all_models":
            selectors = cls.get_show_all_models_button_selectors()
        else:
            return []
        
        # 根据成功率排序
        optimized_selectors = sorted(selectors, key=lambda s: cls._get_selector_success_rate(s))
        
        # 缓存结果
        cls._selector_cache[selector_type] = optimized_selectors
        return optimized_selectors
    
    @classmethod
    def update_selector_success(cls, selector: str, success: bool):
        """更新选择器成功率统计"""
        if selector not in cls._selector_success_rate:
            cls._selector_success_rate[selector] = {'success': 0, 'total': 0}
        
        cls._selector_success_rate[selector]['total'] += 1
        if success:
            cls._selector_success_rate[selector]['success'] += 1
    
    @classmethod
    def _get_selector_success_rate(cls, selector: str) -> float:
        """获取选择器成功率"""
        if selector not in cls._selector_success_rate:
            return 0.5  # 默认成功率
        
        stats = cls._selector_success_rate[selector]
        if stats['total'] == 0:
            return 0.5
        
        return stats['success'] / stats['total']


# =============================================================================
# 选择器使用示例和测试
# =============================================================================

def test_selectors():
    """测试选择器功能"""
    selectors = CarGurusSelectors()
    
    # 测试获取选择器
    model_selectors = selectors.get_model_selectors()
    print(f"车型选择器数量: {len(model_selectors)}")
    
    # 测试选择器信息
    info = selectors.get_selector_info()
    print(f"选择器信息: {info}")
    
    # 测试选择器验证
    valid_selector = "//select[@name='makeModelTrimPaths']//option[contains(@value, '/')]"
    invalid_selector = "invalid_selector"
    
    print(f"有效选择器验证: {selectors.validate_selector(valid_selector)}")
    print(f"无效选择器验证: {selectors.validate_selector(invalid_selector)}")
    
    # 测试优先级
    print(f"选择器优先级: {selectors.get_selector_priority(valid_selector)}")


if __name__ == "__main__":
    test_selectors()
