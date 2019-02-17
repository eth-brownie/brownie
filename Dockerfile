# run with:
# docker build -f Dockerfile -t brownie .
# docker run -v $PWD:/usr/src brownie brownie
# If you need to update the version of brownie then run the docker
# build command again

# For developers: to run local brownie code in docker you can use something like:
# docker run -v $PWD:/usr/src -v $PWD/../brownie/lib:/usr/local/lib/brownie/lib brownie brownie test

FROM ubuntu:bionic
WORKDIR /usr/src

RUN  apt-get update

RUN apt-get install -y python3.6 python3-pip python3-venv wget curl git npm nodejs sudo

RUN npm install -g ganache-cli@6.2.5

RUN curl https://raw.githubusercontent.com/HyperLink-Technology/brownie/master/brownie-install.sh | sh

# Brownie installs compilers at runtime so ensure the updates are
# in the compiled image so it doesn't do this every time
RUN brownie init
RUN brownie test

# Fix UnicodeEncodeError error when running tests
ENV PYTHONIOENCODING=utf-8

# c.f https://github.com/moby/moby/pull/10682#issuecomment-178794901
# Prevent Docker from caching the rest of the commands
# This means we can re-run the build to update brownie without the
# full re-build that adding --no-cache would cause.
ADD http://worldclockapi.com/api/json/est/now /tmp/bustcache
RUN brownie --update
