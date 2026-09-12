FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim AS production
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY . .
ENV DJANGO_SETTINGS_MODULE=config.settings.prod \
    SECRET_KEY=collectstatic-only-example-key-with-more-than-fifty-characters \
    ALLOWED_HOSTS=localhost
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
