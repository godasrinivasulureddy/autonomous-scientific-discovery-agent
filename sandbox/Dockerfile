
FROM python:3.11-slim

WORKDIR /sandbox

RUN useradd --create-home --uid 10001 sandboxuser

USER sandboxuser

CMD ["python", "-I", "-B", "-"]
