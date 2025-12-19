"""
SD Prompt Expander - Local Web GUI
Run with: python app.py
Open: http://localhost:8085
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import requests
import re
import json

app = Flask(__name__)
CORS(app)

OLLAMA_URL = "http://localhost:11434"
SD_URL = "http://localhost:7860"

SYSTEM_PROMPT = """You are an expert Stable Diffusion prompt engineer. Transform simple ideas into detailed, effective prompts.

FIRST, analyze the subject:
- DIFFICULT subjects (need hiding tricks): people with visible hands/faces, animals in motion, multiple figures, complex poses
- EASY subjects (no tricks needed): landscapes, architecture, food, objects, abstract concepts, vehicles, interiors

FOR DIFFICULT SUBJECTS, use these tricks:
- Silhouettes, backlighting, distance shots
- Fog, dust, atmospheric haze to obscure problem areas
- "seen from behind", "side profile", "wide shot"
- Keep figures small in frame or in shadow

FOR EASY SUBJECTS, focus on:
- Rich descriptive detail
- Interesting lighting (not always sunset/backlit!)
- Composition and framing
- Texture and material descriptions
- Time of day variety (morning, noon, golden hour, night, overcast)

GENERAL RULES:
- Never use numbers for counting - use "lone", "pair", "group", "several"
- Include style anchors: "cinematic", "photography", "concept art", "illustration", etc.
- Vary your lighting! Not everything needs god rays or sunset
- Match the mood to the subject (bright for happy, dark for moody, etc.)

