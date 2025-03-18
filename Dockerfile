ARG venv_python=3.12
FROM python:${venv_python}

LABEL Maintainer="CanDIG Project"
LABEL "candigv2"="federation_service"

USER root

RUN groupadd -r candig && useradd -rm candig -g candig

RUN apt-get update && apt-get -y install

COPY requirements.txt /app/federation/requirements.txt

RUN pip install --no-cache-dir -r /app/federation/requirements.txt

COPY . /app/federation

WORKDIR /app/federation

RUN chown -R candig:candig /app/federation

RUN mkdir /app/config

RUN chown -R candig:candig /app/config
RUN touch /app/initial_setup
RUN chmod 777 /app/initial_setup

USER candig

ENTRYPOINT ["bash", "entrypoint.sh"]
