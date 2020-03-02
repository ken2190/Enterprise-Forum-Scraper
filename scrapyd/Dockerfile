FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
ENV DEBIAN_FRONTEND noninteractive

COPY . /code
WORKDIR /code
COPY chromedriver /usr/local/bin/chromedriver


RUN pip install -r /code/requirements.txt
RUN apt update
RUN apt-get -y install wget
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list
RUN wget https://dl.google.com/linux/linux_signing_key.pub
RUN apt-key add linux_signing_key.pub
RUN apt-get -y update
RUN apt-get -y install google-chrome-stable

EXPOSE 6800