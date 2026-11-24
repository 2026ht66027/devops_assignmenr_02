# Kubernetes deployment guide

The manifests use the `aceest` namespace and expect a container image named `aceest-fitness`. Replace image references or set the image with `kubectl set image` after applying the manifests.

## 1. Local deployment with Minikube

Install Docker, `kubectl` and Minikube first. Then:

```bash
minikube start --driver=docker
# Build directly into Minikube's image store.
eval "$(minikube docker-env)"
docker build -t aceest-fitness:local .
./scripts/deploy-minikube.sh aceest-fitness:local
kubectl get all -n aceest
minikube service aceest-fitness -n aceest --url
```

Open the URL printed by the last command. Check the health endpoint by appending `/health`.

If you prefer a locally running Docker daemon, load the image into Minikube instead:

```bash
docker build -t aceest-fitness:local .
minikube image load aceest-fitness:local
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rolling/
kubectl set image deployment/aceest-fitness aceest-fitness=aceest-fitness:local -n aceest
kubectl rollout status deployment/aceest-fitness -n aceest
```

## 2. Rolling update (default)

The default deployment uses three replicas, `maxUnavailable: 0`, readiness/liveness probes and a PodDisruptionBudget.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rolling/
kubectl set image deployment/aceest-fitness \
  aceest-fitness=<dockerhub-user>/aceest-fitness:<tag> -n aceest
kubectl rollout status deployment/aceest-fitness -n aceest
kubectl rollout history deployment/aceest-fitness -n aceest
```

Rollback to the previous ReplicaSet:

```bash
kubectl rollout undo deployment/aceest-fitness -n aceest
kubectl rollout status deployment/aceest-fitness -n aceest
```

## 3. Blue-green deployment

Blue and green are deployed side by side. The Service selector decides which version receives normal traffic. Deploy and verify green first:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/blue-green/blue-deployment.yaml
kubectl apply -f k8s/blue-green/green-deployment.yaml
kubectl apply -f k8s/blue-green/service.yaml
kubectl set image deployment/aceest-green \
  aceest-fitness=<dockerhub-user>/aceest-fitness:<new-tag> -n aceest
kubectl rollout status deployment/aceest-green -n aceest
```

Switch traffic to green:

```bash
kubectl patch service aceest-fitness -n aceest \
  -p '{"spec":{"selector":{"app":"aceest-fitness","track":"green"}}}'
```

Rollback to blue by changing `track` back to `blue` in the same patch. Keep the previous deployment available until the new version is accepted.

## 4. Canary release

The canary Deployment and Service are in `k8s/canary/`. Deploy the canary and verify it directly before routing a small portion of production traffic to it:

```bash
kubectl apply -f k8s/canary/
kubectl set image deployment/aceest-canary \
  aceest-fitness=<dockerhub-user>/aceest-fitness:<candidate-tag> -n aceest
kubectl rollout status deployment/aceest-canary -n aceest
kubectl port-forward service/aceest-canary 8081:80 -n aceest
```

A separate Service is not weighted canary routing by itself. To send (for example) 10% of requests to the canary, configure weighted routing in an ingress controller or service mesh (such as an Istio VirtualService) and increase the weight gradually while watching errors and latency. Roll back by setting the canary weight to zero and removing the canary after validation.

## 5. Shadow deployment

The shadow Deployment and Service are in `k8s/shadow/`. Deploy the candidate and test it directly:

```bash
kubectl apply -f k8s/shadow/
kubectl set image deployment/aceest-shadow \
  aceest-fitness=<dockerhub-user>/aceest-fitness:<candidate-tag> -n aceest
kubectl rollout status deployment/aceest-shadow -n aceest
```

Shadow traffic must be mirrored by an ingress controller or service mesh to the shadow Service while the live response continues to come from the stable Service. Do not expose shadow responses to end users. The provided Service/Deployment are the workload targets; traffic mirroring is an ingress/service-mesh configuration step and is not enabled by a vanilla Service.

## 6. A/B testing

The B variant is in `k8s/ab/`. Deploy it and verify it independently:

```bash
kubectl apply -f k8s/ab/
kubectl set image deployment/aceest-variant-b \
  aceest-fitness=<variant-b-tag> -n aceest
kubectl rollout status deployment/aceest-variant-b -n aceest
```

Route users consistently to variant A or B using an ingress controller, application gateway or service mesh with a stable cohort rule (cookie/header/user segment). Compare the chosen product metrics, then promote the winner by changing the stable Service selector/image. A separate Service alone does not perform cohort assignment.

## 7. Endpoint access and cleanup

For Minikube, `minikube service aceest-fitness -n aceest --url` provides the local endpoint. For a cloud cluster, create an Ingress or LoadBalancer Service and configure DNS/TLS according to the provider.

```bash
kubectl get pods,svc,deploy -n aceest
kubectl describe deployment aceest-fitness -n aceest
kubectl delete namespace aceest  # removes the coursework deployment
```

## Coursework caveats

- These examples demonstrate the Kubernetes workload and traffic-switching concepts. Weighted canary, shadow mirroring and A/B cohort selection need an ingress controller/service mesh configuration; they are not automatically active just because the Deployments and Services exist.
- The application stores data in SQLite. The example uses an ephemeral volume and is not suitable for durable multi-replica production data.
- Use image tags tied to commits (not only `latest`) for traceability.
