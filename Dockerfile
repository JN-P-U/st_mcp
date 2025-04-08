FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 서비스 포트 설정
EXPOSE 8000

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1

# 서버 실행
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"] 