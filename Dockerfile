FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    fontconfig \
    fonts-nanum \
    fonts-nanum-coding \
    fonts-nanum-extra \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -

# Poetry PATH 설정
ENV PATH="/root/.local/bin:$PATH"

# 작업 디렉토리 설정
WORKDIR /mcp

# 프로젝트 파일 복사
COPY pyproject.toml poetry.lock ./
COPY src ./src
COPY main.py ./

# 의존성 설치
RUN poetry config virtualenvs.create false \
    && poetry install --only main

# 스토리지 디렉토리 생성
RUN mkdir -p /mcp/storage /mcp/result

# 폰트 캐시 업데이트
RUN fc-cache -f -v

# 실행
CMD ["poetry", "run", "python", "main.py"] 