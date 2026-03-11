<p align="center">
  <a href="#english">🇬🇧 English</a> &nbsp;•&nbsp;
  <a href="#russian">🇷🇺 Русский</a>
</p>

---

<a name="english"></a>

# Remnawave → VLESS Keys Converter

A lightweight Python tool to extract **VLESS keys** from a [Remnawave](https://remnawave.io) subscription URL. Works in **CLI** (default) and **browser-based GUI** (with `--gui` flag). No third-party packages required.

## Features

| Feature | Details |
|---|---|
| 🖥 **CLI mode** (default) | Interactive terminal, scriptable with arguments |
| 🌐 **Web GUI mode** | Runs a local server, opens in your browser |
| 🔒 **SSL bypass** | Ignore certificate errors with a single flag or checkbox |
| 📦 **Multiple formats** | JSON, Base64, Plain Text subscriptions |
| 🤖 **Client spoofing** | Clash, V2RayNG, Hiddify, Shadowrocket, V2RayN |
| 📋 **Export** | Copy to clipboard or download `.txt` |
| ⚡ **Zero dependencies** | Pure Python 3 stdlib only |

## Quick Start

### CLI (default)

```bash
# Interactive — you will be prompted for the URL
python3 converter.py

# Pass URL directly
python3 converter.py https://your-remnawave.example/sub/TOKEN

# SSL certificate error? Add --insecure
python3 converter.py --insecure https://your-remnawave.example/sub/TOKEN
```

### Web GUI

```bash
# Opens browser at http://127.0.0.1:7788 automatically
python3 converter.py --gui
```

> If the browser doesn't open automatically, copy the URL printed in terminal.  
> Press **Ctrl+C** to stop the server — the port is released immediately.

## CLI Reference

| Argument | Description |
|---|---|
| (none) | Launch interactive CLI |
| `<url>` | Subscription URL (skips the prompt) |
| `--insecure` | Skip SSL certificate verification |
| `--gui` | Launch browser-based GUI instead of CLI |
| `--kill` | Stop the currently running background GUI server |

## Requirements

- **Python 3.7+** — nothing else needed
- *(Optional)* `pip install certifi` — more reliable SSL certificate handling

## SSL Error Fix

Getting `[SSL: CERTIFICATE_VERIFY_FAILED]`?

| Solution | How |
|---|---|
| **Quick** | Add `--insecure` flag or check the box in GUI |
| **Proper** (macOS) | Run `Install Certificates.command` from Applications → Python folder |
| **Proper** (any) | `pip install certifi` |

## Disclaimer

For educational purposes only. The author is not responsible for any misuse.

---

<a name="russian"></a>

# Конвертер подписки Remnawave → ключи VLESS

Лёгкий Python-инструмент для извлечения **VLESS-ключей** из ссылки подписки [Remnawave](https://remnawave.io). Работает в режиме **CLI** (по умолчанию) и **браузерного GUI** (флаг `--gui`). Сторонние пакеты не нужны.

## Возможности

| Функция | Описание |
|---|---|
| 🖥 **CLI режим** (по умолчанию) | Интерактивный терминал, поддержка аргументов |
| 🌐 **Веб GUI режим** | Локальный сервер, открывается в браузере |
| 🔒 **Обход проверки SSL** | Игнорирование ошибок сертификата одним флагом или галочкой в UI |
| 📦 **Много форматов** | JSON, Base64, обычный текст |
| 🤖 **Имитация клиентов** | Clash, V2RayNG, Hiddify, Shadowrocket, V2RayN |
| 📋 **Экспорт** | Копировать в буфер или скачать `.txt` |
| ⚡ **Нет зависимостей** | Только стандартная библиотека Python 3 |

## Быстрый старт

### CLI (по умолчанию)

```bash
# Интерактивный — спросит URL сам
python3 converter.py

# URL в аргументе — сразу начинает работу
python3 converter.py https://your-remnawave.example/sub/TOKEN

# Ошибка SSL? Добавьте --insecure
python3 converter.py --insecure https://your-remnawave.example/sub/TOKEN
```

### Веб GUI

```bash
# Автоматически открывает браузер на http://127.0.0.1:7788
python3 converter.py --gui
```

> Если браузер не открылся сам — скопируйте ссылку из терминала.  
> **Ctrl+C** — остановить сервер. Порт освобождается немедленно.

## Аргументы CLI

| Аргумент | Описание |
|---|---|
| (нет) | Интерактивный CLI |
| `<url>` | URL подписки (без запроса) |
| `--insecure` | Игнорировать проверку SSL |
| `--gui` | Запустить браузерный GUI |
| `--kill` | Выключить локальный фоновый сервер GUI |

## Требования

- **Python 3.7+** — больше ничего не нужно
- *(Опционально)* `pip install certifi` — надёжная обработка SSL

## Решение ошибки SSL

Ошибка `[SSL: CERTIFICATE_VERIFY_FAILED]`?

| Способ | Как |
|---|---|
| **Быстро** | Флаг `--insecure` или галочка в GUI |
| **Правильно** (macOS) | Запустить `Install Certificates.command` из папки Python в Программах |
| **Правильно** (любая ОС) | `pip install certifi` |

## Отказ от ответственности

Только для образовательных целей. Автор не несёт ответственности за неправомерное использование.