# syntax=docker/dockerfile:1

FROM python:3.11
COPY . /server
WORKDIR /server
RUN pip install -r requirements.txt
RUN flask --app runner.py db init
RUN flask --app runner.py db migrate
RUN flask --app runner.py db upgrade
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]