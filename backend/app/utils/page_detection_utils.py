"""
页面检测工具 - 检测页面状态和类型

提供页面封禁检测、车辆可用性检测、页面类型识别等功能。
采用函数式设计，无默认值原则。
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .path_util import get_data_dir


def save_blocked_page(
    page_html: str,
    url: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> str:
    """
    保存被封禁的页面内容到data目录

    Args:
        page_html: 页面HTML内容
        url: 页面URL（可选）
        additional_info: 额外的信息（可选）

    Returns:
        保存的文件路径
    """
    # 创建保存目录
    data_dir = get_data_dir() / "blocked_pages"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名（基于时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"blocked_page_{timestamp}.html"
    filepath = data_dir / filename

    # 保存HTML内容
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(page_html)

    # 保存元数据
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'url': url,
        'page_length': len(page_html),
        'additional_info': additional_info or {}
    }

    metadata_filename = f"blocked_page_{timestamp}_metadata.json"
    metadata_filepath = data_dir / metadata_filename

    with open(metadata_filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return filepath


def is_blocked_page(
    page_html: str,
    url: Optional[str] = None,
    save_blocked: bool = True
) -> bool:
    """
    检测页面是否被封禁

    Args:
        page_html: 页面HTML内容
        url: 页面URL（可选，用于保存时记录）
        save_blocked: 是否保存被封禁的页面（默认True）

    Returns:
        是否被封禁
    """
    if not page_html:
        if save_blocked:
            save_blocked_page(page_html, url, {'reason': 'empty_page'})
        return True

    page_lower = page_html.lower()
    blocked_reason = None

    # 检查特定的HTML结构 - 这些是真正的封禁页面特征
    block_patterns = [
        # 标题中的封禁信息
        (r'<title[^>]*>.*(?:blocked|forbidden|access denied|403|404).*</title>',
         'title_blocked'),
        # 主要标题中的封禁信息
        (r'<h1[^>]*>.*(?:blocked|forbidden|access denied|403|404).*</h1>',
         'h1_blocked'),
        # 错误页面类名
        (r'<div[^>]*class="[^"]*(?:blocked|forbidden|error|not-found)[^"]*"',
         'error_class'),
        (r'<div[^>]*id="[^"]*(?:blocked|forbidden|error|not-found)[^"]*"',
         'error_id'),
        # 特定的封禁页面内容
        (r'<div[^>]*>.*(?:access denied|access blocked|page not found|'
         r'403 forbidden|404 not found).*</div>', 'error_content'),
        # 验证码页面
        (r'<div[^>]*class="[^"]*captcha[^"]*"[^>]*>.*(?:verify|challenge|'
         r'puzzle).*</div>', 'captcha_page'),
        # 维护页面
        (r'<div[^>]*>.*(?:under maintenance|temporarily unavailable|'
         r'service unavailable).*</div>', 'maintenance_page')
    ]

    for pattern, reason in block_patterns:
        if re.search(pattern, page_html, re.IGNORECASE | re.DOTALL):
            blocked_reason = reason
            break

    # 检查页面标题是否包含明显的错误信息
    if not blocked_reason:
        title_match = re.search(
            r'<title[^>]*>(.*?)</title>', page_html, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            title = title_match.group(1).lower()
            error_titles = [
                'access denied',
                'access blocked',
                'forbidden',
                'not found',
                'page not found',
                'error 403',
                'error 404',
                'temporarily unavailable',
                'under maintenance',
                'coming soon'
            ]
            for error_title in error_titles:
                if error_title in title:
                    blocked_reason = f'title_error_{error_title.replace(" ", "_")}'
                    break

    # 检查页面内容中是否包含封禁相关的关键词
    if not blocked_reason:
        block_content_indicators = [
            '你被封禁了',
            '验证码滑块',
            '滑块验证',
            '人机验证',
            '请完成验证',
            '验证失败',
            '访问被拒绝',
            '请求过于频繁',
            '请稍后再试',
            'ip被封禁',
            '账号被封禁',
            '访问受限',
            '需要验证身份',
            '安全验证',
            '反爬虫验证',
            '检测到异常访问',
            '请完成安全验证',
            '验证码验证',
            '滑动验证',
            '点击验证'
        ]

        for indicator in block_content_indicators:
            if indicator in page_html:
                blocked_reason = f'content_blocked_{indicator[:10]}'
                break

    # 检查页面内容长度 - 如果页面太短，可能是错误页面
    if not blocked_reason and len(page_html.strip()) < 1000:
        # 检查是否包含基本的HTML结构
        if not re.search(r'<html[^>]*>', page_html, re.IGNORECASE):
            blocked_reason = 'short_page_no_html'
        # 检查是否包含基本的页面内容
        elif not re.search(r'<body[^>]*>', page_html, re.IGNORECASE):
            blocked_reason = 'short_page_no_body'

    # 检查是否有明显的车辆数据 - 如果有，说明不是封禁页面
    vehicle_indicators = ['vehicle', 'car', 'listing', 'price', 'mileage', 'year', 'make', 'model']
    vehicle_count = sum(1 for indicator in vehicle_indicators if indicator in page_lower)
    if vehicle_count >= 3:
        return False

    # 如果检测到封禁，保存页面
    if blocked_reason and save_blocked:
        additional_info = {
            'reason': blocked_reason,
            'vehicle_indicators_count': vehicle_count,
            'page_length': len(page_html.strip())
        }
        save_blocked_page(page_html, url, additional_info)

    return blocked_reason is not None


def is_vehicle_available(page_html: str) -> bool:
    """
    检测车辆是否可用

    Args:
        page_html: 页面HTML内容

    Returns:
        车辆是否可用
    """
    if not page_html:
        return False

    # 车辆不可用的指示器
    unavailable_indicators = [
        "sold",
        "no longer available",
        "unavailable",
        "not available",
        "removed",
        "deleted",
        "expired",
        "inactive",
        "pending",
        "reserved",
        "hold",
        "withdrawn",
        "discontinued",
        "out of stock",
        "no longer for sale",
        "listing removed",
        "vehicle sold",
        "no longer listed"
    ]

    page_lower = page_html.lower()

    # 检查是否包含不可用指示器
    for indicator in unavailable_indicators:
        if indicator in page_lower:
            return False

    # 检查特定的HTML结构
    unavailable_patterns = [
        r'<div[^>]*class="[^"]*(?:sold|unavailable|removed)[^"]*"',
        r'<span[^>]*class="[^"]*(?:sold|unavailable|removed)[^"]*"',
        r'<p[^>]*class="[^"]*(?:sold|unavailable|removed)[^"]*"'
    ]

    for pattern in unavailable_patterns:
        if re.search(pattern, page_html, re.IGNORECASE):
            return False

    return True


def detect_page_type(page_html: str) -> str:
    """
    检测页面类型

    Args:
        page_html: 页面HTML内容

    Returns:
        页面类型
    """
    if not page_html:
        return "unknown"

    page_lower = page_html.lower()

    # 检测页面类型
    if "search" in page_lower and "results" in page_lower:
        return "search_results"
    elif "listing" in page_lower or "vehicle" in page_lower:
        return "vehicle_listing"
    elif "dealer" in page_lower or "dealership" in page_lower:
        return "dealer_page"
    elif "brand" in page_lower and "models" in page_lower:
        return "brand_models"
    elif "model" in page_lower and "specifications" in page_lower:
        return "model_specifications"
    elif "compare" in page_lower:
        return "comparison_page"
    elif "financing" in page_lower or "loan" in page_lower:
        return "financing_page"
    elif "contact" in page_lower or "phone" in page_lower:
        return "contact_page"
    elif "about" in page_lower:
        return "about_page"
    elif "privacy" in page_lower or "terms" in page_lower:
        return "legal_page"
    elif "login" in page_lower or "sign in" in page_lower:
        return "login_page"
    elif "register" in page_lower or "sign up" in page_lower:
        return "registration_page"
    elif "error" in page_lower or "404" in page_lower:
        return "error_page"
    elif "maintenance" in page_lower or "coming soon" in page_lower:
        return "maintenance_page"
    else:
        return "unknown"


def has_captcha(page_html: str) -> bool:
    """
    检测页面是否有验证码

    Args:
        page_html: 页面HTML内容

    Returns:
        是否有验证码
    """
    if not page_html:
        return False

    # 中文验证码指示器
    chinese_captcha_indicators = [
        "验证码滑块",
        "滑块验证",
        "人机验证",
        "请完成验证",
        "滑动验证",
        "点击验证",
        "验证码验证",
        "安全验证",
        "反爬虫验证",
        "检测到异常访问",
        "请完成安全验证"
    ]

    # 检查中文验证码指示器
    for indicator in chinese_captcha_indicators:
        if indicator in page_html:
            return True

    # 英文验证码指示器
    english_captcha_indicators = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "verification",
        "verify",
        "challenge",
        "puzzle",
        "slider",
        "jigsaw",
        "geetest",
        "cloudflare"
    ]

    page_lower = page_html.lower()

    # 检查是否包含英文验证码指示器
    for indicator in english_captcha_indicators:
        if indicator in page_lower:
            return True

    # 检查特定的HTML结构 - 只检测真正的验证码页面
    captcha_patterns = [
        # 验证码容器
        r'<div[^>]*class="[^"]*(?:captcha|recaptcha|hcaptcha|slider|verification)[^"]*"[^>]*>.*(?:verify|challenge|puzzle|滑块|验证码|人机验证).*</div>',
        # 验证码iframe
        r'<iframe[^>]*src="[^"]*(?:captcha|recaptcha|hcaptcha)[^"]*"[^>]*>',
        # 验证码脚本 - 但排除第三方服务
        r'<script[^>]*src="[^"]*(?:captcha|recaptcha|hcaptcha)[^"]*"[^>]*>',
        # 中文验证码内容
        r'<div[^>]*>.*(?:滑块|验证码|人机验证|请完成验证).*</div>',
        # 验证码表单
        r'<form[^>]*>.*(?:captcha|verification|验证码).*</form>'
    ]

    for pattern in captcha_patterns:
        if re.search(pattern, page_html, re.IGNORECASE | re.DOTALL):
            return True

    # 检查是否有验证码相关的JavaScript变量或配置 - 更精确的检测
    js_captcha_patterns = [
        r'verificationRequired\s*[:=]\s*true',
        r'isCaptchaActive\s*[:=]\s*true',
        r'captchaChallenge\s*[:=]',
        r'showCaptcha\s*[:=]\s*true',
        r'captchaVisible\s*[:=]\s*true'
    ]

    for pattern in js_captcha_patterns:
        if re.search(pattern, page_html, re.IGNORECASE):
            return True

    return False


def is_loading_page(page_html: str) -> bool:
    """
    检测页面是否正在加载

    Args:
        page_html: 页面HTML内容

    Returns:
        是否正在加载
    """
    if not page_html:
        return True

    # 加载指示器
    loading_indicators = [
        "loading",
        "please wait",
        "loading...",
        "spinner",
        "progress",
        "please wait while we load",
        "loading content",
        "fetching data",
        "processing request"
    ]

    page_lower = page_html.lower()

    # 检查是否包含加载指示器
    for indicator in loading_indicators:
        if indicator in page_lower:
            return True

    # 检查特定的HTML结构
    loading_patterns = [
        r'<div[^>]*class="[^"]*(?:loading|spinner|progress)[^"]*"',
        r'<div[^>]*id="[^"]*(?:loading|spinner|progress)[^"]*"',
        r'<img[^>]*src="[^"]*(?:loading|spinner|progress)[^"]*"'
    ]

    for pattern in loading_patterns:
        if re.search(pattern, page_html, re.IGNORECASE):
            return True

    return False


def has_vehicle_data(page_html: str) -> bool:
    """
    检测页面是否包含车辆数据

    Args:
        page_html: 页面HTML内容

    Returns:
        是否包含车辆数据
    """
    if not page_html:
        return False

    # 车辆数据指示器
    vehicle_indicators = [
        "year",
        "make",
        "model",
        "mileage",
        "price",
        "vin",
        "engine",
        "transmission",
        "fuel",
        "color",
        "interior",
        "exterior",
        "features",
        "specifications",
        "history",
        "accident",
        "service",
        "warranty"
    ]

    page_lower = page_html.lower()

    # 检查是否包含车辆数据指示器
    indicator_count = 0
    for indicator in vehicle_indicators:
        if indicator in page_lower:
            indicator_count += 1

    # 如果包含多个车辆数据指示器，认为有车辆数据
    return indicator_count >= 3


def detect_vehicle_count(page_html: str) -> int:
    """
    检测页面中的车辆数量

    Args:
        page_html: 页面HTML内容

    Returns:
        车辆数量
    """
    if not page_html:
        return 0

    # 车辆数量指示器
    count_patterns = [
        r'(\d+)\s+vehicles?',
        r'(\d+)\s+cars?',
        r'(\d+)\s+listings?',
        r'(\d+)\s+results?',
        r'showing\s+(\d+)',
        r'found\s+(\d+)',
        r'total\s+(\d+)'
    ]

    for pattern in count_patterns:
        match = re.search(pattern, page_html, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue

    return 0


def is_search_page(page_html: str) -> bool:
    """
    检测是否是搜索页面

    Args:
        page_html: 页面HTML内容

    Returns:
        是否是搜索页面
    """
    if not page_html:
        return False

    # 搜索页面指示器
    search_indicators = [
        "search",
        "filter",
        "results",
        "sort",
        "compare",
        "favorites",
        "save search",
        "search criteria",
        "search filters",
        "refine search"
    ]

    page_lower = page_html.lower()

    # 检查是否包含搜索指示器
    indicator_count = 0
    for indicator in search_indicators:
        if indicator in page_lower:
            indicator_count += 1

    # 如果包含多个搜索指示器，认为是搜索页面
    return indicator_count >= 2


def has_pagination(page_html: str) -> bool:
    """
    检测页面是否有分页

    Args:
        page_html: 页面HTML内容

    Returns:
        是否有分页
    """
    if not page_html:
        return False

    # 分页指示器
    pagination_indicators = [
        "page",
        "next",
        "previous",
        "first",
        "last",
        "pagination",
        "pager",
        "page numbers",
        "page navigation"
    ]

    page_lower = page_html.lower()

    # 检查是否包含分页指示器
    for indicator in pagination_indicators:
        if indicator in page_lower:
            return True

    # 检查特定的HTML结构
    pagination_patterns = [
        r'<div[^>]*class="[^"]*(?:pagination|pager)[^"]*"',
        r'<nav[^>]*class="[^"]*(?:pagination|pager)[^"]*"',
        r'<ul[^>]*class="[^"]*(?:pagination|pager)[^"]*"'
    ]

    for pattern in pagination_patterns:
        if re.search(pattern, page_html, re.IGNORECASE):
            return True

    return False


def get_page_metadata(page_html: str) -> Dict[str, Any]:
    """
    获取页面元数据

    Args:
        page_html: 页面HTML内容

    Returns:
        页面元数据字典
    """
    metadata = {
        "is_blocked": is_blocked_page(page_html),
        "is_loading": is_loading_page(page_html),
        "has_captcha": has_captcha(page_html),
        "page_type": detect_page_type(page_html),
        "has_vehicle_data": has_vehicle_data(page_html),
        "vehicle_count": detect_vehicle_count(page_html),
        "is_search_page": is_search_page(page_html),
        "has_pagination": has_pagination(page_html)
    }

    return metadata


def is_no_results_page(page_html: str) -> bool:
    """
    检测是否是无结果页面（所有车辆都被过滤掉了）

    Args:
        page_html: 页面HTML内容

    Returns:
        是否是无结果页面
    """
    if not page_html:
        return False

    page_lower = page_html.lower()

    # 无结果页面的指示器
    no_results_indicators = [
        "oops! you've filtered out all of the available listings",
        "adjust your filters to see more listings",
        "no results found",
        "no listings found",
        "no vehicles found",
        "no cars found",
        "no matches found",
        "try adjusting your search criteria",
        "no results match your search",
        "we couldn't find any vehicles",
        "no vehicles match your criteria",
        "search returned no results",
        "no listings match your filters",
        "try removing some filters",
        "no vehicles available",
        "no cars available",
        "no listings available"
    ]

    # 检查是否包含无结果指示器
    for indicator in no_results_indicators:
        if indicator in page_lower:
            return True

    # 检查特定的HTML结构 - 无结果页面的特征
    no_results_patterns = [
        # 包含"Oops"和"filtered out"的div
        r'<div[^>]*>.*oops.*filtered.*out.*all.*listings.*</div>',
        # 包含"adjust your filters"的提示
        r'<div[^>]*>.*adjust.*your.*filters.*see.*more.*listings.*</div>',
        # 无结果页面的特定类名或ID
        r'<div[^>]*class="[^"]*(?:no-results|no-listings|empty-results|filtered-out)[^"]*"',
        r'<div[^>]*id="[^"]*(?:no-results|no-listings|empty-results|filtered-out)[^"]*"',
        # 包含"alert-panel"和"filtered out"的结构
        r'<div[^>]*class="[^"]*alert-panel[^"]*"[^>]*>.*filtered.*out.*all.*</div>'
    ]

    for pattern in no_results_patterns:
        if re.search(pattern, page_html, re.IGNORECASE | re.DOTALL):
            return True

    # 检查是否包含特定的SVG图标（信息图标）
    if 'data-testid="alert-panel-test-id"' in page_html:
        if 'filtered out all' in page_lower or 'adjust your filters' in page_lower:
            return True

    return False


def is_valid_vehicle_page(page_html: str) -> bool:
    """
    检测是否是有效的车辆页面

    Args:
        page_html: 页面HTML内容

    Returns:
        是否是有效的车辆页面
    """
    if not page_html:
        return False

    # 检查基本条件
    if is_blocked_page(page_html):
        return False

    if is_loading_page(page_html):
        return False

    if has_captcha(page_html):
        return False

    # 检查是否是无结果页面
    if is_no_results_page(page_html):
        return False

    # 检查是否包含车辆数据
    if not has_vehicle_data(page_html):
        return False

    # 检查车辆是否可用
    if not is_vehicle_available(page_html):
        return False

    return True
