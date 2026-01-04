"""
抗重放攻击管理器
"""
import time
from typing import Set, Dict


class AntiReplayManager:
    """抗重放攻击管理器"""
    def __init__(self, max_age: float = 300):  # 5分钟默认最大时间差
        self.received_messages = set()  # 已接收消息ID集合
        self.message_timestamps = {}  # 消息时间戳记录
        self.max_age = max_age  # 消息最大有效时间（秒）
        self.nonce_cache = {}  # 防重放随机数缓存
        self.node_nonces = {}  # 每个节点的最新随机数

    def is_replay_attack(self, msg_id: str = None, timestamp: float = None, 
                        nonce: str = None, sender_id: str = None) -> bool:
        """检测是否为重放攻击"""
        current_time = time.time()
        
        # 检查消息ID是否已存在（如果提供）
        if msg_id and msg_id in self.received_messages:
            print(f"[!] 检测到重放攻击，消息ID: {msg_id}")
            return True
        
        # 检查时间戳（如果提供）
        if timestamp:
            # 如果消息时间戳与当前时间相差超过允许范围，认为是重放攻击
            if abs(current_time - timestamp) > self.max_age:
                print(f"[!] 检测到可能的重放攻击，时间差: {abs(current_time - timestamp)}秒")
                return True
        
        # 检查随机数（如果提供）
        if nonce and sender_id:
            # 检查此发送者是否已使用过此随机数
            if sender_id in self.node_nonces:
                if nonce in self.node_nonces[sender_id]:
                    print(f"[!] 检测到重放攻击，发送者 {sender_id} 重复使用随机数: {nonce}")
                    return True
            else:
                self.node_nonces[sender_id] = set()
            
            # 添加随机数到缓存
            self.node_nonces[sender_id].add(nonce)
            
            # 限制每个节点的随机数缓存大小，防止内存溢出
            if len(self.node_nonces[sender_id]) > 1000:
                # 移除最早的一半随机数
                items = list(self.node_nonces[sender_id])
                for item in items[:500]:
                    self.node_nonces[sender_id].remove(item)
        
        return False

    def record_message(self, msg_id: str = None, timestamp: float = None):
        """记录消息以防止重放"""
        if msg_id:
            self.received_messages.add(msg_id)
            if timestamp:
                self.message_timestamps[msg_id] = timestamp

    def cleanup_old_messages(self):
        """清理过期的消息记录"""
        current_time = time.time()
        old_messages = [
            msg_id for msg_id, timestamp in self.message_timestamps.items()
            if current_time - timestamp > self.max_age
        ]
        
        for msg_id in old_messages:
            self.received_messages.discard(msg_id)
            self.message_timestamps.pop(msg_id, None)