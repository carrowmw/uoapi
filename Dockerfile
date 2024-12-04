FROM python:3.10-slim-bookworm

ARG API_CLIENT_ENV=development

LABEL maintainer="c.morris-wiltshire@newcastle.ac.uk"
LABEL vendor="Newcastle University"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PATH="/opt/poetry/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy only dependency files first
COPY pyproject.toml poetry.lock ./

# Install dependencies (utilize Docker cache layer)
RUN poetry install $([ "$API_CLIENT_ENV" = "production" ] && echo "--no-dev") --no-root

# Add non-root user so that the package can be installed without root permissions
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Copy the package code
COPY . .

# Install the package itself
RUN poetry install --only-root

# Default command (can be overridden)
CMD ["poetry", "run", "python", "-m", "uoapi"]

