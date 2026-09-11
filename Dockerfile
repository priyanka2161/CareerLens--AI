FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/home/app/.cache/huggingface
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.8.0 && pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 app
COPY --chown=app:app backend ./backend
COPY --chown=app:app data ./data
COPY --chown=app:app scripts ./scripts
RUN mkdir -p /home/app/.cache/huggingface && chown -R app:app /home/app/.cache
USER app
EXPOSE 8000
CMD ["python","-m","uvicorn","app.main:app","--app-dir","backend","--host","0.0.0.0","--port","8000","--limit-concurrency","16"]
