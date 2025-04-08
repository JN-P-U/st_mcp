#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys

from stock_integrated_analysis import analyze_stock


def main():
    try:
        # STDIN에서 입력 읽기
        input_data = json.loads(sys.stdin.read())

        # API 키 설정
        openai_api_key = input_data.get("openai_api_key")
        dart_api_key = input_data.get("dart_api_key")
        mcp_api_key = input_data.get("mcp_api_key")

        # 종목 코드 가져오기
        stock_code = input_data.get("stock_code")

        if not all([openai_api_key, dart_api_key, mcp_api_key, stock_code]):
            print(json.dumps({"error": "필수 파라미터가 누락되었습니다."}))
            return

        # 주식 분석 수행
        result = analyze_stock(stock_code, openai_api_key, dart_api_key, mcp_api_key)

        # 결과 출력
        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
