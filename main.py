import asyncio
import logging
import yaml
import sys
from pathlib import Path

from src.bot import ChatBot
from src.server import WebSocketServer


def load_config() -> dict:
    """config.yamlを読み込む"""
    config_path = Path("config.yaml")

    if not config_path.exists():
        print("❌ config.yaml が見つかりません")
        print("config.yaml.example をコピーして config.yaml を作成してください")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 必須項目のチェック
        if not config.get('discord', {}).get('token'):
            print("❌ config.yaml に Discord トークンが設定されていません")
            sys.exit(1)

        if config['discord']['token'] == "YOUR_DISCORD_BOT_TOKEN_HERE":
            print("❌ config.yaml の Discord トークンを実際のトークンに書き換えてください")
            sys.exit(1)

        return config

    except Exception as e:
        print(f"❌ config.yaml の読み込みに失敗しました: {e}")
        sys.exit(1)


def setup_logging(config: dict):
    """ロギング設定"""
    log_level = config.get('logging', {}).get('level', 'INFO')

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


async def main():
    """メイン処理"""
    print("=" * 60)
    print("  Discord to OBS Chat Viewer")
    print("=" * 60)

    # 設定読み込み
    config = load_config()
    setup_logging(config)

    logger = logging.getLogger(__name__)
    logger.info("🚀 アプリケーション起動中...")

    # WebSocketサーバー初期化
    ws_server = WebSocketServer(config)

    # Discord Bot初期化（WebSocketサーバーへのコールバック付き）
    async def on_message_callback(msg_type: str, msg_data):
        """Botからのメッセージを受け取ってWebSocketで配信"""
        await ws_server.add_message(msg_type, msg_data)

    bot = ChatBot(config, on_message_callback)

    # 起動情報表示
    logger.info("=" * 60)
    logger.info("設定情報:")
    logger.info(f"  監視チャンネル数: {len(config['discord']['channels'])}")
    logger.info(f"  履歴取得件数: {config['discord']['history_limit']}")
    logger.info(f"  最大保持件数: {config['discord']['max_messages']}")
    logger.info(f"  WebSocketポート: {config['websocket']['port']}")
    logger.info("=" * 60)
    logger.info("コマンド:")
    logger.info("  /add <チャンネル>   - チャンネルを監視リストに追加")
    logger.info("  /remove <チャンネル> - チャンネルを監視リストから削除")
    logger.info("  /list              - 監視中のチャンネル一覧")
    logger.info("=" * 60)

    try:
        # WebSocketサーバーとDiscord Botを並行実行
        await asyncio.gather(
            ws_server.start(),
            bot.start()
        )
    except KeyboardInterrupt:
        logger.info("⛔ 終了処理中...")
    except Exception as e:
        logger.error(f"❌ エラー: {e}", exc_info=True)
    finally:
        await bot.close()
        logger.info("✅ アプリケーション終了")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ 終了しました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)