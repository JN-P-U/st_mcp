import json
from typing import Any, Dict, List

from aiohttp import web
from jsonrpcserver import async_dispatch as dispatch
from jsonrpcserver import method

from mcp_stock_analysis import MCPStockAnalyzer

analyzer = MCPStockAnalyzer()


@method
async def initialize() -> Dict[str, Any]:
    """Smithery.ai 서버 초기화 메서드"""
    return {
        "capabilities": {
            "tools": [
                {
                    "name": "analyze_stock",
                    "description": "주식 종합 분석을 수행합니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "stock_code": {
                                "type": "string",
                                "description": "분석할 주식 종목 코드 (예: 005930)",
                            }
                        },
                        "required": ["stock_code"],
                    },
                },
                {
                    "name": "analyze_technical",
                    "description": "주식의 기술적 분석을 수행합니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "stock_code": {
                                "type": "string",
                                "description": "분석할 주식 종목 코드 (예: 005930)",
                            }
                        },
                        "required": ["stock_code"],
                    },
                },
            ],
            "resources": {
                "memory": "512MB",
                "cpu": "1",
            },
            "prompts": {
                "system": "주식 분석 AI 서비스입니다. 기술적 분석과 종합 분석을 제공합니다.",
                "user": "주식 종목 코드를 입력하면 분석 결과를 제공합니다.",
            },
        }
    }


@method
async def tools_list() -> Dict[str, List[Dict[str, Any]]]:
    """Smithery.ai에서 요구하는 도구 목록을 반환합니다"""
    return {
        "tools": [
            {
                "name": "analyze_stock",
                "description": "주식 종합 분석을 수행합니다",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "분석할 주식 종목 코드 (예: 005930)",
                        }
                    },
                    "required": ["stock_code"],
                },
            },
            {
                "name": "analyze_technical",
                "description": "주식의 기술적 분석을 수행합니다",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "분석할 주식 종목 코드 (예: 005930)",
                        }
                    },
                    "required": ["stock_code"],
                },
            },
        ]
    }


@method
async def analyze_stock(stock_code: str) -> Dict[str, Any]:
    """주식 분석을 수행하는 메서드"""
    try:
        result = analyzer.analyze_technical(stock_code)
        return result
    except Exception as e:
        return {"error": str(e)}


async def handle(request):
    """JSON-RPC 요청을 처리하는 핸들러"""
    request_text = await request.text()
    response = await dispatch(request_text)
    return web.Response(text=str(response), content_type="application/json")


app = web.Application()
app.router.add_post("/", handle)

if __name__ == "__main__":
    web.run_app(app, port=8000)
