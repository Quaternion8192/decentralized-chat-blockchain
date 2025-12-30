import asyncio
from .network import P2PProtocol

class SimplifiedHotStuff:
    def __init__(self, node):
        self.node = node
        self.view_number = 0

    async def start_proposal(self, block_data: str):
        """作为 Leader 发起提案"""
        self.view_number += 1
        proposal = {
            "type": "CONSENSUS_PROPOSAL",
            "view": self.view_number,
            "leader_id": self.node.node_id,
            "block": block_data,
            "signature": self.node.crypto.sign(block_data)
        }
        print(f"[👑] 发起共识提案 (View {self.view_number}): {block_data}")
        
        # 广播给所有已知节点
        for nid, info in self.node.routing_table.items():
            asyncio.create_task(self.send_proposal(info, proposal))

    async def send_proposal(self, target_info, proposal):
        try:
            reader, writer = await asyncio.open_connection(target_info['host'], target_info['port'])
            await P2PProtocol.send_json(writer, proposal)
            writer.close()
        except:
            pass

    async def handle_proposal(self, msg: dict):
        """处理来自 Leader 的提案"""
        leader_id = msg['leader_id']
        block_data = msg['block']
        signature = msg['signature']
        
        # 获取 Leader 公钥
        leader_info = self.node.routing_table.get(leader_id)
        if not leader_info:
            print("[x] 收到未知 Leader 的提案")
            return

        leader_pub_key = self.node.crypto.load_pub_key(leader_info['pub_key'])
        
        # 验签
        if self.node.crypto.verify(leader_pub_key, block_data, signature):
            print(f"[🗳️] 验证提案通过: '{block_data}' 来自 {leader_id}")
            # 这里可以回复 VOTE 消息，此处简化为打印
        else:
            print("[x] 提案签名验证失败")