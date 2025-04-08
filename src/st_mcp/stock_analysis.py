#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP 기반 주식 분석 시스템
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import openai
import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# MCP 환경 설정
MCP_API_KEY = os.getenv("MCP_API_KEY")
MCP_API_URL = os.getenv("MCP_API_URL", "https://api.mcp.example.com")
MCP_STORAGE_PATH = os.getenv("MCP_STORAGE_PATH", "/mcp/storage")

# 한글 폰트 설정
plt.rcParams["font.family"] = "AppleGothic"  # macOS용 한글 폰트
plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지


class StockAnalysis:
    """주식 분석 클래스"""

    def __init__(self, stock_code: str):
        """
        주식 분석 클래스 초기화

        Args:
            stock_code (str): 주식 코드
        """
        self.stock_code = stock_code
        self.stock_name = self._get_stock_name()
        self.stock_data = self._get_stock_data()
        self.financial_data = self._get_financial_data()
        self.technical_analysis = self._perform_technical_analysis()
        self.financial_analysis = self._perform_financial_analysis()
        self.ai_analysis = self._perform_ai_analysis()

    def _get_stock_name(self) -> str:
        """
        주식 코드로 회사명을 조회합니다.

        Returns:
            str: 회사명
        """
        try:
            # MCP API를 통해 회사명 조회
            response = requests.get(
                f"{MCP_API_URL}/company/{self.stock_code}",
                headers={"Authorization": f"Bearer {MCP_API_KEY}"},
            )
            response.raise_for_status()
            return response.json()["name"]
        except Exception as e:
            logger.error(f"회사명 조회 실패: {e}")
            return "Unknown"

    def _get_stock_data(self) -> pd.DataFrame:
        """
        주식 데이터를 조회합니다.

        Returns:
            pd.DataFrame: 주식 데이터
        """
        try:
            # yfinance를 통해 주식 데이터 조회
            stock = yf.Ticker(self.stock_code)
            return stock.history(period="1y")
        except Exception as e:
            logger.error(f"주식 데이터 조회 실패: {e}")
            return pd.DataFrame()

    def _get_financial_data(self) -> Dict[str, Any]:
        """
        재무 데이터를 조회합니다.

        Returns:
            Dict[str, Any]: 재무 데이터
        """
        try:
            # MCP API를 통해 재무 데이터 조회
            response = requests.get(
                f"{MCP_API_URL}/financial/{self.stock_code}",
                headers={"Authorization": f"Bearer {MCP_API_KEY}"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"재무 데이터 조회 실패: {e}")
            return {}

    def _perform_technical_analysis(self) -> Dict[str, Any]:
        """
        기술적 분석을 수행합니다.

        Returns:
            Dict[str, Any]: 기술적 분석 결과
        """
        if self.stock_data.empty:
            return {}

        try:
            # 이동평균 계산
            self.stock_data["MA5"] = self.stock_data["Close"].rolling(window=5).mean()
            self.stock_data["MA20"] = self.stock_data["Close"].rolling(window=20).mean()
            self.stock_data["MA60"] = self.stock_data["Close"].rolling(window=60).mean()

            # RSI 계산
            delta = self.stock_data["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            self.stock_data["RSI"] = 100 - (100 / (1 + rs))

            # MACD 계산
            exp1 = self.stock_data["Close"].ewm(span=12, adjust=False).mean()
            exp2 = self.stock_data["Close"].ewm(span=26, adjust=False).mean()
            self.stock_data["MACD"] = exp1 - exp2
            self.stock_data["Signal"] = (
                self.stock_data["MACD"].ewm(span=9, adjust=False).mean()
            )

            # 볼린저 밴드 계산
            self.stock_data["MA20"] = self.stock_data["Close"].rolling(window=20).mean()
            self.stock_data["STD20"] = self.stock_data["Close"].rolling(window=20).std()
            self.stock_data["Upper"] = (
                self.stock_data["MA20"] + 2 * self.stock_data["STD20"]
            )
            self.stock_data["Lower"] = (
                self.stock_data["MA20"] - 2 * self.stock_data["STD20"]
            )

            # 기술적 분석 결과
            return {
                "MA5": self.stock_data["MA5"].iloc[-1],
                "MA20": self.stock_data["MA20"].iloc[-1],
                "MA60": self.stock_data["MA60"].iloc[-1],
                "RSI": self.stock_data["RSI"].iloc[-1],
                "MACD": self.stock_data["MACD"].iloc[-1],
                "Signal": self.stock_data["Signal"].iloc[-1],
                "Upper": self.stock_data["Upper"].iloc[-1],
                "Lower": self.stock_data["Lower"].iloc[-1],
            }
        except Exception as e:
            logger.error(f"기술적 분석 실패: {e}")
            return {}

    def _perform_financial_analysis(self) -> Dict[str, Any]:
        """
        재무 분석을 수행합니다.

        Returns:
            Dict[str, Any]: 재무 분석 결과
        """
        if not self.financial_data:
            return {}

        try:
            # 재무 분석 결과
            return {
                "ROE": self.financial_data.get("ROE", 0),
                "ROA": self.financial_data.get("ROA", 0),
                "DebtRatio": self.financial_data.get("DebtRatio", 0),
                "CurrentRatio": self.financial_data.get("CurrentRatio", 0),
                "QuickRatio": self.financial_data.get("QuickRatio", 0),
            }
        except Exception as e:
            logger.error(f"재무 분석 실패: {e}")
            return {}

    def _perform_ai_analysis(self) -> str:
        """
        AI 기반 종합 분석을 수행합니다.

        Returns:
            str: AI 기반 종합 분석 결과
        """
        try:
            # 기술적 분석과 재무 분석 결과를 바탕으로 AI 기반 종합 분석 수행
            prompt = f"""
            주식 코드: {self.stock_code}
            회사명: {self.stock_name}
            
            기술적 분석 결과:
            - 이동평균(MA5): {self.technical_analysis.get('MA5', 0)}
            - 이동평균(MA20): {self.technical_analysis.get('MA20', 0)}
            - 이동평균(MA60): {self.technical_analysis.get('MA60', 0)}
            - RSI: {self.technical_analysis.get('RSI', 0)}
            - MACD: {self.technical_analysis.get('MACD', 0)}
            - MACD 시그널: {self.technical_analysis.get('Signal', 0)}
            - 볼린저 밴드 상단: {self.technical_analysis.get('Upper', 0)}
            - 볼린저 밴드 하단: {self.technical_analysis.get('Lower', 0)}
            
            재무 분석 결과:
            - ROE: {self.financial_analysis.get('ROE', 0)}
            - ROA: {self.financial_analysis.get('ROA', 0)}
            - 부채비율: {self.financial_analysis.get('DebtRatio', 0)}
            - 유동비율: {self.financial_analysis.get('CurrentRatio', 0)}
            - 당좌비율: {self.financial_analysis.get('QuickRatio', 0)}
            
            위의 정보를 바탕으로 {self.stock_name}({self.stock_code})에 대한 종합적인 투자 분석을 해주세요.
            """

            # OpenAI API를 통해 AI 기반 종합 분석 수행
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 전문적인 주식 분석가입니다."},
                    {"role": "user", "content": prompt},
                ],
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 기반 종합 분석 실패: {e}")
            return "AI 기반 종합 분석을 수행할 수 없습니다."

    def generate_chart(self) -> str:
        """
        주가 차트를 생성합니다.

        Returns:
            str: 차트 파일 경로
        """
        if self.stock_data.empty:
            return ""

        try:
            # 차트 생성
            plt.figure(figsize=(12, 8))
            plt.plot(self.stock_data.index, self.stock_data["Close"], label="Close")
            plt.plot(self.stock_data.index, self.stock_data["MA5"], label="MA5")
            plt.plot(self.stock_data.index, self.stock_data["MA20"], label="MA20")
            plt.plot(self.stock_data.index, self.stock_data["MA60"], label="MA60")
            plt.plot(self.stock_data.index, self.stock_data["Upper"], label="Upper")
            plt.plot(self.stock_data.index, self.stock_data["Lower"], label="Lower")
            plt.title(f"{self.stock_name}({self.stock_code}) 주가 차트")
            plt.xlabel("Date")
            plt.ylabel("Price")
            plt.legend()
            plt.grid(True)

            # 차트 파일 저장
            chart_path = os.path.join(
                MCP_STORAGE_PATH,
                f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.png",
            )
            plt.savefig(chart_path)
            plt.close()

            return chart_path
        except Exception as e:
            logger.error(f"차트 생성 실패: {e}")
            return ""

    def save_analysis(self) -> str:
        """
        분석 결과를 저장합니다.

        Returns:
            str: 분석 결과 파일 경로
        """
        try:
            # 분석 결과
            analysis = {
                "stock_code": self.stock_code,
                "stock_name": self.stock_name,
                "technical_analysis": self.technical_analysis,
                "financial_analysis": self.financial_analysis,
                "ai_analysis": self.ai_analysis,
            }

            # 분석 결과 파일 저장
            result_path = os.path.join(
                MCP_STORAGE_PATH,
                f"{self.stock_name}({self.stock_code})_{datetime.now().strftime('%Y%m%d')}.txt",
            )
            with open(result_path, "w", encoding="utf-8") as f:
                f.write(f"주식 코드: {self.stock_code}\n")
                f.write(f"회사명: {self.stock_name}\n\n")
                f.write("기술적 분석 결과:\n")
                for key, value in self.technical_analysis.items():
                    f.write(f"- {key}: {value}\n")
                f.write("\n재무 분석 결과:\n")
                for key, value in self.financial_analysis.items():
                    f.write(f"- {key}: {value}\n")
                f.write("\nAI 기반 종합 분석 결과:\n")
                f.write(self.ai_analysis)

            return result_path
        except Exception as e:
            logger.error(f"분석 결과 저장 실패: {e}")
            return ""


def analyze_stock(stock_code: str) -> Dict[str, Any]:
    """
    주식 분석을 수행합니다.

    Args:
        stock_code (str): 주식 코드

    Returns:
        Dict[str, Any]: 분석 결과
    """
    try:
        # 주식 분석 수행
        analysis = StockAnalysis(stock_code)
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
