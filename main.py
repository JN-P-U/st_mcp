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


def get_env_var(var_name, prompt=None):
    """환경 변수를 가져오거나 사용자에게 입력을 요청합니다."""
    value = os.environ.get(var_name)
    if not value and prompt:
        value = input(prompt)
        # 입력받은 값을 환경 변수에 설정
        os.environ[var_name] = value
    return value


def setup_environment():
    """필요한 환경 변수를 설정합니다."""
    # OpenAI API 키 설정
    get_env_var("OPENAI_API_KEY", "OpenAI API 키를 입력하세요: ")

    # MCP API 키 설정
    get_env_var("MCP_API_KEY", "MCP API 키를 입력하세요: ")

    # MCP API URL 설정 (기본값)
    os.environ["MCP_API_URL"] = "https://server.smithery.ai/@JN-P-U/st_mcp"

    # MCP 스토리지 경로 설정 (기본값)
    os.environ["MCP_STORAGE_PATH"] = "/mcp/storage"


def main():
    """메인 함수"""
    try:
        # 환경 변수 설정
        setup_environment()

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
