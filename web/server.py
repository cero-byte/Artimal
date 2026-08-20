#!/usr/bin/env python3
"""Local web server and OpenAI API proxy for the Artimal prototype."""

import base64
import csv
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import ssl
import urllib.error
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
CONFIG_PATH = Path(
    os.environ.get("ARTIMAL_CONFIG_PATH", PROJECT_ROOT / "config.json")
).expanduser().resolve()
DATA_ROOT = Path(
    os.environ.get("ARTIMAL_DATA_DIR", PROJECT_ROOT / "data" / "collected")
).expanduser().resolve()
MAX_REQUEST_BYTES = 25 * 1024 * 1024
ALLOWED_IMAGE_MODELS = {"gpt-image-1-mini", "gpt-image-2"}
ALLOWED_IMAGE_QUALITIES = {"low", "medium", "high"}
ALLOWED_IMAGE_SIZES = {"1024x1024", "1024x1536", "1536x1024"}
DEFAULT_OPENAI_API_BASE_URL = "https://api.openai.com/v1"


def load_config(path=CONFIG_PATH):
    """Load local secrets and API settings without exposing them to the browser."""
    if not path.is_file():
        return {"openai": {"api_base_url": DEFAULT_OPENAI_API_BASE_URL, "api_key": ""}}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read valid JSON configuration from {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError(f"Configuration root must be a JSON object: {path}")
    openai_config = raw.get("openai", {})
    if not isinstance(openai_config, dict):
        raise RuntimeError(f"Configuration field 'openai' must be a JSON object: {path}")

    api_base_url = str(
        openai_config.get("api_base_url") or DEFAULT_OPENAI_API_BASE_URL
    ).strip().rstrip("/")
    api_key = str(openai_config.get("api_key") or "").strip()
    if not api_base_url.startswith(("https://", "http://")):
        raise RuntimeError("openai.api_base_url must start with https:// or http://")
    return {"openai": {"api_base_url": api_base_url, "api_key": api_key}}


APP_CONFIG = load_config()


def configured_api_key():
    """Environment variables override config.json for deployment use."""
    return (
        os.environ.get("OPENAI_API_KEY")
        or APP_CONFIG["openai"]["api_key"]
        or ""
    ).strip()


def openai_api_url(endpoint):
    base_url = (
        os.environ.get("OPENAI_API_BASE_URL")
        or APP_CONFIG["openai"]["api_base_url"]
        or DEFAULT_OPENAI_API_BASE_URL
    ).strip().rstrip("/")
    return f"{base_url}/{endpoint.lstrip('/')}"


class RequestError(ValueError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def get_ssl_context():
    """Return a verified TLS context, optionally using certifi's CA bundle."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()

def post_json(url, payload, api_key, timeout=180):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=timeout, context=get_ssl_context()) as resp:
        return json.loads(resp.read().decode('utf-8'))

def extract_json(text):
    if not text:
        return None
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```$', '', text)
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except Exception:
        return None

def openai_text(api_key, data):
    raw_term = (
        data.get('custom_intention')
        or data.get('selected_image')
        or data.get('chosen_image')
        or data.get('chosen_category')
        or "image"
    )
    lang = (data.get('language') or 'zh').lower()
    answer_language = 'Simplified Chinese' if lang.startswith('zh') else 'English'
    system = (
        "You are an art-therapy imagination guide for an HCI prototype. Return only valid JSON. "
        "Do not diagnose, do not infer hidden trauma, and do not intensify distress. "
        "Your role is reflective scaffolding: respond to the user's own words, gently organize them, validate that the experience is reasonable, and suggest optional next-step imagination actions. "
        "Use principles of body mapping, sensory refinement, metaphor externalization, mental imagery detail observation, dynamic imagery, body-metaphor mapping, and drawing bridge prompts. "
        f"Write all guiding questions in {answer_language}, while understanding user input in either Chinese or English."
    )
    user = f"""
User body input: {data.get('body','')}
Texture words: {data.get('texture','')}
Selected tags: {data.get('tags',[])}
Selected metaphor categories: {data.get('selected_categories',[])}
Chosen trait: {data.get('chosen_trait','')}
Chosen/typed image: {raw_term}

Task:
1. Identify the image/metaphor subject the user wants to imagine. This should be the chosen detailed species/object/scene, not a body organ unless the user explicitly chose an organ as the metaphor.
2. If the term contains injured, bloody, or violent modifiers, remove those for reference-image safety. Keep neutral or gentle modifiers if they are central to the user's image.
3. Generate 4 gentle, open-ended imagination questions. The questions should progress through:
   - visual detail: shape, color, size, edge, distance;
   - dynamic imagery: movement, pressure, floating, sinking, growing, hiding, changing;
   - body-metaphor mapping: how this image lives in the chosen body area;
   - drawing bridge: where to begin on paper, such as point, line, shape, color, or movement.
4. The questions must be reflective, not interpretive. Do not tell the user what the image means. Invite them to observe and choose.
5. The guiding_questions must be written in {answer_language}. The neutral_subject may preserve the user's original language if it is the clearest expression.

Return JSON exactly:
{{
  "raw_intention": "{raw_term}",
  "neutral_subject": "...",
  "removed_modifiers": ["..."],
  "guiding_questions": ["...", "...", "...", "..."]
}}
""".strip()
    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ],
        'temperature': 0.55,
        'response_format': {'type': 'json_object'}
    }
    res = post_json(openai_api_url('chat/completions'), payload, api_key, timeout=90)
    txt = res.get('choices', [{}])[0].get('message', {}).get('content', '')
    parsed = extract_json(txt) or {}
    return parsed

def generate_one_reference(api_key, subject, style_label):
    prompt = (
        f"Create a visual reference image of: {subject}. "
        f"This must be the user's chosen metaphor/object/species/scene, not a human body organ unless the subject itself is an organ. "
        f"If the subject includes injury, blood, or violence, remove those unsafe details. No text, no labels, no UI. "
        f"Style: {style_label}. Gentle art-therapy interface reference, clean composition, soft lighting."
    )
    payload = {
        'model': 'gpt-image-1-mini',
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024',
        'quality': 'low'
    }
    res = post_json(openai_api_url('images/generations'), payload, api_key, timeout=180)
    b64 = None
    if res.get('data'):
        b64 = res['data'][0].get('b64_json')
    if not b64:
        raise RuntimeError('OpenAI image response did not include b64_json')
    return 'data:image/png;base64,' + b64

class ArtimalHandler(SimpleHTTPRequestHandler):
    server_version = "ArtimalLocal/1.0"

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        super().end_headers()

    def do_GET(self):
        if self.path == '/config':
            return self._json(
                200,
                {'server_api_key_configured': bool(configured_api_key())},
            )
        return super().do_GET()

    def do_POST(self):
        if self.path == '/prepare-imagination':
            return self.prepare_imagination()
        if self.path == '/generate-references':
            return self.generate_references()
        if self.path == '/generate-image':
            return self.generate_final_image()
        if self.path == '/reflect-drawing':
            return self.reflect_drawing()
        if self.path == '/save-session':
            return self.save_session()
        self.send_error(404, 'Not found')

    def _read_json(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError as exc:
            raise RequestError(400, 'Invalid Content-Length header.') from exc
        if length <= 0:
            raise RequestError(400, 'Request body must contain JSON.')
        if length > MAX_REQUEST_BYTES:
            raise RequestError(413, 'Request body is too large.')
        try:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestError(400, 'Request body must be valid UTF-8 JSON.') from exc

    @staticmethod
    def _api_key(data):
        """Prefer a server-side key; retain browser input for local demos."""
        return (configured_api_key() or data.get('api_key') or '').strip()

    def _json(self, status, obj):
        out = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def _api_error(self, e):
        if isinstance(e, RequestError):
            return e.status, str(e)
        if isinstance(e, urllib.error.HTTPError):
            raw = e.read().decode('utf-8', errors='replace')
            try:
                j = json.loads(raw)
                return e.code, j.get('error', {}).get('message') or raw
            except Exception:
                return e.code, raw
        return 500, str(e)

    def prepare_imagination(self):
        try:
            data = self._read_json()
            api_key = self._api_key(data)
            if not api_key:
                return self._json(400, {'error':'缺少 OpenAI API key。'})
            info = openai_text(api_key, data)
            subject = (
                info.get('neutral_subject')
                or data.get('selected_image')
                or data.get('custom_intention')
                or data.get('chosen_category')
                or 'image'
            ).strip()
            qs = info.get('guiding_questions') or []
            return self._json(200, {
                'raw_intention': info.get('raw_intention') or data.get('selected_image') or data.get('custom_intention') or subject,
                'neutral_subject': subject,
                'removed_modifiers': info.get('removed_modifiers') or [],
                'guiding_questions': qs[:4] if qs else [
                    f'这个{subject}的哪一部分最先吸引你的注意？',
                    '它更接近流动、静止、保护、距离，还是释放？',
                    '如果这个意象能承载你感受中的一小部分，它会承载什么？',
                    '这个意象似乎落在你身体的哪里？'
                ],
                'reference_images': []
            })
        except Exception as e:
            code, msg = self._api_error(e)
            return self._json(code, {'error': msg})

    def generate_references(self):
        try:
            data = self._read_json()
            api_key = self._api_key(data)
            subject = (data.get('subject') or data.get('selected_image') or data.get('custom_intention') or 'image').strip()
            if not api_key:
                return self._json(400, {'error':'缺少 OpenAI API key。'})
            styles = ['natural clear view', 'soft symbolic view', 'simple poetic silhouette']
            images=[]
            image_errors=[]
            for st in styles:
                try:
                    images.append(generate_one_reference(api_key, subject, st))
                except Exception as e:
                    code, msg = self._api_error(e)
                    image_errors.append(msg)
                    images.append('')
            return self._json(200, {'subject':subject, 'reference_images':images, 'image_errors':image_errors})
        except Exception as e:
            code, msg = self._api_error(e)
            return self._json(code, {'error': msg})

    def reflect_drawing(self):
        try:
            data = self._read_json()
            api_key = self._api_key(data)
            if not api_key:
                return self._json(400, {'error':'缺少 OpenAI API key。'})

            lang = (data.get('language') or 'zh').lower()
            answer_language = 'Simplified Chinese' if lang.startswith('zh') else 'English'
            image_data = data.get('image_data') or ''

            context = f"""
Previous text/choices from the process, for context only:
- Body words: {data.get('body','')}
- Texture words: {data.get('texture','')}
- Chosen image/metaphor: {data.get('selected_image','')}
- User imagination description: {data.get('imagination_description','')}
""".strip()

            system = (
                "You are a warm, strengths-oriented art-therapy reflection assistant for an HCI art-making prototype. "
                "You are NOT diagnosing and NOT evaluating artistic skill. "
                "You may notice difficult, heavy, tense, distant, chaotic, or negative affect in the drawing, "
                "but your response must gently guide the user toward resources, support, agency, boundaries, "
                "care, movement, light, spaciousness, repair, and self-compassion. "
                "Do not force toxic positivity; acknowledge what is visible, then ask questions that help the user move toward what might support them. "
                "IMPORTANT WEIGHTING RULE: If an uploaded drawing image is provided, analyze the drawing itself as the primary source of truth. "
                "Give the visual drawing about 80% weight and the user's earlier words/choices about 20% weight. "
                "If the drawing conflicts with the earlier text, prioritize the drawing. "
                "Use the earlier text only as context, not as the main interpretation. "
                f"Return only valid JSON. Write all user-facing content in {answer_language}."
            )

            user_text = (
                "Please look at the uploaded drawing first. Use visual evidence from the drawing as the main basis. "
                "If the image and previous text do not match, prioritize the image. "
                "Write 4-5 open-ended reflective questions and one short reflection. "
                "The questions should be positively guiding without forced positivity: help the user notice not only negative affect, but also possible support, protection, space, movement, repair, care, and a small gentle transformation inside the image. "
                "Avoid neutral-only wording. Avoid clinical labels, diagnosis, pathology, or certainty about the user's mental state. "
                "Do not say the drawing means one fixed thing. Make the response reflective rather than interpretive: respond to visible elements, gently organize observations, validate the user's experience, and offer one optional next-step imagination action. Include at least one calibration question such as which part feels close to them and which part does not. "
                "Return JSON exactly with keys: questions, reflection.\n\n" + context
            )

            if image_data.startswith('data:image'):
                content = [
                    {'type': 'text', 'text': user_text},
                    {'type': 'image_url', 'image_url': {'url': image_data}}
                ]
            else:
                content = user_text + "\n\nNo drawing image was uploaded. In this fallback case only, use the process context."

            payload = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': content}
                ],
                'temperature': 0.6,
                'response_format': {'type':'json_object'}
            }
            res = post_json(openai_api_url('chat/completions'), payload, api_key, timeout=120)
            txt = res.get('choices', [{}])[0].get('message', {}).get('content', '')
            parsed = extract_json(txt) or {}

            questions = parsed.get('questions') or [
                '先看画面本身：哪一个细节最有生命力，或者最像是在努力保护你？',
                '如果画里有沉重、混乱或距离感，它旁边有没有一点点空间、光、边界或支撑？',
                '画中的哪一部分可以被你轻轻照顾一下，而不是立刻改变？',
                '如果这幅画在提醒你一个小小的需要，它可能是在说：我需要什么支持？'
            ]
            reflection = parsed.get('reflection') or (
                '我会先以你的画面为主来理解它。即使画里有沉重或紧绷的部分，也可以一起看看哪里还有一点支撑、边界、空间，或正在慢慢出现的力量。'
            )
            return self._json(200, {'questions':questions[:5], 'reflection':reflection})
        except Exception as e:
            code, msg = self._api_error(e)
            return self._json(code, {'error': msg})



    def _safe_pid(self, pid):
        pid = str(pid or '').strip()
        pid = re.sub(r'[^\w\u4e00-\u9fff-]+', '_', pid)[:80]
        return pid or 'unknown_participant'

    def _save_data_url_image(self, data_url, out_path):
        if not data_url or not isinstance(data_url, str) or not data_url.startswith('data:image'):
            return ''
        header, b64 = data_url.split(',', 1)
        ext = 'png'
        if 'jpeg' in header or 'jpg' in header:
            ext = 'jpg'
        elif 'webp' in header:
            ext = 'webp'
        final_path = out_path + '.' + ext
        with open(final_path, 'wb') as f:
            f.write(base64.b64decode(b64))
        return final_path

    def save_session(self):
        try:
            data = self._read_json()
            pid = self._safe_pid(data.get('participant_id') or (data.get('session_data') or {}).get('participant_id'))
            event = self._safe_pid(data.get('event') or 'snapshot')
            now = datetime.now().strftime('%Y%m%d_%H%M%S')
            record_id = f'{now}_{event}_{uuid.uuid4().hex[:8]}'

            participant_dir = DATA_ROOT / pid
            participant_dir.mkdir(parents=True, exist_ok=True)

            session_data = data.get('session_data') or {}
            session_data['participant_id'] = pid
            session_data['server_saved_at'] = datetime.now().isoformat()
            session_data['event'] = event
            session_data['record_id'] = record_id

            image_file = ''
            image_data = data.get('image_data') or ''
            if image_data:
                image_prefix = 'drawing' if 'drawing' in event else ('ai_image' if 'image' in event else 'image')
                image_base = str(participant_dir / f'{record_id}_{image_prefix}')
                image_file = self._save_data_url_image(image_data, image_base)
                session_data['saved_image_file'] = os.path.relpath(image_file, str(ROOT)) if image_file else ''

            json_path = participant_dir / f'{record_id}.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            latest_path = participant_dir / 'session_latest.json'
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # Append a compact summary CSV for analysis.
            DATA_ROOT.mkdir(parents=True, exist_ok=True)
            csv_path = DATA_ROOT / 'participants_summary.csv'
            write_header = not csv_path.exists()
            with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'server_saved_at','participant_id','event','record_id',
                    'body_input','texture_input','selected_body_model_zh',
                    'chosen_category','chosen_trait','chosen_image','custom_intention',
                    'selected_imagery_term','imagination_description',
                    'num_placements','saved_image_file'
                ])
                if write_header:
                    writer.writeheader()
                writer.writerow({
                    'server_saved_at': session_data.get('server_saved_at',''),
                    'participant_id': pid,
                    'event': event,
                    'record_id': record_id,
                    'body_input': session_data.get('body_input',''),
                    'texture_input': session_data.get('texture_input',''),
                    'selected_body_model_zh': session_data.get('selected_body_model_zh',''),
                    'chosen_category': session_data.get('chosen_category',''),
                    'chosen_trait': session_data.get('chosen_trait',''),
                    'chosen_image': session_data.get('chosen_image',''),
                    'custom_intention': session_data.get('custom_intention',''),
                    'selected_imagery_term': session_data.get('selected_imagery_term',''),
                    'imagination_description': session_data.get('imagination_description',''),
                    'num_placements': len(session_data.get('imagination_placements') or []),
                    'saved_image_file': session_data.get('saved_image_file','')
                })

            return self._json(200, {
                'ok': True,
                'record_id': record_id,
                'participant_id': pid,
                'participant_folder': os.path.relpath(str(participant_dir), str(ROOT)),
                'json_file': os.path.relpath(str(json_path), str(ROOT)),
                'image_file': os.path.relpath(image_file, str(ROOT)) if image_file else ''
            })
        except Exception as e:
            return self._json(500, {'error': str(e)})


    def generate_final_image(self):
        try:
            data = self._read_json()
            api_key = self._api_key(data)
            prompt = (data.get('prompt') or '').strip()
            if not api_key: return self._json(400, {'error':'缺少 OpenAI API key。'})
            if not prompt: return self._json(400, {'error':'Missing prompt.'})
            model = (data.get('model') or 'gpt-image-2').strip()
            quality = (data.get('quality') or 'high').strip()
            size = (data.get('size') or '1024x1024').strip()
            if model not in ALLOWED_IMAGE_MODELS:
                return self._json(400, {'error': f'Unsupported image model: {model}'})
            if quality not in ALLOWED_IMAGE_QUALITIES:
                return self._json(400, {'error': f'Unsupported image quality: {quality}'})
            if size not in ALLOWED_IMAGE_SIZES:
                return self._json(400, {'error': f'Unsupported image size: {size}'})
            payload = {
                'model': model,
                'prompt': prompt,
                'n': 1,
                'size': size,
                'quality': quality
            }
            res = post_json(openai_api_url('images/generations'), payload, api_key, timeout=180)
            b64 = res.get('data', [{}])[0].get('b64_json') if res.get('data') else None
            if not b64:
                return self._json(500, {'error':'OpenAI response did not include image data.'})
            return self._json(200, {'image':'data:image/png;base64,'+b64})
        except Exception as e:
            code, msg = self._api_error(e)
            return self._json(code, {'error': msg})

if __name__ == '__main__':
    os.chdir(str(ROOT))
    port = int(os.environ.get('ARTIMAL_PORT', '8920'))
    bind = os.environ.get('ARTIMAL_BIND', '127.0.0.1')
    server = ThreadingHTTPServer((bind, port), ArtimalHandler)
    print(f'Artimal server running at http://127.0.0.1:{port}/')
    print(f'Configuration file: {CONFIG_PATH}')
    print(f'OpenAI API key configured: {"yes" if configured_api_key() else "no"}')
    print(f'Participant data directory: {DATA_ROOT}')
    print('Keep this Terminal window open. Press Control+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
