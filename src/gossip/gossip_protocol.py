"""
Gossip协议实现
用于在P2P网络中高效传播消息
"""
import asyncio
import json
import time
import random
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum


class GossipType(Enum):
    """Gossip消息类型"""
    DATA_SYNC = "data_sync"      # 数据同步
    MEMBERSHIP = "membership"    # 成员变更
    CUSTOM = "custom"           # 自定义消息


@dataclass
class GossipMessage:
    """Gossip消息数据类"""
    msg_id: str
    msg_type: GossipType
    content: dict
    sender_id: str
    timestamp: float
    hops: int = 0  # 消息传播跳数
    ttl: int = 5   # 生存时间


class GossipProtocol:
    """Gossip协议主类"""
    
    def __init__(self, node_id: str, routing_table_manager, max_hops: int = 5, fanout: int = 3):
        self.node_id = node_id
        self.routing_table_manager = routing_table_manager
        self.max_hops = max_hops
        self.fanout = fanout  # 每次传播的节点数
        self.received_messages: Set[str] = set()  # 已接收的消息ID集合
        self.message_history: Dict[str, GossipMessage] = {}  # 消息历史
        self.propagation_stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_propagated": 0
        }
        
    async def broadcast(self, msg_type: GossipType, content: dict) -> str:
        """广播Gossip消息"""
        # 生成唯一消息ID
        msg_id = f"{self.node_id}_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # 创建Gossip消息
        gossip_msg = GossipMessage(
            msg_id=msg_id,
            msg_type=msg_type,
            content=content,
            sender_id=self.node_id,
            timestamp=time.time(),
            hops=0,
            ttl=self.max_hops
        )
        
        # 记录消息
        self.received_messages.add(msg_id)
        self.message_history[msg_id] = gossip_msg
        
        # 选择要传播的节点
        target_nodes = self._select_random_nodes(self.fanout)
        
        # 异步传播消息
        tasks = []
        for node_info in target_nodes:
            task = asyncio.create_task(self._send_gossip_message(gossip_msg, node_info))
            tasks.append(task)
        
        # 等待传播完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.propagation_stats["messages_sent"] += 1
        print(f"[ossip] 消息已广播: {msg_id}, 类型: {msg_type.value}")
        
        return msg_id

    def _select_random_nodes(self, count: int) -> List:
        """选择随机节点用于Gossip传播"""
        all_nodes = self.routing_table_manager.get_active_nodes()
        if len(all_nodes) <= count:
            return all_nodes
        return random.sample(all_nodes, count)

    async def _send_gossip_message(self, gossip_msg: GossipMessage, target_node):
        """向目标节点发送Gossip消息"""
        try:
            reader, writer = await asyncio.open_connection(target_node.host, target_node.port)
            
            # 构建消息包
            message_packet = {
                "type": "GOSSIP_MESSAGE",
                "gossip_data": {
                    "msg_id": gossip_msg.msg_id,
                    "msg_type": gossip_msg.msg_type.value,
                    "content": gossip_msg.content,
                    "sender_id": gossip_msg.sender_id,
                    "timestamp": gossip_msg.timestamp,
                    "hops": gossip_msg.hops + 1,
                    "ttl": gossip_msg.ttl - 1
                }
            }
            
            # 使用P2PProtocol发送消息
            from ..network.protocol import P2PProtocol
            await P2PProtocol.send_json(writer, message_packet)
            
            # 等待确认
            response = await P2PProtocol.read_json(reader)
            if response and response.get('type') == 'GOSSIP_ACK':
                print(f"[ossip] 消息 {gossip_msg.msg_id} 已发送到 {target_node.node_id}")
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            print(f"[!] 发送Gossip消息失败到 {target_node.node_id}: {e}")

    async def handle_gossip_message(self, gossip_data: dict) -> Optional[dict]:
        """处理接收到的Gossip消息"""
        msg_id = gossip_data.get('msg_id')
        msg_type = gossip_data.get('msg_type')
        content = gossip_data.get('content')
        sender_id = gossip_data.get('sender_id')
        hops = gossip_data.get('hops', 0)
        ttl = gossip_data.get('ttl', 0)
        
        # 检查消息是否已接收过
        if msg_id in self.received_messages:
            print(f"[ossip] 重复消息，忽略: {msg_id}")
            return {"type": "GOSSIP_ACK", "status": "duplicate"}
        
        # 检查TTL
        if ttl <= 0:
            print(f"[ossip] 消息TTL已过期: {msg_id}")
            return {"type": "GOSSIP_ACK", "status": "ttl_expired"}
        
        # 记录消息
        self.received_messages.add(msg_id)
        self.message_history[msg_id] = GossipMessage(
            msg_id=msg_id,
            msg_type=GossipType(msg_type),
            content=content,
            sender_id=sender_id,
            timestamp=gossip_data.get('timestamp', time.time()),
            hops=hops,
            ttl=ttl
        )
        
        self.propagation_stats["messages_received"] += 1
        
        # 根据消息类型处理
        await self._process_gossip_content(GossipType(msg_type), content, sender_id)
        
        # 如果还有TTL，继续传播
        if ttl > 1:
            await self._propagate_message(gossip_data)
            self.propagation_stats["messages_propagated"] += 1
        
        return {"type": "GOSSIP_ACK", "status": "received"}

    async def _process_gossip_content(self, msg_type: GossipType, content: dict, sender_id: str):
        """处理Gossip消息内容"""
        if msg_type == GossipType.DATA_SYNC:
            # 处理数据同步消息
            print(f"[ossip] 处理数据同步消息来自 {sender_id}: {content}")
            # 这里可以实现数据同步逻辑
            # 例如：同步区块链、同步路由表等
            self._handle_data_sync(content, sender_id)
        elif msg_type == GossipType.MEMBERSHIP:
            # 处理成员变更消息
            print(f"[ossip] 处理成员变更消息来自 {sender_id}: {content}")
            # 这里可以实现成员管理逻辑
            # 例如：添加新节点、移除离线节点等
            self._handle_membership_change(content, sender_id)
        elif msg_type == GossipType.CUSTOM:
            # 处理自定义消息
            print(f"[ossip] 处理自定义消息来自 {sender_id}: {content}")
            # 这里可以实现自定义逻辑
            self._handle_custom_message(content, sender_id)

    def _handle_data_sync(self, content: dict, sender_id: str):
        """处理数据同步消息"""
        # 实现数据同步逻辑
        sync_type = content.get('sync_type')
        sync_data = content.get('data')
        
        if sync_type == 'blockchain':
            # 区块链同步
            print(f"[ossip] 区块链同步数据来自 {sender_id}")
        elif sync_type == 'routing':
            # 路由表同步
            print(f"[ossip] 路由表同步数据来自 {sender_id}")
        elif sync_type == 'status':
            # 状态同步
            print(f"[ossip] 状态同步数据来自 {sender_id}")
        
    def _handle_membership_change(self, content: dict, sender_id: str):
        """处理成员变更消息"""
        change_type = content.get('change_type')
        node_info = content.get('node_info')
        
        if change_type == 'joined':
            # 节点加入
            print(f"[ossip] 节点 {node_info.get('node_id')} 加入网络")
        elif change_type == 'left':
            # 节点离开
            print(f"[ossip] 节点 {node_info.get('node_id')} 离开网络")
        elif change_type == 'updated':
            # 节点信息更新
            print(f"[ossip] 节点 {node_info.get('node_id')} 信息更新")
        
    def _handle_custom_message(self, content: dict, sender_id: str):
        """处理自定义消息"""
        # 处理自定义消息
        custom_type = content.get('custom_type')
        data = content.get('data')
        
        print(f"[ossip] 处理自定义 {custom_type} 消息来自 {sender_id}")

    async def _propagate_message(self, gossip_data: dict):
        """传播Gossip消息到其他节点"""
        # 增加跳数
        gossip_data['hops'] += 1
        gossip_data['ttl'] -= 1
        
        # 选择要传播的节点（排除发送者）
        target_nodes = self._select_random_nodes(self.fanout)
        target_nodes = [node for node in target_nodes if node.node_id != gossip_data['sender_id']]
        
        # 异步传播消息
        tasks = []
        for node_info in target_nodes:
            task = asyncio.create_task(self._send_gossip_message(
                GossipMessage(
                    msg_id=gossip_data['msg_id'],
                    msg_type=GossipType(gossip_data['msg_type']),
                    content=gossip_data['content'],
                    sender_id=gossip_data['sender_id'],
                    timestamp=gossip_data['timestamp'],
                    hops=gossip_data['hops'],
                    ttl=gossip_data['ttl']
                ),
                node_info
            ))
            tasks.append(task)
        
        # 等待传播完成
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_propagation_stats(self) -> dict:
        """获取传播统计信息"""
        return {
            "node_id": self.node_id,
            "stats": self.propagation_stats,
            "received_messages_count": len(self.received_messages),
            "message_history_size": len(self.message_history)
        }

    def cleanup_old_messages(self, max_age: float = 3600):  # 1小时
        """清理过期的消息"""
        current_time = time.time()
        old_msg_ids = [
            msg_id for msg_id, msg in self.message_history.items()
            if current_time - msg.timestamp > max_age
        ]
        
        for msg_id in old_msg_ids:
            del self.message_history[msg_id]
            self.received_messages.discard(msg_id)


