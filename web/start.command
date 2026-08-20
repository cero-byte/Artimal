#!/bin/sh
set -eu
cd "$(dirname "$0")"

ARTIMAL_PORT="${ARTIMAL_PORT:-8920}"
export ARTIMAL_PORT
URL="http://127.0.0.1:${ARTIMAL_PORT}/"

echo "Starting Artimal at ${URL}"
echo "Keep this Terminal window open. Press Control+C to stop."
(sleep 1; open "${URL}") &
python3 server.py
