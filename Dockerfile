FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Chạy scheduler (cập nhật proxy mỗi giờ) và API server trong cùng container?
# Tốt hơn là dùng 2 process. Ở đây ta dùng supervisord hoặc entrypoint script.
# Đơn giản: dùng 2 service trong docker-compose.

# Tạo script start_all.sh
RUN echo '#!/bin/bash\n\
python scheduler.py &\n\
uvicorn api:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
