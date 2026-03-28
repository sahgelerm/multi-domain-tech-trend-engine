#!/bin/bash
# deploy.sh - скрипт для развертывания дашборда

echo "🚀 Начинаю деплой дашборда..."

# Переходим в папку проекта
cd /home/ubuntu/dashboard

# Обновляем код из Git
git pull origin main

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем/обновляем зависимости
pip install -r requirements.txt

# Устанавливаем переменные окружения
export GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/.gcp/service-key.json
export DASHBOARD_MODE=bigquery

# Останавливаем старый процесс (если есть)
pkill -f "streamlit run app.py" || true

# Запускаем дашборд в фоне
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

echo "✅ Дашборд запущен на порту 8501"
echo "📊 Логи: tail -f dashboard.log"
