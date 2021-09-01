FROM ubuntu:latest
MAINTAINER Pedro Gabriel Amorim Soares <pedrogabriebhz@gmail.com>

RUN apt-get update -y
RUN apt-get upgrade -y

RUN apt-get -y install python3 \
                       python3-pip

COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

# default port
ENV ECHO_SERVER_PORT=5678

CMD twistd --nodaemon --python callcenter_server.tac
