import asyncio
import json
import logging
import websockets
from websockets.server import serve
from websockets.http import Headers

# このファイルのロガーを取得
logger = logging.getLogger(__name__)


async def health_check(path: str, request_headers: Headers):
    """
    WebSocket以外の通常のリクエスト(favicon.icoなど)を処理し、エラーが出ないようにする。
    """
    if path == "/favicon.ico":
        return (204, {}, b"")
    return (204, {}, b"")


class WebSocketServer:
    def __init__(self, host, port, message_queue, discord_bot_client, font_list: list):
        self.host = host
        self.port = port
        self.message_queue = message_queue
        self.bot = discord_bot_client
        self.connected_clients = set()
        self.font_list = font_list

    async def _register(self, websocket):
        self.connected_clients.add(websocket)
        logger.info(f"OBSクライアントが接続: {websocket.remote_address}")

    async def _unregister(self, websocket):
        self.connected_clients.remove(websocket)
        logger.info(f"OBSクライアントが切断: {websocket.remote_address}")

    async def _broadcast(self, message_json):
        if self.connected_clients:
            tasks = [asyncio.create_task(client.send(message_json)) for client in self.connected_clients]
            await asyncio.wait(tasks)

    async def _send_initial_messages(self, websocket):
        history = await self.bot.get_initial_history()
        init_data = {
            "type": "init",
            "messages": history,
            "fonts": self.font_list
        }
        await websocket.send(json.dumps(init_data))
        logger.info(f"初期メッセージを送信しました ({len(history)}件)")

    async def _queue_listener(self):
        logger.info("メッセージキューの監視を開始...")
        while True:
            message_data = await self.message_queue.get()
            await self._broadcast(json.dumps(message_data))
            self.message_queue.task_done()

    async def start(self):
        logger.info(f"WebSocketサーバーを ws://{self.host}:{self.port} で起動します。")

        async def handler_with_init(websocket, path=None):
            await self._register(websocket)
            try:
                await self._send_initial_messages(websocket)
                await websocket.wait_closed()
            finally:
                await self._unregister(websocket)

        server = serve(
            handler_with_init,
            self.host,
            self.port,
            process_request=health_check
        )

        await asyncio.gather(server, self._queue_listener())