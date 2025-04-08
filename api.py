import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from mcp_stock_analysis import MCPStockAnalyzer

app = FastAPI(title="MCP Stock Analysis API")
analyzer = MCPStockAnalyzer()


class StockAnalysisRequest(BaseModel):
    stock_code: str


class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/")
async def root():
    return {"status": "ready", "service": "MCP Stock Analysis"}


@app.get("/tools/list")
async def list_tools() -> Dict[str, List[Tool]]:
    tools = [
        Tool(
            name="analyze_stock",
            description="주식 종합 분석을 수행합니다",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "분석할 주식 종목 코드 (예: 005930)",
                    }
                },
                "required": ["stock_code"],
            },
        ),
        Tool(
            name="analyze_technical",
            description="주식의 기술적 분석을 수행합니다",
            parameters={
                "type": "object",
                "properties": {
                    "stock_code": {
                        "type": "string",
                        "description": "분석할 주식 종목 코드 (예: 005930)",
                    }
                },
                "required": ["stock_code"],
            },
        ),
    ]
    return {"tools": tools}


@app.post("/analyze")
async def analyze_stock(request: StockAnalysisRequest) -> Dict[str, Any]:
    try:
        result = analyzer.analyze_technical(request.stock_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
