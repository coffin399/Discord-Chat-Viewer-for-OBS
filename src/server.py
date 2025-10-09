import asyncio
import json
import logging
import websockets

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
        logging.info(f"OBSクライアントが接続: {websocket.remote_address}")

    async def _unregister(self, websocket):
        self.connected_clients.remove(websocket)
        logging.info(f"OBSクライアントが切断: {websocket.remote_address}")

    async def _broadcast(self, message_json):
        if self.connected_clients:
            await asyncio.wait([client.send(message_json) for client in self.connected_clients])

    async def _send_initial_messages(self, websocket):
        # botオブジェクトに履歴の取得を依頼します
        history = await self.bot.get_initial_history()
        init_data = {
            "type": "init",
            "messages": history,
            "fonts": self.font_list
        }
        await websocket.send(json.dumps(init_data))
        logging.info(f"初期メッセージを送信しました ({len(history)}件)")

    async def _queue_listener(self):
        logging.info("メッセージキューの監視を開始...")
        while True:
            message_data = await self.message_queue.get()
            await self._broadcast(json.dumps(message_data))
            self.message_queue.task_done()

    async def connection_handler(self, websocket, path):
        await self._register(websocket)
        try:
            await self._send_initial_messages(websocket)
            await websocket.wait_closed()
        finally:
            await self._unregister(websocket)

    async def start(self):
        logging.info(f"WebSocketサーバーを ws://{self.host}:{self.port} で起動します。")
        server = websockets.serve(self.connection_handler, self.host, self.port)
        await asyncio.gather(server, self._queue_listener())