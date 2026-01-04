"""
激励机制模块
用于鼓励节点贡献资源和维护网络
"""
import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid


class NodeType(Enum):
    """节点类型枚举"""
    FULL = "full"          # 完整节点：存储完整区块链，参与共识
    RELAY = "relay"        # 中继节点：转发消息，存储部分数据
    LIGHT = "light"        # 轻节点：仅进行基本通信


@dataclass
class NodeMetrics:
    """节点指标数据"""
    node_id: str
    uptime: float  # 在线时间（秒）
    bandwidth_provided: int  # 提供的带宽（字节）
    storage_provided: int  # 提供的存储（字节）
    messages_forwarded: int  # 转发的消息数
    blocks_validated: int  # 验证的区块数
    last_updated: float
    reputation_score: float = 0.0  # 声誉分数


class RewardPool:
    """奖励池管理"""
    def __init__(self, initial_supply: int = 1000000):
        self.total_supply = initial_supply
        self.remaining_tokens = initial_supply
        self.distributed_tokens = 0
        self.reward_history: List[Dict] = []

    def distribute_reward(self, node_id: str, amount: int, reason: str) -> bool:
        """分发奖励"""
        if amount <= 0 or amount > self.remaining_tokens:
            return False

        reward = {
            "node_id": node_id,
            "amount": amount,
            "reason": reason,
            "timestamp": time.time(),
            "id": str(uuid.uuid4())
        }

        self.reward_history.append(reward)
        self.distributed_tokens += amount
        self.remaining_tokens -= amount

        return True

    def get_reward_stats(self) -> Dict:
        """获取奖励统计"""
        return {
            "total_supply": self.total_supply,
            "distributed_tokens": self.distributed_tokens,
            "remaining_tokens": self.remaining_tokens,
            "total_rewards": len(self.reward_history)
        }


