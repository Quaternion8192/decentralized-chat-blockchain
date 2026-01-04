"""
节点服务器类
"""
import asyncio
from typing import Callable, Dict
from ..network.protocol import P2PProtocol


class NodeServer:
    """节点服务器类"""
    def __init__(self, host: str, port: int, handler_callback: Callable):
        self.host = host
        self.port = port
        self.handler_callback = handler_callback
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        print(f"[*] 服务监听于 {self.host}:{self.port}")
        asyncio.create_task(self.server.serve_forever())

    async def handle_client(self, reader, writer):
        peer_addr = writer.get_extra_info('peername')
        try:
            while True:
                data = await P2PProtocol.read_json(reader)
                if data is None: break
                # 调用节点逻辑处理消息
                response = await self.handler_callback(data, writer)
                if response:
                    await P2PProtocol.send_json(writer, response)
        except Exception as e:
            print(f"[!] 客户端处理错误: {e}")
        finally:
            writer.close()
            await writer.wait_closed()