#!/usr/bin/env bash
API=${API:-http://127.0.0.1:8001}

MID=$(curl -s -X POST "$API/agent/mission/save" -H "Content-Type: application/json"   -d '{"title":"Quick Mission","goal":"Schnellstart Mission für Demo","owner":"agent"}' | jq -r .mission.id)

echo "Mission: $MID"

curl -s -X POST "$API/agent/task/save" -H "Content-Type: application/json"   -d "{"mission_id":$MID,"title":"Research Persona","kind":"research","payload":{"query":"Persona","k":5}}" | jq .

curl -s "$API/agent/mission/$MID/tasks" | jq .