class IncentiveMechanism:
    """激励机制主类"""
    def __init__(self, reward_pool: RewardPool = None):
        self.reward_pool = reward_pool or RewardPool()
        self.node_metrics: Dict[str, NodeMetrics] = {}
        self.node_types: Dict[str, NodeType] = {}
        self.node_balances: Dict[str, int] = {}
        self.balances_history: Dict[str, List[Tuple[float, int]]] = {}
        self.running = False

    def register_node(self, node_id: str, node_type: NodeType = NodeType.LIGHT):
        """注册节点"""
        self.node_types[node_id] = node_type
        self.node_balances[node_id] = 0
        self.balances_history[node_id] = [(time.time(), 0)]
        self.node_metrics[node_id] = NodeMetrics(
            node_id=node_id,
            uptime=0,
            bandwidth_provided=0,
            storage_provided=0,
            messages_forwarded=0,
            blocks_validated=0,
            last_updated=time.time()
        )

    def update_node_metrics(self, node_id: str, **kwargs):
        """更新节点指标"""
        if node_id not in self.node_metrics:
            self.register_node(node_id)
        
        metrics = self.node_metrics[node_id]
        
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                if isinstance(getattr(metrics, key), (int, float)):
                    setattr(metrics, key, getattr(metrics, key) + value)
                else:
                    setattr(metrics, key, value)
        
        metrics.last_updated = time.time()
        self.calculate_reputation_score(node_id)

    def calculate_reputation_score(self, node_id: str):
        """计算声誉分数"""
        if node_id not in self.node_metrics:
            return 0.0

        metrics = self.node_metrics[node_id]
        
        # 计算声誉分数（基于多个因素）
        uptime_score = min(metrics.uptime / 86400, 10)  # 最多10分，基于天数
        bandwidth_score = min(metrics.bandwidth_provided / 1024 / 1024 / 100, 5)  # 基于MB
        storage_score = min(metrics.storage_provided / 1024 / 1024 / 100, 5)  # 基于MB
        message_score = min(metrics.messages_forwarded / 1000, 5)  # 基于千条消息
        validation_score = min(metrics.blocks_validated / 100, 10)  # 基于百个区块

        # 综合声誉分数
        reputation = (
            uptime_score * 0.3 +
            bandwidth_score * 0.2 +
            storage_score * 0.2 +
            message_score * 0.15 +
            validation_score * 0.15
        )
        
        # 限制在0-100范围内
        reputation = max(0, min(100, reputation))
        metrics.reputation_score = reputation
        
        return reputation

    def calculate_reward(self, node_id: str) -> int:
        """根据节点贡献计算奖励"""
        if node_id not in self.node_metrics:
            return 0

        metrics = self.node_metrics[node_id]
        node_type = self.node_types.get(node_id, NodeType.LIGHT)

        # 基础奖励
        base_reward = 10

        # 根据节点类型调整
        type_multiplier = {
            NodeType.FULL: 3.0,
            NodeType.RELAY: 2.0,
            NodeType.LIGHT: 1.0
        }
        reward = base_reward * type_multiplier[node_type]

        # 根据声誉分数调整
        reward *= (metrics.reputation_score / 50)  # 声誉50分作为基准

        # 根据具体贡献调整
        if node_type in [NodeType.FULL, NodeType.RELAY]:
            # 对于完整节点和中继节点，根据带宽和存储贡献奖励
            reward += metrics.bandwidth_provided / 1024 / 1024 * 0.01  # 每MB 0.01奖励
            reward += metrics.storage_provided / 1024 / 1024 * 0.02  # 每MB 0.02奖励

        if node_type in [NodeType.FULL]:
            # 对于完整节点，根据验证区块数奖励
            reward += metrics.blocks_validated * 0.5

        # 对于中继节点，根据转发消息数奖励
        if node_type == NodeType.RELAY:
            reward += metrics.messages_forwarded * 0.05

        # 根据在线时间给予奖励（长期在线节点获得更多奖励）
        uptime_bonus = min(metrics.uptime / 3600, 24) * 0.1  # 每小时在线时间给予0.1奖励，最多2.4
        reward += uptime_bonus

        # 根据声誉分数给予额外奖励（声誉高的节点获得更多奖励）
        reputation_bonus = (metrics.reputation_score / 100) * 2  # 最多2个奖励
        reward += reputation_bonus

        return int(reward)

    def distribute_rewards(self):
        """分发奖励给所有节点"""
        total_reward = 0
        reward_details = []

        for node_id in self.node_metrics.keys():
            reward = self.calculate_reward(node_id)
            if reward > 0 and self.reward_pool.distribute_reward(node_id, reward, "periodic_distribute"):
                self.node_balances[node_id] += reward
                self.balances_history[node_id].append((time.time(), self.node_balances[node_id]))
                total_reward += reward
                reward_details.append((node_id, reward))

        return reward_details, total_reward

    def get_node_info(self, node_id: str) -> Optional[Dict]:
        """获取节点信息"""
        if node_id not in self.node_metrics:
            return None

        metrics = self.node_metrics[node_id]
        return {
            "node_id": node_id,
            "node_type": self.node_types[node_id].value,
            "balance": self.node_balances[node_id],
            "reputation_score": metrics.reputation_score,
            "uptime": metrics.uptime,
            "bandwidth_provided": metrics.bandwidth_provided,
            "storage_provided": metrics.storage_provided,
            "messages_forwarded": metrics.messages_forwarded,
            "blocks_validated": metrics.blocks_validated
        }

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """获取排行榜"""
        nodes_info = []
        for node_id in self.node_metrics.keys():
            info = self.get_node_info(node_id)
            if info:
                nodes_info.append(info)

        # 按声誉分数排序
        nodes_info.sort(key=lambda x: x['reputation_score'], reverse=True)
        return nodes_info[:limit]

    def get_reward_history(self, node_id: str = None) -> List[Dict]:
        """获取奖励历史"""
        if node_id:
            return [r for r in self.reward_pool.reward_history if r['node_id'] == node_id]
        return self.reward_pool.reward_history.copy()

    def stake_tokens(self, node_id: str, amount: int) -> bool:
        """节点质押代币"""
        if node_id not in self.node_balances or self.node_balances[node_id] < amount or amount <= 0:
            return False

        self.node_balances[node_id] -= amount
        # 在实际实现中，这里会将代币锁定到质押池中
        return True

    def start_reward_distribution(self, interval: int = 3600):  # 默认每小时分发一次
        """开始定期奖励分发"""
        self.running = True
        asyncio.create_task(self._reward_distribution_loop(interval))

    async def _reward_distribution_loop(self, interval: int):
        """奖励分发循环"""
        while self.running:
            try:
                await asyncio.sleep(interval)
                if self.running:
                    details, total = self.distribute_rewards()
                    print(f"[💰] 奖励分发完成: 总计 {total} 代币分发给 {len(details)} 个节点")
            except Exception as e:
                print(f"[!] 奖励分发循环出错: {e}")

    def stop_reward_distribution(self):
        """停止奖励分发"""
        self.running = False