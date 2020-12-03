FROM python:3.6-buster

RUN apt-get update && apt-get install -y software-properties-common

# Set up code directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install linux dependencies
RUN apt-get update && apt-get install -y libssl-dev

RUN curl -sL https://deb.nodesource.com/setup_15.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g ganache-cli

COPY requirements.txt .
COPY requirements-dev.txt .

RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt

WORKDIR /code

RUN curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim.appimage && chmod u+x nvim.appimage && ./nvim.appimage --appimage-extract && ./squashfs-root/AppRun --version && mv squashfs-root / && ln -s /squashfs-root/AppRun /usr/bin/nvim
RUN mkdir -p ~/.local/share/nvim/site/pack/coc/start && cd ~/.local/share/nvim/site/pack/coc/start && curl --fail -L https://github.com/neoclide/coc.nvim/archive/release.tar.gz|tar xzfv -

RUN nvim +'CocInstall -sync coc-pyright' +qall
RUN nvim +CocUpdateSync +qall
