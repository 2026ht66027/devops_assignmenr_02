# ACEest Fitness & Gym — DevOps Assignment 2

A small Flask-based fitness-club application with a Jenkins CI/CD pipeline and Kubernetes deployment examples. The project is arranged around the requirements in the BITS Pilani *Introduction to DevOps* Assignment 2 brief.

**Project contributors:** Sush, Chinmayi and Suhas.

## Application

The Flask application supports:

- Viewing the fitness programmes (Fat Loss, Muscle Gain and Beginner).
- Registering a client with a name, age and fitness goal.
- Deleting a client record.
- Liveness and readiness checks at `/health` and `/ready`.

The ten Python files supplied with Assignment 1 are retained in `legacy_versions/` as the earlier application versions. The current Flask web application is in `app.py`.

## Repository layout

```text
app.py                    Flask application
legacy_versions/          Earlier supplied application versions
templates/                HTML templates
static/                   CSS
 tests/                    Pytest tests
Jenkinsfile                CI/CD pipeline
Dockerfile                 Container build
sonar-project.properties  SonarQube configuration
k8s/                       Kubernetes manifests and strategy notes
scripts/                   Local deploy and rollback helpers
REPORT.md                  Assignment report
```

## Run locally

Python 3.12 or later is recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
pytest -v
python app.py
```

Open `http://127.0.0.1:5000`. The health endpoint is `http://127.0.0.1:5000/health`.

## Build and run with Docker

```bash
docker build -t aceest-fitness:local .
docker run --rm -p 5000:5000 aceest-fitness:local
```

## Deploy to Kubernetes

See [`k8s/README.md`](k8s/README.md) for a Minikube walkthrough, endpoint access, rollout checks, rollback, and the five deployment patterns. The simplest local path is:

```bash
minikube start --driver=docker
eval "$(minikube docker-env)"
docker build -t aceest-fitness:local .
./scripts/deploy-minikube.sh aceest-fitness:local
minikube service aceest-fitness -n aceest --url
```

## Jenkins pipeline

The `Jenkinsfile` runs dependency installation, Pytest, SonarQube analysis and the quality gate on each build. Builds on `main` additionally build and publish a Docker Hub image tagged with the short Git commit SHA, then deploy that image using a Kubernetes rolling update.

Configure the Jenkins items described in [`docs/CI-CD-architecture.md`](docs/CI-CD-architecture.md) before enabling the publishing/deployment stages. The pipeline expects a Jenkins username/password credential named `dockerhub-credentials`, a SonarQube server named `SonarQube`, Docker CLI, `kubectl`, and a kubeconfig context on its agent.

## Notes and limitations

This is a coursework demonstration, not a production deployment. The sample app uses SQLite and the rolling Deployment mounts an ephemeral volume; replicas therefore do not share durable application data. Use a managed database or shared persistent storage for a real multi-replica deployment. Canary percentages, A/B cohort routing and shadow traffic mirroring need an ingress controller or service mesh; ordinary Kubernetes Services alone do not implement those traffic policies. The manifests and instructions identify the required routing component rather than implying that a plain Service provides it.
