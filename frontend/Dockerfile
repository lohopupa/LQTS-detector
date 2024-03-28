FROM python:alpine

WORKDIR /app

ARG EXPOSE_PORT=3000

COPY ./scr ./src

EXPOSE ${EXPOSE_PORT}

CMD ["python", "-m", "http.server", ${EXPOSE_PORT}]
