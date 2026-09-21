#!/usr/bin/env bash
# Probe the API until it responds, then report.
cd "$(dirname "$0")"
ID=$(python3 -c "import json;print(json.load(open('state_k3.json'))['id'])")
z-ai async-result -i "$ID" -o /tmp/probe.json >/dev/null 2>&1
if [ -f /tmp/probe.json ]; then
  python3 -c "import json;d=json.load(open('/tmp/probe.json'));print('PROBE-OK status:', d.get('task_status'))"
else
  echo "PROBE-FAIL still limited"
fi
