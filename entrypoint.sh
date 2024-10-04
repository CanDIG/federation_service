#!/usr/bin/env bash

set -Euo pipefail

export TYK_SECRET_KEY=$(cat /run/secrets/tyk-secret-key)



if [[ -f "initial_setup" ]]; then
    rm initial_setup
fi

# use the following for development
#python3 -m candig_federation

python candig_federation/heartbeat.py &

# use the following instead for production deployment
cd candig_federation
gunicorn server:application