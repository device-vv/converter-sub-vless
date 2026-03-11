#!/usr/bin/env python3
"""
Remnawave Subscription to VLESS Keys Converter v0.3
Работает везде — GUI открывается в браузере, без сторонних библиотек.
"""

import base64
import urllib.request
import urllib.parse
import urllib.error
import json
import ssl
import sys
import re
import os
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler


# ==========================================
# ЯДРО КОНВЕРТЕРА
# ==========================================

class RemnavaveSubscriptionConverter:

    CLIENT_USER_AGENTS = {
        'clash': 'clash-verge/v1.3.8',
        'v2rayng': 'v2rayNG/1.8.5',
        'hiddify': 'Hiddify/2.0.5',
        'shadowrocket': 'Shadowrocket/1.0',
        'v2rayn': 'v2rayN/6.23',
        'generic': 'clash-meta'
    }

    def __init__(self, subscription_url: str, verify_ssl: bool = True, logger=None):
        self.subscription_url = subscription_url
        self.vless_keys = []
        self.verify_ssl = verify_ssl
        self.log = logger if logger else print
        self.ssl_context = self._get_ssl_context()

    def _get_ssl_context(self):
        ctx = ssl.create_default_context()
        if not self.verify_ssl:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            try:
                import certifi
                ctx.load_verify_locations(cafile=certifi.where())
            except ImportError:
                pass
        return ctx

    def fetch_subscription(self, user_agent=None):
        urls_to_try = [
            self.subscription_url,
            f"{self.subscription_url}?format=base64",
            f"{self.subscription_url}?client=v2ray",
            f"{self.subscription_url}?client=clash",
        ]

        if user_agent is None:
            user_agent = self.CLIENT_USER_AGENTS['v2rayng']

        for url in urls_to_try:
            try:
                self.log(f"🔄 Пробую: {url}")
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': user_agent, 'Accept': '*/*', 'Accept-Encoding': 'identity'}
                )
                with urllib.request.urlopen(req, timeout=10, context=self.ssl_context) as response:
                    raw_data = response.read()
                    content_type = response.headers.get('Content-Type', '')
                    decoded = raw_data.decode('utf-8', errors='ignore')
                    if 'text/html' in content_type or decoded.strip().startswith('<!DOCTYPE') or decoded.strip().startswith('<html'):
                        self.log("   ⚠️ Получен HTML, пробую следующий...")
                        continue
                    self.log(f"✅ Успешно ({len(raw_data)} байт)")
                    return decoded, True
            except urllib.error.URLError as e:
                reason = getattr(e, 'reason', str(e))
                if "CERTIFICATE_VERIFY_FAILED" in str(reason):
                    self.log("   ❌ Ошибка SSL. Включите 'Игнорировать SSL' и попробуйте снова.")
                    return "", False
                self.log(f"   ❌ Ошибка: {reason}")
                continue
            except Exception as e:
                self.log(f"   ❌ {e}")
                continue
        return "", False

    def try_all_clients(self):
        self.log("\n🔍 Перебираю VPN клиенты...\n")
        for client_name, user_agent in self.CLIENT_USER_AGENTS.items():
            self.log(f"{'='*60}\n🎯 Клиент: {client_name}\n{'='*60}")
            raw_data, success = self.fetch_subscription(user_agent)
            if success and raw_data:
                self.vless_keys = self.decode_subscription(raw_data)
                if self.vless_keys:
                    self.log(f"\n🎉 Найдено {len(self.vless_keys)} ключей!")
                    return True
        return False

    def try_parse_json(self, data):
        try:
            return json.loads(data)
        except:
            return None

    def extract_vless_from_xray_config(self, config):
        vless_keys = []
        try:
            for outbound in config.get('outbounds', []):
                if outbound.get('protocol') != 'vless':
                    continue
                settings = outbound.get('settings', {})
                stream_settings = outbound.get('streamSettings', {})
                tag = outbound.get('tag', 'Server')
                for server in settings.get('vnext', []):
                    for user in server.get('users', []):
                        vless_url = self.build_vless_url(
                            uuid=user.get('id', ''),
                            address=server.get('address', ''),
                            port=server.get('port', 443),
                            stream_settings=stream_settings,
                            flow=user.get('flow', ''),
                            name=tag
                        )
                        if vless_url:
                            vless_keys.append(vless_url)
        except Exception as e:
            self.log(f"⚠️ Ошибка парсинга Xray: {e}")
        return vless_keys

    def build_vless_url(self, uuid, address, port, stream_settings, flow, name):
        params = {'encryption': 'none', 'type': stream_settings.get('network', 'tcp')}
        if flow:
            params['flow'] = flow
        security = stream_settings.get('security', 'none')
        params['security'] = security
        if security == 'reality':
            rs = stream_settings.get('realitySettings', {})
            if rs.get('publicKey'): params['pbk'] = rs['publicKey']
            if rs.get('shortId'): params['sid'] = rs['shortId']
            if rs.get('serverName'): params['sni'] = rs['serverName']
            if rs.get('fingerprint'): params['fp'] = rs['fingerprint']
        elif security == 'tls':
            ts = stream_settings.get('tlsSettings', {})
            if ts.get('serverName'): params['sni'] = ts['serverName']
            if ts.get('fingerprint'): params['fp'] = ts['fingerprint']
        params_str = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        return f"vless://{uuid}@{address}:{port}?{params_str}#{urllib.parse.quote(name)}"

    def extract_vless_from_text(self, text):
        return re.findall(r'vless://[^\s\n<>"\'\\)]+', text)

    def decode_subscription(self, raw_data):
        json_data = self.try_parse_json(raw_data)
        if json_data:
            self.log("📦 Обнаружен JSON")
            keys = []
            if 'outbounds' in json_data or 'inbounds' in json_data:
                keys = self.extract_vless_from_xray_config(json_data)
            elif isinstance(json_data, list):
                for item in json_data:
                    if isinstance(item, dict):
                        keys.extend(self.extract_vless_from_xray_config(item))
            if keys:
                return keys

        try:
            decoded = base64.b64decode(raw_data).decode('utf-8')
            self.log("🔓 base64 декодировано")
            keys = self.extract_vless_from_text(decoded)
            if keys:
                return keys
        except:
            pass

        self.log("📄 Plain text")
        return self.extract_vless_from_text(raw_data)

    def convert(self):
        success = self.try_all_clients()
        if not success or not self.vless_keys:
            self.log("\n❌ Ключи не найдены.")
            self.log("💡 Проверьте URL или включите 'Игнорировать SSL'.")
            return []
        self.log(f"\n✅ Готово! Получено {len(self.vless_keys)} ключей.")
        return self.vless_keys


# ==========================================
# WEB GUI — встроенный HTTP-сервер
# ==========================================

HTML_PAGE = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Remnawave → VLESS Converter</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #252836;
    --accent: #6c63ff;
    --accent2: #4ecdc4;
    --text: #e8eaf0;
    --text2: #8b8fa8;
    --success: #56cf84;
    --error: #ff6b6b;
    --border: #2e3146;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg); color: var(--text);
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; padding: 24px 16px;
  }
  .container { max-width: 820px; margin: 0 auto; }
  header { text-align: center; margin-bottom: 32px; }
  header h1 { font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }
  header h1 span { 
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  header p { color: var(--text2); font-size: 14px; margin-top: 6px; }
  .power-btn {
    position: absolute; top: 0; left: 0;
    background: transparent; border: 1px solid var(--error); color: var(--error);
    border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600;
    cursor: pointer; transition: all .15s;
  }
  .power-btn:hover { background: var(--error); color: #fff; }
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 24px; margin-bottom: 16px;
  }
  label { display: block; font-size: 13px; color: var(--text2); margin-bottom: 8px; font-weight: 500; }
  input[type="text"] {
    width: 100%; background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px 16px; font-size: 14px; color: var(--text);
    outline: none; transition: border-color .2s;
  }
  input[type="text"]:focus { border-color: var(--accent); }
  .checkbox-row { display: flex; align-items: center; gap: 10px; margin-top: 14px; cursor: pointer; }
  .checkbox-row input { accent-color: var(--accent); width: 16px; height: 16px; cursor: pointer; }
  .checkbox-row span { font-size: 13px; color: var(--text2); }
  .btn {
    width: 100%; margin-top: 16px; padding: 13px;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    color: #fff; border: none; border-radius: 9px;
    font-size: 15px; font-weight: 600; cursor: pointer;
    transition: transform .15s, opacity .15s;
  }
  .btn:hover { opacity: .9; transform: translateY(-1px); }
  .btn:active { transform: translateY(0); }
  .btn:disabled { opacity: .5; cursor: not-allowed; transform: none; }
  .log-box {
    background: #0a0c12; border: 1px solid var(--border); border-radius: 9px;
    padding: 14px; font-family: 'Courier New', monospace; font-size: 12.5px;
    color: #b0bad6; max-height: 220px; overflow-y: auto; line-height: 1.7;
    white-space: pre-wrap; word-break: break-all;
  }
  .keys-area {
    display: none;
  }
  .keys-area.visible { display: block; }
  .key-item {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
    font-family: monospace; font-size: 12px; color: #8dd7f7;
    word-break: break-all; line-height: 1.5; cursor: pointer;
    transition: border-color .15s;
    position: relative;
  }
  .key-item:hover { border-color: var(--accent2); }
  .key-label { font-family: sans-serif; font-size: 11px; color: var(--text2); margin-bottom: 4px; }
  .lang-switch {
    position: absolute; top: 0; right: 0;
    display: flex; gap: 4px;
  }
  .lang-btn {
    background: var(--surface2); border: 1px solid var(--border); color: var(--text2);
    border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600;
    cursor: pointer; transition: all .15s;
  }
  .lang-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  .lang-btn:hover:not(.active) { border-color: var(--accent); color: var(--text); }
  header { position: relative; }
  .copy-hint {
    position: absolute; right: 10px; top: 10px;
    font-size: 11px; color: var(--text2); font-family: sans-serif;
  }
  .actions { display: flex; gap: 10px; margin-top: 14px; }
  .btn-sm {
    flex: 1; padding: 10px; border-radius: 8px; font-size: 13px; font-weight: 600;
    cursor: pointer; border: none; transition: opacity .15s;
  }
  .btn-copy { background: var(--accent); color: #fff; }
  .btn-save { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
  .btn-sm:hover { opacity: .85; }
  .section-title { font-size: 13px; font-weight: 600; color: var(--text2); margin-bottom: 12px; text-transform: uppercase; letter-spacing: .5px; }
  .badge { 
    display: inline-block; background: rgba(108,99,255,.2); color: var(--accent);
    border-radius: 20px; font-size: 12px; padding: 2px 10px; margin-left: 8px; font-weight: 600;
  }
  .spinner { display: none; text-align: center; color: var(--text2); font-size: 13px; padding: 10px 0; }
  .spinner.visible { display: block; }
  .toast {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--success); color: #0a2a1a;
    padding: 12px 20px; border-radius: 9px; font-size: 14px; font-weight: 600;
    transform: translateY(100px); opacity: 0; transition: all .3s;
    pointer-events: none; z-index: 999;
  }
  .toast.show { transform: translateY(0); opacity: 1; }
</style>
</head>
<body>
<div class="container">
  <header>
    <button id="btn-power" class="power-btn" onclick="shutdownServer()"></button>
    <div class="lang-switch">
      <button id="lang-en" class="lang-btn active" onclick="setLang('en')">EN</button>
      <button id="lang-ru" class="lang-btn" onclick="setLang('ru')">RU</button>
    </div>
    <h1>Remnawave <span>→ VLESS</span> Converter</h1>
    <p id="hdr-sub"></p>
  </header>

  <div class="card">
    <label id="lbl-url" for="url-input"></label>
    <input type="text" id="url-input" placeholder="https://your-remnawave-server.com/api/sub/...">
    <label class="checkbox-row" for="insecure-chk">
      <input type="checkbox" id="insecure-chk">
      <span id="lbl-insecure"></span>
    </label>
    <button class="btn" id="convert-btn" onclick="startConvert()"></button>
  </div>

  <div class="card">
    <div class="section-title" id="lbl-log"></div>
    <div class="log-box" id="log-box"></div>
    <div class="spinner" id="spinner"></div>
  </div>

  <div class="card keys-area" id="keys-area">
    <div class="section-title">
      <span id="lbl-keys"></span> <span class="badge" id="keys-count">0</span>
    </div>
    <div id="keys-list"></div>
    <div class="actions">
      <button class="btn-sm btn-copy" id="btn-copy" onclick="copyAll()"></button>
      <button class="btn-sm btn-save" id="btn-save" onclick="saveAll()"></button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const i18n = {
  en: {
    sub:       'Extract VLESS keys from your Remnawave subscription URL',
    urlLabel:  '\uD83D\uDD17 Subscription URL'.replace(/[\uD800-\uDFFF]/g, ''),
    insecure:  '\u26A0\uFE0F Ignore SSL certificate errors (if connection fails)',
    convert:   'Convert',
    logTitle:  'Log',
    logEmpty:  'The conversion log will appear here...',
    spinner:   '\u23F3 Fetching data, please wait...',
    keysTitle: '\uD83D\uDD11 VLESS Keys',
    copyAll:   '\uD83D\uDCCB Copy all',
    saveAll:   '\uD83D\uDCBE Download .txt',
    copyHint:  'click to copy',
    copiedKey: 'Key copied!',
    copiedAll: 'All keys copied!',
    emptyUrl:  'Please enter a subscription URL',
    notFound:  'No keys found. Check the URL.',
    success:   (n) => `\u2705 Got ${n} keys!`,
    error:     'Connection error!',
    power:     '\uD83D\uDED1 Stop Server',
    powerMsg:  'Server stopped. You can close this tab.',
  },
  ru: {
    sub:       '\u0418\u0437\u0432\u043B\u0435\u0447\u0435\u043D\u0438\u0435 VLESS-\u043A\u043B\u044E\u0447\u0435\u0439 \u0438\u0437 \u0441\u0441\u044B\u043B\u043A\u0438 \u043F\u043E\u0434\u043F\u0438\u0441\u043A\u0438 Remnawave',
    urlLabel:  '\uD83D\uDD17 URL \u043F\u043E\u0434\u043F\u0438\u0441\u043A\u0438',
    insecure:  '\u26A0\uFE0F \u0418\u0433\u043D\u043E\u0440\u0438\u0440\u043E\u0432\u0430\u0442\u044C \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0443 SSL-\u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043A\u0430\u0442\u043E\u0432',
    convert:   '\u041A\u043E\u043D\u0432\u0435\u0440\u0442\u0438\u0440\u043E\u0432\u0430\u0442\u044C',
    logTitle:  '\u0416\u0443\u0440\u043D\u0430\u043B',
    logEmpty:  '\u0417\u0434\u0435\u0441\u044C \u0431\u0443\u0434\u0435\u0442 \u043E\u0442\u043E\u0431\u0440\u0430\u0436\u0430\u0442\u044C\u0441\u044F \u043F\u0440\u043E\u0446\u0435\u0441\u0441 \u043A\u043E\u043D\u0432\u0435\u0440\u0442\u0430\u0446\u0438\u0438...',
    spinner:   '\u23F3 \u041F\u043E\u043B\u0443\u0447\u0430\u044E \u0434\u0430\u043D\u043D\u044B\u0435, \u043F\u043E\u0434\u043E\u0436\u0434\u0438\u0442\u0435...',
    keysTitle: '\uD83D\uDD11 \u041A\u043B\u044E\u0447\u0438 VLESS',
    copyAll:   '\uD83D\uDCCB \u0421\u043A\u043E\u043F\u0438\u0440\u043E\u0432\u0430\u0442\u044C \u0432\u0441\u0435',
    saveAll:   '\uD83D\uDCBE \u0421\u043A\u0430\u0447\u0430\u0442\u044C .txt',
    copyHint:  '\u043D\u0430\u0436\u043C\u0438\u0442\u0435 \u0447\u0442\u043E\u0431\u044B \u0441\u043A\u043E\u043F\u0438\u0440\u043E\u0432\u0430\u0442\u044C',
    copiedKey: '\u041A\u043B\u044E\u0447 \u0441\u043A\u043E\u043F\u0438\u0440\u043E\u0432\u0430\u043D!',
    copiedAll: '\u0412\u0441\u0435 \u043A\u043B\u044E\u0447\u0438 \u0441\u043A\u043E\u043F\u0438\u0440\u043E\u0432\u0430\u043D\u044B!',
    emptyUrl:  '\u0412\u0432\u0435\u0434\u0438\u0442\u0435 URL \u043F\u043E\u0434\u043F\u0438\u0441\u043A\u0438',
    notFound:  '\u041A\u043B\u044E\u0447\u0438 \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u044B. \u041F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 URL.',
    success:   (n) => `\u2705 \u041D\u0430\u0439\u0434\u0435\u043D\u043E ${n} \u043A\u043B\u044E\u0447\u0435\u0439!`,
    error:     '\u041E\u0448\u0438\u0431\u043A\u0430 \u0441\u043E\u0435\u0434\u0438\u043D\u0435\u043D\u0438\u044F!',
    power:     '\uD83D\uDED1 \u0412\u044B\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u0441\u0435\u0440\u0432\u0435\u0440',
    powerMsg:  '\u0421\u0435\u0440\u0432\u0435\u0440 \u043E\u0441\u0442\u0430\u043D\u043E\u0432\u043B\u0435\u043D. \u0412\u043A\u043B\u0430\u0434\u043A\u0443 \u043C\u043E\u0436\u043D\u043E \u0437\u0430\u043A\u0440\u044B\u0442\u044C.',
  }
};

let lang = 'en';
let lastKeys = [];

function setLang(l) {
  lang = l;
  document.getElementById('lang-en').classList.toggle('active', l === 'en');
  document.getElementById('lang-ru').classList.toggle('active', l === 'ru');
  const t = i18n[l];
  document.getElementById('hdr-sub').textContent      = t.sub;
  document.getElementById('lbl-url').textContent      = t.urlLabel;
  document.getElementById('lbl-insecure').textContent = t.insecure;
  document.getElementById('convert-btn').textContent  = t.convert;
  document.getElementById('lbl-log').textContent      = t.logTitle;
  document.getElementById('lbl-keys').textContent     = t.keysTitle;
  document.getElementById('btn-copy').textContent     = t.copyAll;
  document.getElementById('btn-save').textContent     = t.saveAll;
  document.getElementById('btn-power').textContent    = t.power;
  const logBox = document.getElementById('log-box');
  if (!logBox._hasContent) logBox.textContent = t.logEmpty;
  document.getElementById('spinner').textContent = t.spinner;
}

// Init English on load
setLang('en');

async function startConvert() {
  const url = document.getElementById('url-input').value.trim();
  if (!url) { showToast(i18n[lang].emptyUrl, true); return; }

  const insecure = document.getElementById('insecure-chk').checked;
  const btn = document.getElementById('convert-btn');
  const log = document.getElementById('log-box');
  const spinner = document.getElementById('spinner');
  const keysArea = document.getElementById('keys-area');

  btn.disabled = true;
  log.textContent = '';
  log._hasContent = false;
  document.getElementById('spinner').textContent = i18n[lang].spinner;
  keysArea.classList.remove('visible');
  spinner.classList.add('visible');
  lastKeys = [];

  try {
    const res = await fetch('/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, insecure })
    });
    const data = await res.json();

    log.textContent = data.log || '';
    log.scrollTop = log.scrollHeight;

    if (data.keys && data.keys.length > 0) {
      lastKeys = data.keys;
      renderKeys(data.keys);
      keysArea.classList.add('visible');
      showToast(i18n[lang].success(data.keys.length));
    } else {
      showToast(i18n[lang].notFound, true);
    }
  } catch (e) {
    log.textContent += '\n❌ ' + e;
    showToast(i18n[lang].error, true);
  } finally {
    btn.disabled = false;
    spinner.classList.remove('visible');
    log._hasContent = true;
  }
}

async function shutdownServer() {
  if (!confirm('Stop the local server?')) return;
  try {
    await fetch('/api/shutdown', { method: 'POST' });
  } catch (e) {}
  document.body.innerHTML = `<h2 style="text-align:center;margin-top:20vh;color:var(--text)">${i18n[lang].powerMsg}</h2>`;
}

function renderKeys(keys) {
  const list = document.getElementById('keys-list');
  document.getElementById('keys-count').textContent = keys.length;
  list.innerHTML = keys.map((k, i) => {
    const name = decodeURIComponent(k.split('#')[1] || ('Key ' + (i + 1)));
    return `<div class="key-item" onclick="copyKey('${escHtml(k)}', this)">
      <div class="key-label">🔑 ${escHtml(name)}</div>
      <span class="copy-hint">${i18n[lang].copyHint}</span>
      ${escHtml(k)}
    </div>`;
  }).join('');
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function copyKey(text, el) {
  navigator.clipboard.writeText(text).then(() => {
    el.style.borderColor = 'var(--success)';
    setTimeout(() => el.style.borderColor = '', 1200);
    showToast(i18n[lang].copiedKey);
  });
}

function copyAll() {
  navigator.clipboard.writeText(lastKeys.join('\\n')).then(() => {
    showToast(i18n[lang].copiedAll);
  });
}

function saveAll() {
  const blob = new Blob([lastKeys.join('\\n')], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'vless_keys.txt';
  a.click();
}

function showToast(msg, err=false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = err ? 'var(--error)' : 'var(--success)';
  t.style.color = err ? '#fff' : '#0a2a1a';
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2800);
}

document.getElementById('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') startConvert();
});
</script>
</body>
</html>'''


class RequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Отключаем стандартный лог сервера

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = HTML_PAGE.encode('utf-8')
            self.wfile.write(html)
        elif self.path == '/api/ping':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"app": "remnawave-vless-converter"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/convert':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except Exception:
                self.send_error(400)
                return

            url = data.get('url', '').strip()
            insecure = data.get('insecure', False)

            log_lines = []
            def logger(msg):
                log_lines.append(msg)

            keys = []
            if url:
                converter = RemnavaveSubscriptionConverter(url, verify_ssl=not insecure, logger=logger)
                keys = converter.convert()

            result = json.dumps({
                'keys': keys or [],
                'log': '\n'.join(log_lines)
            }, ensure_ascii=False)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result.encode('utf-8'))
        elif self.path == '/api/shutdown':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            # Завершаем сервер в отдельном потоке чтобы успеть отдать ответ
            threading.Thread(target=lambda: (print("\\n\\n[GUI requested shutdown]"), os._exit(0))).start()
        else:
            self.send_error(404)


# ==========================================
# КОНСОЛЬНАЯ РЕАЛИЗАЦИЯ (CLI)
# ==========================================

def run_cli(args):
    lang = 'ru' if '--lang=ru' in args else 'en'
    args = [a for a in args if a != '--lang=ru']

    if lang == 'ru':
        banner = """
╔═══════════════════════════════════════════════════════════╗
║   Remnawave Subscription → VLESS Keys Converter v0.3     ║
║   Поддержка Subscription Page, разных VPN клиентов       ║
╚═══════════════════════════════════════════════════════════╝
        """
        url_prompt     = "🔗 Введите URL подписки Remnawave: "
        empty_err      = "❌ URL не может быть пустым"
        ssl_status_on  = "Включена"
        ssl_status_off = "Отключена (--insecure)"
        ssl_label      = "🛠  Проверка SSL"
        keys_header    = "🔑 ВСЕ КЛЮЧИ:"
        save_prompt    = "\n💾 Сохранить в файл? (Enter — пропустить, или имя файла): "
        saved_msg      = "✅ Сохранено"
        done_msg       = "\n✅ Готово!"
    else:
        banner = """
╔═══════════════════════════════════════════════════════════╗
║   Remnawave Subscription → VLESS Keys Converter v0.3     ║
╚═══════════════════════════════════════════════════════════╝
        """
        url_prompt     = "🔗 Enter Remnawave subscription URL: "
        empty_err      = "❌ URL cannot be empty"
        ssl_status_on  = "Enabled"
        ssl_status_off = "Disabled (--insecure)"
        ssl_label      = "🛠  SSL verification"
        keys_header    = "🔑 ALL KEYS:"
        save_prompt    = "\n💾 Save to file? (Enter to skip, or type filename): "
        saved_msg      = "✅ Saved"
        done_msg       = "\n✅ Done!"

    print(banner)

    subscription_url = ""
    verify_ssl = True

    for arg in args:
        if arg == '--insecure':
            verify_ssl = False
        elif not arg.startswith('-'):
            subscription_url = arg

    if not subscription_url:
        subscription_url = input(url_prompt).strip()

    if not subscription_url:
        print(empty_err)
        sys.exit(1)

    ssl_state = ssl_status_on if verify_ssl else ssl_status_off
    print(f"\n{ssl_label}: {ssl_state}")

    converter = RemnavaveSubscriptionConverter(subscription_url, verify_ssl=verify_ssl)
    keys = converter.convert()

    if keys:
        print(f"\n{'='*70}")
        print(keys_header)
        print(f"{'='*70}\n")
        for i, key in enumerate(keys, 1):
            print(f"{i}. {key}\n")

        save_file = input(save_prompt).strip()
        if save_file:
            with open(save_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(keys))
            print(f"{saved_msg}: {save_file}")

    print(done_msg)


# ==========================================
# WEB GUI ЗАПУСК
# ==========================================

class ReuseAddrHTTPServer(ThreadingHTTPServer):
    """HTTP-сервер с разрешением повторного использования порта."""
    allow_reuse_address = True


def find_free_port(start=7788, attempts=20):
    """Ищет свободный порт начиная с start."""
    import socket
    for p in range(start, start + attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', p))
                return p
        except OSError:
            continue
    return None


def check_existing_instance(start=7788, attempts=20):
    """Проверяет, не запущен ли уже конвертер на одном из портов."""
    for p in range(start, start + attempts):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{p}/api/ping")
            with urllib.request.urlopen(req, timeout=0.2) as r:
                if r.status == 200:
                    data = json.loads(r.read().decode('utf-8'))
                    if data.get("app") == "remnawave-vless-converter":
                        return p
        except Exception:
            continue
    return None


def run_web(port=7788):
    import atexit, signal

    existing_port = check_existing_instance(port)
    if existing_port:
        print(f"\n⚡ Приложение уже работает (порт {existing_port}).")
        print(f"🌐 Открываем вкладку с уже запущенным сервером...")
        webbrowser.open(f"http://127.0.0.1:{existing_port}")
        return

    port = find_free_port(port)
    if port is None:
        print("❌ Не удалось найти свободный порт. Завершите предыдущий экземпляр.")
        sys.exit(1)

    server = ReuseAddrHTTPServer(('127.0.0.1', port), RequestHandler)
    url = f"http://127.0.0.1:{port}"

    def shutdown():
        server.shutdown()
        server.server_close()

    atexit.register(shutdown)

    def on_signal(sig, frame):
        print("\n\n👋 Server stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║   Remnawave Subscription → VLESS Keys Converter v0.3    ║
╚══════════════════════════════════════════════════════════╝

🌐 Web GUI started!
   Open in browser: {url}

   (If browser didn't open — copy the link above)
   Press Ctrl+C to stop.
""")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    server.serve_forever()


# ==========================================
# ТОЧКА ВХОДА
# ==========================================

def main():
    args = sys.argv[1:]

    if '--kill' in args:
        port = check_existing_instance()
        if port:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/shutdown", data=b'', timeout=1)
            except Exception:
                pass
            print(f"✅ Убит процесс на порту {port}")
        else:
            print("ℹ️ Нет запущенных экземпляров конвертера.")
        return

    if '--gui' in args:
        run_web()
    else:
        run_cli([a for a in args if a != '--cli'])


if __name__ == "__main__":
    main()
