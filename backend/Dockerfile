# Phase 01 template: requires fully pinned requirements.txt and app/main.py.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip check
RUN groupadd --gid 10001 terratrend && useradd --uid 10001 --gid terratrend --create-home terratrend
COPY --chown=terratrend:terratrend app ./app
USER terratrend
EXPOSE 8000

FROM base AS development
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
