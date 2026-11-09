FROM python:3.12-alpine

WORKDIR /app
RUN apk upgrade --no-cache
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt
RUN addgroup -S appgroup && adduser -S -G appgroup appuser
COPY --chown=appuser:appgroup app.py config.py ./
COPY --chown=appuser:appgroup modulos/ ./modulos/
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/saude', timeout=2)"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
