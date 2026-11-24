#!/usr/bin/env bash
set -euo pipefail
NAMESPACE="${1:-aceest}"
kubectl rollout undo deployment/aceest-fitness -n "${NAMESPACE}"
kubectl rollout status deployment/aceest-fitness -n "${NAMESPACE}" --timeout=180s
