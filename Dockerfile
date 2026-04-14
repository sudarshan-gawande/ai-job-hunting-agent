FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30m --timeout=10s \
  CMD python -c "import os; assert os.path.exists('agent.log')" || exit 1

CMD ["python", "-u", "job_agent.py"]
