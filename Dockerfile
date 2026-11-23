FROM python:3.11-slim

WORKDIR /app
COPY gameplay_ml/ gameplay_ml/

ENTRYPOINT ["python", "-m", "gameplay_ml.audit"]
CMD ["--help"]
