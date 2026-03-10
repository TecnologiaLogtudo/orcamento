FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Instalar dependências de frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend .
RUN npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código Python
COPY . .

# Substituir o bundle estático pelo build do stage Node
COPY --from=frontend-builder /app/frontend/dist ./dist

# Porta interna
EXPOSE 5000

# Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:application"]
