ARG venv_python
ARG alpine_version
FROM python:${venv_python}-alpine${alpine_version}

LABEL Maintainer="CanDIG Project"

USER root

RUN apk update

RUN apk add --no-cache \
  autoconf \
  automake \
  make \
  gcc \
  linux-headers \
  perl \
  bash \
  build-base \
  musl-dev \
  zlib-dev \
  bzip2-dev \
  xz-dev \
  libcurl \
  curl \
  curl-dev \
  yaml-dev \
  libressl-dev \
  pcre-dev \
  git

RUN addgroup candig

COPY requirements.txt /app/federation/requirements.txt

RUN pip install --no-cache-dir -r /app/federation/requirements.txt

COPY . /app/federation

WORKDIR /app/federation

RUN mkdir /app/config

ENTRYPOINT ["bash", "entrypoint.sh"]
