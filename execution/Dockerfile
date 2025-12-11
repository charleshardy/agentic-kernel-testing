FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies including virtualization tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    qemu-system-x86 \
    qemu-system-arm \
    qemu-utils \
    kvm \
    libvirt-daemon-system \
    libvirt-clients \
    bridge-utils \
    ssh \
    telnet \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for artifacts and logs
RUN mkdir -p /app/artifacts /app/logs /app/environments

# Create non-root user and add to necessary groups
RUN useradd --create-home --shell /bin/bash app && \
    usermod -a -G kvm app && \
    chown -R app:app /app
USER app

# Expose port for execution service
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the execution service
CMD ["python", "-m", "execution.test_runner", "--host", "0.0.0.0", "--port", "8002"]