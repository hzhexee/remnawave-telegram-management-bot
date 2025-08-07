# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь исходный код приложения
COPY handlers/ ./handlers/

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Устанавливаем переменную окружения для Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Создаем непривилегированного пользователя для безопасности
RUN groupadd -r botuser && useradd -r -g botuser botuser
RUN chown -R botuser:botuser /app
USER botuser

# Команда для запуска бота
CMD ["python", "handlers/bot/bot.py"]
