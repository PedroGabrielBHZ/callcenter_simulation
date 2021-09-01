FROM centos:7
MAINTAINER Pedro Gabriel Amorim Soares <pedrogabrielbhz@gmail.com>

RUN yum update -y
RUN yum upgrade -y

RUN yum -y install python3 \
                   python3-pip
COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

EXPOSE 5678

# CMD twistd --nodaemon --python callcenter_client.tac

