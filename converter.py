#!/usr/bin/env python3
"""
Remnawave Subscription to VLESS Keys Converter v0.1
С поддержкой Subscription Page и разных клиентов
"""

import base64
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Optional
import sys
import re


class RemnavaveSubscriptionConverter:
    
    # User-Agent для разных VPN клиентов
    CLIENT_USER_AGENTS = {
        'clash': 'clash-verge/v1.3.8',
        'v2rayng': 'v2rayNG/1.8.5',
        'hiddify': 'Hiddify/2.0.5',
        'shadowrocket': 'Shadowrocket/1.0',
        'v2rayn': 'v2rayN/6.23',
        'generic': 'clash-meta'
    }
    
    def __init__(self, subscription_url: str):
        self.subscription_url = subscription_url
        self.vless_keys = []
    
    def fetch_subscription(self, user_agent: str = None) -> tuple[str, bool]:
        """
        Получение данных подписки с сервера
        Возвращает (данные, успешно_ли)
        """
        try:
            # Пробуем разные варианты URL
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
                    print(f"🔄 Пробую: {url}")
                    print(f"   User-Agent: {user_agent}")
                    
                    req = urllib.request.Request(
                        url,
                        headers={
                            'User-Agent': user_agent,
                            'Accept': '*/*',
                            'Accept-Encoding': 'identity'
                        }
                    )
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        raw_data = response.read()
                        content_type = response.headers.get('Content-Type', '')
                        
                        # Проверяем, не HTML ли это
                        decoded = raw_data.decode('utf-8', errors='ignore')
                        
                        if 'text/html' in content_type or decoded.strip().startswith('<!DOCTYPE') or decoded.strip().startswith('<html'):
                            print(f"   ⚠️ Получен HTML, пробую следующий вариант...")
                            continue
                        
                        print(f"✅ Успешно получены данные ({len(raw_data)} байт)")
                        return decoded, True
                    
                except urllib.error.HTTPError as e:
                    print(f"   ❌ HTTP {e.code}: {e.reason}")
                    continue
                except Exception as e:
                    print(f"   ❌ Ошибка: {e}")
                    continue
            
            return "", False
            
        except Exception as e:
            print(f"❌ Критическая ошибка при получении подписки: {e}")
            return "", False
    
    def try_all_clients(self) -> bool:
        """Пробует получить подписку с разными User-Agent клиентов"""
        print(f"\n🔍 Пробую разные VPN клиенты...\n")
        
        for client_name, user_agent in self.CLIENT_USER_AGENTS.items():
            print(f"{'='*70}")
            print(f"🎯 Клиент: {client_name}")
            print(f"{'='*70}")
            
            raw_data, success = self.fetch_subscription(user_agent)
            
            if success and raw_data:
                self.vless_keys = self.decode_subscription(raw_data)
                
                if self.vless_keys:
                    print(f"\n🎉 Успех! Найдено {len(self.vless_keys)} ключей с клиентом {client_name}")
                    return True
        
        return False
    
    def try_parse_json(self, data: str) -> Optional[Dict]:
        """Попытка распарсить JSON"""
        try:
            return json.loads(data)
        except:
            return None
    
    def extract_vless_from_xray_config(self, config: Dict) -> List[str]:
        """Извлечение vless ключей из Xray конфига"""
        vless_keys = []
        
        try:
            outbounds = config.get('outbounds', [])
            
            for outbound in outbounds:
                if outbound.get('protocol') != 'vless':
                    continue
                
                settings = outbound.get('settings', {})
                vnext = settings.get('vnext', [])
                stream_settings = outbound.get('streamSettings', {})
                tag = outbound.get('tag', 'Server')
                
                for server in vnext:
                    address = server.get('address', '')
                    port = server.get('port', 443)
                    users = server.get('users', [])
                    
                    for user in users:
                        uuid = user.get('id', '')
                        flow = user.get('flow', '')
                        
                        vless_url = self.build_vless_url(
                            uuid=uuid,
                            address=address,
                            port=port,
                            stream_settings=stream_settings,
                            flow=flow,
                            name=tag
                        )
                        
                        if vless_url:
                            vless_keys.append(vless_url)
            
        except Exception as e:
            print(f"⚠️ Ошибка при парсинге Xray конфига: {e}")
        
        return vless_keys
    
    def build_vless_url(self, uuid: str, address: str, port: int, 
                       stream_settings: Dict, flow: str, name: str) -> str:
        """Построение vless:// URL из параметров"""
        
        params = {
            'encryption': 'none',
            'type': stream_settings.get('network', 'tcp')
        }
        
        if flow:
            params['flow'] = flow
        
        security = stream_settings.get('security', 'none')
        params['security'] = security
        
        if security == 'reality':
            reality_settings = stream_settings.get('realitySettings', {})
            
            if reality_settings.get('publicKey'):
                params['pbk'] = reality_settings['publicKey']
            if reality_settings.get('shortId'):
                params['sid'] = reality_settings['shortId']
            if reality_settings.get('serverName'):
                params['sni'] = reality_settings['serverName']
            if reality_settings.get('fingerprint'):
                params['fp'] = reality_settings['fingerprint']
        
        elif security == 'tls':
            tls_settings = stream_settings.get('tlsSettings', {})
            
            if tls_settings.get('serverName'):
                params['sni'] = tls_settings['serverName']
            if tls_settings.get('fingerprint'):
                params['fp'] = tls_settings['fingerprint']
        
        params_str = '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()])
        vless_url = f"vless://{uuid}@{address}:{port}?{params_str}#{urllib.parse.quote(name)}"
        
        return vless_url
    
    def extract_vless_from_text(self, text: str) -> List[str]:
        """Извлечение vless:// ключей из текста"""
        pattern = r'vless://[^\s\n<>"\'\)]+' 
        matches = re.findall(pattern, text)
        return matches
    
    def decode_subscription(self, raw_data: str) -> List[str]:
        """Декодирование подписки с поддержкой множества форматов"""
        vless_keys = []
        
        # 1. JSON конфиг
        json_data = self.try_parse_json(raw_data)
        
        if json_data:
            print("📦 Обнаружен JSON формат")
            
            if 'outbounds' in json_data or 'inbounds' in json_data:
                print("🔧 Парсинг Xray конфигурации...")
                vless_keys = self.extract_vless_from_xray_config(json_data)
            
            elif isinstance(json_data, list):
                print("📋 Парсинг массива конфигураций...")
                for item in json_data:
                    if isinstance(item, dict):
                        keys = self.extract_vless_from_xray_config(item)
                        vless_keys.extend(keys)
            
            if vless_keys:
                print(f"✅ Извлечено {len(vless_keys)} ключей из JSON")
                return vless_keys
        
        # 2. Base64
        try:
            decoded = base64.b64decode(raw_data).decode('utf-8')
            print("🔓 Подписка декодирована из base64")
            vless_keys = self.extract_vless_from_text(decoded)
            
            if vless_keys:
                print(f"✅ Найдено {len(vless_keys)} ключей в base64")
                return vless_keys
        except:
            pass
        
        # 3. Plain text
        print("📄 Попытка парсинга как plain text")
        vless_keys = self.extract_vless_from_text(raw_data)
        
        if vless_keys:
            print(f"✅ Найдено {len(vless_keys)} ключей в plain text")
            return vless_keys
        
        return []
    
    def parse_vless_key(self, vless_url: str) -> Dict:
        """Парсинг vless:// URL"""
        if not vless_url.startswith('vless://'):
            return None
        
        url_without_prefix = vless_url[8:]
        parts = url_without_prefix.split('?')
        
        user_and_server = parts[0]
        uuid, server_info = user_and_server.split('@')
        
        if ':' in server_info:
            host, port = server_info.rsplit(':', 1)
        else:
            host = server_info
            port = '443'
        
        params = {}
        name = ""
        
        if len(parts) > 1:
            param_and_name = parts[1].split('#')
            param_string = param_and_name[0]
            
            if len(param_and_name) > 1:
                name = urllib.parse.unquote(param_and_name[1])
            
            for param in param_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = urllib.parse.unquote(value)
        
        return {
            'uuid': uuid,
            'host': host,
            'port': port,
            'name': name,
            'params': params
        }
    
    def print_key_info(self, parsed: Dict, index: int):
        """Красиво выводит информацию о ключе"""
        print(f"\n{'='*70}")
        print(f"🔑 Ключ #{index + 1}: {parsed['name'] or 'Без названия'}")
        print(f"{'='*70}")
        print(f"UUID:      {parsed['uuid']}")
        print(f"Сервер:    {parsed['host']}")
        print(f"Порт:      {parsed['port']}")
        print(f"\nПараметры:")
        for key, value in parsed['params'].items():
            print(f"  {key:15} = {value}")
    
    def convert(self, output_file: str = None, show_details: bool = True):
        """Основной метод конвертации"""
        
        # Пробуем разные клиенты
        success = self.try_all_clients()
        
        if not success or not self.vless_keys:
            print("\n❌ Не удалось получить vless ключи")
            print("\n💡 Дополнительные рекомендации:")
            print("   1. Проверьте, что в Remnawave настроены хосты")
            print("   2. Убедитесь, что пользователь активен")
            print("   3. Попробуйте скопировать ссылку подписки заново")
            print("   4. Откройте URL в браузере и проверьте, работает ли страница")
            return
        
        print(f"\n{'='*70}")
        print("📋 РЕЗУЛЬТАТЫ КОНВЕРТАЦИИ")
        print(f"{'='*70}")
        
        parsed_keys = []
        for i, key in enumerate(self.vless_keys):
            parsed = self.parse_vless_key(key)
            if parsed:
                parsed_keys.append(parsed)
                if show_details:
                    self.print_key_info(parsed, i)
        
        if output_file:
            self.save_to_file(output_file, parsed_keys)
        
        print(f"\n{'='*70}")
        print("🔑 ВСЕ КЛЮЧИ (для копирования):")
        print(f"{'='*70}\n")
        for i, key in enumerate(self.vless_keys, 1):
            print(f"{i}. {key}\n")
    
    def save_to_file(self, filename: str, parsed_keys: List[Dict]):
        """Сохранение ключей в файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Remnawave VLESS Keys\n")
                f.write(f"# Total: {len(self.vless_keys)} keys\n\n")
                
                for i, key in enumerate(self.vless_keys, 1):
                    f.write(f"# Key {i}\n")
                    f.write(f"{key}\n\n")
                
                f.write("\n\n# Detailed JSON Format:\n")
                f.write(json.dumps(parsed_keys, indent=2, ensure_ascii=False))
            
            print(f"💾 Ключи сохранены в файл: {filename}")
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении файла: {e}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║   Remnawave Subscription → VLESS Keys Converter v0.1     ║
║   Поддержка Subscription Page и разных VPN клиентов      ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1:
        subscription_url = sys.argv[1]
    else:
        subscription_url = input("🔗 Введите URL подписки Remnawave: ").strip()
    
    if not subscription_url:
        print("❌ URL не может быть пустым")
        sys.exit(1)
    
    converter = RemnavaveSubscriptionConverter(subscription_url)
    
    save_file = input("\n💾 Сохранить ключи в файл? (Enter - пропустить, или укажите имя файла): ").strip()
    output_file = save_file if save_file else None
    
    converter.convert(output_file=output_file, show_details=True)
    
    print("\n✅ Готово!")


if __name__ == "__main__":
    main()

