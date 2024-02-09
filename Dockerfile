FROM python:3.11-slim-buster

WORKDIR /application

COPY . .
RUN pip3 install -r requirements.txt

CMD [ "python3", "main.py"]