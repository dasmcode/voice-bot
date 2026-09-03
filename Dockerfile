# FROM asia-south1-docker.pkg.dev/ibank-genai-uat/i07721sgcur001/genai-custom-base-image:complaint-v2.1
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
# COPY --chown=1000:1000 . .
COPY . .
EXPOSE 8000
# RUN mkdir -p complaint_files
# USER appuser 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]