FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação
COPY . .

# Porta interna
EXPOSE 5000

# Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:application"]