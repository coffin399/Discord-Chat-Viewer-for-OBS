import asyncio
import logging
import discord
import os
from src.bot import DiscordBot, setup_bot
from src.server import WebSocketServer
from src import config_manager


def get_available_fonts() -> list[str]:
    fonts_dir = 'fonts'
    supported_extensions = ('.ttf', '.otf', '.woff', '.woff2')
    if not os.path.isdir(fonts_dir):
        logging.warning(f"'{fonts_dir}' ディレクトリが見つかりません。")
        return []

    try:
        fonts = [f for f in os.listdir(fonts_dir) if f.lower().endswith(supported_extensions)]
        if fonts:
            logging.info(f"利用可能なフォントを検出しました: {', '.join(fonts)}")
        else:
            logging.info("カスタムフォントが見つかりませんでした。標準フォントを使用します。")
        return fonts
    except Exception as e:
        logging.error(f"フォントディレクトリのスキャン中にエラーが発生しました: {e}")
        return []


async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    available_fonts = get_available_fonts()

    try:
        config = config_manager.load_config()
        token = config["DISCORD_BOT_TOKEN"]
        ws_host = config.get("WEBSOCKET_HOST", "localhost")
        ws_port = config.get("WEBSOCKET_PORT", 8765)
        history_limit = config.get("HISTORY_LIMIT", 20)
    except (KeyError, ValueError) as e:
        logging.error(f"設定ファイル 'config.yaml' の内容が正しくありません: {e}")
        logging.exception("--- 詳細なエラー情報 ---")
        return

    message_queue = asyncio.Queue()
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    bot = DiscordBot(intents=intents, message_queue=message_queue, history_limit=history_limit)
    setup_bot(bot)

    websocket_server = WebSocketServer(
        host=ws_host,
        port=ws_port,
        message_queue=message_queue,
        discord_bot_client=bot,
        font_list=available_fonts
    )

    try:
        await asyncio.gather(
            bot.start(token),
            websocket_server.start()
        )
    except discord.errors.LoginFailure:
        logging.error("Discord Botのトークンが不正です。config.yamlを確認してください。")
    except Exception as e:
        logging.error(f"起動中に予期せぬエラーが発生しました: {e}")
        logging.exception("--- 詳細なエラー情報 ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("プログラムを終了します。")