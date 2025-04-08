#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
주식 통합 분석 도구
재무 분석과 기술적 분석을 결합하고 OpenAI API를 활용하여 종합적인 주식 분석을 제공합니다.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import openai
from dotenv import load_dotenv
from financial_analysis import analyze_financial_statements, fetch_corp_codes
from stock_technical_analysis import analyze_technical

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# API 키 설정
openai_api_key = os.getenv("OPENAI_API_KEY")
dart_api_key = os.getenv("DART_API_KEY")
mcp_api_key = os.getenv("MCP_API_KEY")

if not openai_api_key:
    print(
        "경고: OPENAI_API_KEY가 설정되지 않았습니다. AI 분석 기능이 작동하지 않을 수 있습니다."
    )
else:
    openai.api_key = openai_api_key

if not dart_api_key:
    print(
        "경고: DART_API_KEY가 설정되지 않았습니다. 재무제표 분석 기능이 작동하지 않을 수 있습니다."
    )

if not mcp_api_key:
    print(
        "경고: MCP_API_KEY가 설정되지 않았습니다. 주가 차트 생성 기능이 작동하지 않을 수 있습니다."
    )


class StockAnalysis:
    """주식 분석 클래스"""

    def __init__(
        self, stock_code: str, openai_api_key: str, dart_api_key: str, mcp_api_key: str
    ):
        """
        주식 분석 클래스를 초기화합니다.

        Args:
            stock_code (str): 주식 코드
            openai_api_key (str): OpenAI API 키
            dart_api_key (str): DART API 키
            mcp_api_key (str): MCP API 키
        """
        self.stock_code = stock_code
        self.openai_api_key = openai_api_key
        self.dart_api_key = dart_api_key
        self.mcp_api_key = mcp_api_key

        # API 키 설정
        openai.api_key = openai_api_key
        os.environ["DART_API_KEY"] = dart_api_key
        os.environ["MCP_API_KEY"] = mcp_api_key

        # 분석 결과 초기화
        self.stock_name = "Unknown"
        self.technical_analysis = {}
        self.financial_analysis = {}
        self.ai_analysis = {}

        # 분석 수행
        self._analyze()

    def _analyze(self):
        """주식 분석을 수행합니다."""
        try:
            # 기업명 가져오기
            try:
                companies_df = fetch_corp_codes(self.dart_api_key)
                if not companies_df.empty:
                    matches = companies_df[
                        companies_df["stock_code"] == self.stock_code
                    ]
                    if not matches.empty:
                        self.stock_name = matches.iloc[0]["corp_name"]
            except Exception as e:
                logger.error(f"기업명 가져오기 실패: {e}")

            # 기술적 분석 수행
            self.technical_analysis = analyze_technical(self.stock_code)

            # 재무 분석 수행
            try:
                self.financial_analysis = analyze_financial_statements(
                    self.stock_code, self.dart_api_key
                )
            except Exception as e:
                logger.error(f"재무제표 분석 실패: {e}")
                self.financial_analysis = {
                    "error": "재무제표 데이터를 가져올 수 없습니다."
                }

            # AI 기반 종합 분석 수행
            self.ai_analysis = get_ai_analysis(
                self.stock_code,
                self.technical_analysis,
                self.financial_analysis,
                self.openai_api_key,
            )
        except Exception as e:
            logger.error(f"주식 분석 실패: {e}")

    def generate_chart(self) -> str:
        """
        주식 차트를 생성합니다.

        Returns:
            str: 차트 파일 경로
        """
        try:
            # 차트 생성 로직 구현
            return ""
        except Exception as e:
            logger.error(f"차트 생성 실패: {e}")
            return ""

    def save_analysis(self) -> str:
        """
        분석 결과를 파일로 저장합니다.

        Returns:
            str: 결과 파일 경로
        """
        try:
            # 결과 저장 로직 구현
            return ""
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
            return ""


def get_ai_analysis(
    stock_code: str,
    technical_result: Dict[str, Any],
    financial_result: Dict[str, Any],
    openai_api_key: str,
) -> Dict[str, Any]:
    """
    OpenAI API를 사용하여 종합적인 주식 분석을 제공합니다.

    Args:
        stock_code (str): 주식 코드
        technical_result (dict): 기술적 분석 결과
        financial_result (dict): 재무 분석 결과
        openai_api_key (str): OpenAI API 키

    Returns:
        dict: AI 분석 결과
    """
    try:
        # DataFrame을 문자열로 변환
        analysis_data = {
            "stock_code": stock_code,
            "technical_analysis": str(technical_result),
            "financial_analysis": str(financial_result),
        }

        # OpenAI API 호출
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "주식 분석 전문가로서 주어진 데이터를 바탕으로 종합적인 분석을 제공해주세요.",
                },
                {
                    "role": "user",
                    "content": f"다음 주식 데이터를 분석해주세요: {json.dumps(analysis_data, ensure_ascii=False)}",
                },
            ],
        )

        return {"analysis": response.choices[0].message.content}
    except Exception as e:
        logger.error(f"AI 분석 중 오류 발생: {e}")
        return {"error": f"AI 분석 실패: {str(e)}"}


