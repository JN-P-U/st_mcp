from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from stock_integrated_analysis import analyze_stock

app = FastAPI(title="Stock Analysis API")


class AnalysisRequest(BaseModel):
    stock_code: str
    openai_api_key: str
    dart_api_key: str
    mcp_api_key: str


@app.post("/analyze")
async def analyze_stock_endpoint(request: AnalysisRequest):
    try:
        result = analyze_stock(
            request.stock_code,
            request.openai_api_key,
            request.dart_api_key,
            request.mcp_api_key,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
