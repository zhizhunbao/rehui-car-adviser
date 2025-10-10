"""
URL检查工具 - 检查URL存活状态和有效性

提供URL存活检查、批量URL检查、URL验证等功能。
采用函数式设计，无默认值原则。
"""

import requests
from typing import List, Dict, Optional
from urllib.parse import urlparse
import time
from concurrent.futures import ThreadPoolExecutor




def check_url_alive_sync(url: str, max_retries: int) -> bool:
    """
    检查URL是否存活（同步版本）

    Args:
        url: 要检查的URL
        max_retries: 最大重试次数

    Returns:
        URL是否存活
    """
    if not url or not is_valid_url(url):
        return False

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(1)
            continue

    return False


def batch_check_urls(urls: List[str], max_concurrent: int) -> Dict[str, bool]:
    """
    批量检查URL存活状态

    Args:
        urls: URL列表
        max_concurrent: 最大并发数

    Returns:
        URL存活状态字典
    """
    results = {}

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # 提交所有任务
        future_to_url = {
            executor.submit(check_url_alive_sync, url, 3): url
            for url in urls
        }

        # 收集结果
        for future in future_to_url:
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception:
                results[url] = False

    return results


def is_valid_url(url: str) -> bool:
    """
    验证URL格式是否有效

    Args:
        url: 要验证的URL

    Returns:
        URL是否有效
    """
    if not url:
        return False

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_url_status_code(url: str) -> Optional[int]:
    """
    获取URL状态码

    Args:
        url: 要检查的URL

    Returns:
        状态码，如果请求失败则返回None
    """
    if not url or not is_valid_url(url):
        return None

    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return response.status_code
    except Exception:
        return None


def check_url_redirects(url: str) -> List[str]:
    """
    检查URL重定向链

    Args:
        url: 要检查的URL

    Returns:
        重定向链列表
    """
    if not url or not is_valid_url(url):
        return []

    redirects = []

    try:
        response = requests.get(url, timeout=10, allow_redirects=False)

        while response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = response.headers.get('Location')
            if redirect_url:
                redirects.append(redirect_url)
                response = requests.get(redirect_url, timeout=10, allow_redirects=False)
            else:
                break

    except Exception:
        pass

    return redirects


def get_url_response_time(url: str) -> Optional[float]:
    """
    获取URL响应时间

    Args:
        url: 要检查的URL

    Returns:
        响应时间（秒），如果请求失败则返回None
    """
    if not url or not is_valid_url(url):
        return None

    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()

        if response.status_code < 400:
            return end_time - start_time
        else:
            return None

    except Exception:
        return None


def check_url_content_type(url: str) -> Optional[str]:
    """
    检查URL内容类型

    Args:
        url: 要检查的URL

    Returns:
        内容类型，如果请求失败则返回None
    """
    if not url or not is_valid_url(url):
        return None

    try:
        response = requests.head(url, timeout=10)
        return response.headers.get('Content-Type')
    except Exception:
        return None


def is_url_accessible(url: str) -> bool:
    """
    检查URL是否可访问

    Args:
        url: 要检查的URL

    Returns:
        URL是否可访问
    """
    status_code = get_url_status_code(url)
    return status_code is not None and status_code < 400


def get_url_info(url: str) -> Dict[str, any]:
    """
    获取URL详细信息

    Args:
        url: 要检查的URL

    Returns:
        URL信息字典
    """
    info = {
        "url": url,
        "is_valid": is_valid_url(url),
        "is_accessible": False,
        "status_code": None,
        "response_time": None,
        "content_type": None,
        "redirects": [],
        "error": None
    }

    if not info["is_valid"]:
        info["error"] = "Invalid URL format"
        return info

    try:
        # 检查状态码
        info["status_code"] = get_url_status_code(url)
        info["is_accessible"] = info["status_code"] is not None and info["status_code"] < 400

        # 获取响应时间
        info["response_time"] = get_url_response_time(url)

        # 获取内容类型
        info["content_type"] = check_url_content_type(url)

        # 获取重定向链
        info["redirects"] = check_url_redirects(url)

    except Exception as e:
        info["error"] = str(e)

    return info


def filter_alive_urls(urls: List[str]) -> List[str]:
    """
    过滤出存活的URL

    Args:
        urls: URL列表

    Returns:
        存活的URL列表
    """
    alive_urls = []

    for url in urls:
        if check_url_alive_sync(url, 2):
            alive_urls.append(url)

    return alive_urls


def filter_dead_urls(urls: List[str]) -> List[str]:
    """
    过滤出死链

    Args:
        urls: URL列表

    Returns:
        死链列表
    """
    dead_urls = []

    for url in urls:
        if not check_url_alive_sync(url, 2):
            dead_urls.append(url)

    return dead_urls


def check_urls_batch(urls: List[str], batch_size: int = 10) -> Dict[str, Dict[str, any]]:
    """
    批量检查URL详细信息

    Args:
        urls: URL列表
        batch_size: 批处理大小

    Returns:
        URL详细信息字典
    """
    results = {}

    # 分批处理
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_url = {
                executor.submit(get_url_info, url): url
                for url in batch
            }

            for future in future_to_url:
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    results[url] = {
                        "url": url,
                        "is_valid": False,
                        "is_accessible": False,
                        "error": str(e)
                    }

    return results


def is_same_domain(url1: str, url2: str) -> bool:
    """
    检查两个URL是否属于同一域名

    Args:
        url1: 第一个URL
        url2: 第二个URL

    Returns:
        是否属于同一域名
    """
    try:
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    标准化URL

    Args:
        url: 要标准化的URL

    Returns:
        标准化后的URL
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)

        # 移除默认端口
        if parsed.port:
            if (parsed.scheme == 'http' and parsed.port == 80) or \
               (parsed.scheme == 'https' and parsed.port == 443):
                parsed = parsed._replace(netloc=parsed.hostname)

        # 移除末尾的斜杠（除了根路径）
        if parsed.path == '/':
            path = '/'
        else:
            path = parsed.path.rstrip('/')

        parsed = parsed._replace(path=path)

        return parsed.geturl()

    except Exception:
        return url


def extract_domain(url: str) -> Optional[str]:
    """
    从URL中提取域名

    Args:
        url: 要提取域名的URL

    Returns:
        域名，如果提取失败则返回None
    """
    try:
        return urlparse(url).netloc
    except Exception:
        return None


def is_https_url(url: str) -> bool:
    """
    检查URL是否使用HTTPS

    Args:
        url: 要检查的URL

    Returns:
        是否使用HTTPS
    """
    try:
        return urlparse(url).scheme.lower() == 'https'
    except Exception:
        return False


def convert_to_https(url: str) -> str:
    """
    将HTTP URL转换为HTTPS

    Args:
        url: 要转换的URL

    Returns:
        转换后的HTTPS URL
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() == 'http':
            parsed = parsed._replace(scheme='https')
            return parsed.geturl()
        return url
    except Exception:
        return url
