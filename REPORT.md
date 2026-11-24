# ACEest Fitness & Gym — Assignment 2 Report

**Course:** Introduction to DevOps  
**Project contributors:** Sush, Chinmayi and Suhas

## 1. Application and CI/CD architecture

ACEest Fitness & Gym is implemented as a Flask web application. It displays three fitness programmes and supports basic client registration and deletion. The `/health` and `/ready` endpoints provide container and Kubernetes health checks. The earlier Python application versions supplied with Assignment 1 are retained in `legacy_versions/` for reference.

The source is maintained in Git and hosted on GitHub. Jenkins checks out each change, installs the Python dependencies and runs the Pytest suite. SonarQube performs static analysis and the quality gate controls whether the pipeline proceeds. For commits on `main`, Jenkins builds a Docker image, tags it with the short Git commit SHA, pushes it to Docker Hub and updates the Kubernetes Deployment. Kubernetes readiness/liveness probes and rollout status checks help verify that the new Pods become healthy.

## 2. Deployment and rollback

The default Kubernetes deployment uses a rolling update with three replicas, `maxSurge: 1` and `maxUnavailable: 0`. The repository also contains separate workload examples and operating steps for blue-green, canary, shadow and A/B deployment patterns. Blue-green promotion is performed by switching the stable Service selector; a rolling deployment can be reverted with `kubectl rollout undo`.

Weighted canary routing, shadow request mirroring and A/B cohort assignment require an ingress controller or service mesh. The provided Deployments and Services are the Kubernetes workload targets; the routing policies must be configured in that traffic-management layer. The Minikube walkthrough in `k8s/README.md` provides a repeatable local deployment path and endpoint access instructions.

## 3. Challenges and mitigation

A key design consideration is separating application health from deployment readiness. Dedicated `/health` and `/ready` endpoints are used by container/Kubernetes checks. The pipeline uses commit-based image tags for traceability and waits for Kubernetes rollout completion rather than treating an image push as a successful deployment. Deployment strategy examples also distinguish between workload creation and the traffic-routing configuration required for progressive delivery.

The application uses SQLite to keep the coursework setup lightweight. This is not a suitable shared data store for multiple production replicas, and the sample Kubernetes volume is ephemeral. A production version would use a managed database or a properly designed persistent storage layer, along with backups, TLS, restricted RBAC and image scanning.

## 4. Automation outcomes

The repository contains the Flask application, the supplied earlier versions, Pytest tests, Jenkinsfile, SonarQube configuration, Dockerfile, Kubernetes manifests, deployment/rollback scripts and setup documentation. The intended automated workflow is test → quality analysis → image build/publish → Kubernetes rollout. Live execution of Jenkins, SonarQube, Docker Hub publication and Kubernetes deployment depends on configuring the external services and credentials described in `docs/CI-CD-architecture.md`.
