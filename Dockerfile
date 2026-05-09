FROM python:3.12-slim

# ==============================
# SYSTEM
# ==============================

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ==============================
# INSTALL
# ==============================

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ==============================
# PROJECT
# ==============================

COPY . .

# ==============================
# PORTS
# ==============================

EXPOSE 8001
EXPOSE 8002
EXPOSE 8506
EXPOSE 8508
