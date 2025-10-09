import discord
from discord import app_commands
import logging
from src import config_manager

# このファイルのロガーを取得
logger = logging.getLogger(__name__)


def format_message(message: discord.Message) -> dict:
    """DiscordのMessageオブジェクトをフロントエンド用のJSON形式に変換する"""
    return {
        "author": message.author.display_name,
        "avatar": message.author.display_avatar.url,
        "content": message.content,
        "attachments": [att.url for att in message.attachments],
        "embeds": [
            {
                "title": embed.title,
                "description": embed.description,
                "image": embed.image.url if embed.image else None,
                "video": embed.video.url if embed.video else None,
            }
            for embed in message.embeds
        ],
    }


class DiscordBot(discord.Client):
    def __init__(self, *, intents: discord.Intents, message_queue, history_limit):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.message_queue = message_queue
        self.history_limit = history_limit

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        logger.warning(f'{self.user} としてDiscordにログインしました。')
        channels = config_manager.get_watch_channels()
        logger.warning(f'監視対象チャンネルID: {channels if channels else "なし"}')
        logger.warning("OBSからの接続を待っています...")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        watch_channels = config_manager.get_watch_channels()
        if message.channel.id not in watch_channels:
            return

        logger.info(f"新しいメッセージを受信: #{message.channel.name} - {message.author.display_name}")

        new_message_data = {"type": "new", "message": format_message(message)}
        await self.message_queue.put(new_message_data)

    async def get_initial_history(self) -> list:
        logger.info("--- 過去メッセージの取得を開始 ---")
        history = []
        channel_ids = config_manager.get_watch_channels()

        if not channel_ids:
            logger.warning("監視対象のチャンネルが設定されていません。履歴は0件です。")
            return []

        logger.info(f"設定されたチャンネルID: {channel_ids}")
        logger.info(f"取得上限 (全体): {self.history_limit}件")

        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            if channel:
                logger.info(f"チャンネル '{channel.name}' (ID: {channel_id}) の履歴を取得します...")
                try:
                    limit_per_channel = max(1, self.history_limit // len(channel_ids))
                    messages_in_channel = 0
                    async for msg in channel.history(limit=limit_per_channel):
                        history.append(msg)
                        messages_in_channel += 1
                    logger.info(f" -> {messages_in_channel}件のメッセージを取得しました。")
                except discord.errors.Forbidden:
                    logger.error(f" -> エラー: チャンネル '{channel.name}' のメッセージ履歴を読む権限がありません！")
                except Exception as e:
                    logger.error(f" -> 不明なエラーが発生しました: {e}")
            else:
                logger.warning(f"チャンネルID {channel_id} が見つからないか、Botがアクセスできません。")

        logger.info(f"全チャンネルから合計 {len(history)}件のメッセージを取得しました。")

        history.sort(key=lambda m: m.created_at)
        final_history = [format_message(msg) for msg in history[-self.history_limit:]]

        logger.info(f"最終的に {len(final_history)}件のメッセージをクライアントに送信します。")
        logger.info("--- 過去メッセージの取得を終了 ---")

        return final_history


def setup_bot(bot: DiscordBot):
    @bot.tree.command(name="add", description="OBSに表示するチャンネルを追加します。")
    @app_commands.describe(channel="追加するテキストチャンネル")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def add_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        if config_manager.add_watch_channel(channel.id):
            await interaction.response.send_message(f"✅ チャンネル `#{channel.name}` を監視対象に追加しました。",
                                                    ephemeral=True)
            logger.warning(f"チャンネル追加: #{channel.name} (ID: {channel.id})")
        else:
            await interaction.response.send_message(f"ℹ️ チャンネル `#{channel.name}` は既に追加されています。",
                                                    ephemeral=True)

    @bot.tree.command(name="remove", description="OBSに表示するチャンネルを削除します。")
    @app_commands.describe(channel="削除するテキストチャンネル")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def remove_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        if config_manager.remove_watch_channel(channel.id):
            await interaction.response.send_message(f"🗑️ チャンネル `#{channel.name}` を監視対象から削除しました。",
                                                    ephemeral=True)
            logger.warning(f"チャンネル削除: #{channel.name} (ID: {channel.id})")
        else:
            await interaction.response.send_message(f"ℹ️ チャンネル `#{channel.name}` は監視対象ではありません。",
                                                    ephemeral=True)

    @add_channel.error
    @remove_channel.error
    async def command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ このコマンドを実行するには`チャンネルの管理`権限が必要です。",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("😭 不明なエラーが発生しました。", ephemeral=True)
            logger.error(f"コマンドエラー: {error}")