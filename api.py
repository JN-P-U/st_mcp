import json
import logging
import sys
from typing import Any, Dict, List, Optional

from aiohttp import web
from fastapi import FastAPI
from jsonrpcserver import async_dispatch as dispatch
from jsonrpcserver import method

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

try:
    from mcp_stock_analysis import MCPStockAnalyzer

    logger.info("MCPStockAnalyzer 모듈을 성공적으로 가져왔습니다.")
except Exception as e:
    logger.error(f"MCPStockAnalyzer 모듈을 가져오는 중 오류 발생: {e}")
    raise

# 전역 변수로 analyzer 선언
analyzer: Optional[MCPStockAnalyzer] = None


def get_analyzer() -> MCPStockAnalyzer:
    """필요할 때만 analyzer를 초기화하여 반환합니다"""
    global analyzer
    if analyzer is None:
        try:
            logger.info("MCPStockAnalyzer 초기화 중...")
            analyzer = MCPStockAnalyzer()
            logger.info("MCPStockAnalyzer 초기화 완료")
        except Exception as e:
            logger.error(f"MCPStockAnalyzer 초기화 중 오류 발생: {e}")
            raise
    return analyzer


@method
async def initialize() -> Dict[str, Any]:
    """Smithery.ai 서버 초기화 메서드"""
    logger.info("initialize 메서드 호출됨")
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
    logger.info("tools_list 메서드 호출됨")
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
    logger.info(f"analyze_stock 메서드 호출됨: stock_code={stock_code}")
    try:
        # 실제 분석이 필요할 때만 analyzer 초기화
        analyzer = get_analyzer()
        result = analyzer.analyze_technical(stock_code)
        logger.info(f"분석 완료: {stock_code}")
        return result
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")
        return {"error": str(e)}


async def handle(request):
    """JSON-RPC 요청을 처리하는 핸들러"""
    try:
        request_text = await request.text()
        logger.info(f"요청 수신: {request_text[:100]}...")
        response = await dispatch(request_text)
        logger.info(f"응답 전송: {str(response)[:100]}...")
        return web.Response(text=str(response), content_type="application/json")
    except Exception as e:
        logger.error(f"요청 처리 중 오류 발생: {e}")
        return web.Response(
            text=json.dumps(
                {"jsonrpc": "2.0", "error": {"message": str(e)}, "id": None}
            ),
            content_type="application/json",
            status=500,
        )


# aiohttp 앱
aiohttp_app = web.Application()
aiohttp_app.router.add_post("/", handle)

# FastAPI 앱 (Smithery.ai용)
app = FastAPI(title="MCP Stock Analysis API")


@app.get("/")
async def root():
    return {"status": "ready", "service": "MCP Stock Analysis"}


@app.post("/jsonrpc")
async def jsonrpc(request: dict):
    """JSON-RPC 요청을 처리하는 엔드포인트"""
    try:
        method_name = request.get("method")
        params = request.get("params", {})

        if method_name == "initialize":
            return await initialize()
        elif method_name == "tools_list":
            return await tools_list()
        elif method_name == "analyze_stock":
            stock_code = params.get("stock_code")
            if not stock_code:
                return {"error": "stock_code is required"}
            return await analyze_stock(stock_code)
        else:
            return {"error": f"Unknown method: {method_name}"}
    except Exception as e:
        logger.error(f"JSON-RPC 처리 중 오류 발생: {e}")
        return {"error": str(e)}


# 로컬에서 실행할 때 사용할 클라이언트 함수
def call_local_api(
    method: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """로컬 API를 호출하는 함수"""
    import requests

    response = requests.post(
        "http://localhost:8000/",
        json={"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1},
    )
    return response.json()


if __name__ == "__main__":
    logger.info("주식 분석 API 서버가 시작되었습니다.")
    logger.info("사용 예시:")
    logger.info("  result = call_local_api('analyze_stock', {'stock_code': '005930'})")
    logger.info("  print(result)")
    web.run_app(aiohttp_app, host="0.0.0.0", port=8000)
