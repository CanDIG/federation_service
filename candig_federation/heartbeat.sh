until python candig_federation/heartbeat.py; do
    echo "Heartbeat crashed with exit code $?.  Respawning.." >&2
    sleep 1
done