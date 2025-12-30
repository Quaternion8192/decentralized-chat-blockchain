import asyncio
import time
from typing import Dict
from .crypto_utils import CryptoManager
from .network import NodeServer, P2PProtocol
from .consensus import SimplifiedHotStuff

class ProtocolNode:
    def __init__(self, node_id: str, host: str, port: int, bootstrap_nodes: list = None):
        self.node_id = node_id
        self.addr = (host, port)
        self.crypto = CryptoManager()
        self.server = NodeServer(host, port, self.handle_message)
        
        # 路由表: {node_id: {"host": str, "port": int, "pub_key": str}}
        self.routing_table = {}
        
        # 信鸽缓存: {target_did: [encrypted_msg_dict]}
        self.pigeon_cache = {}
        
        self.bootstrap_nodes = bootstrap_nodes or []
        self.consensus = SimplifiedHotStuff(self)

    def get_did(self) -> str:
        return f"did:p2p:{self.node_id}"

    async def start(self):
        await self.server.start()
        # 加入网络
        for b_host, b_port in self.bootstrap_nodes:
            if (b_host, b_port) != self.addr:
                await self.ping_node(b_host, b_port)

    async def ping_node(self, host, port):
        """握手并交换路由表"""
        try:
            reader, writer = await asyncio.open_connection(host, port)
            
            # 发送 Hello
            hello_msg = {
                "type": "HELLO",
                "sender_id": self.node_id,
                "addr": self.addr,
                "pub_key": self.crypto.get_pub_key_pem()
            }
            await P2PProtocol.send_json(writer, hello_msg)
            
            # 读取回复（对方的路由表）
            response = await P2PProtocol.read_json(reader)
            if response and response['type'] == "WELCOME":
                self.update_routing(response['routing_table'])
                print(f"[+] 已连接到网络节点 {host}:{port}")
            
            writer.close()
            await writer.wait_closed()
        except Exception:
            print(f"[-] 无法连接到节点 {host}:{port}")

    def update_routing(self, new_table: dict):
        for nid, info in new_table.items():
            if nid != self.node_id and nid not in self.routing_table:
                self.routing_table[nid] = info
                # print(f"[*] 发现新节点: {nid}")

    async def handle_message(self, msg: dict, writer) -> dict:
        """处理收到的网络消息"""
        msg_type = msg.get('type')
        
        if msg_type == "HELLO":
            # 记录新节点
            sender_info = {"host": msg['addr'][0], "port": msg['addr'][1], "pub_key": msg['pub_key']}
            self.routing_table[msg['sender_id']] = sender_info
            # 返回我的路由表作为欢迎
            current_routing = self.routing_table.copy()
            current_routing[self.node_id] = {"host": self.addr[0], "port": self.addr[1], "pub_key": self.crypto.get_pub_key_pem()}
            return {"type": "WELCOME", "routing_table": current_routing}

        elif msg_type == "DIRECT_MSG":
            # 尝试解密
            try:
                content = self.crypto.decrypt_message(msg['encrypted_payload'])
                print(f"\n[🔔] 收到来自 {msg['sender_id']} 的加密消息: {content}")
                
                # 检查是否有离线消息需要提取 (模拟 Pigon Protocol 提取)
                if self.get_did() in self.pigeon_cache:
                    # 实际应需要 ZKP 验证，此处简化
                    print(f"    └── [信鸽] 自动提取了 {len(self.pigeon_cache[self.get_did()])} 条离线缓存消息")
                    self.pigeon_cache.pop(self.get_did())
                    
            except Exception as e:
                print(f"[!] 解密失败: {e}")
            return {"type": "ACK", "status": "received"}

        elif msg_type == "RELAY_MSG":
            # 信鸽协议：帮别人缓存消息
            target_did = msg['target_did']
            print(f"[🕊️] 信鸽中继：为 {target_did} 缓存了一条离线消息")
            if target_did not in self.pigeon_cache:
                self.pigeon_cache[target_did] = []
            self.pigeon_cache[target_did].append(msg['payload'])
            return {"type": "ACK", "status": "cached"}
            
        elif msg_type == "CONSENSUS_PROPOSAL":
            await self.consensus.handle_proposal(msg)
            return None

        return None

    async def send_message(self, target_node_id: str, text: str):
        """发送端到端加密消息"""
        target = self.routing_table.get(target_node_id)
        if not target:
            print(f"[!] 未找到节点 {target_node_id}，正在查找...")
            return

        # 加密
        encrypted = CryptoManager.encrypt_for(target['pub_key'], text)
        
        payload = {
            "type": "DIRECT_MSG",
            "sender_id": self.node_id,
            "encrypted_payload": encrypted,
            "timestamp": time.time()
        }

        try:
            reader, writer = await asyncio.open_connection(target['host'], target['port'])
            await P2PProtocol.send_json(writer, payload)
            # 等待 ACK
            resp = await P2PProtocol.read_json(reader)
            if resp and resp.get('type') == 'ACK':
                print(f"[✓] 消息已送达 {target_node_id}")
            writer.close()
            await writer.wait_closed()
        except OSError:
            print(f"[⚠️] 目标 {target_node_id} 离线，转为信鸽中继模式...")
            await self.send_via_relay(target_node_id, encrypted)

    async def send_via_relay(self, target_node_id: str, encrypted_payload: dict):
        """发送给网路中的任意其他节点进行缓存"""
        # 简单选取第一个非目标的邻居作为中继
        for nid, info in self.routing_table.items():
            if nid != target_node_id:
                try:
                    reader, writer = await asyncio.open_connection(info['host'], info['port'])
                    relay_msg = {
                        "type": "RELAY_MSG",
                        "target_did": f"did:p2p:{target_node_id}",
                        "payload": encrypted_payload
                    }
                    await P2PProtocol.send_json(writer, relay_msg)
                    print(f"[✓] 消息已发送至中继节点 {nid}")
                    writer.close()
                    break
                except:
                    continue