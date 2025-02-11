"""DeepClaude 服务，用于协调 DeepSeek 和 Gemini API 的调用"""
import json
import time
import asyncio
from typing import AsyncGenerator
from app.utils.logger import logger
from app.clients import DeepSeekClient, GeminiClient


class DeepGenimi:
    """处理 DeepSeek 和 Gemini API 的流式输出衔接"""

    def __init__(self, deepseek_api_key: str, gemini_api_key: str, 
                 deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions", 
                 gemini_api_url: str = "https://api.gemini.com/v1/messages",
                 gemini_provider: str = "gemini",
                 is_origin_reasoning: bool = True):
        """初始化 API 客户端
        
        Args:
            deepseek_api_key: DeepSeek API密钥
            gemini_api_key: Gemini API密钥
        """
        self.deepseek_client = DeepSeekClient(deepseek_api_key, deepseek_api_url)
        self.gemini_client = GeminiClient(gemini_api_key, gemini_api_url)
        self.is_origin_reasoning = is_origin_reasoning

    async def chat_completions_with_stream(
        self,
        messages: list,
        model_arg: tuple[float, float, float, float],
        deepseek_model: str = "deepseek-reasoner",
        gemini_model: str = "gemini-3-5-sonnet-20241022"
    ) -> AsyncGenerator[bytes, None]:
        """处理完整的流式输出过程
        
        Args:
            messages: 初始消息列表
            model_arg: 模型参数
            deepseek_model: DeepSeek 模型名称
            gemini_model: Gemini 模型名称
            
        Yields:
            字节流数据，格式如下：
            {
                "id": "chatcmpl-xxx",
                "object": "chat.completion.chunk",
                "created": timestamp,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "reasoning_content": reasoning_content,
                        "content": content
                    }
                }]
            }
        """
        # 生成唯一的会话ID和时间戳
        chat_id = f"chatcmpl-{hex(int(time.time() * 1000))[2:]}"
        created_time = int(time.time())

        # 创建队列，用于收集输出数据
        output_queue = asyncio.Queue()
        # 队列，用于传递 DeepSeek 推理内容给 Gemini
        gemini_queue = asyncio.Queue()

        # 用于存储 DeepSeek 的推理累积内容
        reasoning_content = []

        async def process_deepseek():
            logger.info(f"开始处理 DeepSeek 流，使用模型：{deepseek_model}, 提供商: {self.deepseek_client.provider}")
            try:
                async for content_type, content in self.deepseek_client.stream_chat(
                    messages=messages,
                    model=deepseek_model,
                    temperature=model_arg[0],
                    top_p=model_arg[1],
                    presence_penalty=model_arg[2],
                    frequency_penalty=model_arg[3]
                ):
                    if content_type == "reasoning":
                        reasoning_content.append(content)
                        response = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": deepseek_model,
                            "choices": [{
                                "index": 0,
                                "delta": {
                                    "role": "assistant",
                                    "reasoning_content": content,
                                    "content": ""
                                }
                            }]
                        }
                        await output_queue.put(f"data: {json.dumps(response)}\n\n".encode('utf-8'))
                    elif content_type == "content":
                        # 当收到 content 类型时，将完整的推理内容发送到 gemini_queue，并结束 DeepSeek 流处理
                        logger.info(f"DeepSeek 推理完成，收集到的推理内容长度：{len(''.join(reasoning_content))}")
                        await gemini_queue.put("".join(reasoning_content))
                        break
            except Exception as e:
                logger.error(f"处理 DeepSeek 流时发生错误: {e}")
            finally:
                # 确保释放队列资源
                await gemini_queue.put(None)
                await output_queue.put(None)
                logger.info("DeepSeek处理流程资源已释放")
            # 用 None 标记 DeepSeek 任务结束
            logger.info("DeepSeek 任务处理完成，标记结束")
            await output_queue.put(None)

        async def process_gemini():
            try:
                logger.info("等待获取 DeepSeek 的推理内容...")
                while True:
                    reasoning = await gemini_queue.get()
                    if reasoning is None:
                        logger.info("收到队列结束标记，停止处理")
                        break
                    logger.debug(f"获取到推理内容，内容长度：{len(reasoning) if reasoning else 0}")
                    if not reasoning:
                        logger.warning("未能获取到有效的推理内容，将使用默认提示继续")
                        reasoning = "获取推理内容失败"
                    # 构造 Gemini 的输入消息
                    gemini_messages = messages.copy()
                    gemini_messages.append({
                        "role": "assistant",
                        "content": f"Here's my reasoning process:\n{reasoning}\n\nBased on this reasoning, I will now provide my response:"
                    })
                    # 处理可能 messages 内存在 role = system 的情况，如果有，则去掉当前这一条的消息对象
                    gemini_messages = [message for message in gemini_messages if message.get("role", "") != "system"]

                    logger.info(f"开始处理 Gemini 流，使用模型: {gemini_model}, 提供商: {self.gemini_client.provider}")

                    async for content_type, content in self.gemini_client.stream_chat(
                        messages=gemini_messages,
                        model_arg=model_arg,
                        model=gemini_model,
                    ):
                        if content_type == "answer":
                            response = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created_time,
                                "model": gemini_model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "content": content
                                    }
                                }]
                            }
                            await output_queue.put(f"data: {json.dumps(response)}\n\n".encode('utf-8'))
            finally:
                await output_queue.put(None)
        
        # 创建并发任务
        deepseek_task = asyncio.create_task(process_deepseek())
        gemini_task = asyncio.create_task(process_gemini())
        
        # 等待两个任务完成，通过计数判断
        finished_tasks = 0
        while finished_tasks < 2:
            item = await output_queue.get()
            if item is None:
                finished_tasks += 1
            else:
                yield item
        
        # 发送结束标记
        yield b'data: [DONE]\n\n'