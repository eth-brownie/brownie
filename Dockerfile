# run with:
# docker build -f Dockerfile -t brownie .
# docker run -v $PWD:/usr/src brownie brownie

FROM ubuntu:bionic
WORKDIR /usr/src

RUN  apt-get update

RUN apt-get install -y python3.6 python3-pip python3-venv wget curl git npm nodejs

RUN npm install -g ganache-cli@6.2.5

RUN curl https://raw.githubusercontent.com/HyperLink-Technology/brownie/master/brownie-install.sh | sh

# Brownie installs compilers at runtime so ensure the updates are
# in the compiled image so it doesn't do this every time
RUN brownie init; true
RUN brownie test

# Fix UnicodeEncodeError error when running tests
ENV PYTHONIOENCODING=utf-8 
