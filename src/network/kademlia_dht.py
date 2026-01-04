"""
Kademlia DHT 实现
用于去中心化节点发现和信息存储
"""
import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import json
import struct


@dataclass
class Node:
    """DHT节点信息"""
    node_id: str
    ip: str
    port: int
    last_seen: float = 0.0
    
    def __post_init__(self):
        if not self.last_seen:
            self.last_seen = time.time()
    
    def get_address(self) -> Tuple[str, int]:
        return (self.ip, self.port)
    
    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'ip': self.ip,
            'port': self.port,
            'last_seen': self.last_seen
        }


class KBucket:
    """K桶，存储相近的节点"""
    def __init__(self, start: int, end: int, k: int = 20):
        self.start = start
        self.end = end
        self.k = k  # 桶的最大容量
        self.nodes: List[Node] = []
        self.last_accessed = time.time()
    
    def add_node(self, node: Node) -> bool:
        """添加节点到桶"""
        if node in self.nodes:
            # 更新最后访问时间
            for i, n in enumerate(self.nodes):
                if n.node_id == node.node_id:
                    self.nodes[i] = node
                    break
            return True
        
        if len(self.nodes) < self.k:
            self.nodes.append(node)
            return True
        
        # 桶已满，需要处理
        # 检查桶中是否有长时间未响应的节点
        for i, n in enumerate(self.nodes):
            if time.time() - n.last_seen > 900:  # 15分钟未响应
                self.nodes[i] = node
                return True
        
        return False  # 桶满且没有过期节点
    
    def remove_node(self, node_id: str):
        """从桶中移除节点"""
        self.nodes = [n for n in self.nodes if n.node_id != node_id]
    
    def get_nodes(self) -> List[Node]:
        """获取桶中所有节点"""
        return self.nodes[:]
    
    def is_in_range(self, node_id: str) -> bool:
        """检查节点ID是否在桶范围内"""
        node_id_int = int(node_id, 16)
        return self.start <= node_id_int <= self.end


