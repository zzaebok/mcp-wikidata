# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
FROM python:3.11-slim

# Install curl for installation of uv
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install uv - see https://astral.sh/uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add local binary directory to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/
COPY uv.lock ./

# Install project dependencies using pip
RUN pip install --upgrade pip && \
    pip install . --no-cache-dir

# Command to run the MCP server
CMD ["uv", "run", "src/server.py"]
