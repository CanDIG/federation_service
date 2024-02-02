ARG venv_python
ARG alpine_version
FROM python:${venv_python}-alpine${alpine_version}

LABEL Maintainer="CanDIG Project"
LABEL "candigv2"="federation_service"

USER root

RUN apk update

RUN apk add --no-cache \
  autoconf \
  automake \
  make \
  gcc \
  linux-headers \
  libffi-dev \
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
  pcre-dev \
  git

RUN addgroup -S candig && adduser -S candig -G candig

COPY requirements.txt /app/federation/requirements.txt

RUN pip install --no-cache-dir -r /app/federation/requirements.txt

COPY . /app/federation

WORKDIR /app/federation

RUN chown -R candig:candig /app/federation

RUN mkdir /app/config

RUN chown -R candig:candig /app/config

USER candig

ENTRYPOINT ["bash", "entrypoint.sh"]
