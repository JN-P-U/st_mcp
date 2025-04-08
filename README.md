# MCP 기반 주식 분석 시스템

MCP(Multi-Context Processing) 기반의 주식 분석 시스템입니다. 기술적 분석, 재무 분석, AI 기반 종합 분석을 제공합니다.

## 기능

- 기술적 분석: 이동평균선, RSI, MACD, 볼린저 밴드 등
- 재무 분석: ROE, ROA, 부채비율, 영업이익률 등
- AI 기반 종합 분석: 기술적 분석과 재무 분석을 종합하여 투자 의견 제공
- 차트 생성: 기술적 지표와 재무 지표를 시각화한 차트 제공

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/st_mcp.git
cd st_mcp
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```
ALPHA_VANTAGE_API_KEY=your_api_key
```

## 사용 방법

1. 메인 스크립트 실행
```bash
python main.py
```

2. 주식 코드 입력
분석하고자 하는 주식의 코드를 입력합니다. (예: AAPL, MSFT, GOOGL 등)

3. 분석 결과 확인
- 기술적 분석 결과
- 재무 분석 결과
- AI 기반 종합 분석 결과
- 차트 파일 경로
- 분석 결과 파일 경로

## 프로젝트 구조

```
st_mcp/
├── src/
│   └── st_mcp/
│       ├── __init__.py
│       ├── stock_analysis.py
│       ├── technical_analysis.py
│       ├── financial_analysis.py
│       └── ai_analysis.py
├── main.py
├── requirements.txt
└── README.md
```

## 의존성

- Python 3.8 이상
- pandas
- numpy
- yfinance
- alpha_vantage
- matplotlib
- seaborn
- scikit-learn
- tensorflow
- python-dotenv

## 라이선스

MIT License

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 