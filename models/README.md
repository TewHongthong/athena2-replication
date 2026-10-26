# Model pins

`model_pins.json` fixes, for each model of the Vol. 2 panel, the request that the harness sends: the backend and
endpoint, the sampling settings, and an extra request body that locks the serving provider. A run uses an entry with

```
python athena_sim.py run --model-pin luna ...            (from the athena-sim folder)
python athena_sim.py freeze --model-pin luna ... --out-file frozen.json
```

`--model-pin` replaces `--backend`, `--base-url`, `--temperature`, `--max-tokens`, `--omit-temperature`,
`--no-think`, `--extra-body` and the price options. The SHA-256 of the entry is stored in the run configuration and
in a freeze, so a test run refuses to start if the entry has changed since the freeze.

The Vol. 2 panel is GPT-6 Luna, Gemini 3.1 Flash-Lite, Gemma 4 26B (`gemma4_local`) and Qwen3.5-9B. The entries
`deepseek41f`, `mistral_large4` and the hosted `gemma4` stay in the file but are not used in the planned runs.

The entry `luna_draft` is a second pin of GPT-6 Luna with the same route and settings as `luna` except
`max_tokens` (32768 instead of 8192). It is used only to draft the LLM-drafted ontologies (`draft_ontology.py`, one
request per standard) and is not a panel entry for the benchmark runs.

## What a pin fixes and what it cannot fix

None of the hosted models offers a dated snapshot: each vendor identifier (`gpt-6-luna`, `gemini-3.1-flash-lite`,
`deepseek-flash`, `mistral-large-4-0`) may be updated in place by its vendor. Mistral Large 4 is in Public Preview.
A pin therefore fixes the request, not the model. The following is fixed:

- the model slug and the endpoint (OpenRouter for every hosted model, as in Vol. 1, so that the Vol. 1 anchors and
  the new runs go through the same router);
- the serving provider: `provider.order` names one provider and `allow_fallbacks` is false, so a request fails
  instead of being answered by another provider. Vol. 1 did not lock providers; its Gemma 4 ablation trials were
  answered by at least five providers with different deployments;
- `require_parameters`, so that a parameter the provider does not support makes the request fail instead of being
  dropped silently;
- for DeepSeek, `data_collection` set to `allow` in the request: the vendor's endpoint may use prompts for training,
  and an OpenRouter account that excludes such endpoints would otherwise get an HTTP 404 for every request. The
  prompts contain only public standards and public source code;
- the sampling settings, including whether a temperature is sent at all, and reasoning or thinking settings where
  the vendor documents them.

The following is recorded per trial instead (in `trials.jsonl`): the model name returned by the endpoint
(`model`), the provider that answered (`provider`), the response id (`response_id`, which for OpenRouter is the
generation id) and `system_fingerprint` when the provider sends one.

## Drift check

Because the hosted models can change silently, every model's test run is bracketed by a fixed canary run:

1. before the first test trial and after the last one, run the same canary set with the same pin: 30 dev units of
   each pack, condition `none`, 1 repeat (`--split dev --conditions none --per-language 0 --limit 30 --seed 42`),
   in run folders named `canary_<pin>_start` and `canary_<pin>_end`;
2. report, per model, the change in `core_ok` between the two canary runs and the share of units whose proposed
   name is identical in both runs;
3. report any change of `model`, `provider` or `system_fingerprint` seen across the trials of a model.

The canary costs well under 1% of the B1 trials. The rule that decides whether a difference between the canary runs
leads to any action is stated in `HYPOTHESES_v2.md`, Section 2.1.

## Dense retrieval: embedding model

The `dense` condition ranks the passages of a standard by cosine similarity of embeddings. Its model is pinned in the
`embeddings` section of `model_pins.json` and selected with `--embed-pin NAME` (`qwen3_embedding_06b`). The entry fixes the model
id sent to the server, the instruction that is put in front of a query (passages are embedded without one), the batch size, and the
identity of the model file. The instruction is part of the pin and is not tuned. A run refuses an entry that is marked `incomplete`.

The model is `Qwen3-Embedding-0.6B-Q8_0.gguf` from `Qwen/Qwen3-Embedding-0.6B-GGUF`, served by a second llama-server on the same
Windows machine as Qwen3.5-9B (it needs well under 1 GB of GPU memory). The entry becomes `pinned` once the hash computed on the
serving machine and the llama.cpp build are filled in.

Download at the pinned revision, then record the hash and the build (on the serving machine):

```
C:\Windows\System32\curl.exe -L --fail -C - -o C:\llama.cpp\models\Qwen3-Embedding-0.6B-Q8_0.gguf https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/370f27d7550e0def9b39c1f16d3fbaa13aa67728/Qwen3-Embedding-0.6B-Q8_0.gguf
C:\Windows\System32\certutil.exe -hashfile C:\llama.cpp\models\Qwen3-Embedding-0.6B-Q8_0.gguf SHA256
C:\llama.cpp\llama-server.exe --version
```

The download uses the `curl.exe` that ships with Windows 10 (the full path avoids the PowerShell alias), the file is addressed by the
pinned revision in the URL, and `-C -` resumes an interrupted transfer; no Hugging Face client is needed on the serving machine.
The hash must equal `gguf_sha256_listed` of the entry. Start the server in embedding mode with last-token pooling and a batch size
large enough for the longest passage or snippet (the default micro-batch of 512 tokens is too small):

