FROM python:3.8-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN curl -sSL https://install.python-poetry.org | python3 -

# Poetry 환경 변수 설정
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.4.0
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="/opt/poetry/bin:$PATH"

# 프로젝트 파일 복사
COPY pyproject.toml poetry.lock ./
COPY src ./src
COPY main.py ./
COPY .env ./

# 의존성 설치
RUN poetry install --no-dev

# 실행 명령
CMD ["python", "main.py"] 