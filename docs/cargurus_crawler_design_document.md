# 🚗 CarGurusCrawler 重构设计文档

## 📖 文档概述

本文档详细描述了 CarGurusCrawler 的重构设计，包括架构设计、类职责划分、调用逻辑、使用示例等。重构后的系统采用模块化设计，遵循单一职责原则，提高了代码的可维护性和可扩展性。

**文档版本**: v1.0  
**创建日期**: 2025年1月27日  
**维护者**: Rehui Car Adviser 开发团队

---

## 🎯 重构目标

### 设计原则
1. **单一职责原则**: 每个类只负责一个特定功能
2. **开闭原则**: 对扩展开放，对修改关闭
3. **组合模式**: 通过组合实现复杂功能
4. **向后兼容**: 保持对外接口不变
5. **代码复用**: 避免重复代码

### 重构目标
- ✅ 将大型类拆分为多个专门的小类
- ✅ 提高代码可读性和可维护性
- ✅ 增强系统的可测试性
- ✅ 降低代码耦合度
- ✅ 提高代码复用性

---

## 🏗️ 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    CarGurusCrawler                          │
│                    (主协调器)                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Config    │ │ URLBuilder  │ │DataExtractor│
│  (配置管理)  │ │ (URL构建)   │ │ (数据提取)   │
└─────────────┘ └─────────────┘ └─────────────┘
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  DataSaver  │ │BrandCollector│ │ModelCollector│
│  (数据保存)  │ │ (品牌收集)   │ │ (车型收集)   │
└─────────────┘ └─────────────┘ └─────────────┘
                      │
                      ▼
              ┌─────────────┐
              │CarSearcher  │
              │ (车源搜索)   │
              └─────────────┘
```

### 类职责划分

| 类名 | 职责 | 主要方法 |
|------|------|----------|
| `CarGurusConfig` | 配置管理 | `get_city_zip_codes()`, `get_make_code()` |
| `CarGurusURLBuilder` | URL构建 | `build_search_url()`, `build_brand_url()`, `build_model_url()` |
| `CarGurusDataExtractor` | 数据提取 | `extract_listing_data()`, `extract_year_from_title()` |
| `CarGurusDataSaver` | 数据保存 | `save_brands_data()`, `save_models_data()` |
| `CarGurusBrandCollector` | 品牌收集 | `collect_brands()` |
| `CarGurusModelCollector` | 车型收集 | `collect_models_for_brand()` |
| `CarGurusCarSearcher` | 车源搜索 | `search_cars()` |
| `CarGurusCrawler` | 主协调器 | `search_cars()`, `collect_brands()`, `collect_models_for_brand()` |

---

## 📋 详细设计

### 1. CarGurusConfig (配置管理类)

**职责**: 管理城市ZIP代码和品牌代码映射

```python
class CarGurusConfig:
    """CarGurus 配置管理类"""
    
    # 主要城市及其ZIP代码
    MAJOR_CITIES = {
        'toronto': ['M5V', 'M6G', 'M4Y', 'M5A', 'M5H', 'M5B', 'M5C', 'M5E'],
        'vancouver': ['V6B', 'V6Z', 'V6E', 'V6H', 'V6J', 'V6K', 'V6L', 'V6M'],
        # ... 更多城市
    }
    
    # 品牌代码映射
    MAKE_CODES = {
        'toyota': 'm7', 'honda': 'm6', 'nissan': 'm12',
        # ... 更多品牌
    }
    
    @classmethod
    def get_city_zip_codes(cls, city_name: str) -> List[str]:
        """根据城市名称获取ZIP代码列表"""
        
    @classmethod
    def get_make_code(cls, make_name: str) -> str:
        """根据品牌名称获取品牌代码"""
```

**设计特点**:
- 使用类方法，无需实例化
- 支持精确匹配和部分匹配
- 提供默认值处理

### 2. CarGurusURLBuilder (URL构建类)

**职责**: 构建各种类型的CarGurus URL

```python
class CarGurusURLBuilder:
    """CarGurus URL构建器"""
    
    BASE_URL = "https://www.cargurus.ca/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action"
    
    @classmethod
    def build_search_url(cls, parsed_query: ParsedQuery, distance: int = 100) -> str:
        """构建车源搜索URL"""
        
    @classmethod
    def build_brand_url(cls, brand_code: str, zip_code: str, distance: int = 100) -> str:
        """构建品牌页面URL"""
        
    @classmethod
    def build_model_url(cls, model_code: str, zip_code: str, distance: int = 100) -> str:
        """构建车型页面URL"""
