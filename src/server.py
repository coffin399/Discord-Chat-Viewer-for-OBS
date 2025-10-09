import asyncio
import websockets
import json
from typing import Set
import logging

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocketサーバー for OBS連携"""

    def __init__(self, config: dict):
        self.config = config
        self.host = config['websocket']['host']
        self.port = config['websocket']['port']
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.message_history = []
        self.max_messages = config['discord']['max_messages']

    async def handler(self, websocket, path):
        """WebSocket接続ハンドラー"""
        logger.info(f"🔌 WebSocketクライアント接続: {websocket.remote_address}")
        self.connected_clients.add(websocket)

        try:
            # 接続時に初期データ(メッセージ履歴)を送信
            await websocket.send(json.dumps({
                "type": "init",
                "messages": self.message_history,
                "fonts": []
            }, ensure_ascii=False))

            # クライアントからのメッセージを待機(keepalive用)
            async for message in websocket:
                # クライアントからのメッセージは特に処理しない
                logger.debug(f"クライアントメッセージ: {message}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 WebSocketクライアント切断: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"WebSocketエラー: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def broadcast(self, data: dict):
        """全接続クライアントにデータを送信"""
        if not self.connected_clients:
            logger.debug("送信先クライアントなし")
            return

        message = json.dumps(data, ensure_ascii=False)
        disconnected = set()

        for client in self.connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"メッセージ送信エラー: {e}")
                disconnected.add(client)

        # 切断されたクライアントを削除
        self.connected_clients.difference_update(disconnected)

        if disconnected:
            logger.info(f"切断されたクライアントを削除: {len(disconnected)}件")

    async def add_message(self, message_type: str, message_data):
        """メッセージを追加してブロードキャスト"""

        if message_type == "init":
            # 初期データ: メッセージ履歴を置き換え
            self.message_history = message_data
            logger.info(f"📋 初期メッセージ設定: {len(self.message_history)}件")

        elif message_type == "new":
            # 新規メッセージ: 履歴に追加してブロードキャスト
            self.message_history.append(message_data)

            # 最大数を超えたら古いメッセージを削除
            if len(self.message_history) > self.max_messages:
                removed = len(self.message_history) - self.max_messages
                self.message_history = self.message_history[-self.max_messages:]
                logger.debug(f"古いメッセージを削除: {removed}件")

            # クライアントに送信
            await self.broadcast({
                "type": "new",
                "message": message_data
            })

        elif message_type == "bulk":
            # 一括追加: 履歴に追加してブロードキャスト
            for msg in message_data:
                self.message_history.append(msg)
                await self.broadcast({
                    "type": "new",
                    "message": msg
                })
                await asyncio.sleep(0.1)  # 少し間隔を開ける

            # 最大数を超えたら古いメッセージを削除
            if len(self.message_history) > self.max_messages:
                self.message_history = self.message_history[-self.max_messages:]

    async def start(self):
        """WebSocketサーバーを起動"""
        logger.info(f"🌐 WebSocketサーバー起動: ws://{self.host}:{self.port}")

        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # 永続実行

    def get_client_count(self) -> int:
        """接続中のクライアント数を取得"""
        return len(self.connected_clients)