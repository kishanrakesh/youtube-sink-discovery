FROM mcr.microsoft.com/playwright/python:v1.43.1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ app/
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]