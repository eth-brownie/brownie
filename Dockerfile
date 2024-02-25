FROM ghcr.io/foundry-rs/foundry:nightly as foundry

FROM python:3.9

# Install linux dependencies
RUN --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update \
    && apt-get install --no-install-recommends -y curl libssl-dev

# install node v18 for ganache and hardhat
# c22ac94432765ecaa9b4c462b9a7f8dd509071da is v8.2.0
RUN --mount=type=cache,target=/root/.cache \
    curl -L https://raw.githubusercontent.com/tj/n/c22ac94432765ecaa9b4c462b9a7f8dd509071da/bin/n -o /usr/local/bin/n \
    && chmod 755 /usr/local/bin/n \
    && n 18 \
    && npm set cache /root/.cache/npm --global \
    && npm install -g npm@latest

# install ganache
RUN --mount=type=cache,target=/root/.cache \
    npm install --verbose --global "ganache@7.2.0"

# (hardhat is installed with npx if needed)

# prepare python dependencies
ENV PIP_NO_WARN_ABOUT_ROOT_USER 0
RUN --mount=type=cache,target=/root/.cache \
    pip install --upgrade pip setuptools wheel

# install anvil
COPY --from=foundry /usr/local/bin/anvil /usr/local/bin/

# install python dependencies
WORKDIR /usr/src/app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

COPY requirements-dev.txt .
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements-dev.txt

# Set up code directory
# use docker volumes to mount brownie's code at /code
WORKDIR /code
