# PodTriage 🩺☸️
### Automated SRE Incident-Response & Pod Diagnostic Engine for Kubernetes

[![GitHub Actions CI/CD](https://github.com/Durvankur-aiml/podtraige/actions/workflows/ci.yml/badge.svg)](https://github.com/Durvankur-aiml/podtraige/actions/workflows/ci.yml)
[![Docker Image](https://img.shields.io/badge/docker-podtriage%3Av1.0-blue?logo=docker)](file:///d:/podtraige/Dockerfile)
[![Kubernetes RBAC](https://img.shields.io/badge/kubernetes-v1.30+-326CE5?logo=kubernetes)](file:///d:/podtraige/k8s)
[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python)](file:///d:/podtraige/podtriage.py)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📌 Project Overview

**PodTriage** is a lightweight, production-grade Site Reliability Engineering (SRE) diagnostic utility engineered to detect, classify, and troubleshoot degraded Kubernetes workloads across all cluster namespaces in real time.

When distributed microservices degrade due to kernel memory kills, expired registry tokens, or scheduling bottlenecks, manual investigation using raw `kubectl describe` or `kubectl logs` slows down Mean Time to Resolution (MTTR). **PodTriage** automates root-cause analysis by evaluating container exit codes, termination states, restart velocity, and failure reasons, outputting color-coded diagnostic tables paired with immediate, actionable remediation steps.

### Key Capabilities
- **Comprehensive Failure Pattern Recognition**:
  - `CrashLoopBackOff` with exit code introspection (`137` OOMKilled, `1` application unhandled exception, `143` SIGTERM).
  - `ImagePullBackOff` / `ErrImagePull` (expired tokens, invalid credentials, missing tags).
  - `Pending` (CPU/RAM exhaustion, taint/toleration mismatches, node affinity constraints).
  - `Evicted` (node disk pressure, memory pressure thresholds).
- **Graceful Zero-Dependency Fallback**: Automatically activates a simulated production incident benchmark across `production`, `monitoring`, and `default` namespaces if the live cluster daemon is unreachable.
- **Enterprise DevOps Architecture**: Packaged into an ultra-lean Alpine container, automated via Kubernetes CronJobs & RBAC, and validated on every push with GitHub Actions.

---

## 🏗️ Architecture & Workflow Diagram

```
                 +-------------------------------------------------------------+
                 |                 Kubernetes Cluster (API Server)             |
                 +-------------------------------------------------------------+
                                      |                             |
                                      | (Query Pods & Events)       | (Scheduled Job)
                                      v                             v
+-----------------------+     +------------------+     +-------------------------------+
| SRE On-Call Engineer  |     |   PodTriage CLI  |     | Kubernetes CronJob Scanner    |
| (Interactive Terminal)| --> |   Diagnostic     | <-- | (k8s/cronjob.yaml: */15 * * *)|
+-----------------------+     |   Rule Engine    |     +-------------------------------+
                              +------------------+
                                        |
       +--------------------------------+--------------------------------+
       |                                |                                |
       v                                v                                v
+----------------------+     +----------------------+     +----------------------+
| CrashLoopBackOff     |     | ImagePullBackOff     |     | Evicted / Pending    |
| Root Cause & Memory  |     | Registry Credential  |     | Scheduler & Storage  |
| Remediation (Exit 137|     | Token Rotation Steps |     | Pressure Diagnostics |
+----------------------+     +----------------------+     +----------------------+
```

---

## 🛠️ DevOps & Kubernetes Tool Integrations Breakdown

PodTriage implements a three-tier DevOps architecture integrating industry-standard tools:

### 1. Docker (Containerization & Runtime Hardening)
- **Base Image**: `python:3.11-alpine` for an ultra-small image footprint (~20MB compressed).
- **Security & Portability**: Runs with non-root security principles, self-contained dependencies, and clean entrypoints (`ENTRYPOINT ["python", "/app/podtriage.py"]`).
- **Build Efficiency**: Incorporates `.dockerignore` to filter out local virtualenvs, cache files, and repository metadata, speeding up image creation and maintaining supply-chain hygiene.

### 2. Kubernetes (RBAC, Automated Scheduling & Workload Testing)
- **Least-Privilege RBAC (`k8s/rbac.yaml`)**:
  - `ServiceAccount: podtriage-sa`
  - `ClusterRole: podtriage-reader` with read-only API access (`get`, `list`, `watch`) restricted to `pods`, `pods/log`, `pods/status`, and `events`.
  - `ClusterRoleBinding: podtriage-reader-binding` binding the reader role strictly to the triage service account.
- **Continuous SRE CronJob (`k8s/cronjob.yaml`)**:
  - Runs every 15 minutes (`schedule: "*/15 * * * *"`) with concurrency policy `Forbid` and resource quotas (`cpu: 100m`, `memory: 128Mi`).
- **Failure Simulation Workload (`k8s/test-workloads.yaml`)**:
  - Sample `auth-service-oom` deployment with a strict `16Mi` memory limit that deliberately triggers Linux cgroup memory violations (Exit 137) to benchmark scanner detection accuracy.

### 3. GitHub Actions (Automated CI/CD Validation Pipeline)
- **Pipeline (`.github/workflows/ci.yml`)**:
  - **Job 1: `lint-and-validate`**: Verifies Python code syntax with `py_compile`, tests simulated cluster execution, and validates structured JSON telemetry exports.
  - **Job 2: `docker-build-check`**: Leverages Docker Buildx to build image `podtriage:ci` and executes a containerized verification run in the CI runner.
  - **Job 3: `k8s-manifest-lint`**: Multi-document YAML validation engine validating all manifests in `k8s/*.yaml` before deployment.

---

## 📸 Proof of Implementation & Screenshots

### 1. Core CLI Diagnostic Output
*Live terminal diagnostic table rendering namespaces, degraded health states, restart counts, root causes, and actionable fixes.*

![Core CLI Diagnostic Output](screenshots/01-cli-execution.png)

---

### 2. Docker Containerization & Verification
*Building the lightweight Alpine container image (`podtriage:v1.0`) and validating container execution.*

![Docker Containerization Verification](screenshots/02-docker-build.png)

---

### 3. Kubernetes Orchestration & Manifest Validation
*Client dry-run validation confirming Kubernetes RBAC, scheduled CronJob, and OOM test workload definitions.*

![Kubernetes Manifest Validation](screenshots/03-k8s-manifests.png)

---

### 4. GitHub Actions CI/CD Pipeline Execution
*Automated 3-stage validation pipeline running code linting, container builds, and Kubernetes manifest validation.*

![GitHub Actions CI/CD Pipeline](screenshots/04-github-actions.png)

---

## 🚀 Local Setup & Usage Guide

### Prerequisites
- Python 3.10+
- Docker Engine 24.0+
- `kubectl` CLI configured with cluster context (optional; simulated fallback activates automatically if cluster is offline)

### Option A: Running CLI Locally
```bash
# Clone the repository
git clone https://github.com/Durvankur-aiml/podtraige.git
cd podtraige

# Run cluster scan across all namespaces
python podtriage.py

# Filter by specific namespace
python podtriage.py -n production

# Export structured JSON diagnostics (for SIEM / PagerDuty integration)
python podtriage.py --json

# Run in benchmark simulation mode
python podtriage.py --simulate
```

### Option B: Running with Docker
```bash
# Build the production image
docker build -t podtriage:v1.0 .

# Execute containerized triage scan
docker run --rm podtriage:v1.0

# Scan in simulation mode
docker run --rm podtriage:v1.0 --simulate
```

### Option C: Deploying to Kubernetes
```bash
# Validate manifests via dry-run
kubectl apply -f k8s/ --dry-run=client

# Deploy RBAC permissions and Scheduled CronJob scanner
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/cronjob.yaml

# Deploy degraded test workload to trigger OOM triage
kubectl apply -f k8s/test-workloads.yaml

# Manually trigger a triage job from the CronJob
kubectl create job --from=cronjob/podtriage-scheduled-scan manual-scan-01

# Inspect diagnostic logs from the pod
kubectl logs job/manual-scan-01
```

---

## 📋 Project Submission Details

| Field | Detail |
| :--- | :--- |
| **Project Name** | `podtriage` - Kubernetes Pod Health & Incident Triage Engine |
| **Course / Subject** | DevOps and Kubernetes |
| **Assessment** | In-Semester Evaluation 2 (ISE-2) |
| **Author / Developer** | Durvankur Tibile |
| **Repository URL** | [https://github.com/Durvankur-aiml/podtraige.git](https://github.com/Durvankur-aiml/podtraige.git) |
| **Repository Branch** | `main` |
| **Commit Target** | 4 Sequential Semantic Commits (Core CLI, Docker, Kubernetes, CI/CD Docs) |

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
