import os
import json

def cargar_configuracion(filename='config.json'):
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            with open(filename, 'r') as f:
                config = json.load(f)

                return {
                    'broker': config.get('MQTT_BROKER', ''),
                    'username': config.get('MQTT_USERNAME', ''),
                    'password': config.get('MQTT_PASSWORD', ''),
                    'bot_token': config.get('TELEGRAM_BOT_TOKEN', '')
                }
        except FileNotFoundError:
            pass
    return ""

def guardar_configuracion(broker, username, password, bot_token, filename='config.json'):
    config = {
        'MQTT_BROKER': broker,
        'MQTT_USERNAME': username,
        'MQTT_PASSWORD': password,
        'TELEGRAM_BOT_TOKEN': bot_token
    }
    with open(filename, 'w') as f:
        json.dump(config, f)
