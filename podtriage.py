#!/usr/bin/env python3
"""
podtriage - Lightweight SRE & Incident-Response CLI for Kubernetes Pod Diagnostics
==================================================================================
Inspects Kubernetes pod health across namespaces, detects degraded states
(CrashLoopBackOff, OOMKilled, ImagePullBackOff, Evicted, Pending, Error), and
provides automated root-cause analysis and actionable remediation guidance.
"""

import sys
import os
import re
import json
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

__version__ = "1.0.0"

# Ensure UTF-8 output encoding for terminals & Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Enable ANSI escape sequences on Windows console
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        os.system("")

# ANSI Color & Style Palette
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # High-intensity bold
    B_RED = "\033[1;31m"
    B_GREEN = "\033[1;32m"
    B_YELLOW = "\033[1;33m"
    B_BLUE = "\033[1;34m"
    B_MAGENTA = "\033[1;35m"
    B_CYAN = "\033[1;36m"
    B_WHITE = "\033[1;37m"


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text for accurate column width calculations."""
    return re.sub(r"\033\[[0-9;]*m", "", text)


def visible_len(text: str) -> int:
    """Return the visible length of a string ignoring ANSI color escape codes."""
    return len(strip_ansi(text))


# Simulated production triage dataset when cluster daemon is offline
SIMULATED_POD_DATA = {
    "apiVersion": "v1",
    "kind": "PodList",
    "items": [
        {
            "metadata": {
                "name": "auth-service-7d8b-px1",
                "namespace": "production",
                "creationTimestamp": "2026-10-30T16:15:00Z",
                "labels": {"app": "auth-service", "env": "production", "tier": "backend"}
            },
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "auth-service",
                        "ready": False,
                        "restartCount": 14,
                        "image": "registry.internal.corp/production/auth-service:v2.1.4",
                        "state": {
                            "waiting": {
                                "reason": "CrashLoopBackOff",
                                "message": "back-off 5m0s restarting failed container=auth-service pod=auth-service-7d8b-px1_production"
                            }
                        },
                        "lastState": {
                            "terminated": {
                                "exitCode": 137,
                                "reason": "OOMKilled",
                                "finishedAt": "2026-10-30T18:22:10Z",
                                "message": "Container exceeded allocated memory limit (512Mi)"
                            }
                        }
                    }
                ]
            }
        },
        {
            "metadata": {
                "name": "payment-worker-91a-zz0",
                "namespace": "production",
                "creationTimestamp": "2026-10-30T17:40:00Z",
                "labels": {"app": "payment-worker", "env": "production", "tier": "worker"}
            },
            "status": {
                "phase": "Pending",
                "containerStatuses": [
                    {
                        "name": "payment-worker",
                        "ready": False,
                        "restartCount": 0,
                        "image": "registry.internal.corp/fintech/payment-worker:v3.8.0",
                        "state": {
                            "waiting": {
                                "reason": "ImagePullBackOff",
                                "message": "Back-off pulling image 'registry.internal.corp/fintech/payment-worker:v3.8.0': ErrImagePull: unauthorized: registry token expired"
                            }
                        },
                        "lastState": {}
                    }
                ]
            }
        },
        {
            "metadata": {
                "name": "redis-cache-master-0",
                "namespace": "default",
                "creationTimestamp": "2026-10-28T09:00:00Z",
                "labels": {"app": "redis", "role": "master", "tier": "cache"}
            },
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "redis",
                        "ready": True,
                        "restartCount": 0,
                        "image": "redis:7.2-alpine",
                        "state": {
                            "running": {
                                "startedAt": "2026-10-28T09:01:00Z"
                            }
                        },
                        "lastState": {}
                    }
                ]
            }
        },
        {
            "metadata": {
                "name": "prometheus-node-exporter-k8s-4f9",
                "namespace": "monitoring",
                "creationTimestamp": "2026-10-28T08:30:00Z",
                "labels": {"app": "node-exporter", "tier": "telemetry"}
            },
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "node-exporter",
                        "ready": True,
                        "restartCount": 0,
                        "image": "prom/node-exporter:v1.7.0",
                        "state": {
                            "running": {
                                "startedAt": "2026-10-28T08:30:15Z"
                            }
                        },
                        "lastState": {}
                    }
                ]
            }
        }
    ]
}


class PodTriageItem:
    """Parsed and classified pod diagnostic result."""
    def __init__(
        self,
        namespace: str,
        name: str,
        health_state: str,
        restart_count: int,
        severity: str,  # CRITICAL, WARNING, HEALTHY
        root_cause: str,
        remediation: str,
        container_name: str = "",
        image: str = ""
    ):
        self.namespace = namespace
        self.name = name
        self.health_state = health_state
        self.restart_count = restart_count
        self.severity = severity
        self.root_cause = root_cause
        self.remediation = remediation
        self.container_name = container_name
        self.image = image

    def to_dict(self) -> Dict[str, Any]:
        return {
            "namespace": self.namespace,
            "pod_name": self.name,
            "health_state": self.health_state,
            "restart_count": self.restart_count,
            "severity": self.severity,
            "sre_root_cause": self.root_cause,
            "remediation_step": self.remediation,
            "container": self.container_name,
            "image": self.image
        }


def analyze_pod(pod: Dict[str, Any]) -> PodTriageItem:
    """
    SRE Diagnostic Rule Engine: Inspects pod metadata and container statuses
    to detect failure patterns, exit codes, and actionable remedies.
    """
    metadata = pod.get("metadata", {})
    namespace = metadata.get("namespace", "default")
    name = metadata.get("name", "unknown")
    status = pod.get("status", {})
    phase = status.get("phase", "Unknown")
    pod_reason = status.get("reason", "")
    pod_message = status.get("message", "")

    # Aggregate container statuses
    c_statuses = status.get("containerStatuses", [])
    init_c_statuses = status.get("initContainerStatuses", [])
    all_statuses = c_statuses + init_c_statuses

    max_restarts = 0
    degraded_state = None
    severity = "HEALTHY"
    root_cause = ""
    remediation = ""
    culprit_container = ""
    culprit_image = ""

    # Check for Evicted phase first
    if pod_reason == "Evicted" or "evicted" in pod_message.lower():
        severity = "WARNING"
        degraded_state = "Evicted"
        root_cause = f"Pod evicted by Kubelet due to node resource pressure ({pod_message or 'ephemeral-storage/memory threshold exceeded'})."
        remediation = f"Inspect node pressure: 'kubectl describe node' & clean evicted pods: 'kubectl delete pod {name} -n {namespace}'."

    # Inspect container states
    for cs in all_statuses:
        c_name = cs.get("name", "")
        c_image = cs.get("image", "")
        restarts = cs.get("restartCount", 0)
        if restarts > max_restarts:
            max_restarts = restarts

        state = cs.get("state", {})
        last_state = cs.get("lastState", {})

        waiting = state.get("waiting", {})
        terminated = state.get("terminated", {})
        last_terminated = last_state.get("terminated", {})

        # 1. CrashLoopBackOff detection
        if waiting.get("reason") == "CrashLoopBackOff":
            culprit_container = c_name
            culprit_image = c_image
            severity = "CRITICAL"
            
            exit_code = last_terminated.get("exitCode")
            last_reason = last_terminated.get("reason", "")
            
            if exit_code == 137 or last_reason == "OOMKilled":
                degraded_state = "CrashLoopBackOff (Exit 137 - OOMKilled)"
                root_cause = "Cgroup memory limit exceeded. Linux kernel invoked OOM Killer (SIGKILL / 137)."
                remediation = f"Increase 'resources.limits.memory' in Deployment manifest; profile memory leaks via pprof."
            elif exit_code == 1:
                degraded_state = "CrashLoopBackOff (Exit 1 - App Error)"
                root_cause = "Application crashed on startup with unhandled exception or failed initialization."
                remediation = f"Inspect prior container logs: 'kubectl logs {name} -n {namespace} -c {c_name} --previous'."
            elif exit_code == 143:
                degraded_state = "CrashLoopBackOff (Exit 143 - SIGTERM)"
                root_cause = "Container was prematurely terminated by SIGTERM (graceful shutdown or liveness failure)."
                remediation = f"Check livenessProbe timing ('initialDelaySeconds') to prevent early termination."
            else:
                code_str = f"Exit {exit_code}" if exit_code is not None else "CrashLoop"
                degraded_state = f"CrashLoopBackOff ({code_str})"
                root_cause = f"Repeated container crash cycles detected (restart count: {restarts})."
                remediation = f"Run 'kubectl describe pod {name} -n {namespace}' and inspect events."
            break

        # 2. Direct OOMKilled detection (terminated)
        if terminated.get("reason") == "OOMKilled" or terminated.get("exitCode") == 137 or last_terminated.get("reason") == "OOMKilled":
            culprit_container = c_name
            culprit_image = c_image
            severity = "CRITICAL"
            degraded_state = "OOMKilled (Exit 137)"
            root_cause = "Container exceeded memory allocation limits and was terminated by kernel OOM killer."
            remediation = f"Raise memory limit in pod spec ('resources.limits.memory') or scale deployment."
            break

        # 3. ImagePullBackOff / ErrImagePull detection
        wait_reason = waiting.get("reason", "")
        if wait_reason in ("ImagePullBackOff", "ErrImagePull"):
            culprit_container = c_name
            culprit_image = c_image
            severity = "CRITICAL"
            wait_msg = waiting.get("message", "")
            
            if "unauthorized" in wait_msg.lower() or "token expired" in wait_msg.lower() or "authentication" in wait_msg.lower():
                degraded_state = "ImagePullBackOff (ErrImagePull - registry token expired)"
                root_cause = "Container registry authentication failure: access token expired or invalid credentials."
                remediation = f"Rotate registry credentials: 'kubectl create secret docker-registry' and verify imagePullSecrets."
            elif "not found" in wait_msg.lower() or "manifest unknown" in wait_msg.lower():
                degraded_state = "ImagePullBackOff (ErrImagePull - Tag Not Found)"
                root_cause = f"Image tag does not exist in target registry: {c_image}."
                remediation = f"Verify CI/CD artifact push and update deployment image tag."
            else:
                degraded_state = "ImagePullBackOff (ErrImagePull)"
                root_cause = f"Kubelet failed to pull container image '{c_image}': network timeout or invalid repository URL."
                remediation = f"Verify node network access to registry and check 'kubectl describe pod {name} -n {namespace}'."
            break

        # 4. ContainerCreating / CreateContainerConfigError
        if wait_reason == "CreateContainerConfigError":
            culprit_container = c_name
            severity = "CRITICAL"
            degraded_state = "CreateContainerConfigError"
            root_cause = "Missing ConfigMap, Secret, or invalid environment variable key reference."
            remediation = f"Check missing ConfigMaps/Secrets: 'kubectl describe pod {name} -n {namespace}'."
            break

        # 5. Direct Error exit
        if terminated.get("reason") == "Error" or (terminated.get("exitCode") and terminated.get("exitCode") != 0):
            culprit_container = c_name
            severity = "CRITICAL"
            exit_code = terminated.get("exitCode", 1)
            degraded_state = f"Error (Exit {exit_code})"
            root_cause = f"Container terminated abnormally with non-zero exit code {exit_code}."
            remediation = f"Inspect logs: 'kubectl logs {name} -n {namespace} -c {c_name} --previous'."
            break

    # 6. Pending phase analysis (if no container-level error triggered)
    if not degraded_state and phase == "Pending":
        severity = "WARNING"
        degraded_state = "Pending"
        root_cause = "Pod is unschedulable due to insufficient node CPU/memory or unsatisfied taints/tolerations."
        remediation = f"Check scheduler events: 'kubectl describe pod {name} -n {namespace}' and verify cluster capacity."

    # 7. Healthy baseline
    if not degraded_state:
        if phase == "Running":
            degraded_state = "Running (Healthy)"
            severity = "HEALTHY"
            root_cause = "All containers operational and passing liveness/readiness health probes."
            remediation = "Steady state verified. No remediation required."
        elif phase == "Succeeded":
            degraded_state = "Completed"
            severity = "HEALTHY"
            root_cause = "Job / batch container completed lifecycle successfully."
            remediation = "No action required. Clean up finished jobs according to TTL policy."
        else:
            degraded_state = phase
            severity = "WARNING"
            root_cause = f"Pod is in non-standard phase: {phase}."
            remediation = f"Inspect pod lifecycle: 'kubectl get pod {name} -n {namespace} -o yaml'."

    return PodTriageItem(
        namespace=namespace,
        name=name,
        health_state=degraded_state,
        restart_count=max_restarts,
        severity=severity,
        root_cause=root_cause,
        remediation=remediation,
        container_name=culprit_container,
        image=culprit_image
    )


def fetch_kubernetes_pods(simulate: bool = False, namespace_filter: Optional[str] = None) -> Tuple[List[Dict[str, Any]], bool, str]:
    """
    Execute `kubectl get pods -A -o json` to retrieve cluster state.
    Gracefully falls back to simulated high-fidelity production data if offline.
    
    Returns:
        (pod_items, is_simulated, source_description)
    """
    if simulate:
        items = SIMULATED_POD_DATA["items"]
        if namespace_filter:
            items = [p for p in items if p.get("metadata", {}).get("namespace") == namespace_filter]
        return items, True, "Simulated Cluster Mode (--simulate specified)"

    # Attempt live query with kubectl
    cmd = ["kubectl", "get", "pods", "-A", "-o", "json"]
    if namespace_filter:
        cmd = ["kubectl", "get", "pods", "-n", namespace_filter, "-o", "json"]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=8
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            items = data.get("items", [])
            return items, False, "Live Kubernetes Cluster (via kubectl)"
        else:
            reason = "Live cluster unreachable (cluster daemon offline / authentication required)"
    except FileNotFoundError:
        reason = "kubectl CLI binary not found in system PATH"
    except subprocess.TimeoutExpired:
        reason = "kubectl connection timed out (cluster daemon offline)"
    except Exception as ex:
        reason = f"cluster connection error: {str(ex)}"

    # Graceful fallback to simulation
    items = SIMULATED_POD_DATA["items"]
    if namespace_filter:
        items = [p for p in items if p.get("metadata", {}).get("namespace") == namespace_filter]
    return items, True, f"Simulated Fallback ({reason})"


def wrap_text(text: str, max_width: int) -> List[str]:
    """Wrap plain text into multiple lines with maximum width."""
    if not text:
        return [""]
    words = text.split()
    lines = []
    current_line = []
    current_len = 0

    for word in words:
        if current_len + len(word) + (1 if current_line else 0) <= max_width:
            current_line.append(word)
            current_len += len(word) + (1 if len(current_line) > 1 else 0)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines or [""]


def pad_cell(text: str, width: int, align: str = "left") -> str:
    """Pad text to exact visible cell width, accounting for ANSI codes."""
    v_len = visible_len(text)
    pad = max(0, width - v_len)
    if align == "center":
        left = pad // 2
        right = pad - left
        return " " + (" " * left) + text + (" " * right) + " "
    elif align == "right":
        return " " + (" " * pad) + text + " "
    else:
        return " " + text + (" " * pad) + " "


def render_triage_box(
    items: List[PodTriageItem],
    source_description: str,
    is_simulated: bool,
    namespace_filter: Optional[str] = None,
    use_color: bool = True
) -> str:
    """
    Renders an ASCII / Unicode diagnostic table box with color highlights,
    structured root-cause analysis, and actionable remediation steps.
    """
    # Color formatting helpers
    c_red = Colors.B_RED if use_color else ""
    c_yellow = Colors.B_YELLOW if use_color else ""
    c_green = Colors.B_GREEN if use_color else ""
    c_cyan = Colors.B_CYAN if use_color else ""
    c_blue = Colors.B_BLUE if use_color else ""
    c_bold = Colors.BOLD if use_color else ""
    c_dim = Colors.DIM if use_color else ""
    c_reset = Colors.RESET if use_color else ""

    # Column Widths
    col_ns_w = 12
    col_pod_w = 32
    col_state_w = 40
    col_rst_w = 10
    col_sre_w = 48

    # Box Drawing Characters
    T_TOP_LEFT = "┌"
    T_TOP_MID = "┬"
    T_TOP_RIGHT = "┐"
    T_MID_LEFT = "├"
    T_MID_MID = "┼"
    T_MID_RIGHT = "┤"
    T_BOT_LEFT = "└"
    T_BOT_MID = "┴"
    T_BOT_RIGHT = "┘"
    H_LINE = "─"
    V_LINE = "│"

    top_border = (
        f"{c_dim}{T_TOP_LEFT}"
        f"{H_LINE * (col_ns_w + 2)}{T_TOP_MID}"
        f"{H_LINE * (col_pod_w + 2)}{T_TOP_MID}"
        f"{H_LINE * (col_state_w + 2)}{T_TOP_MID}"
        f"{H_LINE * (col_rst_w + 2)}{T_TOP_MID}"
        f"{H_LINE * (col_sre_w + 2)}{T_TOP_RIGHT}{c_reset}"
    )

    header_sep = (
        f"{c_dim}{T_MID_LEFT}"
        f"{H_LINE * (col_ns_w + 2)}{T_MID_MID}"
        f"{H_LINE * (col_pod_w + 2)}{T_MID_MID}"
        f"{H_LINE * (col_state_w + 2)}{T_MID_MID}"
        f"{H_LINE * (col_rst_w + 2)}{T_MID_MID}"
        f"{H_LINE * (col_sre_w + 2)}{T_MID_RIGHT}{c_reset}"
    )

    row_sep = header_sep

    bot_border = (
        f"{c_dim}{T_BOT_LEFT}"
        f"{H_LINE * (col_ns_w + 2)}{T_BOT_MID}"
        f"{H_LINE * (col_pod_w + 2)}{T_BOT_MID}"
        f"{H_LINE * (col_state_w + 2)}{T_BOT_MID}"
        f"{H_LINE * (col_rst_w + 2)}{T_BOT_MID}"
        f"{H_LINE * (col_sre_w + 2)}{T_BOT_RIGHT}{c_reset}"
    )

    # Header Row
    headers = [
        ("NAMESPACE", col_ns_w, "left"),
        ("POD NAME", col_pod_w, "left"),
        ("HEALTH STATE", col_state_w, "left"),
        ("RESTARTS", col_rst_w, "center"),
        ("SRE ROOT-CAUSE ANALYSIS & ACTIONABLE REMEDIATION", col_sre_w, "left")
    ]
    hdr_cells = []
    for title, width, align in headers:
        hdr_cells.append(pad_cell(f"{c_bold}{c_cyan}{title}{c_reset}", width, align))
    header_line = f"{c_dim}{V_LINE}{c_reset}" + f"{c_dim}{V_LINE}{c_reset}".join(hdr_cells) + f"{c_dim}{V_LINE}{c_reset}"

    # Build Header Banner
    banner_lines = []
    banner_lines.append(f"{c_bold}{c_blue}PODTRIAGE{c_reset} {c_dim}v{__version__}{c_reset} - {c_bold}Kubernetes Pod Health & Incident Triage Engine{c_reset}")
    status_mode_color = c_yellow if is_simulated else c_green
    scope_str = f"Namespace '{namespace_filter}' (-n)" if namespace_filter else "All Namespaces (-A)"
    banner_lines.append(f"{c_dim}Target Cluster: {status_mode_color}{source_description}{c_reset}")
    banner_lines.append(f"{c_dim}Timestamp:      {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')} | Scan Scope: {scope_str}{c_reset}")
    banner_lines.append("")

    # Build Table Rows
    table_lines = [top_border, header_line, header_sep]

    critical_count = sum(1 for i in items if i.severity == "CRITICAL")
    warning_count = sum(1 for i in items if i.severity == "WARNING")
    healthy_count = sum(1 for i in items if i.severity == "HEALTHY")

    for idx, item in enumerate(items):
        # 1. Namespace lines
        ns_lines = [f"{c_bold}{item.namespace}{c_reset}"]

        # 2. Pod Name lines
        pod_lines = wrap_text(item.name, col_pod_w)

        # 3. Health State lines with color
        raw_state_lines = wrap_text(item.health_state, col_state_w)
        if item.severity == "CRITICAL":
            state_color = c_red
        elif item.severity == "WARNING":
            state_color = c_yellow
        else:
            state_color = c_green
        state_lines = [f"{state_color}{line}{c_reset}" for line in raw_state_lines]

        # 4. Restarts line
        if item.restart_count > 10:
            rst_color = c_red
        elif item.restart_count > 0:
            rst_color = c_yellow
        else:
            rst_color = c_dim
        rst_lines = [f"{rst_color}{item.restart_count}{c_reset}"]

        # 5. SRE Root-Cause and Remediation
        cause_prefix = "CAUSE: "
        fix_prefix   = "FIX:   "
        cause_wrapped = wrap_text(item.root_cause, col_sre_w - len(cause_prefix))
        fix_wrapped   = wrap_text(item.remediation, col_sre_w - len(fix_prefix))

        sre_lines = []
        for i, line in enumerate(cause_wrapped):
            prefix = f"{c_bold}{c_yellow}{cause_prefix}{c_reset}" if i == 0 else " " * len(cause_prefix)
            sre_lines.append(f"{prefix}{line}")
        for i, line in enumerate(fix_wrapped):
            prefix = f"{c_bold}{c_green}{fix_prefix}{c_reset}" if i == 0 else " " * len(fix_prefix)
            sre_lines.append(f"{prefix}{line}")

        # Determine row height
        row_height = max(len(ns_lines), len(pod_lines), len(state_lines), len(rst_lines), len(sre_lines))

        for line_idx in range(row_height):
            c1_str = ns_lines[line_idx] if line_idx < len(ns_lines) else ""
            c2_str = pod_lines[line_idx] if line_idx < len(pod_lines) else ""
            c3_str = state_lines[line_idx] if line_idx < len(state_lines) else ""
            c4_str = rst_lines[line_idx] if line_idx < len(rst_lines) else ""
            c5_str = sre_lines[line_idx] if line_idx < len(sre_lines) else ""

            cell1 = pad_cell(c1_str, col_ns_w, "left")
            cell2 = pad_cell(c2_str, col_pod_w, "left")
            cell3 = pad_cell(c3_str, col_state_w, "left")
            cell4 = pad_cell(c4_str, col_rst_w, "center")
            cell5 = pad_cell(c5_str, col_sre_w, "left")

            row_str = (
                f"{c_dim}{V_LINE}{c_reset}"
                f"{cell1}{c_dim}{V_LINE}{c_reset}"
                f"{cell2}{c_dim}{V_LINE}{c_reset}"
                f"{cell3}{c_dim}{V_LINE}{c_reset}"
                f"{cell4}{c_dim}{V_LINE}{c_reset}"
                f"{cell5}{c_dim}{V_LINE}{c_reset}"
            )
            table_lines.append(row_str)

        if idx < len(items) - 1:
            table_lines.append(row_sep)

    table_lines.append(bot_border)

    # Summary Box
    summary_lines = []
    summary_lines.append("")
    summary_lines.append(f"{c_bold}Cluster Triage Summary:{c_reset}")
    summary_lines.append(
        f"  Total Pods: {c_bold}{len(items)}{c_reset}  |  "
        f"Degraded/Critical: {c_red}{critical_count}{c_reset}  |  "
        f"Warnings: {c_yellow}{warning_count}{c_reset}  |  "
        f"Healthy: {c_green}{healthy_count}{c_reset}"
    )

    if critical_count > 0:
        summary_lines.append(
            f"  {c_red}⚡ ACTION REQUIRED: {critical_count} degraded pod(s) detected across cluster namespaces.{c_reset}"
        )
    else:
        summary_lines.append(
            f"  {c_green}✓ HEALTH NOMINAL: All surveyed pods are operating within normal parameters.{c_reset}"
        )

    return "\n".join(banner_lines + table_lines + summary_lines)


def main():
    parser = argparse.ArgumentParser(
        description="podtriage: Lightweight SRE & Incident-Response CLI for Kubernetes Pod Diagnostics."
    )
    parser.add_argument(
        "-A", "--all-namespaces",
        action="store_true",
        default=True,
        help="Inspect pod health across all Kubernetes namespaces (default: True)."
    )
    parser.add_argument(
        "-n", "--namespace",
        type=str,
        default=None,
        help="Filter triage inspection to a specific namespace (e.g. production, monitoring)."
    )
    parser.add_argument(
        "--simulate", "--demo",
        action="store_true",
        help="Force execution in simulated cluster mode with benchmark incident scenarios."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output diagnostics in structured JSON format for automated alerting / CI/CD pipelines."
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color highlights."
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"podtriage {__version__}"
    )

    args = parser.parse_args()

    # Determine color output (support ANSI colors by default unless --no-color or NO_COLOR env)
    use_color = not args.no_color and (os.environ.get("NO_COLOR") is None)

    # Fetch pods
    raw_pods, is_simulated, source_desc = fetch_kubernetes_pods(
        simulate=args.simulate,
        namespace_filter=args.namespace
    )

    # Analyze all pods
    triage_results = [analyze_pod(p) for p in raw_pods]

    # Output JSON mode if requested
    if args.json:
        payload = {
            "version": __version__,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "is_simulated": is_simulated,
            "source": source_desc,
            "total_pods": len(triage_results),
            "critical_count": sum(1 for i in triage_results if i.severity == "CRITICAL"),
            "warning_count": sum(1 for i in triage_results if i.severity == "WARNING"),
            "healthy_count": sum(1 for i in triage_results if i.severity == "HEALTHY"),
            "diagnostics": [i.to_dict() for i in triage_results]
        }
        print(json.dumps(payload, indent=2))
        return 0

    # Render terminal diagnostic table
    output = render_triage_box(
        items=triage_results,
        source_description=source_desc,
        is_simulated=is_simulated,
        namespace_filter=args.namespace,
        use_color=use_color
    )
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
