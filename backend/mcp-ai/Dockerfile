# Use official python slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /usr/src/app

# Install system dependencies if any are needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies directly to global environment (no venv needed inside Docker)
RUN pip install --no-cache-dir \
    "langchain-groq>=0.3.8" \
    "mcp-use>=1.3.11" \
    "pika>=1.3.2" \
    "requests>=2.31.0" \
    "cohere>=5.0.0" \
    "python-dotenv>=1.0.1"

# Copy all source files
COPY . .

# Command is overridden in docker-compose.yml for each agent
CMD ["python", "orchestrator_mcp.py"]
