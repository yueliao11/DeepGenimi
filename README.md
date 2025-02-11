<div align="center">
<h1>DeepGenimi 🐬🧠 - OpenAI Compatible</h1>
<p>Combining DeepSeek and Gemini Pro for Enhanced AI Capabilities</p>
<p>结合 DeepSeek 和 Gemini Pro 实现增强型 AI 能力</p>


# Introduction / 简介

Spec Thanks to DeepClaude
DeepGenimi is an innovative project that combines the powerful reasoning capabilities of DeepSeek with the natural language generation abilities of Google's Gemini Pro. This combination creates a unique synergy that enhances the overall AI performance.

DeepGenimi 是一个创新项目，它将 DeepSeek 的强大推理能力与 Google Gemini Pro 的自然语言生成能力相结合。这种组合创造了独特的协同效应，提升了 AI 的整体表现。

# Features / 特性

## Two-Stage Processing / 两阶段处理
- DeepSeek handles the reasoning process / DeepSeek 负责推理过程
- Gemini Pro generates natural responses / Gemini Pro 生成自然回应

## Streaming Support / 流式输出支持
- Real-time reasoning visualization / 实时推理过程可视化
- Efficient response generation / 高效的响应生成

## OpenAI Compatible API / OpenAI 兼容接口
- Easy integration with existing tools / 易于集成到现有工具
- Standard streaming response format / 标准的流式响应格式

# Quick Start / 快速开始

## Prerequisites / 前置要求
1. Python 3.11+
2. DeepSeek API Key
3. Google Gemini Pro API Key

## Installation / 安装

```bash
# Clone the repository
git clone https://github.com/yueliao11/DeepGenimi.git
cd DeepGenimi

# Install dependencies using uv (recommended)
uv sync

# Activate virtual environment
# For macOS/Linux
source .venv/bin/activate
# For Windows
.venv\Scripts\activate
```

## Configuration / 配置

```bash
# Copy environment variables template
cp .env.example .env

# Edit .env file with your API keys and settings
vim .env
```

## Running / 运行

```bash
uvicorn app.main:app --reload
```

# Thanks to / 鸣谢

- [deepresearcher.site](https://deepresearcher.site/)
- [DeepClaude](https://github.com/ErlichLiu/DeepClaude)
- [Gemini Pro](https://generativelanguage.googleapis.com/)
- [uv](https://github.com/microsoft/uv)
- [DeepSeek](https://ai.com/)

