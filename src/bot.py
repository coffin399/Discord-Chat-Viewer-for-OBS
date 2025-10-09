import discord
from discord import app_commands
import logging
from src import config_manager


def format_message(message: discord.Message) -> dict:
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
        logging.info(f'{self.user} としてDiscordにログインしました。')
        channels = config_manager.get_watch_channels()
        logging.info(f'監視対象チャンネルID: {channels if channels else "なし"}')
        logging.info("OBSからの接続を待っています...")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        watch_channels = config_manager.get_watch_channels()
        if message.channel.id not in watch_channels:
            return

        logging.info(f"新しいメッセージを受信: #{message.channel.name} - {message.author.display_name}")

        new_message_data = {"type": "new", "message": format_message(message)}
        await self.message_queue.put(new_message_data)

    async def get_initial_history(self) -> list:
        history = []
        # config_manager経由で監視チャンネルを取得します
        channel_ids = config_manager.get_watch_channels()
        if not channel_ids:
            return []

        for channel_id in channel_ids:
            channel = self.get_channel(channel_id)
            if channel:
                limit_per_channel = max(1, self.history_limit // len(channel_ids))
                async for msg in channel.history(limit=limit_per_channel):
                    history.append(msg)

        history.sort(key=lambda m: m.created_at)
        return [format_message(msg) for msg in history[-self.history_limit:]]


def setup_bot(bot: DiscordBot):
    @bot.tree.command(name="add", description="OBSに表示するチャンネルを追加します。")
    @app_commands.describe(channel="追加するテキストチャンネル")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def add_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        if config_manager.add_watch_channel(channel.id):
            await interaction.response.send_message(f"✅ チャンネル `#{channel.name}` を監視対象に追加しました。",
                                                    ephemeral=True)
            logging.info(f"チャンネル追加: #{channel.name} (ID: {channel.id})")
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
            logging.info(f"チャンネル削除: #{channel.name} (ID: {channel.id})")
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
            logging.error(f"コマンドエラー: {error}")