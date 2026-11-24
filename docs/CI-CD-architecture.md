# CI/CD architecture and Jenkins setup

## Pipeline flow

Git commit → GitHub → Jenkins checkout → dependency installation → Pytest → SonarQube analysis → quality gate → Docker build → Docker Hub publication → Kubernetes rolling deployment → rollout health check.

Tests and the quality gate run before the image is published. Image tags use the short Git commit SHA so a deployment can be traced to source. Only the `main` branch publishes and deploys.

## Jenkins prerequisites

Install/configure:

- Jenkins Pipeline, Git, Credentials Binding, JUnit, SonarQube Scanner and Workspace Cleanup plugins.
- A Python 3.12+ runtime, Docker CLI/daemon and `kubectl` on the build agent.
- A SonarQube server configured in **Manage Jenkins → System** with the name `SonarQube`.
- The SonarQube scanner tool configured in **Manage Jenkins → Tools**.
- A Jenkins username/password credential with ID `dockerhub-credentials`. Use the Docker Hub account username and an access token as the password.
- A Kubernetes context/kubeconfig available to the agent, with permission to manage Deployments, Services, Pods and namespaces in the target cluster.

Create a Multibranch Pipeline or Pipeline-from-SCM job pointing to this GitHub repository. Configure a GitHub webhook to trigger builds on pushes, or use SCM polling. The default branch must be `main` for the publishing/deployment stages to run.

## Docker Hub and Kubernetes

The Jenkins pipeline obtains the Docker Hub namespace from the configured credential username and publishes:

- `<dockerhub-user>/aceest-fitness:<short-git-sha>`
- `<dockerhub-user>/aceest-fitness:latest`

The Kubernetes deployment stage applies the namespace and rolling manifests, updates the Deployment image to the commit-tagged image and waits for rollout completion. The Kubernetes cluster must be able to pull the published image. For a private Docker Hub repository, create an imagePullSecret and reference it in the Pod spec.

## Rollback

If a deployment is unhealthy, inspect the rollout and return to the previous ReplicaSet:

```bash
kubectl rollout status deployment/aceest-fitness -n aceest
kubectl rollout history deployment/aceest-fitness -n aceest
kubectl rollout undo deployment/aceest-fitness -n aceest
```

## Progressive delivery

Rolling update is the automated default. The repository also contains blue-green, canary, shadow and A/B workload manifests with operational instructions in `k8s/README.md`. Blue-green traffic switching is implemented by changing the stable Service selector. Weighted canary, request mirroring and A/B cohort selection require ingress-controller or service-mesh configuration; a basic ClusterIP Service does not implement those policies.

## Security and operational notes

Do not commit credentials, kubeconfig files, `.env` files or tokens. Keep credentials in Jenkins Credentials and Kubernetes Secrets. This coursework app uses SQLite and an ephemeral Kubernetes volume; production use requires a durable shared database/storage design, backups, TLS, least-privilege RBAC, image scanning and pinned image digests.
