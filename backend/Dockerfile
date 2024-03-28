FROM python:3.10

WORKDIR /app

RUN pip3 install --upgrade pip
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir

COPY . /app

EXPOSE 5000

WORKDIR /app/src

CMD ["uvicorn", "app:router", "--host", "0.0.0.0", "--port", "5000", "--reload"]
