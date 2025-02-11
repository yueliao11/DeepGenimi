import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.utils.logger import logger
from app.utils.auth import verify_api_key
from app.deepgenimi.deepgenimi import DeepGenimi

app = FastAPI(title="DeepGenimi API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request details
    logger.debug(f"[REQUEST_START] {request.method} {request.url}")
    logger.debug(f"[REQUEST_HEADERS] {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Log response details
        logger.debug(
            f"[REQUEST_COMPLETE] {request.method} {request.url} | "
            f"Processing Time: {process_time:.2f}ms | "
            f"Status Code: {response.status_code}"
        )
        return response
    except Exception as e:
        logger.error(f"[REQUEST_ERROR] {str(e)}")
        logger.error("Request error details:", exc_info=True)
        raise

# Get CORS configuration, API keys, URLs and model names from environment variables
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_PROVIDER = os.getenv("GEMINI_PROVIDER", "google") # Gemini模型提供商, 默认为google
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:streamGenerateContent")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL")

IS_ORIGIN_REASONING = os.getenv("IS_ORIGIN_REASONING", "True").lower() == "true"

# CORS设置
allow_origins_list = ALLOW_ORIGINS.split(",") if ALLOW_ORIGINS else [] # 将逗号分隔的字符串转换为列表

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建 DeepGenimi 实例, 提出为Global变量
if not DEEPSEEK_API_KEY or not GEMINI_API_KEY:
    logger.critical("请设置环境变量 GEMINI_API_KEY 和 DEEPSEEK_API_KEY")
    sys.exit(1)

deep_genimi = DeepGenimi(
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY,
    DEEPSEEK_API_URL,
    GEMINI_API_URL,
    GEMINI_PROVIDER,
    IS_ORIGIN_REASONING
)

# 验证日志级别
logger.debug("当前日志级别为 DEBUG")
logger.info("开始请求")

@app.get("/", dependencies=[Depends(verify_api_key)])
async def root():
    logger.info("访问了根路径")
    return {"message": "Welcome to DeepGenimi API"}

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(request: Request):
    """Handle chat completion request and return streaming response
    
    Request body should be compatible with OpenAI API format, including:
    - messages: List of messages
    - model: Model name (optional)
    - stream: Whether to use streaming output (must be True)
    - temperature: Randomness (optional)
    - top_p: Top-p sampling (optional)
    - presence_penalty: Topic freshness (optional)
    - frequency_penalty: Frequency penalty (optional)
    """

    try:
        # 1. Get basic information
        body = await request.json()
        messages = body.get("messages")

        # 2. Get and validate parameters
        model_arg = (
            get_and_validate_params(body)
        )

        # 3. Return streaming response
        return StreamingResponse(
            deep_genimi.chat_completions_with_stream(
                messages=messages,
                model_arg=model_arg,
                deepseek_model=DEEPSEEK_MODEL,
                gemini_model=GEMINI_MODEL
            ),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {"error": str(e)}


def get_and_validate_params(body):
    """Function to extract and validate request parameters"""
    # TODO: Allow customization of default values
    temperature: float = body.get("temperature", 0.5)
    top_p: float = body.get("top_p", 0.9)
    presence_penalty: float = body.get("presence_penalty", 0.0)
    frequency_penalty: float = body.get("frequency_penalty", 0.0)

    if not body.get("stream", False):
        raise ValueError("Currently only supports streaming output, stream must be True")

    if "sonnet" in body.get("model", ""): # For Sonnet models, temperature must be between 0 and 1
        if not isinstance(temperature, (float)) or temperature < 0.0 or temperature > 1.0:
            raise ValueError("For Sonnet models, temperature must be between 0 and 1")

    return (temperature, top_p, presence_penalty, frequency_penalty)
