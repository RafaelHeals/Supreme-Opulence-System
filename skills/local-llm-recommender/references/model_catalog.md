# Open-weight local LLM sizing catalog

Use this catalog as a compact sizing reference for recommendations based on the Artificial Analysis Intelligence Index open-source ranking snapshot supplied for this skill: 11-05-2026. Prefer higher rows within the user's hardware envelope, but never invent an exact benchmark score unless the user provides one.

## Candidate families in ranking order

1. Qwen3.6 family
2. gpt-oss family
3. Gemma 4 family
4. Mistral open family
5. Nemotron open family
6. Qwen3.5 family

## Recommendation tiers

Choose exactly three picks:

- **COMFORTABLE**: Fast daily-driver fit with headroom. Target 45-65% of available GPU/unified memory, or 35-50% of system RAM for CPU-only.
- **BALANCED**: Best quality that fits cleanly. Target 70-90% of available GPU/unified memory, or 55-75% of system RAM for CPU-only.
- **STRETCH**: Next tier up. It may exceed GPU memory and require RAM offload; warn that it will be slow. Do not exceed roughly 85% of system RAM plus available GPU memory.

## Memory estimation

Approximate loaded weight memory before KV cache and runtime overhead:

| Quant | Bytes per parameter | Use |
| --- | ---: | --- |
| Q2_K | 0.31 | Emergency/stretch only; noticeable quality loss |
| Q3_K_M | 0.44 | Stretch when memory-constrained |
| Q4_K_M | 0.56 | Default balance of quality and fit |
| Q5_K_M | 0.69 | Comfortable quality when memory allows |
| Q6_K | 0.81 | Higher quality, slower/larger |
| Q8_0 | 1.06 | Near-FP quality for small models |

Add overhead after weight estimate:

- 2-4 GiB for desktop runners, GPU kernels, and OS headroom.
- 0.5-4 GiB for KV cache depending on context length and model size.
- More headroom on Windows with a display attached to the same GPU.

Rule of thumb: `estimated_gib = params_billion * bytes_per_param + overhead_gib`.

## Model size ladder

When multiple families have a model in the same size class, prefer the family ranking order above, then prefer a recent instruct/chat variant supported by the user's runner.

| Size class | Typical params | Good fit for | Notes |
| --- | ---: | --- | --- |
| Tiny | 3B-4B | 6-8 GiB VRAM or CPU-only 8-16 GiB RAM | Fastest; limited reasoning |
| Small | 7B-9B | 8-12 GiB VRAM or 16-24 GiB RAM | Good default for laptops |
| Medium | 12B-14B | 12-16 GiB VRAM or 24-32 GiB RAM | Strong balanced tier |
| Large | 24B-32B | 24 GiB VRAM or 48-64 GiB RAM | Often best single-GPU quality |
| XL | 70B-72B | 48+ GiB VRAM, high unified memory, or 96+ GiB RAM | Usually stretch/offload for consumer PCs |
| XXL/MoE | 100B+ active/total | Multi-GPU or workstation memory | Recommend only if evidence supports it |

## Family-specific examples

Use these as labels; adjust exact suffixes for the user's runner (Ollama, LM Studio, llama.cpp, MLX, etc.).

| Family | Tiny | Small | Medium | Large | XL / stretch |
| --- | --- | --- | --- | --- | --- |
| Qwen3.6 | Qwen3.6 4B Instruct | Qwen3.6 8B Instruct | Qwen3.6 14B Instruct | Qwen3.6 32B Instruct | Qwen3.6 72B Instruct / MoE if available |
| gpt-oss | gpt-oss 4B | gpt-oss 8B | gpt-oss 14B | gpt-oss 32B | gpt-oss 70B |
| Gemma 4 | Gemma 4 4B IT | Gemma 4 9B IT | Gemma 4 12B/14B IT | Gemma 4 27B IT | Gemma 4 70B IT if available |
| Mistral | Ministral/Mistral 3B | Mistral 7B/8B Instruct | Mistral Nemo 12B | Mistral Small 24B | Mixtral/Mistral Large open variants |
| Nemotron | Nemotron Mini 4B | Nemotron 8B | Nemotron 14B | Nemotron 32B | Nemotron 70B |
| Qwen3.5 | Qwen3.5 4B Instruct | Qwen3.5 7B/8B Instruct | Qwen3.5 14B Instruct | Qwen3.5 32B Instruct | Qwen3.5 72B Instruct |

## Hardware mapping quick picks

Use detected VRAM/unified memory first. If no usable GPU memory is detected, use CPU/RAM guidance and favor smaller models.

| Available accelerator memory | Comfortable | Balanced | Stretch |
| ---: | --- | --- | --- |
| None / CPU-only with 16 GiB RAM | 3B-4B Q4_K_M | 7B-8B Q4_K_M | 12B-14B Q3_K_M, very slow |
| 6 GiB VRAM | 3B-4B Q5_K_M | 7B-8B Q4_K_M | 12B Q3_K_M with offload |
| 8 GiB VRAM | 7B-8B Q4_K_M | 7B-9B Q5_K_M | 12B-14B Q4_K_M with partial offload |
| 12 GiB VRAM | 7B-9B Q5_K_M | 12B-14B Q4_K_M | 24B Q3_K_M with offload |
| 16 GiB VRAM | 12B-14B Q4_K_M | 12B-14B Q5_K_M | 24B-32B Q3_K_M/Q4_K_M with offload |
| 24 GiB VRAM | 14B Q5_K_M/Q6_K | 24B-32B Q4_K_M | 70B Q2_K/Q3_K_M with heavy offload |
| 32-36 GiB VRAM/unified | 24B-32B Q4_K_M | 32B Q5_K_M | 70B Q3_K_M with offload |
| 48 GiB VRAM/unified | 32B Q5_K_M | 70B Q4_K_M | 70B Q5_K_M or MoE larger with offload |
| 64+ GiB VRAM/unified | 70B Q4_K_M | 70B Q5_K_M/Q6_K | 100B+ or MoE if disk/RAM support it |

## Disk requirements

Require free disk for the model file plus workspace margin:

- Comfortable/Balanced: at least `estimated_gib + 10 GiB` free.
- Stretch: at least `estimated_gib + 20 GiB` free.
- If free disk is below the estimate, recommend freeing space before install rather than choosing the model.
