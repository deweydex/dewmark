#!/bin/bash
# usage: restart.sh <OLLAMA_ORIGINS value or -> <tag>
cd "$(dirname "$0")"
[ -f ollama.pid ] && kill $(cat ollama.pid) 2>/dev/null; sleep 1
for p in $(pgrep -x ollama); do kill $p 2>/dev/null; done; sleep 1
if [ "$1" = "-" ]; then unset OLLAMA_ORIGINS; else export OLLAMA_ORIGINS="$1"; fi
OLLAMA_MODELS=$PWD/models OLLAMA_HOST=${OLLAMA_HOST:-127.0.0.1:11434} OLLAMA_NO_CLOUD=1 nohup ./x/bin/ollama serve > "serve-$2.log" 2>&1 &
echo $! > ollama.pid; sleep 3
