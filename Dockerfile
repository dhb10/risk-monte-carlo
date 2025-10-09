# ----------------------
# Stage 1: Build React frontend
# ----------------------
FROM node:20.18.2-alpine AS frontend-builder

WORKDIR /app

COPY package*.json ./
RUN npm install

# Copy all required frontend files for build
COPY . .

# Build React app to /app/dist
RUN npm run build

# ----------------------
# Stage 2: Final backend image. 
#
#docker builder prune
#the hash mismatch error was a real issue the only thing that worked was
#changing from python:3.13.4-slim to current
# ----------------------
# FROM python:3.13.4

FROM python:3.12-slim

# Install system dependencies (Postgres, build-essential, supervisor, and required libraries)
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --fix-missing \
    libpq-dev \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    supervisor \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*



# Create appuser and set up folders
RUN useradd -m appuser && mkdir -p /app /var/log/supervisord /app/supervisord_logs && \
    chown -R appuser:appuser /app /var/log/supervisord /app/supervisord_logs

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (explicitly, to avoid node_modules pollution)
COPY app.py tasks.py celery_config.py supervisord.conf ./
COPY pycomponents ./pycomponents
COPY public ./public

# Copy in built frontend
COPY --from=frontend-builder /app/dist ./dist

USER appuser

EXPOSE 5000

CMD ["/usr/bin/supervisord", "-n"]