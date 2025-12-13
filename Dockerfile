FROM --platform=linux/amd64 python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./api /code/api

COPY server-ca.pem /code/
COPY client-cert.pem /code/
COPY client-key.pem /code/

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]