"""
智能路由表管理器
实现更智能的路由表管理机制，包括节点健康检查、连接优化、动态更新等功能
"""
import asyncio
import time
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """节点类型枚举"""
    FULL = "full"          # 完整节点：存储完整区块链，参与共识
    RELAY = "relay"        # 中继节点：帮助转发消息，不存储完整区块链
    LIGHT = "light"        # 轻节点：只存储部分区块链，依赖其他节点


@dataclass
class NodeInfo:
    """节点信息数据类"""
    node_id: str
    host: str
    port: int
    pub_key: str
    public_url: Optional[str] = None
    node_type: NodeType = NodeType.LIGHT
    last_seen: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    ping_count: int = 0
    ping_success: int = 0
    connection_attempts: int = 0
    failed_attempts: int = 0
    reputation_score: float = 1.0  # 声誉分数，1.0为满分
    latency: float = float('inf')  # 延迟时间（毫秒）
    bandwidth: float = 0.0  # 带宽（Mbps）
    is_active: bool = True  # 是否活跃

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "pub_key": self.pub_key,
            "public_url": self.public_url,
            "node_type": self.node_type.value,
            "last_seen": self.last_seen,
            "last_ping": self.last_ping,
            "ping_count": self.ping_count,
            "ping_success": self.ping_success,
            "connection_attempts": self.connection_attempts,
            "failed_attempts": self.failed_attempts,
            "reputation_score": self.reputation_score,
            "latency": self.latency,
            "bandwidth": self.bandwidth,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建节点信息"""
        node_type = NodeType(data.get('node_type', 'light'))
        return cls(
            node_id=data['node_id'],
            host=data['host'],
            port=data['port'],
            pub_key=data['pub_key'],
            public_url=data.get('public_url'),
            node_type=node_type,
            last_seen=data.get('last_seen', time.time()),
            last_ping=data.get('last_ping', time.time()),
            ping_count=data.get('ping_count', 0),
            ping_success=data.get('ping_success', 0),
            connection_attempts=data.get('connection_attempts', 0),
            failed_attempts=data.get('failed_attempts', 0),
            reputation_score=data.get('reputation_score', 1.0),
            latency=data.get('latency', float('inf')),
            bandwidth=data.get('bandwidth', 0.0),
            is_active=data.get('is_active', True)
        )


class RoutingTableManager:
    """智能路由表管理器"""
    
    def __init__(self, local_node_id: str, max_nodes: int = 100, 
                 cleanup_interval: int = 300,  # 5分钟清理一次
                 health_check_interval: int = 60):  # 1分钟健康检查一次
        self.local_node_id = local_node_id
        self.max_nodes = max_nodes
        self.cleanup_interval = cleanup_interval
        self.health_check_interval = health_check_interval
        
        # 路由表: {node_id: NodeInfo}
        self.routing_table: Dict[str, NodeInfo] = {}
        
        # 统计信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "total_messages_routed": 0,
            "total_health_checks": 0
        }
        
        # 健康检查任务
        self.health_check_task = None
        self.cleanup_task = None
        
    def add_node(self, node_id: str, host: str, port: int, pub_key: str, 
                 public_url: str = None, node_type: NodeType = NodeType.LIGHT) -> bool:
        """添加节点到路由表"""
        try:
            if node_id == self.local_node_id:
                return False  # 不添加自己到路由表
                
            if node_id in self.routing_table:
                # 更新现有节点信息
                node_info = self.routing_table[node_id]
                node_info.host = host
                node_info.port = port
                node_info.pub_key = pub_key
                if public_url:
                    node_info.public_url = public_url
                node_info.node_type = node_type
                node_info.last_seen = time.time()
                node_info.is_active = True
            else:
                # 添加新节点
                if len(self.routing_table) >= self.max_nodes:
                    # 如果达到最大节点数，移除最不活跃的节点
                    self._remove_least_active_node()
                    
                self.routing_table[node_id] = NodeInfo(
                    node_id=node_id,
                    host=host,
                    port=port,
                    pub_key=pub_key,
                    public_url=public_url,
                    node_type=node_type
                )
            
            return True
        except Exception as e:
            print(f"[!] 添加节点失败: {e}")
            return False

    def remove_node(self, node_id: str) -> bool:
        """从路由表中移除节点"""
        if node_id in self.routing_table:
            del self.routing_table[node_id]
            return True
        return False

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """获取节点信息"""
        return self.routing_table.get(node_id)

    def get_all_nodes(self) -> List[NodeInfo]:
        """获取所有节点信息"""
        return list(self.routing_table.values())

    def get_active_nodes(self) -> List[NodeInfo]:
        """获取活跃节点列表"""
        return [node for node in self.routing_table.values() if node.is_active]

    def get_reliable_nodes(self, min_reputation: float = 0.5, 
                          max_latency: float = 500.0) -> List[NodeInfo]:
        """获取高可靠性节点（根据声誉和延迟）"""
        return [
            node for node in self.routing_table.values()
            if node.is_active and 
            node.reputation_score >= min_reputation and 
            node.latency <= max_latency
        ]

    def get_nodes_by_type(self, node_type: NodeType) -> List[NodeInfo]:
        """根据节点类型获取节点"""
        return [
            node for node in self.routing_table.values()
            if node.node_type == node_type
        ]

    def update_node_status(self, node_id: str, is_active: bool = None, 
                          latency: float = None, bandwidth: float = None) -> bool:
        """更新节点状态"""
        try:
            if node_id not in self.routing_table:
                return False
                
            node_info = self.routing_table[node_id]
            
            if is_active is not None:
                node_info.is_active = is_active
                node_info.last_seen = time.time()
                
            if latency is not None:
                # 更新延迟（使用移动平均）
                if node_info.latency == float('inf'):
                    node_info.latency = latency
                else:
                    # 移动平均，给新值更高权重
                    node_info.latency = 0.3 * latency + 0.7 * node_info.latency
                    
            if bandwidth is not None:
                # 更新带宽（使用移动平均）
                node_info.bandwidth = 0.3 * bandwidth + 0.7 * node_info.bandwidth
                
            return True
        except Exception as e:
            print(f"[!] 更新节点状态失败: {e}")
            return False

    def update_node_reputation(self, node_id: str, success: bool, 
                              latency: float = None) -> bool:
        """更新节点声誉分数"""
        try:
            if node_id not in self.routing_table:
                return False
                
            node_info = self.routing_table[node_id]
            node_info.ping_count += 1
            
            if success:
                node_info.ping_success += 1
                # 成功连接：提高声誉
                success_rate = node_info.ping_success / node_info.ping_count
                node_info.reputation_score = min(1.0, success_rate * 1.1)
                
                if latency is not None:
                    # 根据延迟调整声誉（延迟越低声誉越高）
                    if latency < 100:  # 优秀延迟
                        node_info.reputation_score = min(1.0, node_info.reputation_score * 1.05)
                    elif latency > 1000:  # 高延迟
                        node_info.reputation_score = max(0.1, node_info.reputation_score * 0.95)
            else:
                node_info.failed_attempts += 1
                # 失败连接：降低声誉
                success_rate = node_info.ping_success / max(1, node_info.ping_count)
                node_info.reputation_score = max(0.1, success_rate * 0.9)
                
            # 如果声誉分数过低，标记为不活跃
            if node_info.reputation_score < 0.1:
                node_info.is_active = False
                
            return True
        except Exception as e:
            print(f"[!] 更新节点声誉失败: {e}")
            return False

    def _remove_least_active_node(self):
        """移除最不活跃的节点"""
        if not self.routing_table:
            return
            
        # 按最后活跃时间排序，移除最旧的节点
        least_active_node = min(
            self.routing_table.values(),
            key=lambda x: x.last_seen
        )
        del self.routing_table[least_active_node.node_id]

    def cleanup_inactive_nodes(self):
        """清理不活跃节点"""
        current_time = time.time()
        inactive_nodes = []
        
        for node_id, node_info in self.routing_table.items():
            # 如果节点超过30分钟没有活动，标记为不活跃
            if current_time - node_info.last_seen > 1800:  # 30分钟
                inactive_nodes.append(node_id)
                
        for node_id in inactive_nodes:
            self.routing_table[node_id].is_active = False

    def get_optimal_route(self, target_node_id: str, 
                         exclude_nodes: List[str] = None) -> Optional[NodeInfo]:
        """获取到目标节点的最优路由"""
        if exclude_nodes is None:
            exclude_nodes = []
            
        # 优先选择声誉高、延迟低的活跃节点
        candidates = [
            node for node in self.routing_table.values()
            if node.node_id != target_node_id and 
            node.node_id not in exclude_nodes and 
            node.is_active
        ]
        
        if not candidates:
            return None
            
        # 按声誉分数和延迟排序（声誉高且延迟低的优先）
        candidates.sort(
            key=lambda x: (x.reputation_score, -x.latency), 
            reverse=True
        )
        
        return candidates[0] if candidates else None

    def get_best_nodes_for_broadcast(self, count: int = 5) -> List[NodeInfo]:
        """获取最适合广播的节点（声誉高、连接稳定的节点）"""
        all_nodes = self.get_active_nodes()
        
        # 按声誉分数和连接稳定性排序
        all_nodes.sort(
            key=lambda x: (x.reputation_score, x.ping_success / max(1, x.ping_count)), 
            reverse=True
        )
        
        return all_nodes[:min(count, len(all_nodes))]

    def get_routing_stats(self) -> dict:
        """获取路由表统计信息"""
        active_nodes = self.get_active_nodes()
        full_nodes = self.get_nodes_by_type(NodeType.FULL)
        relay_nodes = self.get_nodes_by_type(NodeType.RELAY)
        light_nodes = self.get_nodes_by_type(NodeType.LIGHT)
        
        return {
            "total_nodes": len(self.routing_table),
            "active_nodes": len(active_nodes),
            "full_nodes": len(full_nodes),
            "relay_nodes": len(relay_nodes),
            "light_nodes": len(light_nodes),
            "avg_reputation": sum(node.reputation_score for node in active_nodes) / max(1, len(active_nodes)),
            "avg_latency": sum(node.latency for node in active_nodes if node.latency != float('inf')) / max(1, len([n for n in active_nodes if n.latency != float('inf')])),
            "stats": self.stats
        }

    def start_health_check(self):
        """启动健康检查任务"""
        try:
            if self.health_check_task is None or self.health_check_task.done():
                self.health_check_task = asyncio.create_task(self._health_check_loop())
        except RuntimeError:
            # 在测试环境或其他没有事件循环的环境中，我们不启动健康检查
            print("[!] 未找到运行的事件循环，无法启动健康检查任务")
            pass

    def stop_health_check(self):
        """停止健康检查任务"""
        if self.health_check_task:
            self.health_check_task.cancel()

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                print("[!] 健康检查任务被取消")
                break
            except Exception as e:
                print(f"[!] 健康检查循环出错: {e}")

    async def _perform_health_check(self):
        """执行健康检查"""
        self.stats["total_health_checks"] += 1
        
        # 随机选择一些节点进行健康检查
        active_nodes = self.get_active_nodes()
        if not active_nodes:
            return
            
        # 检查最近未检查的节点
        nodes_to_check = [
            node for node in active_nodes
            if time.time() - node.last_ping > self.health_check_interval * 2
        ][:5]  # 最多检查5个节点
        
        for node in nodes_to_check:
            success = await self._ping_node(node)
            self.update_node_reputation(node.node_id, success)
            if success:
                node.last_ping = time.time()

    async def _ping_node(self, node_info: NodeInfo) -> bool:
        """尝试连接节点以测试其可用性"""
        try:
            # 尝试连接到节点并发送一个简单的ping消息
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(node_info.host, node_info.port), 
                timeout=5.0
            )
            
            # 发送一个简单的ping请求
            ping_msg = {
                "type": "PING",
                "sender_id": self.local_node_id,
                "timestamp": time.time()
            }
            
            from ..network.protocol import P2PProtocol
            await P2PProtocol.send_json(writer, ping_msg)
            
            # 等待响应
            start_time = time.time()
            response = await asyncio.wait_for(
                P2PProtocol.read_json(reader), 
                timeout=5.0
            )
            
            # 计算延迟
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 更新节点状态
            self.update_node_status(node_info.node_id, latency=latency)
            
            writer.close()
            await writer.wait_closed()
            
            return True
        except asyncio.TimeoutError:
            print(f"[!] Ping节点 {node_info.node_id} 超时")
            # 标记节点为不活跃
            self.update_node_status(node_info.node_id, is_active=False)
            return False
        except Exception as e:
            print(f"[!] Ping节点 {node_info.node_id} 失败: {e}")
            # 标记节点为不活跃
            self.update_node_status(node_info.node_id, is_active=False)
            return False

    def to_dict(self) -> dict:
        """将路由表转换为字典格式以便存储"""
        return {
            "local_node_id": self.local_node_id,
            "routing_table": {
                node_id: node_info.to_dict() 
                for node_id, node_info in self.routing_table.items()
            },
            "stats": self.stats
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典恢复路由表"""
        manager = cls(data["local_node_id"])
        manager.routing_table = {
            node_id: NodeInfo.from_dict(node_data)
            for node_id, node_data in data["routing_table"].items()
        }
        manager.stats = data.get("stats", {})
        return manager