class GossipManager:
    """Gossip管理器，用于协调多个Gossip协议实例"""
    
    def __init__(self, node_id: str, routing_table_manager):
        self.node_id = node_id
        self.routing_table_manager = routing_table_manager
        self.gossip_protocols: Dict[str, GossipProtocol] = {}
        
        # 创建默认的Gossip协议实例
        self.default_gossip = GossipProtocol(node_id, routing_table_manager)
        self.gossip_protocols["default"] = self.default_gossip
        
    def create_gossip_protocol(self, name: str, max_hops: int = 5, fanout: int = 3) -> GossipProtocol:
        """创建新的Gossip协议实例"""
        protocol = GossipProtocol(
            self.node_id, 
            self.routing_table_manager, 
            max_hops, 
            fanout
        )
        self.gossip_protocols[name] = protocol
        return protocol
    
    async def broadcast_message(self, msg_type: GossipType, content: dict, protocol_name: str = "default"):
        """使用指定协议广播消息"""
        protocol = self.gossip_protocols.get(protocol_name, self.default_gossip)
        return await protocol.broadcast(msg_type, content)
    
    async def handle_incoming_gossip(self, gossip_data: dict, protocol_name: str = "default"):
        """处理传入的Gossip消息"""
        protocol = self.gossip_protocols.get(protocol_name, self.default_gossip)
        return await protocol.handle_gossip_message(gossip_data)
    
    def get_gossip_stats(self) -> dict:
        """获取所有Gossip协议的统计信息"""
        stats = {}
        for name, protocol in self.gossip_protocols.items():
            stats[name] = protocol.get_propagation_stats()
        return stats
    
    def cleanup_old_messages(self):
        """清理所有协议的过期消息"""
        for protocol in self.gossip_protocols.values():
            protocol.cleanup_old_messages()