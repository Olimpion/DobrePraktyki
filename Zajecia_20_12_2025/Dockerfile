FROM python:3.9-slim

# Instalacja zależności systemowych (poprawione nazwy)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY requirements .
RUN pip install --no-cache-dir -r requirements

COPY . .