```

**设计特点**:
- 统一的URL构建逻辑
- 支持参数化配置
- 使用类方法，便于调用

### 3. CarGurusDataExtractor (数据提取类)

**职责**: 从HTML元素中提取结构化数据

```python
class CarGurusDataExtractor:
    """CarGurus 数据提取器"""
    
    @staticmethod
    def extract_listing_data(listing) -> Dict[str, str]:
        """提取单个listing的数据"""
        
    @staticmethod
    def extract_year_from_title(title: str) -> int:
        """从标题中提取年份"""
```

**设计特点**:
- 使用静态方法，无状态
- 安全的元素访问
- 数据清洗和格式化

### 4. CarGurusDataSaver (数据保存类)

**职责**: 将数据保存为JSON和CSV格式

```python
class CarGurusDataSaver:
    """CarGurus 数据保存器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_brands_data(self, brands: List[Dict[str, str]], date_str: str):
        """保存品牌数据到文件"""
        
    async def save_models_data(self, models: List[Dict[str, str]], brand_name: str, date_str: str):
        """保存车型数据到文件"""
```

**设计特点**:
- 支持多种格式输出
- 自动创建目录
- 异步操作

### 5. CarGurusBrandCollector (品牌收集器)

**职责**: 专门负责收集品牌数据

```python
class CarGurusBrandCollector:
    """CarGurus 品牌数据收集器"""
    
    def __init__(self, profile_name: str, zip_code: str, distance: int = 100):
        self.profile_name = profile_name
        self.zip_code = zip_code
        self.distance = distance
    
    async def collect_brands(self, limit: int = None) -> List[Dict[str, str]]:
        """收集 CarGurus 品牌数据"""
        
    async def _extract_brands_from_page(self, driver, limit: int = None) -> List[Dict[str, str]]:
        """从页面提取品牌数据"""
        
    async def _handle_captcha(self, driver) -> bool:
        """处理滑块验证码"""
        
    def _simulate_human_behavior(self, driver):
        """模拟人类浏览行为"""
```

**设计特点**:
- 包含验证码处理逻辑
- 支持多种提取策略
- 人类行为模拟

### 6. CarGurusModelCollector (车型收集器)

**职责**: 专门负责收集车型数据

```python
class CarGurusModelCollector:
    """CarGurus 车型数据收集器"""
    
    def __init__(self, profile_name: str, zip_code: str, distance: int = 100):
        self.profile_name = profile_name
        self.zip_code = zip_code
        self.distance = distance
    
    async def collect_models_for_brand(self, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """收集指定品牌的车型数据"""
        
    async def _extract_models_from_page(self, driver, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """从页面提取车型数据"""
```

**设计特点**:
- 复用验证码处理逻辑
- 支持品牌特定的车型收集
- 硬编码备用方案

### 7. CarGurusCarSearcher (车源搜索器)

**职责**: 专门负责搜索车源

```python
class CarGurusCarSearcher:
    """CarGurus 车源搜索器"""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
    
    async def search_cars(self, parsed_query: ParsedQuery, max_results: int = 20) -> List[CarListing]:
        """搜索车源"""
        
    async def _handle_captcha(self, driver) -> bool:
        """处理滑块验证码"""
        
    def _simulate_human_behavior(self, driver):
        """模拟人类浏览行为"""
```

**设计特点**:
- 与CarGurusScraper兼容的接口
- 返回标准化的CarListing对象
- 复用验证码处理逻辑

### 8. CarGurusCrawler (主协调器)

**职责**: 组合各个组件，提供统一的对外接口

```python
class CarGurusCrawler:
    """CarGurus 主爬虫协调器 - 重构版本"""
    
    def __init__(self, date_str: str, make_name: str, zip_code: str, profile_name: str = None):
        # 初始化各个组件
        self.data_saver = CarGurusDataSaver(self.output_dir)
        self.brand_collector = CarGurusBrandCollector(self.profile_name, zip_code, self.distance)
        self.model_collector = CarGurusModelCollector(self.profile_name, zip_code, self.distance)
        self.car_searcher = CarGurusCarSearcher(self.profile_name)
    
    async def search_cars(self, parsed_query: ParsedQuery, max_results: int = 20) -> List[CarListing]:
        """搜索车源 - 与CarGurusScraper兼容的接口"""
        return await self.car_searcher.search_cars(parsed_query, max_results)
    
    async def collect_brands(self, limit: int = None) -> List[Dict[str, str]]:
        """收集 CarGurus 品牌数据"""
        return await self.brand_collector.collect_brands(limit)
    
    async def collect_models_for_brand(self, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """收集指定品牌的车型数据"""
        return await self.model_collector.collect_models_for_brand(brand_name, limit)
```

**设计特点**:
- 组合模式实现
- 保持向后兼容性
- 统一的配置管理

---

## 🔄 调用逻辑

### 1. Web API 调用场景

```python
# 在 SearchService 中的调用
class SearchService:
    def __init__(self):
        # 注意：这里需要修复初始化问题
        self.cargurus_crawler = None  # 延迟初始化
    
    async def search_cars(self, request: SearchRequest):
        # 1. 延迟初始化爬虫
        if not self.cargurus_crawler:
            date_str = time.strftime('%Y%m%d')
            self.cargurus_crawler = CarGurusCrawler(date_str, "Toyota", "M5V")
        
        # 2. AI解析用户查询
        parsed_query = await self.gemini_service.parse_user_query(request.query)
        
        # 3. 调用爬虫搜索车源
        cars = await self.cargurus_crawler.search_cars(parsed_query, max_results=20)
        
        # 4. 返回搜索结果
        return SearchResponse(success=True, data=cars)
```

**调用链**:
```
用户请求 → SearchService.search_cars() 
→ CarGurusCrawler.search_cars() 
→ CarGurusCarSearcher.search_cars()
→ CarGurusURLBuilder.build_search_url()
→ CarGurusDataExtractor.extract_listing_data()
```

### 2. 命令行脚本调用场景

```python
# 品牌数据收集
async def collect_brands(limit=None, test_mode=False):
    # 1. 创建爬虫实例
    date_str = time.strftime('%Y%m%d')
    crawler = CarGurusCrawler(date_str, "Toyota", "M5V")
    
    # 2. 收集品牌数据
    brands = await crawler.collect_brands(limit=limit)
    
    # 3. 保存数据
    await crawler.save_brands_data(brands)
    
    return brands

# 车型数据收集
async def collect_models_for_brand(brand_name="Acura", limit=None):
    # 1. 创建爬虫实例
    crawler = CarGurusCrawler(date_str, brand_name, "M5V")
    
    # 2. 收集车型数据
    models = await crawler.collect_models_for_brand(brand_name, limit=limit)
    
    # 3. 保存数据
    await crawler.save_models_data(models, brand_name)
    
    return models
```

**调用链**:
```
命令行 → collect_brands() 
→ CarGurusCrawler.collect_brands() 
→ CarGurusBrandCollector.collect_brands()
→ CarGurusDataSaver.save_brands_data()
```

### 3. 直接使用场景

```python
async def main():
    # 1. 创建爬虫实例
    date_str = time.strftime('%Y%m%d')
    make_name = "Toyota"
    zip_code = "M5V"
    crawler = CarGurusCrawler(date_str, make_name, zip_code)
    
    # 2. 获取城市ZIP代码
    city_zips = crawler.get_city_zip_codes("Toronto")
    
    # 3. 收集品牌数据
    brands = await crawler.collect_brands(limit=10)
    if brands:
        await crawler.save_brands_data(brands)
```

---

## 🚀 使用示例

### 1. 基本使用

```python
import asyncio
from app.services.cargurus_crawler import CarGurusCrawler

async def basic_usage():
    # 创建爬虫实例
    crawler = CarGurusCrawler("20250127", "Toyota", "M5V")
    
    # 搜索车源
    from app.models.schemas import ParsedQuery
    query = ParsedQuery(make="Toyota", model="Camry", year=2020)
    cars = await crawler.search_cars(query, max_results=10)
    
    print(f"找到 {len(cars)} 辆车源")
    for car in cars:
        print(f"- {car.title}: ${car.price}")

# 运行示例
asyncio.run(basic_usage())
```

### 2. 品牌数据收集

```python
async def collect_brand_data():
    # 创建爬虫实例
    crawler = CarGurusCrawler("20250127", "Toyota", "M5V")
    
    # 收集品牌数据
    brands = await crawler.collect_brands(limit=20)
    
    # 保存数据
    await crawler.save_brands_data(brands)
    
    print(f"收集了 {len(brands)} 个品牌")
    for brand in brands:
        print(f"- {brand['name']}: {brand['value']}")

asyncio.run(collect_brand_data())
```

### 3. 车型数据收集

```python
async def collect_model_data():
    # 创建爬虫实例
    crawler = CarGurusCrawler("20250127", "Acura", "M5V")
    
    # 收集车型数据
    models = await crawler.collect_models_for_brand("Acura", limit=10)
    
    # 保存数据
    await crawler.save_models_data(models, "Acura")
    
    print(f"收集了 {len(models)} 个车型")
    for model in models:
        print(f"- {model['name']}: {model['count']} 辆车")

asyncio.run(collect_model_data())
```

### 4. 配置使用

```python
# 使用配置类
from app.services.cargurus_crawler import CarGurusConfig

# 获取城市ZIP代码
toronto_zips = CarGurusConfig.get_city_zip_codes("Toronto")
print(f"Toronto ZIP codes: {toronto_zips}")

# 获取品牌代码
toyota_code = CarGurusConfig.get_make_code("Toyota")
print(f"Toyota code: {toyota_code}")

# 部分匹配示例
bmw_code = CarGurusConfig.get_make_code("BMW X5")  # 会匹配到 "bmw"
print(f"BMW code: {bmw_code}")
```

---

## 🔧 配置说明

### 环境变量

```bash
# 必需配置
GOOGLE_GEMINI_API_KEY=your_gemini_api_key

# 可选配置
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
DEBUG=True
```

### 初始化参数

```python
crawler = CarGurusCrawler(
    date_str="20250127",      # 日期字符串，用于文件命名
    make_name="Toyota",       # 品牌名称
    zip_code="M5V",          # ZIP代码
    profile_name=None         # 可选的profile名称，默认自动生成
)
```

### 配置参数

```python
# 在 CarGurusCrawler 初始化时设置
self.distance = 100          # 搜索距离（公里）
self.max_pages = 50         # 最大页数
self.per_page = 24          # 每页结果数
```

---

## ⚠️ 注意事项

### 1. 初始化问题修复

**问题**: SearchService 中的初始化缺少必要参数
```python
# ❌ 错误的方式
self.cargurus_crawler = CarGurusCrawler()  # 缺少参数

# ✅ 正确的方式
self.cargurus_crawler = None  # 延迟初始化

async def search_cars(self, request: SearchRequest):
    if not self.cargurus_crawler:
        date_str = time.strftime('%Y%m%d')
        self.cargurus_crawler = CarGurusCrawler(date_str, "Toyota", "M5V")
```

### 2. 异步调用

所有主要方法都是异步的，需要使用 `await` 调用：

```python
# ✅ 正确
cars = await crawler.search_cars(query)

# ❌ 错误
cars = crawler.search_cars(query)  # 会返回协程对象
```

### 3. 错误处理

每个组件都有独立的错误处理机制：

```python
try:
    brands = await crawler.collect_brands()
except Exception as e:
    logger.log_result("品牌收集失败", f"错误: {str(e)}")
    # 处理错误
```

### 4. 资源管理

使用 `async with` 确保浏览器资源正确释放：

```python
async with browser_utils.get_driver(profile_name) as driver:
    # 使用 driver
    pass  # 自动释放资源
```

---

## 🧪 测试建议

### 1. 单元测试

```python
import pytest
from app.services.cargurus_crawler import CarGurusConfig, CarGurusURLBuilder

def test_city_zip_codes():
    """测试城市ZIP代码获取"""
    zips = CarGurusConfig.get_city_zip_codes("Toronto")
    assert len(zips) > 0
    assert "M5V" in zips

def test_make_code():
    """测试品牌代码获取"""
    code = CarGurusConfig.get_make_code("Toyota")
    assert code == "m7"

def test_url_builder():
    """测试URL构建"""
    from app.models.schemas import ParsedQuery
    query = ParsedQuery(make="Toyota", model="Camry")
    url = CarGurusURLBuilder.build_search_url(query)
    assert "cargurus.ca" in url
    assert "m7" in url
```

### 2. 集成测试

```python
@pytest.mark.asyncio
async def test_crawler_integration():
    """测试爬虫集成功能"""
    crawler = CarGurusCrawler("20250127", "Toyota", "M5V")
    
    # 测试品牌收集
    brands = await crawler.collect_brands(limit=5)
    assert len(brands) > 0
    
    # 测试数据保存
    await crawler.save_brands_data(brands)
    # 验证文件是否创建
```

### 3. 性能测试

```python
import time

@pytest.mark.asyncio
async def test_performance():
    """测试性能"""
    crawler = CarGurusCrawler("20250127", "Toyota", "M5V")
    
    start_time = time.time()
    brands = await crawler.collect_brands(limit=10)
    end_time = time.time()
    
    assert end_time - start_time < 30  # 应该在30秒内完成
    assert len(brands) > 0
```

---

## 📈 性能优化

### 1. 并发处理

```python
async def collect_multiple_brands():
    """并发收集多个品牌数据"""
    brands = ["Toyota", "Honda", "BMW", "Mercedes"]
    
    tasks = []
    for brand in brands:
        crawler = CarGurusCrawler("20250127", brand, "M5V")
        task = crawler.collect_brands(limit=5)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 缓存机制

```python
from functools import lru_cache

class CarGurusConfig:
    @classmethod
    @lru_cache(maxsize=128)
    def get_city_zip_codes(cls, city_name: str) -> List[str]:
        """缓存城市ZIP代码查询结果"""
        # ... 实现逻辑
    
    @classmethod
    @lru_cache(maxsize=256)
    def get_make_code(cls, make_name: str) -> str:
        """缓存品牌代码查询结果"""
        # ... 实现逻辑
```

### 3. 资源池管理

```python
class BrowserPool:
    """浏览器资源池"""
    def __init__(self, max_size=5):
        self.max_size = max_size
        self.pool = asyncio.Queue(maxsize=max_size)
    
    async def get_driver(self):
        """获取浏览器实例"""
        if self.pool.empty():
            return await browser_utils.get_driver()
        return await self.pool.get()
    
    async def return_driver(self, driver):
        """归还浏览器实例"""
        await self.pool.put(driver)
```

---

## 🔮 未来扩展

### 1. 多数据源支持

```python
class MultiSourceCrawler:
    """多数据源爬虫"""
    def __init__(self):
        self.cargurus_crawler = CarGurusCrawler(...)
        self.autotrader_crawler = AutoTraderCrawler(...)
        self.kijiji_crawler = KijijiCrawler(...)
    
    async def search_all_sources(self, query):
        """从所有数据源搜索"""
        tasks = [
            self.cargurus_crawler.search_cars(query),
            self.autotrader_crawler.search_cars(query),
            self.kijiji_crawler.search_cars(query)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self.merge_results(results)
```

### 2. 数据持久化

```python
class DatabaseSaver:
    """数据库保存器"""
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def save_cars(self, cars: List[CarListing]):
        """保存车源到数据库"""
        for car in cars:
            await self.db.execute(
                "INSERT INTO cars (title, price, year, mileage, city, link) VALUES (?, ?, ?, ?, ?, ?)",
                (car.title, car.price, car.year, car.mileage, car.city, car.link)
            )
```

### 3. 智能重试机制

```python
class RetryableCrawler:
    """支持重试的爬虫"""
    def __init__(self, max_retries=3, backoff_factor=2):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def search_with_retry(self, query):
        """带重试的搜索"""
        for attempt in range(self.max_retries):
            try:
                return await self.search_cars(query)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.backoff_factor ** attempt)
```

---

## 📋 总结

### 重构优势

1. **单一职责**: 每个类只负责一个特定功能，职责清晰
2. **代码复用**: 验证码处理和行为模拟逻辑被复用
3. **易于维护**: 修改某个功能只需要修改对应的类
4. **易于测试**: 每个类可以独立测试
5. **向后兼容**: 主接口保持不变，现有代码无需修改
6. **可扩展性**: 新功能可以通过添加新类实现

### 设计模式应用

- **组合模式**: 主协调器组合各个专门组件
- **策略模式**: 多种数据提取策略
- **工厂模式**: URL构建器
- **单例模式**: 配置管理类

### 最佳实践

- 使用类型注解提高代码可读性
- 异步编程提高性能
- 错误处理确保系统稳定性
- 日志记录便于调试和监控
- 配置外部化提高灵活性

---

**文档版本**: v1.0  
**最后更新**: 2025年1月27日  
**维护者**: Rehui Car Adviser 开发团队
