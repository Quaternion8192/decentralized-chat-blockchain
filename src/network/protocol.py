"""
P2P协议类
"""
import asyncio
import json
import struct
from typing import Dict


class P2PProtocol:
    """P2P协议类"""
    @staticmethod
    async def send_json(writer: asyncio.StreamWriter, data: dict):
        """发送 JSON 数据，使用 4字节长度前缀 防止粘包"""
        try:
            message = json.dumps(data).encode('utf-8')
            # packing length as 4-byte big-endian integer
            writer.write(struct.pack('>I', len(message)))
            writer.write(message)
            await writer.drain()
        except ConnectionResetError:
            print("[!] 连接被重置")
            raise
        except Exception as e:
            print(f"[!] 发送JSON数据失败: {e}")
            raise

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
            print("[!] 连接已重置或读取不完整")
            return None
        except json.JSONDecodeError as e:
            print(f"[!] JSON解码错误: {e}")
            return None
        except Exception as e:
            print(f"[!] 读取JSON数据失败: {e}")
            return None