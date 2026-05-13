#!/usr/bin/env python3
"""Detect local hardware for local LLM sizing using real host commands.

Outputs JSON with OS, CPU, GPU/VRAM, RAM, and free disk. The script is
best-effort and intentionally keeps raw command output evidence so the calling
agent can explain uncertainty instead of guessing.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def run(cmd: list[str], timeout: int = 8) -> dict[str, Any]:
    path = shutil.which(cmd[0])
    if not path:
        return {"cmd": cmd, "found": False, "ok": False, "stdout": "", "stderr": ""}
    try:
        proc = subprocess.run(
            [path, *cmd[1:]],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "cmd": cmd,
            "found": True,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # hardware probing should never abort the task
        return {"cmd": cmd, "found": True, "ok": False, "stdout": "", "stderr": repr(exc)}


def parse_int(text: str) -> int | None:
    m = re.search(r"(\d+)", text.replace(",", ""))
    return int(m.group(1)) if m else None


def bytes_to_gib(value: float | int | None) -> float | None:
    if value is None:
        return None
    return round(float(value) / (1024**3), 2)


def detect_ram() -> dict[str, Any]:
    sysname = platform.system()
    evidence: dict[str, Any] = {}
    total_bytes: int | None = None

    if sysname == "Linux":
        meminfo = Path("/proc/meminfo")
        if meminfo.exists():
            evidence["/proc/meminfo"] = meminfo.read_text(errors="ignore").splitlines()[:5]
            for line in meminfo.read_text(errors="ignore").splitlines():
                if line.startswith("MemTotal:"):
                    kb = parse_int(line)
                    total_bytes = kb * 1024 if kb is not None else None
                    break
    elif sysname == "Darwin":
        out = run(["sysctl", "-n", "hw.memsize"])
        evidence["sysctl_hw_memsize"] = out
        if out["ok"]:
            total_bytes = parse_int(out["stdout"])
    elif sysname == "Windows":
        out = run(["wmic", "computersystem", "get", "totalphysicalmemory", "/value"])
        evidence["wmic_totalphysicalmemory"] = out
        if out["ok"]:
            total_bytes = parse_int(out["stdout"])

    return {"total_gib": bytes_to_gib(total_bytes), "evidence": evidence}


def detect_cpu() -> dict[str, Any]:
    sysname = platform.system()
    evidence: dict[str, Any] = {}
    model = platform.processor() or platform.machine()
    cores_logical = os.cpu_count()

    if sysname == "Linux":
        out = run(["lscpu"])
        evidence["lscpu"] = out
        if out["ok"]:
            for line in out["stdout"].splitlines():
                if line.startswith("Model name:"):
                    model = line.split(":", 1)[1].strip()
                    break
    elif sysname == "Darwin":
        brand = run(["sysctl", "-n", "machdep.cpu.brand_string"])
        evidence["sysctl_cpu_brand"] = brand
        if brand["ok"] and brand["stdout"]:
            model = brand["stdout"]
    elif sysname == "Windows":
        out = run(["wmic", "cpu", "get", "name,numberofcores,numberoflogicalprocessors", "/format:list"])
        evidence["wmic_cpu"] = out
        if out["ok"]:
            for line in out["stdout"].splitlines():
                if line.lower().startswith("name="):
                    model = line.split("=", 1)[1].strip()
                    break

    return {"model": model, "logical_cores": cores_logical, "evidence": evidence}


def detect_gpus() -> list[dict[str, Any]]:
    sysname = platform.system()
    gpus: list[dict[str, Any]] = []

    nvidia = run([
        "nvidia-smi",
        "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ])
    if nvidia["ok"] and nvidia["stdout"]:
        for row in nvidia["stdout"].splitlines():
            parts = [p.strip() for p in row.split(",")]
            if len(parts) >= 2:
                gpus.append({
                    "vendor": "NVIDIA",
                    "name": parts[0],
                    "vram_gib": round((parse_int(parts[1]) or 0) / 1024, 2),
                    "driver": parts[2] if len(parts) > 2 else None,
                    "evidence": {"nvidia-smi": nvidia},
                })

    rocm = run(["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--json"])
    if rocm["ok"] and rocm["stdout"]:
        try:
            data = json.loads(rocm["stdout"])
            for card, values in data.items():
                name = values.get("Card series") or values.get("Card model") or card
                total = None
                for key, val in values.items():
                    if "VRAM Total Memory" in key:
                        total = parse_int(str(val))
                        break
                gpus.append({
                    "vendor": "AMD",
                    "name": name,
                    "vram_gib": bytes_to_gib(total),
                    "evidence": {"rocm-smi": rocm},
                })
        except json.JSONDecodeError:
            gpus.append({"vendor": "AMD", "name": "ROCm GPU detected", "vram_gib": None, "evidence": {"rocm-smi": rocm}})

    if sysname == "Darwin":
        sp = run(["system_profiler", "SPDisplaysDataType"])
        hw = run(["system_profiler", "SPHardwareDataType"])
        if sp["ok"] or hw["ok"]:
            names = []
            for line in sp.get("stdout", "").splitlines():
                if "Chipset Model:" in line:
                    names.append(line.split(":", 1)[1].strip())
            unified = None
            for line in hw.get("stdout", "").splitlines():
                if "Memory:" in line:
                    unified = line.split(":", 1)[1].strip()
            gpus.append({
                "vendor": "Apple",
                "name": ", ".join(names) or "Apple Silicon / Metal GPU",
                "vram_gib": None,
                "unified_memory": unified,
                "evidence": {"system_profiler_displays": sp, "system_profiler_hardware": hw},
            })

    if not gpus and sysname == "Linux":
        lspci = run(["lspci"])
        if lspci["ok"]:
            display = [line for line in lspci["stdout"].splitlines() if re.search(r"VGA|3D|Display", line, re.I)]
            for line in display:
                gpus.append({"vendor": "Unknown", "name": line, "vram_gib": None, "evidence": {"lspci": lspci}})

    return gpus


def main() -> None:
    disk = shutil.disk_usage(Path.cwd())
    result = {
        "os": {"system": platform.system(), "release": platform.release(), "version": platform.version(), "machine": platform.machine()},
        "cpu": detect_cpu(),
        "ram": detect_ram(),
        "gpus": detect_gpus(),
        "disk": {"path": str(Path.cwd()), "free_gib": bytes_to_gib(disk.free), "total_gib": bytes_to_gib(disk.total)},
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
