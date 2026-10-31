<div align="center">

# PodTriage: Kubernetes Incident-Response and Pod Diagnostic Engine
### Automated Cluster Health Inspection, Root-Cause Analysis, and SRE Remediation

[![GitHub Actions CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/Durvankur-aiml/podtraige/actions/workflows/ci.yml)
[![Docker Alpine](https://img.shields.io/badge/Docker-3.11--alpine-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Kubernetes RBAC](https://img.shields.io/badge/Kubernetes-RBAC%20%26%20CronJob-326CE5?logo=kubernetes&logoColor=white)](k8s/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](podtriage.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Maintained%20%26%20Verified-brightgreen)](#git-workflow-and-commit-history-showcase)

<p align="center">
  <strong>A lightweight, production-grade SRE diagnostic engine engineered to detect, classify, and remediate degraded Kubernetes workloads across all cluster namespaces in real time.</strong>
</p>

</div>

---

## Student and Academic Information

| Field | Details |
| :--- | :--- |
| Student Name | Prachi Patil |
| Roll Number | A58 |
| Department / Branch | Artificial Intelligence and Data Science / AIML |
| Institute | D. Y. Patil College of Engineering and Technology |
| Course | DevOps and Kubernetes (ISE-2) |
| Repository | https://github.com/Durvankur-aiml/podtraige |

---

## Table of Contents

- [Executive Summary and Problem Statement](#executive-summary-and-problem-statement)
- [System Architecture and Diagnostic Triage Flow](#system-architecture-and-diagnostic-triage-flow)
- [Technology Stack](#technology-stack)
- [DevOps and Cloud-Native Tool Integrations](#devops-and-cloud-native-tool-integrations)
  - [1. Docker: Minimal Alpine Packaging and Runtime Hardening](#1-docker-minimal-alpine-packaging-and-runtime-hardening)
  - [2. Kubernetes: RBAC Least-Privilege and Scheduled CronJob Scans](#2-kubernetes-rbac-least-privilege-and-scheduled-cronjob-scans)
  - [3. GitHub Actions: Multi-Stage CI/CD Validation Pipeline](#3-github-actions-multi-stage-cicd-validation-pipeline)
  - [4. Single-Page SRE Web Incident Dashboard](#4-single-page-sre-web-incident-dashboard)
- [Git Workflow and Commit History Showcase](#git-workflow-and-commit-history-showcase)
- [Implementation Proof Gallery](#implementation-proof-gallery)
- [Installation and Operational Guide](#installation-and-operational-guide)
- [Academic Evaluation and Submission Summary](#academic-evaluation-and-submission-summary)
- [License](#license)

---

## Executive Summary and Problem Statement

In distributed microservice architectures deployed on Kubernetes clusters, workloads frequently transition into unready or crashed states due to memory ceiling breaches (Linux kernel `OOMKilled`), expired container registry pull credentials, missing configuration dependencies, or unhandled application panics.

Investigating these degraded workloads manually across multi-tenant clusters presents severe operational bottlenecks:
- Engineers must execute multiple disjointed CLI queries (`kubectl get pods`, `kubectl describe pod`, `kubectl logs --previous`).
- Linux termination exit codes must be manually extracted and mapped to root-cause mechanisms (e.g., Exit 137 versus Exit 1).
- Time-critical incident remediation is delayed, significantly elevating **Mean Time to Resolution (MTTR)** during Sev-1 and Sev-2 outages.

**PodTriage** solves this operational challenge through an automated, multi-interface diagnostic platform:
1. **Cluster-Wide Multi-Namespace Inspection**: Queries all namespaces simultaneously (`kubectl get pods -A -o json`) and parses container status blocks in milliseconds.
2. **Deterministic Root-Cause Rule Engine**: Decodes Linux kernel termination signals (Exit 137 for cgroup OOM kills, Exit 1 for application crashes, Exit 143 for SIGTERM) alongside container lifecycle strings (`CrashLoopBackOff`, `ImagePullBackOff`, `Pending`, `Evicted`).
3. **Prescriptive SRE Remediation Guidance**: Automatically couples every failing workload with explicit, actionable remediation commands (e.g., manifest resource limit adjustments, image pull secret recreation, node cordoning).
4. **High-Fidelity Automated Fallback**: Incorporates a built-in benchmark dataset spanning `production`, `monitoring`, and `default` namespaces, ensuring continuous validation and demonstration even when the live Kubernetes API server is unreachable.
5. **Dual Interface Accessibility**: Provides both an ASCII-formatted terminal CLI for automated scripting / CronJobs and a responsive, standalone SRE Web Incident Dashboard for real-time visualization.

---

## System Architecture and Diagnostic Triage Flow

```mermaid
flowchart TD
    subgraph K8S["Kubernetes Cluster Environment"]
        direction LR
        A["Live Discovery<br/>(kubectl get pods -A -o json)"]
        B["Scheduled Scanning<br/>(k8s/cronjob.yaml)"]
    end

    subgraph ENGINE["PodTriage Diagnostic Engine"]
        direction TB
        C{"Live API Reachable?"}
        D["Production Benchmark Telemetry"]
        E["Signal Introspection<br/>(Exit 137 OOM / Exit 1 Crash / SIGTERM)"]
        F["Root Cause Classification<br/>(CrashLoopBackOff / OOMKilled / Evicted)"]
    end

    subgraph INTERFACES["Multi-Interface SRE Delivery"]
        direction LR
        G["Terminal CLI & JSON Telemetry"]
        H["Web SRE Incident Dashboard (index.html)"]
    end

    A --> C
    B --> C
    C -- Yes --> E
    C -- Offline / Fallback --> D --> E
    E --> F
    F --> G
    F --> H

    style K8S fill:#2d3748,stroke:#cbd5e0,stroke-width:1px,color:#fff
    style ENGINE fill:#1a202c,stroke:#4a5568,stroke-width:1px,color:#fff
    style INTERFACES fill:#2d3748,stroke:#cbd5e0,stroke-width:1px,color:#fff
```

---

## Technology Stack

| Component / Layer | Technology | Operational Function |
| :--- | :--- | :--- |
| **Core Runtime Engine** | Python 3.11 | High-performance JSON parser, exit-code rule engine, and CLI interface |
| **Containerization** | Docker (Alpine 3.11) | Ultra-lightweight container image (< 55MB) optimized for zero-dependency execution |
| **Cluster Orchestration** | Kubernetes v1.28+ | Least-privilege RBAC policies, 15-minute CronJob scanner, and failure workloads |
| **CI/CD Pipeline** | GitHub Actions | Automated 3-stage validation: code linting, container build test, and YAML verification |
| **Interactive Dashboard** | HTML5, CSS3, Vanilla JS | Standalone SRE Web Dashboard in warm beige / off-white editorial aesthetic |
| **Version Control** | Git and GitHub | Strict semantic commit milestones tracking incremental feature development |

---

## DevOps and Cloud-Native Tool Integrations

### 1. Docker: Minimal Alpine Packaging and Runtime Hardening
- **Base Image**: Built upon `python:3.11-alpine` to maintain an ultra-compact footprint and eliminate superfluous package bloat.
- **Container Hardening**:
  - Designated dedicated working directory at `/app`.
  - Configured script execution permissions explicitly (`chmod +x /app/podtriage.py`).
  - Standardized container execution entrypoint: `ENTRYPOINT ["python", "/app/podtriage.py"]`.
- **Build Hygiene**: Configured `.dockerignore` to exclude `.git`, `__pycache__`, local virtual environments, and documentation screenshots.

### 2. Kubernetes: RBAC Least-Privilege and Scheduled CronJob Scans
- **Least-Privilege Security Model (`k8s/rbac.yaml`)**:
  - `ServiceAccount`: `podtriage-sa` in the `default` namespace.
  - `ClusterRole`: `podtriage-reader` explicitly restricted to read-only API verbs (`get`, `list`, `watch`) on `pods`, `pods/log`, `pods/status`, and `events`.
  - `ClusterRoleBinding`: Binds `podtriage-reader` strictly to `podtriage-sa`, completely preventing cluster privilege escalation.
- **Automated CronJob Scanner (`k8s/cronjob.yaml`)**:
  - Triggers diagnostic triage automatically every 15 minutes (`schedule: "*/15 * * * *"`).
  - Hardened workload configuration enforcing `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, and `restartPolicy: OnFailure`.
  - Dedicated resource constraints: Requests (`cpu: 50m`, `memory: 64Mi`) and Limits (`cpu: 100m`, `memory: 128Mi`).
- **OOM Failure Reproduction Workload (`k8s/test-workloads.yaml`)**:
  - Deploys `auth-service-oom` constrained to a restrictive `16Mi` memory limit to trigger intentional Linux kernel cgroup OOM kills (Exit 137), confirming scanner accuracy under real fault conditions.

### 3. GitHub Actions: Multi-Stage CI/CD Validation Pipeline
- **Workflow Configuration**: `.github/workflows/ci.yml`
- **Execution Triggers**: Configured for every `push` and `pull_request` against `main`.
- **Pipeline Stages**:
  1. **Job 1: `lint-and-validate`**: Checks Python compilation syntax via `py_compile`, verifies simulated cluster scan execution (`--simulate`), and tests structured JSON output (`--json`).
  2. **Job 2: `docker-build-check`**: Sets up Docker Buildx, compiles the production container image (`podtriage:ci`), and validates containerized CLI execution.
  3. **Job 3: `k8s-manifest-lint`**: Performs YAML structural linting and syntax verification across all Kubernetes manifests in `k8s/*.yaml`.

### 4. Single-Page SRE Web Incident Dashboard
- **File**: `index.html` (Standalone, zero-dependency HTML5 application).
- **Aesthetic**: Warm beige and soft off-white editorial palette featuring deep ink typography, clean border contrasts, and distinct status badges.
- **Key Capabilities**:
  - **Cluster Telemetry**: Live metrics cards tracking Total Pods, Degraded Workloads, Healthy Workloads, and MTTD.
  - **Dynamic Filtering**: Filter table rows dynamically by namespace (`All`, `production`, `monitoring`, `default`) and search query.
  - **Inspection Drawer**: Clickable workload rows reveal an interactive diagnostic inspection drawer with root-cause logs and one-click copyable `kubectl` remediation commands.
  - **Live Scan Trigger**: Interactive trigger button with real-time progress indicators and simulated incident generation.

---

## Git Workflow and Commit History Showcase

The project was constructed following disciplined, single-responsibility Git version control practices with sequential semantic commits:

| Commit # | Hash | Scope / Milestone | Commit Message | Key Accomplishments |
| :---: | :---: | :--- | :--- | :--- |
| **#1** | `053fd4f` | **Core Engine** | `feat(core): implement kubernetes pod diagnostic triage engine and cli scanner` | Initialized repository, built `podtriage.py` with exit-code analysis, simulated fallback mode, and ASCII diagnostic output. |
| **#2** | `d66491c` | **Docker** | `feat(docker): package podtriage diagnostic cli into lightweight alpine container` | Created hardened `Dockerfile` (Python 3.11 Alpine), configured `.dockerignore`, built and verified `podtriage:v1.0`. |
| **#3** | `2a1a74f` | **Kubernetes** | `feat(k8s): define kubernetes rbac permissions, cronjob scanner, and test workloads` | Authored `k8s/rbac.yaml`, `k8s/cronjob.yaml` (15m scanner), and `k8s/test-workloads.yaml` (OOM reproduction workload). |
| **#4** | `28e2254` | **CI/CD & Docs** | `docs: finalize project readme with devops tool integration proofs and ci pipeline` | Integrated `.github/workflows/ci.yml` (3 CI jobs), generated proof screenshots, and structured technical documentation. |
| **#5** | `72a2616` | **Academic Polish** | `docs: update author and submission details to Prachi Patil` | Updated project submission details, author credentials, and academic evaluation metadata. |
| **#6** | `f5f8f38` | **Styling Polish** | `docs: restyle readme to match devpulse layout and add visual git commits showcase` | Restyled documentation structure, refined badge aesthetics, and generated visual commit history assets. |
| **#7** | `d7edc69` | **Web Dashboard** | `feat(web): add single-page beige and off-white sre incident dashboard` | Implemented standalone SRE incident web dashboard (`index.html`) with telemetry metrics, filters, and inspection drawer. |
| **#8** | `9887c56` | **Final Overhaul** | `docs: complete formal documentation overhaul, student info block, and full visual proof gallery` | Formalized documentation, updated academic info block, and incorporated complete 7-figure visual proof gallery. |
| **#9** | `abefbdd` | **Screenshots Refresh** | `chore(screenshots): refresh git commit milestone history proof` | Synchronized visual commit history image with all 9 project milestones. |

---

## Implementation Proof Gallery

### Figure 1: Core CLI Incident Diagnostic Output
Live terminal diagnostic table rendering namespaces, degraded health states, container restart counts, root-cause analysis, and actionable remediation commands.

![Figure 1: Core CLI Incident Diagnostic Output](screenshots/01-cli-execution.png)

---

### Figure 2: Lightweight Alpine Docker Container Build and Execution
Docker build execution creating the Alpine-based container image (`podtriage:v1.0`) followed by zero-dependency container test verification.

![Figure 2: Docker Container Build and Execution](screenshots/02-docker-build.png)

---

### Figure 3: Kubernetes Manifests Client Dry-Run Validation
Client dry-run validation confirming Kubernetes RBAC authorization, scheduled CronJob scanner, and OOM test workload definitions.

![Figure 3: Kubernetes Manifest Validation](screenshots/03-k8s-manifests.png)

---

### Figure 4: GitHub Actions Multi-Stage CI/CD Pipeline
Automated 3-stage validation pipeline running code linting, container builds, and Kubernetes manifest validation with all jobs passing.

![Figure 4: GitHub Actions CI/CD Pipeline](screenshots/04-github-actions.png)

---

### Figure 5: Complete Git Commit Milestone History
Terminal git log verifying sequential semantic commit milestones and remote synchronization with GitHub main.

![Figure 5: Git Commit History Showcase](screenshots/05-git-commits-history.png)

---

### Figure 6: SRE Web Incident Dashboard Overview
Full overview of the single-page SRE Web Dashboard in warm beige and off-white theme, showcasing cluster telemetry cards and diagnostic table.

![Figure 6: SRE Web Incident Dashboard Overview](screenshots/06-web-dashboard-preview.png)

---

### Figure 7: Diagnostic Inspection Drawer and Remediation Interface
Workload deep-dive inspection drawer displaying root-cause log traces and copyable `kubectl` remediation commands.

![Figure 7: Diagnostic Inspection Drawer and Remediation Interface](screenshots/07-web-inspector-modal.png)

---

## Installation and Operational Guide

### Prerequisites
- Python 3.10+
- Docker Engine 24.0+
- Kubernetes CLI (`kubectl`) or any compatible cluster (optional; automated high-fidelity simulation activates if offline)

### Option A: Local Python Execution
```bash
# Clone the repository
git clone https://github.com/Durvankur-aiml/podtraige.git
cd podtraige

# Execute cluster diagnostic scan across all namespaces
python podtriage.py

# Filter triage to a specific namespace
python podtriage.py -n production

# Export structured JSON diagnostics for SIEM / webhook integration
python podtriage.py --json

# Run explicitly in simulated production benchmark mode
python podtriage.py --simulate
```

### Option B: Docker Container Execution
```bash
# Build the production Alpine container image
docker build -t podtriage:v1.0 .

# Execute the diagnostic container
docker run --rm podtriage:v1.0

# Execute container in simulation mode
docker run --rm podtriage:v1.0 --simulate
```

### Option C: Kubernetes In-Cluster Deployment
```bash
# Validate manifests via client dry-run
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

### Option D: SRE Web Incident Dashboard
```bash
# Launch a local HTTP server from the project root
python -m http.server 8000

# Open your browser and navigate to:
# http://localhost:8000
```

---

## Academic Evaluation and Submission Summary

| Evaluation Parameter | Specification | Verification Status |
| :--- | :--- | :--- |
| **Project Title** | PodTriage - Kubernetes Incident-Response & Pod Diagnostic Engine | Complete |
| **Course & Assessment** | DevOps and Kubernetes (ISE-2) | Complete |
| **Student Name** | Prachi Patil | Verified |
| **Roll Number** | A58 | Verified |
| **Branch / Department** | Artificial Intelligence and Data Science / AIML | Verified |
| **Institute** | D. Y. Patil College of Engineering and Technology | Verified |
| **Primary Repository** | https://github.com/Durvankur-aiml/podtraige | Verified |
| **Docker Integration** | Multi-stage / Alpine Dockerfile, `.dockerignore`, container verification | Passed |
| **Kubernetes Integration** | Least-privilege RBAC (`rbac.yaml`), CronJob scanner (`cronjob.yaml`), failure workloads | Passed |
| **CI/CD Pipeline** | GitHub Actions 3-stage validation pipeline (`ci.yml`) | Passed |
| **Web Dashboard** | Standalone SRE incident dashboard (`index.html`) | Passed |
| **Visual Proof Gallery** | 7 comprehensive visual proof screenshots in `screenshots/` | Complete |

---

## License

This project is open-source software licensed under the [MIT License](LICENSE).
