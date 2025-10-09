import discord
from discord.ext import commands
from typing import Set, List, Callable, Awaitable
import logging
import yaml

logger = logging.getLogger(__name__)


class ChatBot:
    """Discord Bot for monitoring channels"""

    def __init__(self, config: dict, on_message_callback: Callable):
        self.config = config
        self.on_message_callback = on_message_callback
        self.monitored_channels: Set[int] = set(config['discord']['channels'])
        self.history_limit = config['discord']['history_limit']
        self.max_messages = config['discord']['max_messages']

        # Bot設定
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        self.bot = commands.Bot(command_prefix="/", intents=intents)
        self._setup_events()
        self._setup_commands()

    def _setup_events(self):
        """イベントハンドラーの設定"""

        @self.bot.event
        async def on_ready():
            logger.info(f"✅ Discord Bot準備完了: {self.bot.user}")
            logger.info(f"監視中のチャンネル: {len(self.monitored_channels)}件")

            # 起動時に過去のメッセージを取得
            all_messages = []
            for channel_id in self.monitored_channels:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    logger.info(f"チャンネル '{channel.name}' から過去のメッセージを取得中...")
                    try:
                        async for msg in channel.history(limit=self.history_limit):
                            all_messages.insert(0, self.format_message(msg))
                        logger.info(f"  → {self.history_limit}件取得しました")
                    except Exception as e:
                        logger.error(f"  → エラー: {e}")
                else:
                    logger.warning(f"⚠️ チャンネルID {channel_id} が見つかりません")

            # コールバックで初期メッセージを送信
            if all_messages:
                await self.on_message_callback("init", all_messages)

        @self.bot.event
        async def on_message(message: discord.Message):
            # Bot自身のメッセージは無視
            if message.author.bot:
                await self.bot.process_commands(message)
                return

            # 監視対象チャンネルのメッセージのみ処理
            if message.channel.id not in self.monitored_channels:
                await self.bot.process_commands(message)
                return

            logger.info(f"📨 [{message.channel.name}] {message.author.display_name}: {message.content[:50]}")

            # メッセージをフォーマットして送信
            formatted_msg = self.format_message(message)
            await self.on_message_callback("new", formatted_msg)

            # コマンド処理
            await self.bot.process_commands(message)

    def _setup_commands(self):
        """コマンドの設定"""

        @self.bot.command(name="add")
        @commands.has_permissions(administrator=True)
        async def add_channel(ctx, channel: discord.TextChannel):
            """チャンネルを監視リストに追加"""
            if channel.id in self.monitored_channels:
                await ctx.send(f"❌ {channel.mention} は既に監視中です")
                return

            self.monitored_channels.add(channel.id)
            logger.info(f"➕ チャンネル追加: {channel.name} (ID: {channel.id})")

            # config.yamlを更新
            self._update_config()

            # 過去のメッセージを取得
            messages = []
            try:
                async for msg in channel.history(limit=self.history_limit):
                    messages.insert(0, self.format_message(msg))

                if messages:
                    await self.on_message_callback("bulk", messages)

                await ctx.send(f"✅ {channel.mention} を監視リストに追加しました（{len(messages)}件のメッセージを取得）")
            except Exception as e:
                logger.error(f"メッセージ取得エラー: {e}")
                await ctx.send(f"⚠️ {channel.mention} を追加しましたが、メッセージ取得に失敗しました")

        @self.bot.command(name="remove")
        @commands.has_permissions(administrator=True)
        async def remove_channel(ctx, channel: discord.TextChannel):
            """チャンネルを監視リストから削除"""
            if channel.id not in self.monitored_channels:
                await ctx.send(f"❌ {channel.mention} は監視されていません")
                return

            self.monitored_channels.discard(channel.id)
            logger.info(f"➖ チャンネル削除: {channel.name} (ID: {channel.id})")

            # config.yamlを更新
            self._update_config()

            await ctx.send(f"✅ {channel.mention} を監視リストから削除しました")

        @self.bot.command(name="list")
        async def list_channels(ctx):
            """現在監視中のチャンネル一覧"""
            if not self.monitored_channels:
                await ctx.send("📝 監視中のチャンネルはありません")
                return

            channel_list = []
            for channel_id in self.monitored_channels:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    channel_list.append(f"• {channel.mention} (`{channel.id}`)")
                else:
                    channel_list.append(f"• 不明なチャンネル (`{channel_id}`)")

            await ctx.send(f"📝 **監視中のチャンネル ({len(self.monitored_channels)}件)**\n" + "\n".join(channel_list))

        @add_channel.error
        @remove_channel.error
        async def command_error(ctx, error):
            if isinstance(error, commands.MissingPermissions):
                await ctx.send("❌ このコマンドを実行する権限がありません（管理者権限が必要です）")
            elif isinstance(error, commands.ChannelNotFound):
                await ctx.send("❌ チャンネルが見つかりません")
            else:
                logger.error(f"コマンドエラー: {error}")
                await ctx.send(f"❌ エラーが発生しました: {error}")

    def _update_config(self):
        """config.yamlを更新"""
        try:
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            config['discord']['channels'] = list(self.monitored_channels)

            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            logger.info("✅ config.yaml を更新しました")
        except Exception as e:
            logger.error(f"config.yaml更新エラー: {e}")

    @staticmethod
    def format_message(message: discord.Message) -> dict:
        """Discordメッセージを表示用フォーマットに変換"""

        # 添付ファイルの処理
        attachments = []
        for att in message.attachments:
            attachments.append({
                "url": att.url,
                "filename": att.filename,
                "content_type": att.content_type
            })

        # Embedsの処理
        embeds = []
        for embed in message.embeds:
            embed_data = {
                "title": embed.title,
                "description": embed.description,
                "url": embed.url,
                "color": embed.color.value if embed.color else None,
                "image": embed.image.url if embed.image else None,
                "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
            }
            embeds.append(embed_data)

        return {
            "id": message.id,
            "author": message.author.display_name,
            "avatar": str(message.author.display_avatar.url),
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "channel_name": message.channel.name,
            "attachments": attachments,
            "embeds": embeds
        }

    async def start(self):
        """Botを起動"""
        token = self.config['discord']['token']
        await self.bot.start(token)

    async def close(self):
        """Botを停止"""
        await self.bot.close()