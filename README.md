i got tired of the ads saying "oh do you have a bajillion recipes saved on instagram but cant find them? here download our app!!" so i just made my own

self hosted LLM instances:
- qwen 2.5 7B AWQ for vision to text
- qwen 2.5 7B for text to text
- whisper asr for audio to text

takes in instagram reel link, outputs a markdown formatted file w recipe and saves it to my obsidian vault
you can remove the obsidian part if you dont care, i have my obsidian vaults synced across devices so i can run this on my pc, sync my vault over git, and it gets autosynced on my phone :)

CONFIG.py is needed in project directory

```python
VAULT_ROOT = "/path/to/your/obsidian/vault"
VAULT_PATH = "/path/to/your/obsidian/vault/some/subfolder"

VISION_CONTAINER  = "vllm-vision"
TEXT_CONTAINER    = "vllm-text"
WHISPER_CONTAINER = "whisper-asr"

VISION_URL  = "http://localhost:8000/v1"
TEXT_URL    = "http://localhost:8000/v1"
WHISPER_URL = "http://localhost:9000/asr"

VISION_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct-AWQ"
TEXT_MODEL   = "Qwen/Qwen2.5-7B-Instruct"

VLLM_API_KEY = "token"

CONTAINERS = {
    VISION_CONTAINER:  "http://localhost:8000/v1/models",
    TEXT_CONTAINER:    "http://localhost:8000/v1/models",
    WHISPER_CONTAINER: "http://localhost:9000/docs",
}

VISION_MAX_TOKENS    = 150
TEXT_MAX_TOKENS_DOC  = 2500
TEXT_MAX_TOKENS_NAME = 20

STARTUP_TIMEOUT = 420
POLL_INTERVAL   = 3
```

**docker containers** — build image first using the included `Dockerfile`, then create containers:

```bash
docker build -t vllm-local /path/to/Dockerfile/dir/

# vision model
docker create --name vllm-vision --gpus '"device=0"' -p 8000:8000 \
  -e HF_HUB_OFFLINE=1 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm-local \
  --model Qwen/Qwen2.5-VL-7B-Instruct-AWQ \
  --quantization awq --dtype float16 \
  --max-model-len 32768 --gpu-memory-utilization 0.75

# text model
docker create --name vllm-text --gpus '"device=0"' -p 8000:8000 \
  -e HF_HUB_OFFLINE=1 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm-local \
  --model Qwen/Qwen2.5-7B-Instruct \
  --gpu-memory-utilization 0.9

# whisper (CPU)
docker create --name whisper-asr -p 9000:9000 \
  onerahmet/openai-whisper-asr-webservice:latest
```

`ffmpeg` also needs to be installed on your system.

```bash
python reel_to_recipe.py <instagram_reel_url>
```

there's also a `server.py` (fastapi) if you want to trigger it over HTTP

i use apple shortcuts over my tailnet