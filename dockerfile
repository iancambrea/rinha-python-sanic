FROM python:slim

WORKDIR /sanic

COPY ./app .

COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

EXPOSE 80

CMD ["python3", "server.py"]