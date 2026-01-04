"""
工业级安全节点服务器
集成X3DH密钥交换、双棘轮算法、TLS加密和Kademlia DHT
"""
import asyncio
import json
import time
from typing import Callable, Dict, Optional, List, Tuple
from ..crypto.advanced_crypto_manager import AdvancedCryptoManager
from ..network.tls_protocol import SecureProtocol
from ..network.kademlia_dht import DHTNode, Node as DHTNodeInfo
import struct
import logging


class SecureNodeServer:
    """安全节点服务器类"""
    
    def __init__(self, host: str, port: int, 
                 handler_callback: Callable,
                 enable_tls: bool = True,
                 obfuscation_method: str = 'random_padding'):
        self.host = host
        self.port = port
        self.handler_callback = handler_callback
        self.server = None
        self.crypto_manager = AdvancedCryptoManager()
        self.secure_protocol = SecureProtocol(
            self.crypto_manager, 
            use_tls=enable_tls,
            obfuscation_method=obfuscation_method
        )
        self.dht_node = None
        self.active_sessions = {}  # 存储活跃会话
        self.peer_connections = {}  # 存储对等连接
        self.connection_handlers = {}  # 存储连接处理器任务
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    async def start(self, dht_bootstrap_nodes: List[Tuple[str, int, str]] = None):
        """启动安全节点服务器"""
        print(f"[*] 启动安全节点服务器于 {self.host}:{self.port}")
        
        # 启动DHT节点
        self.dht_node = DHTNode(self.crypto_manager.get_node_id(), self.host, self.port + 1)
        if dht_bootstrap_nodes:
            await self.dht_node.join_network(dht_bootstrap_nodes)
        await self.dht_node.start_server()
        
        # 启动主服务器
        self.server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        
        print(f"[*] 安全节点服务器监听于 {self.host}:{self.port}")
        print(f"[*] 节点ID: {self.crypto_manager.get_node_id()}")
        
        # 保持服务器运行
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """处理客户端连接"""
        peer_addr = writer.get_extra_info('peername')
        print(f"[+] 新连接来自 {peer_addr}")
        
        try:
            # 处理安全会话请求
            session_id = await self.secure_protocol.handle_secure_session_request(reader, writer)
            if not session_id:
                print(f"[-] 无法建立安全会话来自 {peer_addr}")
                return
            
            print(f"[+] 安全会话建立成功，会话ID: {session_id}")
            
            # 将会话添加到活跃会话中
            self.active_sessions[session_id] = {
                'reader': reader,
                'writer': writer,
                'peer_addr': peer_addr,
                'established_time': time.time()
            }
            
            # 持续处理来自客户端的消息
            while True:
                message = await self.secure_protocol.read_secure_message(reader, session_id)
                if message is None:
                    break
                
                # 调用节点逻辑处理消息
                response = await self.handler_callback(message, writer, session_id)
                if response:
                    await self.secure_protocol.send_secure_message(writer, session_id, response)
        
        except ConnectionResetError:
            print(f"[-] 连接被重置来自 {peer_addr}")
        except asyncio.IncompleteReadError:
            print(f"[-] 连接不完整读取来自 {peer_addr}")
        except Exception as e:
            print(f"[!] 客户端处理错误: {e}")
        finally:
            # 清理会话
            for sess_id, sess_info in list(self.active_sessions.items()):
                if sess_info['reader'] == reader:
                    del self.active_sessions[sess_id]
                    break
            
            writer.close()
            await writer.wait_closed()
            print(f"[-] 连接关闭来自 {peer_addr}")
    
    def get_identity_info(self) -> Dict:
        """获取节点身份信息，用于密钥交换"""
        return self.crypto_manager.get_identity_info()
    
    async def connect_to_peer(self, host: str, port: int, peer_identity_info: Dict):
        """连接到对等节点"""
        try:
            session_id, writer, reader = await self.secure_protocol.establish_secure_session(
                host, port, peer_identity_info
            )
            
            # 存储连接信息
            self.peer_connections[session_id] = {
                'reader': reader,
                'writer': writer,
                'host': host,
                'port': port,
                'established_time': time.time()
            }
            
            print(f"[+] 成功连接到对等节点 {host}:{port}, 会话ID: {session_id}")
            
            # 启动后台任务处理来自此对等节点的消息
            handler_task = asyncio.create_task(
                self._handle_peer_messages(session_id, reader, writer)
            )
            self.connection_handlers[session_id] = handler_task
            
            return session_id
        except Exception as e:
            print(f"[!] 连接到对等节点失败 {host}:{port} - {e}")
            return None
    
    async def _handle_peer_messages(self, session_id: str, 
                                   reader: asyncio.StreamReader, 
                                   writer: asyncio.StreamWriter):
        """处理来自对等节点的消息"""
        try:
            while True:
                message = await self.secure_protocol.read_secure_message(reader, session_id)
                if message is None:
                    break
                
                # 处理消息（可以在这里实现特定的业务逻辑）
                print(f"[消息] 来自会话 {session_id}: {message[:50]}...")
                
                # 根据需要调用业务处理函数
                # response = await self.handler_callback(message, writer, session_id)
                # if response:
                #     await self.secure_protocol.send_secure_message(writer, session_id, response)
        except Exception as e:
            print(f"[!] 处理对等节点消息错误: {e}")
        finally:
            # 清理连接
            if session_id in self.peer_connections:
                del self.peer_connections[session_id]
            if session_id in self.connection_handlers:
                del self.connection_handlers[session_id]
    
    async def broadcast_message(self, message: str, exclude_session: str = None):
        """广播消息到所有连接的对等节点"""
        successful_sends = 0
        
        for session_id, conn_info in self.peer_connections.items():
            if session_id == exclude_session:
                continue
            
            try:
                writer = conn_info['writer']
                await self.secure_protocol.send_secure_message(writer, session_id, message)
                successful_sends += 1
            except Exception as e:
                print(f"[!] 广播消息到会话 {session_id} 失败: {e}")
                # 移除失败的连接
                if session_id in self.peer_connections:
                    del self.peer_connections[session_id]
        
        print(f"[广播] 成功发送到 {successful_sends} 个对等节点")
        return successful_sends
    
    def get_node_stats(self) -> Dict:
        """获取节点统计信息"""
        return {
            'node_id': self.crypto_manager.get_node_id(),
            'active_sessions': len(self.active_sessions),
            'connected_peers': len(self.peer_connections),
            'uptime': time.time() - getattr(self, '_start_time', time.time()),
            'dht_info': self.dht_node.get_local_info() if self.dht_node else None
        }
    
    def stop(self):
        """停止节点服务器"""
        if self.server:
            self.server.close()
        
        # 取消所有连接处理任务
        for task in self.connection_handlers.values():
            task.cancel()
        
        print("[停止] 节点服务器已停止")


