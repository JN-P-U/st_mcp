import json
import logging
import sys
from typing import Any, Dict, List, Optional

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
                }
            ]
        }
    }


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
            }
        ]
    }


async def analyze_stock(stock_code: str) -> Dict[str, Any]:
    """주식 분석을 수행하는 메서드"""
    logger.info(f"analyze_stock 메서드 호출됨: stock_code={stock_code}")
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze_technical(stock_code)
        logger.info(f"분석 완료: {stock_code}")
        return result
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")
        return {"error": str(e)}


async def handle_request(request_text: str) -> str:
    """JSON-RPC 요청을 처리하는 핸들러"""
    try:
        request = json.loads(request_text)
        logger.info(f"요청 수신: {request}")

        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            result = await initialize()
        elif method == "tools_list":
            result = await tools_list()
        elif method == "analyze_stock":
            stock_code = params.get("stock_code")
            if not stock_code:
                return json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "error": {"message": "stock_code is required"},
                        "id": request.get("id"),
                    }
                )
            result = await analyze_stock(stock_code)
        else:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "error": {"message": f"Unknown method: {method}"},
                    "id": request.get("id"),
                }
            )

        response = {"jsonrpc": "2.0", "result": result, "id": request.get("id")}
        logger.info(f"응답 전송: {response}")
        return json.dumps(response)
    except Exception as e:
        logger.error(f"요청 처리 중 오류 발생: {e}")
        return json.dumps({"jsonrpc": "2.0", "error": {"message": str(e)}, "id": None})


async def main():
    """메인 함수"""
    logger.info("JSON-RPC 서버 시작")
    while True:
        try:
            request_text = input()
            response = await handle_request(request_text)
            print(response, flush=True)
        except EOFError:
            break
        except Exception as e:
            logger.error(f"서버 실행 중 오류 발생: {e}")
            break
    logger.info("JSON-RPC 서버 종료")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
