#!/usr/bin/env python3
"""
IP地址到ZIP码转换服务
通过IP地址获取用户的地理位置信息，包括ZIP码
"""

from typing import Any, Dict, Optional

import httpx

from app.utils.core.logger import get_logger

logger = get_logger(__name__)


class IPToZipService:
    """IP地址到ZIP码转换服务"""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        # 使用免费的IP地理位置API服务
        self.api_urls = [
            "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,query",
            "https://ipapi.co/{ip}/json/",
            "https://api.ipgeolocation.io/ipgeo?apiKey=free&ip={ip}",
        ]
        self.current_api_index = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self.client is None or self.client.is_closed:
            timeout = httpx.Timeout(10.0)
            self.client = httpx.AsyncClient(timeout=timeout)
        return self.client

    async def close(self):
        """关闭HTTP客户端"""
        if self.client and not self.client.is_closed:
            await self.client.aclose()

    async def get_zip_from_ip(self, ip_address: str) -> Optional[str]:
        """
        通过IP地址获取ZIP码

        Args:
            ip_address: IP地址

        Returns:
            ZIP码，如果获取失败返回None
        """
        if not ip_address or ip_address == "unknown":
            logger.log_result("IP地址无效", "IP地址为空或unknown")
            return None

        # 跳过私有IP地址
        if self._is_private_ip(ip_address):
            logger.log_result("跳过私有IP地址", f"IP: {ip_address}")
            # 开发环境：如果是本地回环地址，返回默认的ZIP码
            if ip_address == "127.0.0.1":
                logger.log_result(
                    "开发环境检测", "使用默认ZIP码: M5V (多伦多)"
                )
                return "M5V"
            return None

        client = await self._get_client()

        # 尝试多个API服务
        for i in range(len(self.api_urls)):
            api_url = self.api_urls[self.current_api_index]
            try:
                zip_code = await self._try_api(client, api_url, ip_address)
                if zip_code:
                    logger.log_result(
                        "成功获取ZIP码", f"IP: {ip_address}, ZIP: {zip_code}"
                    )
                    return zip_code
            except Exception as e:
                logger.log_result(
                    "API请求失败", f"API {self.current_api_index}: {e}"
                )

            # 切换到下一个API
            self.current_api_index = (self.current_api_index + 1) % len(
                self.api_urls
            )

        logger.log_result("所有API都失败", f"无法获取IP {ip_address} 的ZIP码")
        return None

    async def _try_api(
        self, client: httpx.AsyncClient, api_url: str, ip_address: str
    ) -> Optional[str]:
        """尝试使用特定的API获取ZIP码"""
        url = api_url.format(ip=ip_address)

        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return self._extract_zip_from_response(data, api_url)
            else:
                logger.log_result(
                    "API请求失败", f"状态码: {response.status_code}"
                )
                return None
        except Exception as e:
            logger.log_result("API请求异常", str(e))
            return None

    def _extract_zip_from_response(
        self, data: Dict[str, Any], api_url: str
    ) -> Optional[str]:
        """从API响应中提取ZIP码"""
        try:
            # ip-api.com 格式
            if "ip-api.com" in api_url:
                if data.get("status") == "success":
                    zip_code = data.get("zip")
                    if zip_code:
                        return str(zip_code)

            # ipapi.co 格式
            elif "ipapi.co" in api_url:
                zip_code = data.get("postal")
                if zip_code:
                    return str(zip_code)

            # ipgeolocation.io 格式
            elif "ipgeolocation.io" in api_url:
                zip_code = data.get("zipcode")
                if zip_code:
                    return str(zip_code)

            logger.log_result("无法提取ZIP码", f"API响应: {data}")
            return None

        except Exception as e:
            logger.log_result("解析API响应出错", str(e))
            return None

    def _is_private_ip(self, ip_address: str) -> bool:
        """检查是否为私有IP地址"""
        try:
            parts = ip_address.split(".")
            if len(parts) != 4:
                return True

            first_octet = int(parts[0])
            second_octet = int(parts[1])

            # 私有IP地址范围
            if first_octet == 10:
                return True
            elif first_octet == 172 and 16 <= second_octet <= 31:
                return True
            elif first_octet == 192 and second_octet == 168:
                return True
            elif first_octet == 127:  # 本地回环
                return True

            return False
        except (ValueError, IndexError):
            return True

    async def get_location_info(
        self, ip_address: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取IP地址的完整地理位置信息

        Args:
            ip_address: IP地址

        Returns:
            包含地理位置信息的字典
        """
        if not ip_address or ip_address == "unknown":
            return None

        if self._is_private_ip(ip_address):
            # 开发环境：如果是本地回环地址，返回默认的地理位置信息
            if ip_address == "127.0.0.1":
                logger.log_result("开发环境检测", "使用默认地理位置: 多伦多")
                return {
                    "ip": "127.0.0.1",
                    "country": "Canada",
                    "country_code": "CA",
                    "region": "Ontario",
                    "city": "Toronto",
                    "zip": "M5V",
                    "latitude": 43.6532,
                    "longitude": -79.3832,
                    "timezone": "America/Toronto",
                }
            return None

        client = await self._get_client()
        api_url = self.api_urls[0]  # 使用ip-api.com，它提供最完整的信息
        url = api_url.format(ip=ip_address)

        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "ip": data.get("query"),
                        "country": data.get("country"),
                        "country_code": data.get("countryCode"),
                        "region": data.get("regionName"),
                        "city": data.get("city"),
                        "zip": data.get("zip"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "timezone": data.get("timezone"),
                    }
        except Exception as e:
            logger.log_result("获取地理位置信息失败", str(e))

        return None


# 全局实例
ip_to_zip_service = IPToZipService()
