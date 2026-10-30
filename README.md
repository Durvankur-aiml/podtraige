<div align="center">

# PodTriage 🩺☸️
### Automated SRE Incident-Response & Pod Diagnostic Engine for Kubernetes

[![GitHub Actions CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/Durvankur-aiml/podtraige/actions/workflows/ci.yml)
[![Docker Alpine](https://img.shields.io/badge/Docker-3.11--alpine-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Kubernetes RBAC](https://img.shields.io/badge/Kubernetes-RBAC%20%26%20CronJob-326CE5?logo=kubernetes&logoColor=white)](k8s/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](podtriage.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Maintained](https://img.shields.io/badge/Status-Maintained%20%26%20Verified-brightgreen)](#-git-workflow--commit-history-showcase)

<p align="center">
  <strong>A lightweight, production-grade SRE diagnostic CLI engineered to detect, classify, and remediate degraded Kubernetes workloads across all cluster namespaces in real time.</strong>
</p>

</div>

---

## 📋 Table of Contents
- [🎯 Project Overview & Problem Statement](#-project-overview--problem-statement)
- [🏗️ System Architecture & Incident Triage Flow](#️-system-architecture--incident-triage-flow)
- [🛠️ Technology Stack](#️-technology-stack)
- [⚙️ DevOps & Kubernetes Tool Integrations](#️-devops--kubernetes-tool-integrations)
  - [1. Docker (Containerization & Runtime Hardening)](#1-docker-containerization--runtime-hardening)
  - [2. Kubernetes (RBAC, Scheduled CronJob & Resource Quotas)](#2-kubernetes-rbac-scheduled-cronjob--resource-quotas)
  - [3. GitHub Actions (Automated CI/CD Validation Pipeline)](#3-github-actions-automated-cicd-validation-pipeline)
- [🔄 Git Workflow & Commit History Showcase](#-git-workflow--commit-history-showcase)
- [📸 Implementation Proof Gallery](#-implementation-proof-gallery)
- [🚀 Quick Start & Local Setup Guide](#-quick-start--local-setup-guide)
- [📋 Academic & Evaluation Metadata](#-academic--evaluation-metadata)
- [📄 License](#-license)

---

## 🎯 Project Overview & Problem Statement

In microservice architectures deployed on Kubernetes, workloads frequently degrade due to memory ceiling breaches (kernel `OOMKilled`), expired container registry access tokens, unhandled startup panics, or scheduling constraints. 

Investigating these failures manually across multi-tenant clusters requires running disjointed commands (`kubectl get pods`, `kubectl describe`, `kubectl logs --previous`), extracting container exit codes, and cross-referencing node pressure events. This manual toil drastically increases **Mean Time to Resolution (MTTR)** during Sev-1/Sev-2 incidents.

**PodTriage** solves this by providing:
- **Instant Cluster-Wide Diagnostic Inspection**: Scans all namespaces simultaneously (`kubectl get pods -A -o json`) and analyzes container termination states in milliseconds.
- **Root-Cause Analysis Rule Engine**: Dissects Linux exit codes (e.g., `137` OOMKilled via cgroup memory ceiling, `1` unhandled exceptions, `143` SIGTERM) and registry failure strings (`ErrImagePull`, authentication token expiry).
- **Prescriptive SRE Remediation**: Pairs every degraded workload with concrete, immediate operational commands (e.g., manifest memory adjustments, secret rotation, node pressure drain commands).
- **Zero-Dependency High-Fidelity Fallback**: Automatically activates a simulated production incident dataset across `production`, `monitoring`, and `default` namespaces whenever the cluster API daemon is unreachable or unauthenticated.

---

## 🏗️ System Architecture & Incident Triage Flow

```
+-----------------------------------------------------------------------------------------+
|                                KUBERNETES CLUSTER ENVIRONMENT                           |
+-----------------------------------------------------------------------------------------+
       |                                                                   |
       | Live API Scan                                                     | Scheduled Triage
       | (kubectl get pods -A -o json)                                     | (k8s/cronjob.yaml)
       v                                                                   v
+------------------+         Fallback (Offline/Auth Failed)        +----------------------+
|  PodTriage CLI   | <============================================ | High-Fidelity Mock   |
| Diagnostic Engine|                                               | Production Benchmark |
+------------------+                                               +----------------------+
       |
       +---> [1] Inspection & State Extraction (phase, reason, containerStatuses)
       |
       +---> [2] Exit Code Introspection (Exit 137 = OOMKilled | Exit 1 = App Crash)
       |
       +---> [3] Pattern Recognition (ImagePullBackOff, Evicted, Pending, CrashLoop)
       |
       v
+-----------------------------------------------------------------------------------------+
|                              SRE INCIDENT REPORT OUTPUT                                 |
+-----------------------------------------------------------------------------------------+
|  - NAMESPACE   : Isolated failure scope (production, monitoring, default)               |
|  - POD NAME    : Target degraded workload identifier                                    |
|  - HEALTH STATE: Precise classified condition with exit code annotation                 |
|  - RESTARTS    : Container crash velocity indicator                                     |
|  - SRE ANALYSIS: Direct kernel/kubelet root cause + actionable fix command              |
+-----------------------------------------------------------------------------------------+
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Core Runtime** | Python 3.11 | High-performance diagnostic rule engine, JSON parsing & ASCII terminal table layout |
| **Containerization** | Docker (Alpine 3.11) | Ultra-lightweight container packaging with non-root security principles |
| **Orchestration** | Kubernetes v1.28+ | Least-privilege RBAC, automated 15-minute CronJob scanner & OOM failure simulation |
| **CI/CD Automation** | GitHub Actions | 3-stage validation pipeline: code linting, container build test, and YAML schema audit |
| **Version Control** | Git & GitHub | Strict sequential milestone development tracking with semantic commits |

---

## ⚙️ DevOps & Kubernetes Tool Integrations

PodTriage is built around three foundational pillars of cloud-native DevOps engineering:

### 1. Docker (Containerization & Runtime Hardening)
- **Base Image**: `python:3.11-alpine` for minimum image size (~20MB compressed).
- **Container Hardening**:
  - Sets explicit working directory (`/app`).
  - Pre-configures script execution permissions (`chmod +x /app/podtriage.py`).
  - Self-contained entrypoint: `ENTRYPOINT ["python", "/app/podtriage.py"]`.
- **Hygiene**: Uses `.dockerignore` to exclude local caches, virtual environments, and `.git` trees from production images.

### 2. Kubernetes (RBAC, Scheduled CronJob & Resource Quotas)
- **Least-Privilege RBAC (`k8s/rbac.yaml`)**:
  - `ServiceAccount: podtriage-sa`
  - `ClusterRole: podtriage-reader` explicitly restricted to read-only verbs (`get`, `list`, `watch`) on `pods`, `pods/log`, `pods/status`, and `events` across core and `events.k8s.io` API groups.
  - `ClusterRoleBinding: podtriage-reader-binding` binds the read-only role directly to the service account.
- **Continuous Scanner CronJob (`k8s/cronjob.yaml`)**:
  - Automated execution every 15 minutes (`schedule: "*/15 * * * *"`).
  - Hardened container spec with `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, and `restartPolicy: OnFailure`.
  - Enforces explicit resource quotas (`requests: cpu 50m, memory 64Mi` | `limits: cpu 100m, memory 128Mi`).
- **Failure Simulation Workload (`k8s/test-workloads.yaml`)**:
  - Deploys `auth-service-oom` with a strict `16Mi` memory limit to trigger intentional Linux cgroup OOM kills (Exit 137) for validating automated scanner accuracy.

### 3. GitHub Actions (Automated CI/CD Validation Pipeline)
- **Workflow File**: `.github/workflows/ci.yml`
- **Triggers**: Every `push` and `pull_request` targeting `main`.
- **Pipeline Architecture**:
  1. **Job 1: `lint-and-validate`**: Verifies Python bytecode syntax via `py_compile`, runs CLI simulation mode (`--simulate`), and checks structured JSON schema output (`--json`).
  2. **Job 2: `docker-build-check`**: Utilizes Docker Buildx to compile `podtriage:ci` and executes containerized smoke tests inside the runner.
  3. **Job 3: `k8s-manifest-lint`**: Parses and validates multi-document YAML syntax across all files in `k8s/*.yaml` before merging.

---

## 🔄 Git Workflow & Commit History Showcase

The project was constructed following strict, discipline-driven Git version control practices with incremental, single-responsibility semantic commits:

| Commit # | Hash | Scope / Milestone | Commit Message | Key Accomplishments |
| :---: | :---: | :--- | :--- | :--- |
| **#1** | `053fd4f` | **Core Engine** | `feat(core): implement kubernetes pod diagnostic triage engine and cli scanner` | Initialized repository, built `podtriage.py` with exit-code analysis, simulated fallback mode, and ASCII diagnostic box. |
| **#2** | `d66491c` | **Docker** | `feat(docker): package podtriage diagnostic cli into lightweight alpine container` | Created hardened `Dockerfile` (Python 3.11 Alpine), configured `.dockerignore`, built and verified `podtriage:v1.0`. |
| **#3** | `2a1a74f` | **Kubernetes** | `feat(k8s): define kubernetes rbac permissions, cronjob scanner, and test workloads` | Authored `k8s/rbac.yaml`, `k8s/cronjob.yaml` (15m scanner), and `k8s/test-workloads.yaml` (OOM reproduction workload). |
| **#4** | `28e2254` | **CI/CD & Docs** | `docs: finalize project readme with devops tool integration proofs and ci pipeline` | Integrated `.github/workflows/ci.yml` (3 CI jobs), generated proof screenshots, and structured comprehensive README. |
| **#5** | `72a2616` | **Academic Polish** | `docs: update author and submission details to Paras Sarnobat` | Updated project submission details, author credentials, and academic evaluation metadata. |

### Visual Git Milestone Log
![Git Commits History](screenshots/05-git-commits-history.png)
*Figure 5: Terminal git log verifying sequential semantic commit milestones and remote synchronization with GitHub main.*

---

## 📸 Implementation Proof Gallery

### 1. Core CLI Diagnostic Output
*Live terminal diagnostic table rendering namespaces, degraded health states, restart counts, root causes, and actionable fixes.*

![Core CLI Diagnostic Output](screenshots/01-cli-execution.png)
*Figure 1: PodTriage terminal diagnostic scan rendering degraded workload states and SRE remediation guidance.*

---

### 2. Docker Containerization & Verification
*Building the lightweight Alpine container image (`podtriage:v1.0`) and validating container execution.*

![Docker Containerization Verification](screenshots/02-docker-build.png)
*Figure 2: Docker build output and successful zero-dependency containerized execution test.*

---

### 3. Kubernetes Orchestration & Manifest Validation
*Client dry-run validation confirming Kubernetes RBAC, scheduled CronJob, and OOM test workload definitions.*

![Kubernetes Manifest Validation](screenshots/03-k8s-manifests.png)
*Figure 3: Client dry-run validation output proving syntax and API schema validity across all Kubernetes manifests.*

---

### 4. GitHub Actions CI/CD Pipeline Execution
*Automated 3-stage validation pipeline running code linting, container builds, and Kubernetes manifest validation.*

![GitHub Actions CI/CD Pipeline](screenshots/04-github-actions.png)
*Figure 4: GitHub Actions CI/CD pipeline verifying all 3 jobs passed successfully on branch main.*

---

## 🚀 Quick Start & Local Setup Guide

### Prerequisites
- Python 3.10+
- Docker Engine 24.0+
- `kubectl` CLI (optional; automated high-fidelity fallback activates if cluster is offline)

### Option A: Local Python Execution
```bash
# Clone the repository
git clone https://github.com/Durvankur-aiml/podtraige.git
cd podtraige

# Run cluster diagnostic scan across all namespaces
python podtriage.py

# Filter triage to a specific namespace
python podtriage.py -n production

# Export structured JSON diagnostics (for SIEM, PagerDuty, or Slack webhooks)
python podtriage.py --json

# Force benchmark simulation mode
python podtriage.py --simulate
```

### Option B: Docker Container Execution
```bash
# Build the production container image
docker build -t podtriage:v1.0 .

# Run the diagnostic container
docker run --rm podtriage:v1.0

# Run container in simulation mode
docker run --rm podtriage:v1.0 --simulate
```

### Option C: Kubernetes In-Cluster Deployment
```bash
# Validate manifests via dry-run
kubectl apply -f k8s/ --dry-run=client

# Deploy RBAC permissions and 15-minute scheduled CronJob scanner
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/cronjob.yaml

# Deploy degraded test workload to trigger OOM triage
kubectl apply -f k8s/test-workloads.yaml

# Manually trigger an immediate scan from the CronJob
kubectl create job --from=cronjob/podtriage-scheduled-scan manual-scan-01

# Inspect diagnostic report in job pod logs
kubectl logs job/manual-scan-01
```

---

## 📋 Academic & Evaluation Metadata

| Field | Detail |
| :--- | :--- |
| **Project Title** | `podtriage` - Kubernetes Pod Health & Incident Triage Engine |
| **Subject / Course** | DevOps and Kubernetes (ISE-2) |
| **Student Name** | **Paras Sarnobat** |
| **Assessment Type** | In-Semester Evaluation 2 (ISE-2) |
| **Repository URL** | [https://github.com/Durvankur-aiml/podtraige.git](https://github.com/Durvankur-aiml/podtraige.git) |
| **Primary Branch** | `main` |
| **DevOps Tools Covered** | Docker, Kubernetes (RBAC & CronJobs), GitHub Actions CI/CD, Git Version Control |

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
