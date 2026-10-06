# Gemini Prompt Rewriter for ComfyUI

A ComfyUI custom node that sends text to the Google Gemini API and outputs the model's
response as a `STRING`. Type your instruction and prompt into the single `text` field, then wire the
output into any text input, such as **CLIP Text Encode**.

- One node, one text field
- No extra Python packages: it uses only the standard library
- API key read from a local config file or environment variable, never stored in workflows
- Defaults to `gemini-3.1-flash-lite`, Gemini's fastest and cheapest current model

## Installation

### ComfyUI Manager
Use **Install via Git URL** and paste this repository's URL.

### Manual
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/rb-dimitri/comfyui-gemini-prompt-sanitizer.git
```
Restart ComfyUI afterwards.

## API key

Get a key from [Google AI Studio](https://aistudio.google.com/apikey), then use one of these options.

### Option 1: config file (recommended)
Copy `config.example.json` to `config.json` in this node's folder and paste in your key:
```json
{
  "api_key": "your-key-here"
}
```
`config.json` is listed in `.gitignore`, so it is never committed. Changes take effect on the next run,
without restarting ComfyUI.

### Option 2: environment variable
**Windows**
```bash
setx GEMINI_API_KEY "your-key-here"
```

**Linux / macOS**
```bash
export GEMINI_API_KEY="your-key-here"
```

`GOOGLE_API_KEY` is also accepted. Restart ComfyUI, and the terminal that launches it, after setting the key.

If both are set, `config.json` takes priority.

## Usage

Find the node under **text/LLM → Gemini Prompt Rewriter**.

| Input | Type | Default | Description |
|---|---|---|---|
| `text` | STRING | empty | Full message sent to Gemini (instruction + prompt). Can be typed or connected. |
| `model` | choice | `gemini-3.1-flash-lite` | Gemini model to use. |
| `temperature` | FLOAT | `0.0` | 0 gives the most consistent output. |
| `timeout_seconds` | INT | `60` | Seconds to wait before failing. |

| Output | Type | Description |
|---|---|---|
| `response` | STRING | Gemini's text response. |

ComfyUI caches the result, so the API is only called again when an input changes.

### Models

| Model | Input / Output price per 1M tokens | Notes |
|---|---|---|
| `gemini-3.1-flash-lite` | $0.25 / $1.50 | Default. Fast, cheap, strong at translation |
| `gemini-3.5-flash-lite` | $0.30 / $2.50 | |
| `gemini-2.5-flash-lite` | $0.10 / $0.40 | Older, cheapest |
| `gemini-3.8-flash` | $0.75 / $3.75 | Most capable in the list |

Prices as of October 2026; see [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing).

## Error handling

If the API key is missing, or the request fails, is blocked, times out or returns an empty response,
the node raises an error and the workflow stops. It never passes the input through unprocessed.

## Privacy

- The API key is read from `config.json` (git-ignored) or the environment, and never stored in workflows.
- Text typed into the node is saved inside ComfyUI workflow `.json` files. Don't commit workflows
  that contain private instructions.
