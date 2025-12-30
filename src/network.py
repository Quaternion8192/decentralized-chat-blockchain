import asyncio
import json
import struct
from typing import Callable

class P2PProtocol:
    @staticmethod
    async def send_json(writer: asyncio.StreamWriter, data: dict):
        """发送 JSON 数据，使用 4字节长度前缀 防止粘包"""
        message = json.dumps(data).encode('utf-8')
        # packing length as 4-byte big-endian integer
        writer.write(struct.pack('>I', len(message)))
        writer.write(message)
        await writer.drain()

    @staticmethod
    async def read_json(reader: asyncio.StreamReader):
        """读取带长度前缀的 JSON 数据"""
        try:
            # 读取 4字节长度
            header = await reader.readexactly(4)
            length = struct.unpack('>I', header)[0]
            # 根据长度读取内容
            body = await reader.readexactly(length)
            return json.loads(body.decode('utf-8'))
        except (asyncio.IncompleteReadError, ConnectionResetError):
            return None

class NodeServer:
    def __init__(self, host, port, handler_callback: Callable):
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
        # print(f"[*] 新连接: {peer_addr}")
        try:
            while True:
                data = await P2PProtocol.read_json(reader)
                if data is None: break
                # 调用节点逻辑处理消息
                response = await self.handler_callback(data, writer)
                if response:
                    await P2PProtocol.send_json(writer, response)
        except Exception as e:
            # print(f"[!] 连接断开: {e}")
            pass
        finally:
            writer.close()
            await writer.wait_closed()