def analyze_stock(
    stock_code: str,
    openai_api_key: str,
    dart_api_key: str,
    mcp_api_key: str,
) -> Dict[str, Any]:
    """
    주식 분석을 수행합니다.

    Args:
        stock_code (str): 주식 코드
        openai_api_key (str): OpenAI API 키
        dart_api_key (str): DART API 키
        mcp_api_key (str): MCP API 키

    Returns:
        Dict[str, Any]: 분석 결과
    """
    try:
        # 주식 분석 수행
        analysis = StockAnalysis(stock_code, openai_api_key, dart_api_key, mcp_api_key)
        chart_path = analysis.generate_chart()
        result_path = analysis.save_analysis()

        return {
            "stock_code": stock_code,
            "stock_name": analysis.stock_name,
            "technical_analysis": analysis.technical_analysis,
            "financial_analysis": analysis.financial_analysis,
            "ai_analysis": analysis.ai_analysis,
            "chart_path": chart_path,
            "result_path": result_path,
        }
    except Exception as e:
        logger.error(f"주식 분석 실패: {e}")
        return {
            "stock_code": stock_code,
            "stock_name": "Unknown",
            "technical_analysis": {},
            "financial_analysis": {},
            "ai_analysis": "주식 분석을 수행할 수 없습니다.",
            "chart_path": "",
            "result_path": "",
        }


def save_analysis_result(
    stock_code: str,
    stock_name: str,
    technical_analysis: Dict[str, Any],
    financial_analysis: Dict[str, Any],
    ai_analysis: Dict[str, Any],
) -> str:
    """
    분석 결과를 파일로 저장합니다.

    Args:
        stock_code (str): 주식 코드
        stock_name (str): 종목명
        technical_analysis (dict): 기술적 분석 결과
        financial_analysis (dict): 재무 분석 결과
        ai_analysis (dict): AI 분석 결과

    Returns:
        str: 저장된 파일 경로
    """
    # 결과 디렉토리 설정
    output_dir = "/mcp/result"
    os.makedirs(output_dir, exist_ok=True)

    # 현재 날짜를 파일명에 포함
    current_date = datetime.now().strftime("%Y%m%d")
    filename = f"{stock_name}({stock_code})_{current_date}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        # 파일 첫 줄에 종목명(종목코드) 출력
        f.write(f"{stock_name}({stock_code})\n\n")

        # 기술적 분석 결과
        f.write("=== 기술적 분석 ===\n")
        if isinstance(technical_analysis, dict) and "error" in technical_analysis:
            f.write(f"오류: {technical_analysis['error']}\n")
        else:
            for indicator, value in technical_analysis.items():
                f.write(f"{indicator}: {value}\n")

        # 재무 분석 결과
        f.write("\n=== 재무 분석 ===\n")
        if isinstance(financial_analysis, dict) and "error" in financial_analysis:
            f.write(f"오류: {financial_analysis['error']}\n")
        else:
            if isinstance(financial_analysis, dict):
                if "balance_sheet" in financial_analysis:
                    f.write("\n[재무상태표]\n")
                    f.write(str(financial_analysis["balance_sheet"]))
                    f.write("\n")

                if "income_statement" in financial_analysis:
                    f.write("\n[손익계산서]\n")
                    f.write(str(financial_analysis["income_statement"]))
                    f.write("\n")

                if "financial_health" in financial_analysis:
                    f.write("\n[재무건전성]\n")
                    for key, value in financial_analysis["financial_health"].items():
                        f.write(f"{key}: {value}\n")

        # AI 분석 결과
        f.write("\n=== AI 분석 ===\n")
        if isinstance(ai_analysis, dict) and "error" in ai_analysis:
            f.write(f"오류: {ai_analysis['error']}\n")
        else:
            f.write(str(ai_analysis))

    return filepath


def main():
    try:
        # API 키 입력
        print("API 키를 입력해주세요.")
        sys.stdout.flush()
        openai_api_key = input("OpenAI API 키: ").strip()
        sys.stdout.flush()
        dart_api_key = input("DART API 키: ").strip()
        sys.stdout.flush()
        mcp_api_key = input("MCP API 키: ").strip()
        sys.stdout.flush()

        # OpenAI API 키 설정
        openai.api_key = openai_api_key

        # 분석할 종목 코드 입력
        print("\n분석할 종목 코드를 입력해주세요.")
        sys.stdout.flush()
        stock_code = input("종목 코드 (예: 005930): ").strip()
        sys.stdout.flush()

        # 주식 종합 분석 수행
        result = analyze_stock(stock_code, openai_api_key, dart_api_key, mcp_api_key)

        # 분석 결과 저장
        filepath = save_analysis_result(
            stock_code,
            result["stock_name"],
            result["technical_analysis"],
            result["financial_analysis"],
            result["ai_analysis"],
        )

        print(f"\n분석 결과가 저장되었습니다: {filepath}")
        return result
    except EOFError:
        print("입력이 중단되었습니다.")
        return None
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
        return None


if __name__ == "__main__":
    main()
