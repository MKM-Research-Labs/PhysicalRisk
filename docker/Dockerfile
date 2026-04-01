FROM python:3.13-slim

# Install GDAL, build tools, and geospatial system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY app.py .
COPY src/ src/

# Data should be volume-mounted in production; copy for dev convenience
COPY data/ data/

EXPOSE 5001

ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1

CMD ["python", "app.py", "server", "--host", "0.0.0.0", "--port", "5001"]
