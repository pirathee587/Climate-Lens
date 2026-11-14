FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-runtime.lock ./
RUN python -m pip install --no-cache-dir -r requirements.txt && python -m pip check
RUN groupadd --gid 10001 terratrend && useradd --uid 10001 --gid terratrend --create-home terratrend
COPY --chown=terratrend:terratrend app ./app
USER terratrend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3   CMD python -c "import json,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2); assert json.load(r)=={'status':'ok','service':'terratrend-api','api_version':'v1'}"

FROM base AS development
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--no-access-log"]

FROM base AS production
ENV APP_ENV=production
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