class KademliaDHT:
    """Kademlia DHT 主类"""
    
    def __init__(self, node_id: str, ip: str, port: int, k: int = 20, bucket_size: int = 8):
        self.node_id = node_id
        self.local_node = Node(node_id, ip, port)
        self.k = k
        self.bucket_size = bucket_size
        self.buckets: List[KBucket] = []
        self.node_cache: Dict[str, Node] = {}  # 节点缓存
        self.data_store: Dict[str, any] = {}  # 本地数据存储
        self.rpc_timeout = 5.0
        
        # 初始化桶
        self._init_buckets()
        
        # 添加自己到桶中
        self.add_node(self.local_node)
    
    def _init_buckets(self):
        """初始化K桶"""
        # 创建256个桶，对应256位节点ID的每一位
        for i in range(256):
            start = 1 << i if i > 0 else 0
            end = (1 << (i + 1)) - 1
            self.buckets.append(KBucket(start, end, self.k))
    
    def _distance(self, node_id1: str, node_id2: str) -> int:
        """计算两个节点ID之间的XOR距离"""
        id1 = int(node_id1, 16)
        id2 = int(node_id2, 16)
        return id1 ^ id2
    
    def _get_bucket_index(self, node_id: str) -> int:
        """获取节点所属桶的索引"""
        distance = self._distance(self.node_id, node_id)
        if distance == 0:
            return 255
        return distance.bit_length() - 1
    
    def _hash(self, key: str) -> str:
        """生成SHA-256哈希作为节点ID"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def add_node(self, node: Node):
        """添加节点到DHT"""
        if node.node_id == self.node_id:
            return  # 不添加自己
        
        bucket_idx = self._get_bucket_index(node.node_id)
        if 0 <= bucket_idx < len(self.buckets):
            self.buckets[bucket_idx].add_node(node)
        
        # 更新节点缓存
        self.node_cache[node.node_id] = node
    
    def remove_node(self, node_id: str):
        """从DHT中移除节点"""
        bucket_idx = self._get_bucket_index(node_id)
        if 0 <= bucket_idx < len(self.buckets):
            self.buckets[bucket_idx].remove_node(node_id)
        
        # 从缓存中移除
        if node_id in self.node_cache:
            del self.node_cache[node_id]
    
    def find_node(self, target_id: str) -> List[Node]:
        """查找最接近目标ID的k个节点"""
        # 计算与目标的距离
        target_distance = self._distance(self.node_id, target_id)
        
        # 从最近的桶开始搜索
        bucket_idx = self._get_bucket_index(target_id)
        nodes = []
        
        # 搜索附近的桶
        for i in range(max(0, bucket_idx - 2), min(len(self.buckets), bucket_idx + 3)):
            nodes.extend(self.buckets[i].get_nodes())
        
        # 按距离排序并返回前k个
        nodes.sort(key=lambda n: self._distance(target_id, n.node_id))
        return nodes[:self.k]
    
    def get_peers(self, topic: str) -> List[Node]:
        """获取特定主题的对等节点"""
        # 在DHT中查找与主题相关的节点
        topic_hash = self._hash(topic)
        return self.find_node(topic_hash)
    
    def store(self, key: str, value: any):
        """在本地存储键值对"""
        self.data_store[key] = value
    
    def get(self, key: str) -> any:
        """从本地获取键值对"""
        return self.data_store.get(key)
    
    def ping(self, node: Node) -> bool:
        """检查节点是否在线（模拟）"""
        # 在实际实现中，这里会发送ping消息
        # 现在我们简单地认为节点在线
        return True
    
    def get_closest_nodes(self, target_id: str) -> List[Node]:
        """获取最接近目标ID的节点"""
        nodes = []
        for bucket in self.buckets:
            nodes.extend(bucket.get_nodes())
        
        # 按距离排序
        nodes.sort(key=lambda n: self._distance(target_id, n.node_id))
        return nodes[:self.k]
    
    async def find_node_async(self, target_id: str, peers: List[Node]) -> List[Node]:
        """异步查找节点"""
        # 在实际实现中，这里会向peers发送FIND_NODE请求
        # 模拟异步查找过程
        tasks = []
        for peer in peers[:5]:  # 只查询前5个节点
            tasks.append(self._query_node(peer, target_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_nodes = []
        for result in results:
            if isinstance(result, list):
                all_nodes.extend(result)
        
        # 去重并按距离排序
        unique_nodes = {}
        for node in all_nodes:
            unique_nodes[node.node_id] = node
        
        sorted_nodes = sorted(
            unique_nodes.values(),
            key=lambda n: self._distance(target_id, n.node_id)
        )
        
        return sorted_nodes[:self.k]
    
    async def _query_node(self, node: Node, target_id: str) -> List[Node]:
        """向节点查询"""
        # 模拟网络查询
        # 在实际实现中，这里会发送网络请求
        await asyncio.sleep(0.1)  # 模拟网络延迟
        
        # 返回一些模拟节点
        # 在实际实现中，这里会从目标节点获取其知道的节点列表
        return self.find_node(target_id)


class DHTNode:
    """DHT网络节点，处理DHT协议消息"""
    
    def __init__(self, node_id: str, ip: str, port: int):
        self.dht = KademliaDHT(node_id, ip, port)
        self.ip = ip
        self.port = port
        self.server = None
    
    async def start_server(self):
        """启动DHT服务器"""
        self.server = await asyncio.start_server(
            self.handle_connection, self.ip, self.port
        )
        print(f"[DHT] DHT服务器启动在 {self.ip}:{self.port}")
    
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """处理DHT连接"""
        try:
            # 读取请求
            length_bytes = await reader.readexactly(4)
            length = struct.unpack('>I', length_bytes)[0]
            data = await reader.readexactly(length)
            
            request = json.loads(data.decode())
            response = await self.process_request(request)
            
            # 发送响应
            response_data = json.dumps(response).encode()
            writer.write(struct.pack('>I', len(response_data)))
            writer.write(response_data)
            await writer.drain()
        except Exception as e:
            print(f"[DHT] 处理DHT连接错误: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def process_request(self, request: Dict) -> Dict:
        """处理DHT请求"""
        request_type = request.get('type')
        if request_type == 'find_node':
            target_id = request.get('target_id')
            nodes = self.dht.find_node(target_id)
            return {
                'type': 'find_node_response',
                'nodes': [node.to_dict() for node in nodes]
            }
        elif request_type == 'ping':
            return {
                'type': 'pong',
                'node_id': self.dht.local_node.node_id
            }
        elif request_type == 'store':
            key = request.get('key')
            value = request.get('value')
            self.dht.store(key, value)
            return {
                'type': 'store_response',
                'success': True
            }
        elif request_type == 'find_value':
            key = request.get('key')
            value = self.dht.get(key)
            if value is not None:
                return {
                    'type': 'find_value_response',
                    'key': key,
                    'value': value,
                    'found': True
                }
            else:
                # 返回最接近的节点
                nodes = self.dht.find_node(key)
                return {
                    'type': 'find_value_response',
                    'key': key,
                    'nodes': [node.to_dict() for node in nodes],
                    'found': False
                }
        else:
            return {
                'type': 'error',
                'message': 'Unknown request type'
            }
    
    def add_bootstrap_node(self, ip: str, port: int, node_id: str):
        """添加引导节点"""
        bootstrap_node = Node(node_id, ip, port)
        self.dht.add_node(bootstrap_node)
    
    async def join_network(self, bootstrap_nodes: List[Tuple[str, int, str]]):
        """加入DHT网络"""
        for ip, port, node_id in bootstrap_nodes:
            self.add_bootstrap_node(ip, port, node_id)
        
        # 向引导节点发送find_node请求以发现更多节点
        for ip, port, node_id in bootstrap_nodes[:3]:  # 只对前3个引导节点执行
            try:
                await self._find_and_connect_to_nodes(ip, port, self.dht.node_id)
            except Exception as e:
                print(f"[DHT] 连接引导节点失败 {ip}:{port} - {e}")
    
    async def _find_and_connect_to_nodes(self, ip: str, port: int, target_id: str):
        """查找并连接到节点"""
        # 这里需要实现实际的网络连接逻辑
        # 为了简化，我们跳过这部分
        pass
    
    def get_local_info(self) -> Dict:
        """获取本地节点信息"""
        return {
            'node_id': self.dht.local_node.node_id,
            'ip': self.dht.local_node.ip,
            'port': self.dht.local_node.port
        }