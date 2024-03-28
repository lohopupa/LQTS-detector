FROM python:alpine

WORKDIR /app

COPY . /app

EXPOSE 3000

CMD ["python3", "-m", "http.server", "3000", "--directory", "./src/"]