```
C:\llama.cpp\llama-server.exe -m C:\llama.cpp\models\Qwen3-Embedding-0.6B-Q8_0.gguf --alias qwen3-embedding-0.6b-q8_0 --embedding --pooling last -c 8192 -b 8192 -ub 8192 -np 1 -ngl 99 --host 127.0.0.1 --port 8081
```

The harness reaches it through an SSH tunnel and checks it before any run:

```
ssh -N -L 8081:127.0.0.1:8081 <user>@<serving machine>
export ATHENA_EMBED_BASE_URL=http://127.0.0.1:8081/v1
python athena_sim.py embed-check --embed-pin qwen3_embedding_06b        (from the athena-sim folder)
```

`embed-check` embeds four obvious passages and three queries and prints which passage is nearest to each query; all three must be
found. It tests the serving setup (pooling, end-of-text handling, templates), not the experiment. Vectors are cached by the hash of
the entry, so a changed entry starts from an empty cache.

## Qwen3.5-9B

Qwen3.5-9B runs with llama-server on a Windows machine of the lab (RTX 4000 Ada, 20 GB), so the pin is a file, not a
slug: `Qwen3.5-9B-UD-Q8_K_XL.gguf` from `unsloth/Qwen3.5-9B-GGUF` at the revision recorded in the entry. The SHA-256
computed on the serving machine matches the hash listed by the repository, and the llama.cpp build and the server
command are recorded in the entry; a different build or command is a different deployment.

Download at the pinned revision and record the hash and build (on the serving machine):

```
C:\Windows\System32\curl.exe -L --fail -C - -o C:\llama.cpp\models\Qwen3.5-9B-UD-Q8_K_XL.gguf https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/resolve/3885219b6810b007914f3a7950a8d1b469d598a5/Qwen3.5-9B-UD-Q8_K_XL.gguf
C:\Windows\System32\certutil.exe -hashfile C:\llama.cpp\models\Qwen3.5-9B-UD-Q8_K_XL.gguf SHA256
C:\llama.cpp\llama-server.exe --version
```

Start the server with a fixed alias and a context large enough for the longest prompt (the full text of the Odoo
guideline alone is about 48 KB; Vol. 1 used 4,096 tokens, which is too small):

```
C:\llama.cpp\llama-server.exe -m C:\llama.cpp\models\Qwen3.5-9B-UD-Q8_K_XL.gguf --alias qwen3.5-9b-ud-q8_k_xl -ngl 99 -c 32768 -np 1 --jinja --host 127.0.0.1 --port 8080
```

The harness reaches it through an SSH tunnel, so the server does not need to listen on the network:

```
ssh -N -L 8080:127.0.0.1:8080 <user>@<serving machine>
OPENAI_BASE_URL=http://127.0.0.1:8080/v1 python athena_sim.py run --model-pin qwen35_9b ...
```

Vol. 1 ran Qwen3.5-9B as Q4_K_M on another machine, so its Qwen anchors come from a different deployment.

## Gemma 4 26B (local)

The Gemma 4 26B (A4B) pin `gemma4_local` runs the model with llama-server on the same Windows machine as Qwen3.5-9B,
so the pin is a file: `gemma-4-26B-A4B-it-UD-Q4_K_M.gguf` from `unsloth/gemma-4-26B-A4B-it-GGUF` at the revision
recorded in the entry. The SHA-256 computed on the serving machine matches the hash listed by the repository, and the
llama.cpp build is the same as for Qwen3.5-9B. The hosted entry `gemma4` (OpenRouter, bf16, one locked provider) is kept
in the pin file as an alternative; a run uses one of the two, and the choice is recorded through the entry hash.

Download at the pinned revision and record the hash and the build (on the serving machine):

```
C:\Windows\System32\curl.exe -L --fail -C - -o C:\llama.cpp\models\gemma-4-26B-A4B-it-UD-Q4_K_M.gguf https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/resolve/c099eb48e663fd284577b04978a94ffccb261841/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf
C:\Windows\System32\certutil.exe -hashfile C:\llama.cpp\models\gemma-4-26B-A4B-it-UD-Q4_K_M.gguf SHA256
C:\llama.cpp\llama-server.exe --version
```

The file is about 17 GB, so on a 20 GB GPU the model is served alone: stop the other llama-server processes first (the
Qwen3.5-9B server and the embedding server cannot run next to it). With a context of 32,768 tokens the server uses about
17.4 GB of GPU memory. Start the server with a fixed alias:

```
C:\llama.cpp\llama-server.exe -m C:\llama.cpp\models\gemma-4-26B-A4B-it-UD-Q4_K_M.gguf --alias gemma-4-26b-a4b-it-ud-q4_k_m -ngl 99 -c 32768 -np 1 --jinja --host 127.0.0.1 --port 8080
```

The chat template of the model thinks by default. The pin therefore sets `no_think`, which sends
`chat_template_kwargs.enable_thinking=false` with every request; without it the token budget is spent on reasoning and
the answer can be empty. The harness reaches the server through an SSH tunnel, as for Qwen3.5-9B:

```
ssh -N -L 8080:127.0.0.1:8080 <user>@<serving machine>
OPENAI_BASE_URL=http://127.0.0.1:8080/v1 python athena_sim.py run --model-pin gemma4_local ...
```

Vol. 1 ran Gemma 4 26B as a local Ollama Q4_K_M build, which is a different GGUF and runtime, so its Gemma anchors come
from a different deployment.
