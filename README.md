<p align="center">
  <a href="#-remnawave-subscription-to-vless-keys-converter">English</a> •
  <a href="#-конвертер-подписки-remnawave-в-ключи-vless">Русский</a>
</p>

# Remnawave Subscription to VLESS Keys Converter

This script converts a Remnawave subscription URL into VLESS keys. It supports various subscription formats and can simulate different VPN clients to fetch the subscription data.

## Features

- Converts Remnawave subscription URLs to VLESS keys.
- Supports multiple subscription formats:
    - JSON
    - Base64
    - Plain text
- Simulates different VPN clients using their user agents:
    - Clash
    - V2RayNG
    - Hiddify
    - Shadowrocket
    - V2RayN
- Extracts VLESS keys from Xray configurations.
- Builds `vless://` URLs from parameters.
- Displays the extracted VLESS keys in the console.
- Saves the extracted VLESS keys to a file.

## How to Use

1. **Run the script:**
   ```bash
   python3 converter.py
   ```
2. **Enter the Remnawave subscription URL when prompted:**
   ```
   🔗 Enter the Remnawave subscription URL: [your_subscription_url]
   ```
3. **(Optional) Specify a file to save the keys:**
   ```
   💾 Save keys to a file? (Enter to skip, or specify a filename): [your_filename]
   ```
4. **The script will then fetch the subscription, convert it, and display the VLESS keys.**

## Command-line Arguments

You can also provide the subscription URL as a command-line argument:

```bash
python3 converter.py [your_subscription_url]
```

## Requirements

- Python 3

## Disclaimer

This script is for educational purposes only. The author is not responsible for any misuse of this script.

---

# Конвертер подписки Remnawave в ключи VLESS

Этот скрипт преобразует URL-адрес подписки Remnawave в ключи VLESS. Он поддерживает различные форматы подписки и может имитировать различные VPN-клиенты для получения данных подписки.

## Возможности

- Преобразует URL-адреса подписок Remnawave в ключи VLESS.
- Поддерживает несколько форматов подписки:
    - JSON
    - Base64
    - Обычный текст
- Имитирует различные VPN-клиенты, используя их пользовательские агенты:
    - Clash
    - V2RayNG
    - Hiddify
    - Shadowrocket
    - V2RayN
- Извлекает ключи VLESS из конфигураций Xray.
- Собирает URL-адреса `vless://` из параметров.
- Отображает извлеченные ключи VLESS в консоли.
- Сохраняет извлеченные ключи VLESS в файл.

## Как использовать

1. **Запустите скрипт:**
   ```bash
   python3 converter.py
   ```
2. **Введите URL-адрес подписки Remnawave, когда будет предложено:**
   ```
   🔗 Введите URL подписки Remnawave: [ваш_url_подписки]
   ```
3. **(Необязательно) Укажите файл для сохранения ключей:**
   ```
   💾 Сохранить ключи в файл? (Enter - пропустить, или укажите имя файла): [ваше_имя_файла]
   ```
4. **Затем скрипт получит подписку, преобразует ее и отобразит ключи VLESS.**

## Аргументы командной строки

Вы также можете указать URL-адрес подписки в качестве аргумента командной строки:

```bash
python3 converter.py [ваш_url_подписки]
```

## Требования

- Python 3

## Отказ от ответственности

Этот скрипт предназначен только для образовательных целей. Автор не несет ответственности за любое неправильное использование этого скрипта.