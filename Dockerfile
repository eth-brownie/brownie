FROM ghcr.io/foundry-rs/foundry:v1.7.1@sha256:8347b728d5d393dac1c018691b36f506d23b9dcd78341d40ea0fcb11c3a19cdd AS foundry

FROM python:3.12

# Set up code directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install linux dependencies
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked apt-get update \
 && apt-get install -y libssl-dev npm

RUN --mount=type=cache,target=/root/.npm,sharing=locked npm install -g ganache@7.9.2

COPY requirements.txt .
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked pip install uv==0.11.16
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked uv pip install --system -r requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked UV_PYTHON_INSTALL_DIR=/root/.cache/uv/python uv export --locked --python 3.10.20 --only-group dev --no-hashes --output-file /tmp/brownie-dev-requirements.txt \
 && uv pip install --system -r /tmp/brownie-dev-requirements.txt

COPY --from=foundry /usr/local/bin/anvil /usr/local/bin/anvil

WORKDIR /code
