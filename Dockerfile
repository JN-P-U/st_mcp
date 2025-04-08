FROM python:3.8-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치 (최신 방식)
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Poetry 환경 변수 설정
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.4.0
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="/opt/poetry/bin:$PATH"

# 프로젝트 파일 복사
COPY pyproject.toml ./
# poetry.lock 파일이 있으면 복사, 없으면 무시
COPY poetry.lock* ./
COPY src ./src
COPY main.py ./

# 의존성 설치 (poetry.lock 파일이 없을 경우 대비)
RUN if [ -f poetry.lock ]; then \
        poetry install --no-dev; \
    else \
        poetry install --no-dev --no-root; \
    fi

# 환경 변수 기본값 설정 (실제 값은 런타임에 주입)
ENV OPENAI_API_KEY=""
ENV MCP_API_KEY=""
ENV MCP_API_URL="https://api.mcp.example.com"
ENV MCP_STORAGE_PATH="/mcp/storage"

# 실행 명령
CMD ["python", "main.py"] 