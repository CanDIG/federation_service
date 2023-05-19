#!/usr/bin/env bash

set -Euo pipefail

export OPA_SECRET=$(cat /run/secrets/opa-service-token)
export TYK_SECRET_KEY=$(cat /run/secrets/tyk-secret-key)



if [[ -f "initial_setup" ]]; then
    rm initial_setup
fi

# use the following for development
#python3 -m candig_federation

# use the following instead for production deployment
uwsgi federation.ini