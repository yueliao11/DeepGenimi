"""基础客户端类，定义通用接口"""
from typing import AsyncGenerator, Any
import aiohttp
from app.utils.logger import logger
from abc import ABC, abstractmethod


class BaseClient(ABC):
    def __init__(self, api_key: str, api_url: str):
        logger.debug(f"[初始化客户端] 正在初始化 {self.__class__.__name__} | API地址: {api_url}")
        logger.debug(f"[Debug] Initializing {self.__class__.__name__} | API endpoint: {api_url}")
        """初始化基础客户端
        
        Args:
            api_key: API密钥
            api_url: API地址
        """
        self.api_key = api_key
        self.api_url = api_url
        
    async def _make_request(self, headers: dict, data: dict) -> AsyncGenerator[bytes, None]:
        logger.debug(f"[准备请求] 发送请求到API | 请求头: {headers}")
        logger.debug(f"[准备请求] 请求数据: {json.dumps(data, ensure_ascii=False)}")
        logger.debug(f"[Debug] Sending request | Headers: {headers}")
        logger.debug(f"[Debug] Request data: {json.dumps(data, ensure_ascii=False)}")
        """发送请求并处理响应
        
        Args:
            headers: 请求头
            data: 请求数据
            
        Yields:
            bytes: 原始响应数据
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API 请求失败: {error_text}")
                        return
                        
                    async for chunk in response.content.iter_any():
                        yield chunk
                        
        except Exception as e:
            logger.error(f"请求 API 时发生错误: {e}")
            
    @abstractmethod
    async def stream_chat(self, messages: list, model: str) -> AsyncGenerator[tuple[str, str], None]:
        """流式对话，由子类实现
        
        Args:
            messages: 消息列表
            model: 模型名称
            
        Yields:
            tuple[str, str]: (内容类型, 内容)
        """
        pass
