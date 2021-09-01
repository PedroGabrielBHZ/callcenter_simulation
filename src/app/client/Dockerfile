FROM ubuntu:latest
MAINTAINER Pedro Gabriel Amorim Soares <pedrogabrielbhz@gmail.com>

RUN apt-get update -y
RUN apt-get upgrade -y

RUN apt-get -y install python3 \
                       python3-pip
COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

CMD twistd --nodaemon --python callcenter_client.tac
