FROM python:3.11-slim

WORKDIR /mcp

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -

# 프로젝트 파일 복사
COPY pyproject.toml poetry.lock ./
COPY src/st_mcp ./st_mcp
COPY main.py ./

# Poetry 설정 및 의존성 설치
RUN poetry config virtualenvs.create false \
    && poetry install --only main

# 결과 디렉토리 생성
RUN mkdir -p /mcp/storage /mcp/result

# 폰트 캐시 업데이트
RUN fc-cache -f -v

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 