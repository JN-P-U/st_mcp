# 재무제표 분석(dart_api)

import json
import os
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests


def register_api_key(api_key):
    """
    DART API 키를 등록합니다.
    """
    config_dir = os.path.expanduser("~/.mcp")
    config_file = os.path.join(config_dir, "dart_config.json")

    # 설정 디렉토리가 없으면 생성
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # 설정 파일이 없으면 생성
    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            json.dump({"api_key": api_key}, f)
    else:
        # 기존 설정 파일 읽기
        with open(config_file, "r") as f:
            config = json.load(f)

        # API 키 업데이트
        config["api_key"] = api_key

        # 설정 파일 저장
        with open(config_file, "w") as f:
            json.dump(config, f)

    return True


def get_api_key():
    """
    등록된 DART API 키를 가져옵니다.
    """
    # 환경 변수에서 API 키 확인
    api_key = os.getenv("DART_API_KEY")
    if api_key:
        return api_key

    # 설정 파일에서 API 키 확인
    config_file = os.path.join(os.path.expanduser("~/.mcp"), "dart_config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            return config.get("api_key")

    return None


def fetch_corp_codes(api_key):
    """
    DART API에서 기업 코드 목록을 가져옵니다.
    """
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {"crtfc_key": api_key}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        # 응답 내용 확인 (바이너리로 처리)
        content = response.content

        # 응답이 ZIP 파일인지 확인
        if content.startswith(b"PK"):
            # ZIP 파일을 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # ZIP 파일 압축 해제
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # XML 파일 경로
                xml_file_path = os.path.join(temp_dir, "CORPCODE.xml")

                # XML 파일이 존재하는지 확인
                if not os.path.exists(xml_file_path):
                    print("XML 파일을 찾을 수 없습니다.")
                    os.unlink(temp_file_path)
                    return pd.DataFrame()

                # XML 파일 읽기
                with open(xml_file_path, "rb") as f:
                    xml_content = f.read()

                # XML 파싱
                root = ET.fromstring(xml_content)

                # 결과를 저장할 리스트
                companies = []

                # 각 기업 정보 추출
                for corp in root.findall(".//list"):
                    try:
                        company = {
                            "corp_code": (
                                corp.find("corp_code").text
                                if corp.find("corp_code") is not None
                                else ""
                            ),
                            "corp_name": (
                                corp.find("corp_name").text
                                if corp.find("corp_name") is not None
                                else ""
                            ),
                            "stock_code": (
                                corp.find("stock_code").text
                                if corp.find("stock_code") is not None
                                else ""
                            ),
                            "modify_date": (
                                corp.find("modify_date").text
                                if corp.find("modify_date") is not None
                                else ""
                            ),
                            "status": (
                                corp.find("status").text
                                if corp.find("status") is not None
                                else ""
                            ),
                        }
                        companies.append(company)
                    except Exception as e:
                        print(f"기업 정보 파싱 중 오류 발생: {str(e)}")
                        continue

                # 임시 파일 삭제
                os.unlink(temp_file_path)

                # DataFrame으로 변환
                df = pd.DataFrame(companies)

                # 종목 코드가 있는 기업만 필터링
                df = df[df["stock_code"].notna() & (df["stock_code"] != "")]

                # 종목 코드 정규화 (앞뒤 공백 제거)
                df["stock_code"] = df["stock_code"].str.strip()

                # 디버깅 정보 출력
                print(f"총 {len(df)}개의 기업 정보를 가져왔습니다.")
                print("삼성전자 검색 결과:")
                samsung = df[df["corp_name"].str.contains("삼성전자", na=False)]
                if not samsung.empty:
                    print(samsung[["corp_name", "stock_code", "corp_code"]])
                else:
                    print("삼성전자를 찾을 수 없습니다.")

                return df
        else:
            print("API 응답이 ZIP 파일이 아닙니다.")
            print(f"응답 내용: {content[:200]}...")  # 처음 200자만 출력
            return pd.DataFrame()

    except Exception as e:
        print(f"기업 코드 목록을 가져오는 중 오류가 발생했습니다: {str(e)}")
        return pd.DataFrame()


def find_corp_code_by_name(companies_df, corp_name):
    """
    기업명으로 기업 코드를 찾습니다.
    """
    # 정확한 일치 검색
    exact_match = companies_df[companies_df["corp_name"] == corp_name]
    if not exact_match.empty:
        return exact_match.iloc[0]["corp_code"]

    # 부분 일치 검색
    partial_match = companies_df[
        companies_df["corp_name"].str.contains(corp_name, na=False)
    ]
    if not partial_match.empty:
        return partial_match.iloc[0]["corp_code"]

    return None


def find_corp_code_by_stock_code(companies_df, stock_code):
    """
    종목 코드로 기업 코드를 찾습니다.
    """
    # 종목 코드 정규화 (앞뒤 공백 제거)
    stock_code = stock_code.strip()

    # 데이터프레임 인덱스 리셋
    companies_df = companies_df.reset_index(drop=True)

    # 디버깅 정보 출력
    print(f"\n종목 코드 '{stock_code}' 검색:")
    matches = companies_df[companies_df["stock_code"] == stock_code]
    if not matches.empty:
        print("찾은 기업 정보:")
        print(matches[["corp_name", "stock_code", "corp_code"]])
        return matches.iloc[0]["corp_code"]

    # 종목 코드가 없는 경우
    print(f"종목 코드 '{stock_code}'에 해당하는 기업을 찾을 수 없습니다.")
    return None


def fetch_financial_statements(api_key, corp_code, year):
    """
    특정 연도의 재무제표 데이터를 가져옵니다.
    """
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"

    # 보고서 코드: 11011(사업보고서), 11012(반기보고서), 11013(분기보고서), 11014(등록법인결산서)
    report_codes = ["11011", "11012", "11013", "11014"]

    # 재무제표 구분: O(별도), C(연결)
    fs_divs = ["OFS", "CFS"]

    for fs_div in fs_divs:
        for reprt_code in report_codes:
            params = {
                "crtfc_key": api_key,
                "corp_code": corp_code,
                "bsns_year": year,
                "reprt_code": reprt_code,
                "fs_div": fs_div,
            }

            try:
                response = requests.get(url, params=params)
                data = response.json()

                if data.get("status") == "000":  # 정상 응답
                    result = data.get("list", [])
                    if result:
                        print(
                            f"{year}년 {reprt_code} 보고서 ({fs_div}) 데이터를 가져왔습니다."
                        )
                        return result
            except Exception as e:
                print(f"재무제표 데이터를 가져오는 중 오류 발생: {e}")
                continue

    print(f"{year}년 데이터가 없습니다.")
    return []


def analyze_financial_statements(stock_code, api_key=None):
    """
    주식 코드를 기반으로 재무제표를 분석합니다.

    Args:
        stock_code (str): 주식 코드
        api_key (str, optional): DART API 키. None인 경우 환경 변수에서 가져옵니다.
    """
    # DART API 키 가져오기
    if api_key is None:
        api_key = get_api_key()

    if not api_key:
        print("DART API 키가 설정되지 않았습니다.")
        return {
            "income_statement": pd.DataFrame(),
            "balance_sheet": pd.DataFrame(),
            "cash_flow": pd.DataFrame(),
            "growth_rates": pd.DataFrame(),
            "financial_health": {
                "부채비율 상태": "N/A",
                "유동비율 상태": "N/A",
                "영업이익률 상태": "N/A",
                "종합 평가": "N/A",
            },
        }

    # 상장기업 목록 가져오기
    print("상장기업 목록을 가져오는 중...")
    companies_df = fetch_corp_codes(api_key)
    if companies_df.empty:
        print("상장기업 목록을 가져오는데 실패했습니다.")
        return None

    # 종목 코드 정규화 (6자리 숫자로 변환)
    stock_code = stock_code.strip().zfill(6)

    # 기업 정보 찾기
    company_info = companies_df[companies_df["stock_code"] == stock_code]
    if company_info.empty:
        print(f"종목 코드 '{stock_code}'에 해당하는 기업을 찾을 수 없습니다.")
        return None

    # 기업 코드 가져오기
    corp_code = company_info.iloc[0]["corp_code"]

    # 최근 3년간의 재무제표 데이터 가져오기
    current_year = datetime.now().year
    years = [str(year) for year in range(current_year - 2, current_year + 1)]
    financial_data = []

    for year in years:
        data = fetch_financial_statements(api_key, corp_code, year)
        if data:
            financial_data.extend(data)

    if not financial_data:
        print("재무제표 데이터를 가져오는데 실패했습니다.")
        return None

    # 재무제표 데이터를 DataFrame으로 변환
    df = pd.DataFrame(financial_data)

    # 재무상태표(BS) 데이터 추출
    balance_sheet = df[df["sj_div"] == "BS"].pivot_table(
        index="bsns_year", columns="account_nm", values="thstrm_amount", aggfunc="first"
    )

    # 손익계산서(IS) 데이터 추출
    income_statement = df[df["sj_div"] == "IS"].pivot_table(
        index="bsns_year", columns="account_nm", values="thstrm_amount", aggfunc="first"
    )

    # 현금흐름표(CF) 데이터 추출
    cash_flow = df[df["sj_div"] == "CF"].pivot_table(
        index="bsns_year", columns="account_nm", values="thstrm_amount", aggfunc="first"
    )

    # 재무 건전성 분석
    financial_health = analyze_financial_health(balance_sheet, income_statement)

    return {
        "balance_sheet": balance_sheet,
        "income_statement": income_statement,
        "cash_flow": cash_flow,
        "financial_health": financial_health,
    }


def analyze_financial_health(balance_sheet, income_statement):
    """
    재무 건전성을 분석합니다.
    """
    try:
        # 문자열에서 천 단위 구분자 제거 함수
        def clean_number(value):
            if isinstance(value, str):
                return float(value.replace(",", ""))
            return float(value)

        # 부채비율 계산 (부채총계 / 자본총계 * 100)
        debt_ratio = (
            clean_number(balance_sheet["부채총계"].iloc[-1])
            / clean_number(balance_sheet["자본총계"].iloc[-1])
            * 100
        )
        debt_status = (
            "양호" if debt_ratio < 200 else "주의" if debt_ratio < 400 else "위험"
        )

        # 유동비율 계산 (유동자산 / 유동부채 * 100)
        current_ratio = (
            clean_number(balance_sheet["유동자산"].iloc[-1])
            / clean_number(balance_sheet["유동부채"].iloc[-1])
            * 100
        )
        current_status = (
            "양호" if current_ratio > 150 else "주의" if current_ratio > 100 else "위험"
        )

        # 영업이익률 계산 (영업이익 / 매출액 * 100)
        operating_margin = (
            clean_number(income_statement["영업이익"].iloc[-1])
            / clean_number(income_statement["매출액"].iloc[-1])
            * 100
        )
        operating_status = (
            "양호"
            if operating_margin > 10
            else "주의" if operating_margin > 5 else "위험"
        )

        # 종합 평가
        scores = {"양호": 3, "주의": 2, "위험": 1}
        total_score = (
            scores[debt_status] + scores[current_status] + scores[operating_status]
        ) / 3
        overall = (
            "양호" if total_score > 2.5 else "주의" if total_score > 1.5 else "위험"
        )

        return {
            "부채비율": debt_ratio,
            "부채비율 상태": debt_status,
            "유동비율": current_ratio,
            "유동비율 상태": current_status,
            "영업이익률": operating_margin,
            "영업이익률 상태": operating_status,
            "종합 평가": overall,
        }
    except Exception as e:
        print(f"재무 건전성 분석 중 오류 발생: {e}")
        return {
            "부채비율 상태": "N/A",
            "유동비율 상태": "N/A",
            "영업이익률 상태": "N/A",
            "종합 평가": "N/A",
        }


def analyze_by_stock_code(api_key, stock_code):
    """
    종목 코드로 기업을 찾아 재무제표를 분석합니다.
    """
    # 상장기업 목록 가져오기
    print("상장기업 목록을 가져오는 중...")
    companies_df = fetch_corp_codes(api_key)
    if companies_df.empty:
        print("상장기업 목록을 가져오는데 실패했습니다.")
        return

    # 종목 코드로 기업 코드 찾기
    corp_code = find_corp_code_by_stock_code(companies_df, stock_code)
    if not corp_code:
        return

    # 기업 정보 출력
    company_info = companies_df[companies_df["corp_code"] == corp_code].iloc[0]
    print(
        f"\n선택한 기업: {company_info['corp_name']} " f"({company_info['stock_code']})"
    )
    print(f"기업 코드: {corp_code}")

    # 최근 5개년 재무제표 데이터 가져오기
    current_year = datetime.today().year
    years = range(current_year - 4, current_year + 1)

    financial_data_by_year = {}
    for year in years:
        print(f"\n{year}년 재무제표 데이터를 가져오는 중...")
        financial_data = fetch_financial_statements(api_key, corp_code, year)
        if financial_data:
            print(f"{year}년 데이터 항목 수: {len(financial_data)}")
            # 데이터 샘플 출력 (처음 3개 항목)
            for i, item in enumerate(financial_data[:3]):
                print(
                    f"  항목 {i+1}: {item.get('account_nm')} = "
                    f"{item.get('thstrm_amount')}"
                )

        financial_analysis = analyze_financial_statements(stock_code)
        if financial_analysis:
            financial_data_by_year[year] = financial_analysis
        else:
            print(f"{year}년 데이터 분석 실패")

    if not financial_data_by_year:
        print("재무제표 데이터를 가져오는데 실패했습니다.")
        return

    # 재무제표 데이터 출력
    print("\n===== 재무제표 분석 결과 =====")

    # 데이터프레임으로 변환
    df = pd.DataFrame(financial_data_by_year).T

    # 주요 지표 선택
    key_indicators = [
        "매출액",
        "영업이익",
        "당기순이익",
        "영업이익률",
        "순이익률",
        "자산총계",
        "부채총계",
        "자본총계",
        "부채비율",
        "유동비율",
        "영업활동현금흐름",
        "투자활동현금흐름",
        "재무활동현금흐름",
    ]

    # 존재하는 지표만 선택
    available_indicators = [col for col in key_indicators if col in df.columns]

    if not available_indicators:
        print("분석 가능한 재무지표가 없습니다.")
        return

    # 선택된 지표만 출력
    selected_df = df[available_indicators]

    # 데이터 출력
    if "매출액" in available_indicators:
        print("\n[손익계산서]")
        income_statement_cols = [
            col
            for col in ["매출액", "영업이익", "당기순이익", "영업이익률", "순이익률"]
            if col in available_indicators
        ]
        print(selected_df[income_statement_cols])

    if "자산총계" in available_indicators:
        print("\n[대차대조표]")
        balance_sheet_cols = [
            col
            for col in ["자산총계", "부채총계", "자본총계", "부채비율", "유동비율"]
            if col in available_indicators
        ]
        print(selected_df[balance_sheet_cols])

    if "영업활동현금흐름" in available_indicators:
        print("\n[현금흐름표]")
        cash_flow_cols = [
            col
            for col in ["영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름"]
            if col in available_indicators
        ]
        print(selected_df[cash_flow_cols])

    # 성장률 계산
    print("\n[성장률 분석]")
    growth_rates = {}
    for year in years[1:]:
        prev_year = year - 1
        if prev_year in financial_data_by_year and year in financial_data_by_year:
            # 0으로 나누기 방지
            prev_revenue = financial_data_by_year[prev_year]["매출액"]
            prev_operating_income = financial_data_by_year[prev_year]["영업이익"]
            prev_net_income = financial_data_by_year[prev_year]["당기순이익"]

            curr_revenue = financial_data_by_year[year]["매출액"]
            curr_operating_income = financial_data_by_year[year]["영업이익"]
            curr_net_income = financial_data_by_year[year]["당기순이익"]

            # 0으로 나누기 방지
            revenue_growth = 0
            if prev_revenue != 0:
                revenue_growth = ((curr_revenue / prev_revenue) - 1) * 100

            operating_income_growth = 0
            if prev_operating_income != 0:
                operating_income_growth = (
                    (curr_operating_income / prev_operating_income) - 1
                ) * 100

            net_income_growth = 0
            if prev_net_income != 0:
                net_income_growth = ((curr_net_income / prev_net_income) - 1) * 100

            growth_rates[year] = {
                "매출액 성장률": revenue_growth,
                "영업이익 성장률": operating_income_growth,
                "순이익 성장률": net_income_growth,
            }

    if growth_rates:
        growth_df = pd.DataFrame(growth_rates).T
        print(growth_df)

    # 재무건전성 평가
    print("\n[재무건전성 평가]")
    latest_year = max(financial_data_by_year.keys())
    latest_data = financial_data_by_year[latest_year]

    # 부채비율 평가
    debt_ratio = latest_data["부채비율"]
    debt_ratio_evaluation = (
        "양호" if debt_ratio < 200 else "주의" if debt_ratio < 400 else "위험"
    )

    # 유동비율 평가
    current_ratio = latest_data["유동비율"]
    current_ratio_evaluation = (
        "양호" if current_ratio > 200 else "주의" if current_ratio > 150 else "위험"
    )

    # 영업이익률 평가
    operating_margin = latest_data["영업이익률"]
    operating_margin_evaluation = (
        "양호" if operating_margin > 10 else "주의" if operating_margin > 5 else "위험"
    )

    print(f"부채비율: {debt_ratio:.2f}% ({debt_ratio_evaluation})")
    print(f"유동비율: {current_ratio:.2f}% ({current_ratio_evaluation})")
    print(f"영업이익률: {operating_margin:.2f}% ({operating_margin_evaluation})")

    # 종합 평가
    risk_count = sum(
        1
        for eval in [
            debt_ratio_evaluation,
            current_ratio_evaluation,
            operating_margin_evaluation,
        ]
        if eval == "위험"
    )
    caution_count = sum(
        1
        for eval in [
            debt_ratio_evaluation,
            current_ratio_evaluation,
            operating_margin_evaluation,
        ]
        if eval == "주의"
    )

    if risk_count >= 2:
        overall_evaluation = "위험"
    elif risk_count == 1 or caution_count >= 2:
        overall_evaluation = "주의"
    else:
        overall_evaluation = "양호"

    print(f"\n종합 평가: {overall_evaluation}")


def main():
    # API 키 확인 또는 등록
    api_key = get_api_key()
    if not api_key:
        print("DART API 키가 등록되어 있지 않습니다.")
        api_key = input("DART API 키를 입력하세요: ")
        if register_api_key(api_key):
            print("API 키가 성공적으로 등록되었습니다.")
        else:
            print("API 키 등록에 실패했습니다.")
            return

    # 분석 방식 선택
    print("\n분석 방식을 선택하세요:")
    print("1. 기업명으로 분석")
    print("2. 종목 코드로 분석")
    choice = input("선택 (1 또는 2): ").strip()

    if choice == "1":
        # 상장기업 목록 가져오기
        print("상장기업 목록을 가져오는 중...")
        companies_df = fetch_corp_codes(api_key)
        if companies_df.empty:
            print("상장기업 목록을 가져오는데 실패했습니다.")
            return

        # 사용자에게 기업명 입력 요청
        corp_name = input("\n분석할 기업명을 입력하세요: ")

        # 기업명으로 기업 코드 찾기
        corp_code = find_corp_code_by_name(companies_df, corp_name)
        if not corp_code:
            print(f"'{corp_name}' 기업을 찾을 수 없습니다.")
            return

        # 기업 정보 출력
        company_info = companies_df[companies_df["corp_code"] == corp_code].iloc[0]
        print(
            f"\n선택한 기업: {company_info['corp_name']} "
            f"({company_info['stock_code']})"
        )
        print(f"기업 코드: {corp_code}")

        # 최근 5개년 재무제표 데이터 가져오기
        current_year = datetime.today().year
        years = range(current_year - 4, current_year + 1)

        financial_data_by_year = {}
        for year in years:
            print(f"\n{year}년 재무제표 데이터를 가져오는 중...")
            financial_data = fetch_financial_statements(api_key, corp_code, year)
            if financial_data:
                print(f"{year}년 데이터 항목 수: {len(financial_data)}")
                # 데이터 샘플 출력 (처음 3개 항목)
                for i, item in enumerate(financial_data[:3]):
                    print(
                        f"  항목 {i+1}: {item.get('account_nm')} = "
                        f"{item.get('thstrm_amount')}"
                    )

            financial_analysis = analyze_financial_statements(
                company_info["stock_code"], api_key
            )
            if financial_analysis:
                financial_data_by_year[year] = financial_analysis
            else:
                print(f"{year}년 데이터 분석 실패")

        if not financial_data_by_year:
            print("재무제표 데이터를 가져오는데 실패했습니다.")
            return

        # 재무제표 데이터 출력
        print("\n===== 재무제표 분석 결과 =====")

        # 데이터프레임으로 변환
        df = pd.DataFrame(financial_data_by_year).T

        # 주요 지표 선택
        key_indicators = [
            "매출액",
            "영업이익",
            "당기순이익",
            "영업이익률",
            "순이익률",
            "자산총계",
            "부채총계",
            "자본총계",
            "부채비율",
            "유동비율",
            "영업활동현금흐름",
            "투자활동현금흐름",
            "재무활동현금흐름",
        ]

        # 존재하는 지표만 선택
        available_indicators = [col for col in key_indicators if col in df.columns]

        if not available_indicators:
            print("분석 가능한 재무지표가 없습니다.")
            return

        # 선택된 지표만 출력
        selected_df = df[available_indicators]

        # 데이터 출력
        if "매출액" in available_indicators:
            print("\n[손익계산서]")
            income_statement_cols = [
                col
                for col in [
                    "매출액",
                    "영업이익",
                    "당기순이익",
                    "영업이익률",
                    "순이익률",
                ]
                if col in available_indicators
            ]
            print(selected_df[income_statement_cols])

        if "자산총계" in available_indicators:
            print("\n[대차대조표]")
            balance_sheet_cols = [
                col
                for col in ["자산총계", "부채총계", "자본총계", "부채비율", "유동비율"]
                if col in available_indicators
            ]
            print(selected_df[balance_sheet_cols])

        if "영업활동현금흐름" in available_indicators:
            print("\n[현금흐름표]")
            cash_flow_cols = [
                col
                for col in ["영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름"]
                if col in available_indicators
            ]
            print(selected_df[cash_flow_cols])

        # 성장률 계산
        print("\n[성장률 분석]")
        growth_rates = {}
        for year in years[1:]:
            prev_year = year - 1
            if prev_year in financial_data_by_year and year in financial_data_by_year:
                # 0으로 나누기 방지
                prev_revenue = financial_data_by_year[prev_year]["매출액"]
                prev_operating_income = financial_data_by_year[prev_year]["영업이익"]
                prev_net_income = financial_data_by_year[prev_year]["당기순이익"]

                curr_revenue = financial_data_by_year[year]["매출액"]
                curr_operating_income = financial_data_by_year[year]["영업이익"]
                curr_net_income = financial_data_by_year[year]["당기순이익"]

                # 0으로 나누기 방지
                revenue_growth = 0
                if prev_revenue != 0:
                    revenue_growth = ((curr_revenue / prev_revenue) - 1) * 100

                operating_income_growth = 0
                if prev_operating_income != 0:
                    operating_income_growth = (
                        (curr_operating_income / prev_operating_income) - 1
                    ) * 100

                net_income_growth = 0
                if prev_net_income != 0:
                    net_income_growth = ((curr_net_income / prev_net_income) - 1) * 100

                growth_rates[year] = {
                    "매출액 성장률": revenue_growth,
                    "영업이익 성장률": operating_income_growth,
                    "순이익 성장률": net_income_growth,
                }

        if growth_rates:
            growth_df = pd.DataFrame(growth_rates).T
            print(growth_df)

        # 재무건전성 평가
        print("\n[재무건전성 평가]")
        latest_year = max(financial_data_by_year.keys())
        latest_data = financial_data_by_year[latest_year]

        # 부채비율 평가
        debt_ratio = latest_data["부채비율"]
        debt_ratio_evaluation = (
            "양호" if debt_ratio < 200 else "주의" if debt_ratio < 400 else "위험"
        )

        # 유동비율 평가
        current_ratio = latest_data["유동비율"]
        current_ratio_evaluation = (
            "양호" if current_ratio > 200 else "주의" if current_ratio > 150 else "위험"
        )

        # 영업이익률 평가
        operating_margin = latest_data["영업이익률"]
        operating_margin_evaluation = (
            "양호"
            if operating_margin > 10
            else "주의" if operating_margin > 5 else "위험"
        )

        print(f"부채비율: {debt_ratio:.2f}% ({debt_ratio_evaluation})")
        print(f"유동비율: {current_ratio:.2f}% ({current_ratio_evaluation})")
        print(f"영업이익률: {operating_margin:.2f}% ({operating_margin_evaluation})")

        # 종합 평가
        risk_count = sum(
            1
            for eval in [
                debt_ratio_evaluation,
                current_ratio_evaluation,
                operating_margin_evaluation,
            ]
            if eval == "위험"
        )
        caution_count = sum(
            1
            for eval in [
                debt_ratio_evaluation,
                current_ratio_evaluation,
                operating_margin_evaluation,
            ]
            if eval == "주의"
        )

        if risk_count >= 2:
            overall_evaluation = "위험"
        elif risk_count == 1 or caution_count >= 2:
            overall_evaluation = "주의"
        else:
            overall_evaluation = "양호"

        print(f"\n종합 평가: {overall_evaluation}")

    elif choice == "2":
        # 사용자에게 종목 코드 입력 요청
        stock_code = input("\n분석할 종목 코드를 입력하세요 (예: 005930): ")

        # 종목 코드로 분석
        analyze_by_stock_code(api_key, stock_code)

    else:
        print("잘못된 선택입니다. 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