Respond with ONLY valid JSON:
{"prompt": "the detailed positive prompt", "negative": "things to avoid", "tip": "one sentence explaining your approach"}"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SD Prompt Expander</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e4e4e7;
            padding: 2rem;
        }
        .container { max-width: 800px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 2rem; }
        h1 { color: #f97316; font-size: 2rem; margin-bottom: 0.5rem; }
        .subtitle { color: #71717a; font-size: 0.9rem; }
        .badge {
            display: inline-block;
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            margin-left: 0.5rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .model-selector {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }
        .model-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.75rem;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.2s;
            text-align: left;
            color: #e4e4e7;
        }
        .model-btn:hover { border-color: rgba(249, 115, 22, 0.5); }
        .model-btn.active { border-color: #f97316; background: rgba(249, 115, 22, 0.1); }
        .model-btn .name { font-weight: 600; font-size: 0.9rem; }
        .model-btn .meta { font-size: 0.75rem; color: #71717a; margin-top: 0.25rem; }
        textarea {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.75rem;
            padding: 1rem;
            color: #e4e4e7;
            font-size: 1rem;
            resize: vertical;
            min-height: 100px;
            font-family: inherit;
        }
        textarea:focus { outline: none; border-color: #f97316; }
        textarea::placeholder { color: #52525b; }
        .btn-row { display: flex; gap: 0.75rem; margin-top: 1rem; }
        .btn {
            flex: 1;
            padding: 1rem 1.5rem;
            border: none;
            border-radius: 0.75rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: white; }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(249, 115, 22, 0.4); }
        .btn-primary:disabled { background: #3f3f46; color: #71717a; transform: none; box-shadow: none; cursor: not-allowed; }
        .btn-secondary { background: rgba(255, 255, 255, 0.1); color: #e4e4e7; border: 1px solid rgba(255, 255, 255, 0.1); }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.15); }
        .btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
        .result-card { background: rgba(0, 0, 0, 0.3); border-radius: 0.75rem; padding: 1rem; margin-top: 1rem; }
        .result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .result-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        .result-label.positive { color: #4ade80; }
        .result-label.negative { color: #f87171; }
        .result-label.tip { color: #f97316; }
        .copy-btn { background: none; border: none; color: #71717a; cursor: pointer; font-size: 0.8rem; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
        .copy-btn:hover { color: #e4e4e7; background: rgba(255,255,255,0.1); }
        .result-text { color: #d4d4d8; line-height: 1.6; }
        .status { text-align: center; padding: 2rem; color: #71717a; }
        .status.error { color: #f87171; }
        .spinner {
            display: inline-block;
            width: 20px; height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #f97316;
            animation: spin 1s linear infinite;
            margin-right: 0.5rem;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .response-time { text-align: right; font-size: 0.75rem; color: #71717a; margin-top: 0.5rem; }
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #52525b;
            font-size: 0.8rem;
        }
        .preview-section { margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1); }
        .preview-section h3 { font-size: 0.9rem; color: #a1a1aa; margin-bottom: 1rem; }
        .preview-image { width: 100%; border-radius: 0.75rem; margin-top: 1rem; }
        .settings-row { display: flex; gap: 1rem; margin-top: 1rem; }
        .setting { flex: 1; }
        .setting label { display: block; font-size: 0.75rem; color: #71717a; margin-bottom: 0.25rem; }
        .setting input {
            width: 100%;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 0.5rem;
            padding: 0.5rem;
            color: #e4e4e7;
            font-size: 0.9rem;
        }
        .setting input:focus { outline: none; border-color: #f97316; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SD Prompt Expander <span class="badge">LOCAL</span></h1>
            <p class="subtitle">Transform simple ideas into optimized Stable Diffusion prompts</p>
        </header>

        <div class="card">
            <label style="font-size: 0.75rem; color: #71717a; text-transform: uppercase; letter-spacing: 0.05em;">Model</label>
            <div class="model-selector" style="margin-top: 0.5rem;">
                <button class="model-btn active" data-model="gemma2:2b">
                    <div class="name">Gemma2 2B</div>
                    <div class="meta">1.6GB - Fast</div>
                </button>
                <button class="model-btn" data-model="llama3.1:8b">
                    <div class="name">Llama 3.1 8B</div>
                    <div class="meta">4.9GB - Better</div>
                </button>
                <button class="model-btn" data-model="qwen2.5:14b">
                    <div class="name">Qwen 2.5 14B</div>
                    <div class="meta">9GB - Best</div>
                </button>
            </div>

            <textarea id="idea" placeholder="Enter a simple idea... e.g. 'a wizard in a library' or 'cyberpunk city'"></textarea>
            
            <div class="btn-row">
                <button class="btn btn-primary" id="expandBtn">Expand Prompt</button>
                <button class="btn btn-secondary" id="generateBtn" disabled>Generate Image</button>
            </div>
        </div>

        <div id="results" style="display: none;">
            <div class="card">
                <div class="result-card">
                    <div class="result-header">
                        <span class="result-label positive">Positive Prompt</span>
                        <button class="copy-btn" onclick="copyText('positive')">Copy</button>
                    </div>
                    <p class="result-text" id="positive"></p>
                </div>

                <div class="result-card">
                    <div class="result-header">
                        <span class="result-label negative">Negative Prompt</span>
                        <button class="copy-btn" onclick="copyText('negative')">Copy</button>
                    </div>
                    <p class="result-text" id="negative"></p>
                </div>

                <div class="result-card">
                    <div class="result-header">
                        <span class="result-label tip">Why This Works</span>
                    </div>
                    <p class="result-text" id="tip"></p>
                </div>

                <p class="response-time" id="responseTime"></p>

                <div class="preview-section">
                    <h3>Generation Settings</h3>
                    <div class="settings-row">
                        <div class="setting">
                            <label>Width</label>
                            <input type="number" id="width" value="1216" step="64">
                        </div>
                        <div class="setting">
                            <label>Height</label>
                            <input type="number" id="height" value="832" step="64">
                        </div>
                        <div class="setting">
                            <label>Steps</label>
                            <input type="number" id="steps" value="30">
                        </div>
                        <div class="setting">
                            <label>CFG Scale</label>
                            <input type="number" id="cfg" value="7" step="0.5">
                        </div>
                    </div>
                    <div id="imagePreview"></div>
                </div>
            </div>
        </div>

        <div id="status" class="status" style="display: none;"></div>

        <footer class="footer">
            Powered by Ollama + Stable Diffusion WebUI - Running on your GPU
        </footer>
    </div>

    <script>
        let selectedModel = 'gemma2:2b';
        let currentPrompts = { prompt: '', negative: '' };

        document.querySelectorAll('.model-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.model-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedModel = btn.dataset.model;
            });
        });

        document.getElementById('expandBtn').addEventListener('click', expandPrompt);
        document.getElementById('idea').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) expandPrompt();
        });

        async function expandPrompt() {
            const idea = document.getElementById('idea').value.trim();
            if (!idea) return;

            const btn = document.getElementById('expandBtn');
            const status = document.getElementById('status');
            const results = document.getElementById('results');

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>Thinking...';
            status.style.display = 'block';
            status.className = 'status';
            status.textContent = 'Generating prompt with ' + selectedModel + '...';
            results.style.display = 'none';

            try {
                const startTime = Date.now();
                const response = await fetch('/api/expand', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ idea, model: selectedModel })
                });

                const data = await response.json();
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

                if (data.error) throw new Error(data.error);

                currentPrompts = { prompt: data.prompt, negative: data.negative };
                document.getElementById('positive').textContent = data.prompt;
                document.getElementById('negative').textContent = data.negative;
                document.getElementById('tip').textContent = data.tip || '';
                document.getElementById('responseTime').textContent = 'Generated in ' + elapsed + 's';

                results.style.display = 'block';
                status.style.display = 'none';
                document.getElementById('generateBtn').disabled = false;

            } catch (err) {
                status.className = 'status error';
                status.textContent = 'Error: ' + err.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Expand Prompt';
            }
        }

        document.getElementById('generateBtn').addEventListener('click', generateImage);

        async function generateImage() {
            const btn = document.getElementById('generateBtn');
            const preview = document.getElementById('imagePreview');

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>Generating...';
            preview.innerHTML = '<p style="text-align:center;color:#71717a;padding:2rem;">Generating image...</p>';

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        prompt: currentPrompts.prompt,
                        negative_prompt: currentPrompts.negative,
                        width: parseInt(document.getElementById('width').value),
                        height: parseInt(document.getElementById('height').value),
                        steps: parseInt(document.getElementById('steps').value),
                        cfg_scale: parseFloat(document.getElementById('cfg').value)
                    })
                });

                const data = await response.json();
                if (data.error) throw new Error(data.error);

                preview.innerHTML = '<img src="data:image/png;base64,' + data.image + '" class="preview-image">';

            } catch (err) {
                preview.innerHTML = '<p style="text-align:center;color:#f87171;padding:2rem;">Error: ' + err.message + '</p>';
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Generate Image';
            }
        }

        function copyText(id) {
            const text = document.getElementById(id).textContent;
            navigator.clipboard.writeText(text).then(() => {
                const btn = event.target;
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/expand', methods=['POST'])
def expand_prompt():
    data = request.json
    idea = data.get('idea', '')
    model = data.get('model', 'gemma2:2b')

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": f"{SYSTEM_PROMPT}\n\nTransform this idea: \"{idea}\"",
                "stream": False
            },
            timeout=120
        )
        result = response.json()
        text = result.get('response', '')

        json_match = re.search(r'\{[\s\S]*?\}', text)
        if json_match:
            parsed = json.loads(json_match.group())
            return jsonify(parsed)
        else:
            return jsonify({
                "prompt": text.strip(),
                "negative": "blurry, deformed, bad anatomy, watermark, low quality",
                "tip": "Raw output used as prompt"
            })

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot connect to Ollama. Is it running?"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_image():
    data = request.json

    try:
        payload = {
            "prompt": data.get('prompt', ''),
            "negative_prompt": data.get('negative_prompt', ''),
            "width": data.get('width', 1216),
            "height": data.get('height', 832),
            "steps": data.get('steps', 30),
            "cfg_scale": data.get('cfg_scale', 7),
            "sampler_name": "DPM++ 2M SDE",
            "seed": -1
        }

        response = requests.post(
            f"{SD_URL}/sdapi/v1/txt2img",
            json=payload,
            timeout=300
        )
        result = response.json()

        if 'images' in result and result['images']:
            return jsonify({"image": result['images'][0]})
        else:
            return jsonify({"error": "No image returned from SD"}), 500

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot connect to SD WebUI. Is it running?"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  SD Prompt Expander")
    print("="*50)
    print(f"  Ollama API: {OLLAMA_URL}")
    print(f"  SD WebUI:   {SD_URL}")
    print("="*50)
    print("\n  Open in browser: http://localhost:8085\n")
    app.run(host='0.0.0.0', port=8085, debug=False)
