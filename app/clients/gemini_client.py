import google.generativeai as genai
from typing import AsyncGenerator
from app.clients.base_client import BaseClient

class GeminiClient(BaseClient):
    """Google Gemini Pro客户端实现"""
    
    def __init__(self, api_key: str, api_url: str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:streamGenerateContent"):
        super().__init__(api_key, api_url)
        genai.configure(api_key=api_key)
        self.model_name = "gemini-pro"
        
    async def stream_chat(self, messages: list, model: str, **kwargs) -> AsyncGenerator[dict, None]:
        try:
            model = genai.GenerativeModel(self.model_name)
            chat = model.start_chat(history=[])
            
            response = chat.send_message(
                content=self._format_messages(messages),
                stream=True,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2048,
                    temperature=0.7
                )
            )
            
            async for chunk in response:
                yield {
                    "content": chunk.text,
                    "finish_reason": chunk.candidates[0].finish_reason.value
                }
                
        except Exception as e:
            self.logger.error(f"Gemini API错误: {str(e)}")
            yield {"error": str(e)}
            
    def _format_messages(self, messages: list) -> str:
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
