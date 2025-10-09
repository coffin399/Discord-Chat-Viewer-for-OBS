import yaml
import os
from typing import List, Dict, Any

CONFIG_FILE = 'config.yaml'

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        print(f"[ERROR] 設定ファイルが見つかりません。")
        print(f"        カレントディレクトリ: {os.getcwd()}")
        print(f"        探したファイル: {os.path.abspath(CONFIG_FILE)}")
        exit()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] 設定ファイルの読み込み中にエラーが発生しました: {e}")
        exit()

def _save_config(config_data: Dict[str, Any]):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)

def get_watch_channels() -> List[int]:
    config = load_config()
    return config.get("WATCH_CHANNELS", [])

def add_watch_channel(channel_id: int) -> bool:
    config = load_config()
    channels = config.get("WATCH_CHANNELS", [])
    if channel_id not in channels:
        channels.append(channel_id)
        config["WATCH_CHANNELS"] = channels
        _save_config(config)
        return True
    return False

def remove_watch_channel(channel_id: int) -> bool:
    config = load_config()
    channels = config.get("WATCH_CHANNELS", [])
    if channel_id in channels:
        channels.remove(channel_id)
        config["WATCH_CHANNELS"] = channels
        _save_config(config)
        return True
    return False