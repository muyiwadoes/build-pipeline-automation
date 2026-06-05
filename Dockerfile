FROM python:3.11-slim

# -----------------------
# Environment configuration
# -----------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# -----------------------
# System & Python setup
# -----------------------
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# -----------------------
# Install runtime dependencies only
# -----------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------
# Copy application code
# -----------------------
COPY src/ ./src/
COPY pipeline-config.yml ./

# -----------------------
# Create non-root user (security)
# -----------------------
RUN useradd --create-home --shell /bin/false appuser && \
    chown -R appuser:appuser /app

USER appuser

# -----------------------
# Healthcheck (robust single-line Python)
# -----------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from src.pipeline import Pipeline; \
sys.exit(0 if Pipeline() is not None else 1)"

# -----------------------
# Entrypoint
# -----------------------
ENTRYPOINT ["python", "-m", "src.pipeline"]