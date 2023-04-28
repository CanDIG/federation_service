#!/usr/bin/env bash

set -Euo pipefail

export CANDIG_OPA_SECRET=$(cat /run/secrets/opa-service-token)

if [[ -f "initial_setup" ]]; then
    rm initial_setup
fi

# use the following for development
#python3 -m candig_federation

# use the following instead for production deployment
uwsgi federation.ini