class SecureChatNode:
    """安全聊天节点"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.node_server = SecureNodeServer(
            host, port, 
            self.handle_message,
            enable_tls=True,
            obfuscation_method='random_padding'
        )
        self.message_history = []  # 简单的消息历史
        self.known_peers = {}  # 已知的对等节点
    
    async def handle_message(self, message: str, writer: asyncio.StreamWriter, session_id: str):
        """处理传入的消息"""
        try:
            # 解析消息
            msg_data = json.loads(message)
            msg_type = msg_data.get('type', 'chat')
            
            if msg_type == 'chat':
                # 处理聊天消息
                chat_msg = msg_data.get('message', '')
                sender = msg_data.get('sender', 'unknown')
                
                print(f"[聊天] {sender}: {chat_msg}")
                self.message_history.append({
                    'sender': sender,
                    'message': chat_msg,
                    'timestamp': time.time(),
                    'session_id': session_id
                })
                
                # 广播消息到其他节点（回显消息给发送者之外的所有节点）
                await self.node_server.broadcast_message(message, exclude_session=session_id)
                
                return json.dumps({
                    'type': 'ack',
                    'status': 'received',
                    'message_id': msg_data.get('id')
                })
            
            elif msg_type == 'peer_discovery':
                # 处理节点发现请求
                return json.dumps({
                    'type': 'peer_list',
                    'peers': list(self.known_peers.values())
                })
            
            else:
                # 未知消息类型
                return json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {msg_type}'
                })
        
        except json.JSONDecodeError:
            print(f"[!] 无法解析消息: {message[:50]}...")
            return json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            })
        except Exception as e:
            print(f"[!] 处理消息错误: {e}")
            return json.dumps({
                'type': 'error',
                'message': str(e)
            })
    
    async def start_node(self, bootstrap_nodes: List[Tuple[str, int, str]] = None):
        """启动聊天节点"""
        print(f"[*] 启动安全聊天节点 {self.node_server.crypto_manager.get_node_id()}")
        
        # 保存节点启动时间
        self.node_server._start_time = time.time()
        
        # 启动节点服务器
        await self.node_server.start(bootstrap_nodes)
    
    def get_identity_info(self) -> Dict:
        """获取节点身份信息"""
        return self.node_server.get_identity_info()
    
    async def connect_to_peer_node(self, host: str, port: int, peer_identity_info: Dict):
        """连接到对等节点"""
        return await self.node_server.connect_to_peer(host, port, peer_identity_info)
    
    def get_stats(self) -> Dict:
        """获取节点统计信息"""
        stats = self.node_server.get_node_stats()
        stats['message_count'] = len(self.message_history)
        return stats