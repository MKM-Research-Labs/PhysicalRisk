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

# Copy data (mount as volume in production)
COPY data/ data/

EXPOSE 5001

ENV FLASK_ENV=production

CMD ["python", "app.py", "server", "--host", "0.0.0.0", "--port", "5001"]
