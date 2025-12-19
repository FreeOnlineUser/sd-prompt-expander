# SD Prompt Expander

A local web GUI that uses Ollama to expand simple ideas into optimized Stable Diffusion prompts, then generates images via SD WebUI.

## Features

- **Local LLM prompt expansion** via Ollama (gemma2:2b, llama3.1:8b, or qwen2.5:14b)
- **Direct SD WebUI integration** - generate images without leaving the app
- **Smart prompt engineering** built-in:
  - Uses spatial words instead of numbers
  - Applies hiding tricks (silhouettes, fog, backlighting)
  - Specifies viewpoints to avoid anatomy issues
  - Adds atmospheric elements
  - Includes style anchors

## Requirements

- Python 3.8+
- [Ollama](https://ollama.com/) running locally with at least one model
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) running with API enabled

## Installation

```bash
git clone https://github.com/FreeOnlineUser/sd-prompt-expander.git
cd sd-prompt-expander
pip install -r requirements.txt
```

## Usage

1. Make sure Ollama is running (`ollama serve`)
2. Make sure SD WebUI is running with `--api` flag
3. Run the app:
   ```bash
   python app.py
   ```
   Or double-click `run.bat` on Windows
4. Open http://localhost:8085 in your browser

## Configuration

Edit `app.py` to change:
- `OLLAMA_URL` - default: `http://localhost:11434`
- `SD_URL` - default: `http://localhost:7860`
- Port - default: `8085`

## How It Works

1. Enter a simple idea like "a dragon" or "cyberpunk city"
2. Select an Ollama model (smaller = faster, larger = better)
3. Click "Expand Prompt" - the LLM applies SD prompt engineering principles
4. Review the positive/negative prompts and tips
5. Adjust generation settings if needed
6. Click "Generate Image" to create via SD WebUI

## License

MIT
