#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-aceest-fitness:local}"
NAMESPACE="aceest"

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rolling/
kubectl set image deployment/aceest-fitness \
  "aceest-fitness=${IMAGE}" -n "${NAMESPACE}"
kubectl rollout status deployment/aceest-fitness -n "${NAMESPACE}" --timeout=180s
kubectl get pods,svc -n "${NAMESPACE}"
