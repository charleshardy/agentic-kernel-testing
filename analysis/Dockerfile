FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies including analysis tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    lcov \
    gcov \
    git \
    build-essential \
    linux-perf \
    coccinelle \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for analysis data
RUN mkdir -p /app/coverage_data /app/performance_data /app/security_reports

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port for analysis service
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the analysis service
CMD ["python", "-m", "analysis.coverage_analyzer", "--host", "0.0.0.0", "--port", "8003"]