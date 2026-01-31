FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

COPY backend/ ./backend/
COPY backend/configs/ ./configs/

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🔄 Waiting for database..."\n\
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "postgres" -c "\\q" 2>/dev/null; do\n\
  sleep 1\n\
done\n\
\n\
echo "✅ Database is ready!"\n\
echo "📊 Running migrations..."\n\
python backend/run_migrations.py\n\
\n\
echo "🚀 Starting application..."\n\
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
