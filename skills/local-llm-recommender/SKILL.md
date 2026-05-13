---
name: local-llm-recommender
description: >-
  Detects the host machine's OS, CPU, GPU, VRAM, system RAM, and free disk space using real shell commands, then recommends three open-weight local LLMs sized exactly to the hardware: one COMFORTABLE fast option with headroom, one BALANCED top-quality clean fit, and one STRETCH next-tier option that may be slow due to RAM offload. Use when the user asks what LLM can run locally, which AI model fits their computer, recommends a local model for their hardware, asks whether a GPU/Mac/PC is good enough for a model, asks what to install in Ollama/LM Studio/llama.cpp, asks how big a model they can run, asks how much VRAM they need, or mentions downloading/installing/trying open-weight models such as Qwen, gpt-oss, Gemma, Mistral, Nemotron, DeepSeek, or Llama locally. Skip only when the user explicitly wants cloud/API access or has already picked a specific model and only needs install steps.
---

# Local LLM Recommender

## Core workflow

1. **Run real hardware detection first.** Execute:
   ```bash
   python skills/local-llm-recommender/scripts/detect_hardware.py
   ```
   If the skill is installed outside the current repo, resolve the script path relative to this `SKILL.md`.
2. **Read the catalog.** Use `references/model_catalog.md` for sizing thresholds, quantization estimates, model-family priority, and disk guidance.
3. **Base recommendations on evidence.** Use detected accelerator memory first; use system RAM only for CPU-only fallback or stretch offload. Mention when VRAM is unknown and treat the result conservatively.
4. **Return exactly three recommendations:**
   - **COMFORTABLE**: fast, lower quant/model tier, clear headroom.
   - **BALANCED**: best quality that fits cleanly without painful offload.
   - **STRETCH**: next tier up; explicitly warn when RAM offload will make it slow.
5. **Include install-runner guidance.** Name a suitable runner based on the host:
   - NVIDIA/AMD/Linux/Windows: Ollama, LM Studio, or llama.cpp GGUF.
   - Apple Silicon: MLX when available, otherwise Ollama/LM Studio.
   - CPU-only: llama.cpp/Ollama with conservative context.

## Recommendation rules

- Prefer model families from the Artificial Analysis Intelligence Index open-source ranking snapshot supplied for this skill (11-05-2026): Qwen3.6, gpt-oss, Gemma 4, Mistral, Nemotron, then Qwen3.5.
- Do not claim live benchmark positions unless you browse or the user provides current data. Treat the bundled catalog as a snapshot.
- Size to the detected machine, not generic internet advice. Include RAM, VRAM, and free disk constraints in the explanation.
- Account for runtime overhead and KV cache; do not fill 100% of VRAM.
- If multiple GPUs are present, recommend for the largest single GPU unless the user asks for multi-GPU setup.
- If free disk is insufficient for a pick, either choose the next smaller pick or mark the disk cleanup required.
- Keep advice practical: model name, quant, expected performance, why it fits, and any offload/context caveat.

## Response template

Use this structure for the final answer:

```markdown
## Hardware detected
- OS:
- CPU:
- GPU/VRAM:
- RAM:
- Free disk:

## Three local LLM picks
| Tier | Model | Quant | Why this fits | Expected speed/caveat |
| --- | --- | --- | --- | --- |
| COMFORTABLE | ... | ... | ... | ... |
| BALANCED | ... | ... | ... | ... |
| STRETCH | ... | ... | ... | ... |

## What I would install first
...

## Commands to try
...
```

If hardware commands fail, show the failed command and give a conservative recommendation only after clearly stating what could not be detected.
