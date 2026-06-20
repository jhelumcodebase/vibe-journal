# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set workspace directory
WORKDIR /workspace

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for highly optimized dependency compilation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency configuration files
COPY pyproject.toml uv.lock ./

# Sync project dependencies (without dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application and reference configuration files
COPY app/ ./app/
COPY tests/ ./tests/
COPY README.md GEMINI.md ./

# Expose port 8080 (matching Cloud Run requirements)
EXPOSE 8080

# Configure system PATH to target the virtual environment, and configure Streamlit
ENV PATH="/workspace/.venv/bin:$PATH"
ENV PYTHONPATH="/workspace"
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Command to execute the Streamlit application
CMD ["streamlit", "run", "app/main.py"]
