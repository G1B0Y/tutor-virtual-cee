FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-ml.txt ./
# INCLUIR_ML=no arma una imagen sin Sentence Transformers ni Torch (solo para CI o pruebas con embeddings "hash").
ARG INCLUIR_ML=si
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INCLUIR_ML" = "si" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
