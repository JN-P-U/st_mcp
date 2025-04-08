#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP 기반 주식 분석 시스템
"""

import logging
import os
import sys

from st_mcp import analyze_stock

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 환경 변수 확인
required_env_vars = ["OPENAI_API_KEY", "MCP_API_KEY", "MCP_API_URL", "MCP_STORAGE_PATH"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    logger.error(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
    sys.exit(1)


def main():
    """메인 함수"""
    try:
        # 주식 코드 입력
        stock_code = input("분석할 주식 코드를 입력하세요: ")

        # 주식 분석 수행
        result = analyze_stock(stock_code)

        # 분석 결과 출력
        print(f"\n주식 코드: {result['stock_code']}")
        print(f"회사명: {result['stock_name']}")
        print("\n기술적 분석 결과:")
        for key, value in result["technical_analysis"].items():
            print(f"- {key}: {value}")
        print("\n재무 분석 결과:")
        for key, value in result["financial_analysis"].items():
            print(f"- {key}: {value}")
        print("\nAI 기반 종합 분석 결과:")
        print(result["ai_analysis"])
        print(f"\n차트 파일 경로: {result['chart_path']}")
        print(f"분석 결과 파일 경로: {result['result_path']}")
    except Exception as e:
        logger.error(f"주식 분석 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
