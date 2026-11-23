FROM python:3.12

# Set up code directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install linux dependencies
RUN apt-get update \
 && apt-get install -y libssl-dev npm

RUN npm install n -g \
 && npm install -g npm@latest
RUN npm install -g ganache

COPY requirements.txt .
COPY pyproject.toml uv.lock ./

RUN pip install uv
RUN uv pip install --system -r requirements.txt
RUN uv export --locked --only-group dev --no-hashes --output-file /tmp/brownie-dev-requirements.txt \
 && uv pip install --system -r /tmp/brownie-dev-requirements.txt

WORKDIR /code
