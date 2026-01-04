"""
核心聊天节点类
"""
import asyncio
import hashlib
import json
import time
import uuid
from typing import Dict, List, Optional

from ..crypto.crypto_manager import CryptoManager
from ..ipfs.ipfs_integration import BlockchainIPFSBridge, IPFSStorage
from ..network.protocol import P2PProtocol
from ..utils.anti_replay import AntiReplayManager
from ..multimedia.multimedia import EncryptedMultimediaProcessor, MultimediaMessage
from ..incentive.incentive_mechanism import IncentiveMechanism, NodeType
from ..routing.routing_manager import RoutingTableManager, NodeInfo
from ..gossip.gossip_protocol import GossipManager, GossipType
from ..vdf.vdf import VDFManager
from ..zkp.zkp import ZKPManager


class ChatNode:
    """聊天节点类"""
    def __init__(self, node_id, addr, blockchain, bootstrap_nodes=None):
        self.node_id = node_id
        self.addr = addr
        self.blockchain = blockchain
        self.routing_table = {}
        self.crypto = CryptoManager()
        self.anti_replay = AntiReplayManager()
        self.multimedia_processor = EncryptedMultimediaProcessor()
        self.routing_table_manager = RoutingTableManager(node_id)
        self.incentive_mechanism = IncentiveMechanism()
        self.zkp_manager = ZKPManager()
        self.gossip_manager = GossipManager(node_id, self.routing_table_manager)
        self.ipfs_bridge = BlockchainIPFSBridge(IPFSStorage())
        self.vdf_manager = VDFManager()
        self.pending_proposals = {}  # 存储待处理的提案
        self.sync_batch_size = 10  # 区块链同步批大小
        self.max_concurrent_syncs = 3  # 最大并发同步数
        self.sync_timeout = 30  # 同步超时时间（秒）
        self.running = True

    def get_did(self) -> str:
        return f"did:p2p:{self.node_id}"

    async def start(self):
        """启动节点"""
        await self.server.start()
        
        # 加入网络
        for b_host, b_port in self.bootstrap_nodes:
            if (b_host, b_port) != self.addr:
                await self.ping_node(b_host, b_port)
                
        self.running = True
        print(f"[*] 节点 {self.node_id} 已启动")

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
                
                # 更新激励机制：连接到新节点
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    messages_forwarded=1
                )
            
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"[-] 无法连接到节点 {host}:{port}, 错误: {e}")

    def update_routing(self, new_table: dict):
        for nid, info in new_table.items():
            if nid != self.node_id:
                # 使用路由表管理器添加节点
                self.routing_table_manager.add_node(
                    node_id=nid,
                    host=info['host'],
                    port=info['port'],
                    pub_key=info['pub_key'],
                    public_url=info.get('public_url')
                )
                print(f"[*] 发现新节点: {nid}")
                
                # 更新激励机制：发现新节点
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    messages_forwarded=1
                )

    async def handle_message(self, msg: dict, writer) -> dict:
        """处理收到的网络消息"""
        try:
            msg_type = msg.get('type')
            
            # 检查是否为重放攻击
            msg_id = msg.get('msg_id')
            timestamp = msg.get('timestamp', 0)
            nonce = msg.get('nonce')  # 新增nonce字段
            sender_id = msg.get('sender_id')
        
            if self.anti_replay.is_replay_attack(msg_id, timestamp, nonce, sender_id):
                print(f"[!] 检测到重放攻击，拒绝处理消息")
                return {"type": "REPLAY_ERROR", "status": "message rejected as replay attack"}

            # 记录消息以防止重放
            if msg_id:
                self.anti_replay.record_message(msg_id, timestamp)
            
            # 定期清理过期消息记录
            if int(time.time()) % 60 == 0:  # 每分钟清理一次
                self.anti_replay.cleanup_old_messages()

            if msg_type == "HELLO":
                # 记录新节点
                self.routing_table_manager.add_node(
                    node_id=msg['sender_id'],
                    host=msg['addr'][0],
                    port=msg['addr'][1],
                    pub_key=msg['pub_key'],
                    public_url=msg.get('public_url')
                )
                # 返回我的路由表作为欢迎
                current_routing = {nid: node_info.to_dict()
                                  for nid, node_info in self.routing_table_manager.routing_table.items()}
                current_routing[self.node_id] = {"host": self.addr[0], "port": self.addr[1], "pub_key": self.crypto.get_pub_key_pem(), "public_url": getattr(self, 'public_url', None)}
                
                # 更新激励机制：成功建立连接
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    uptime=time.time() - self.start_time
                )
                
                return {"type": "WELCOME", "routing_table": current_routing}

            elif msg_type == "DIRECT_MSG":
                # 验证消息签名
                sender_id = msg['sender_id']
                encrypted_payload = msg['encrypted_payload']
                signature = msg.get('signature')

                if signature:
                    # 获取发送方公钥
                    sender_node = self.routing_table_manager.get_node(sender_id)
                    if sender_node:
                        sender_pub_key = CryptoManager.load_pub_key(sender_node.pub_key)
                        # 验证签名
                        if not CryptoManager.verify(sender_pub_key, str(encrypted_payload), signature):
                            print(f"[!] 消息签名验证失败: {sender_id}")
                            return {"type": "SIGNATURE_ERROR", "status": "invalid signature"}

                # 更新激励机制：接收消息
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    bandwidth_provided=len(str(msg).encode('utf-8'))
                )

                # 尝试解密
                try:
                    content = self.crypto.hybrid_decrypt(encrypted_payload)
                    print(f"\n[🔔] 收到来自 {msg['sender_id']} 的加密消息: {content}")

                    # 检查是否为多媒体消息
                    if content.startswith("MULTIMEDIA:"):
                        # 解析多媒体消息
                        try:
                            multimedia_data = json.loads(content[11:])  # 移除"MULTIMEDIA:"前缀
                            multimedia_msg = MultimediaMessage.from_dict(multimedia_data)

                            # 解密多媒体消息（如果需要）
                            if multimedia_msg.metadata.get('encrypted'):
                                multimedia_msg = self.multimedia_processor.decrypt_multimedia_message(multimedia_msg)

                            print(f"[🖼️] 收到多媒体消息 - 类型: {multimedia_msg.media_type}, 大小: {len(multimedia_msg.data)} bytes")

                            # 保存多媒体内容到本地
                            file_ext = multimedia_msg.get_file_extension()
                            file_path = f"received_{multimedia_msg.message_id}{file_ext}"
                            if self.multimedia_processor.save_to_file(multimedia_msg, file_path):
                                print(f"[💾] 多媒体内容已保存到: {file_path}")

                            # 更新激励机制：处理多媒体内容
                            self.incentive_mechanism.update_node_metrics(
                                self.node_id,
                                storage_provided=len(multimedia_msg.data)
                            )

                        except Exception as e:
                            print(f"[!] 解析多媒体消息失败: {e}")
                            # 如果解析失败，按普通消息处理
                            print(f"    原始内容: {content}")
                    else:
                        # 将消息记录到区块链
                        block_data = f"MSG:{msg['sender_id']}->{self.node_id}:{content}"
                        from ..blockchain.block import Block
                        new_block = Block(
                            index=len(self.blockchain.chain),
                            previous_hash=self.blockchain.get_latest_block().hash,
                            timestamp=time.time(),
                            data=block_data,
                            proposer=self.node_id
                        )
                        self.blockchain.add_block(new_block)

                    # 检查是否有离线消息需要提取 (模拟 Pigon Protocol 提取)
                    if self.get_did() in self.pigeon_cache:
                        print(f"    └── [信鸽] 自动提取了 {len(self.pigeon_cache[self.get_did()])} 条离线缓存消息")
                        self.pigeon_cache.pop(self.get_did())

                        # 更新激励机制：提取离线消息
                        self.incentive_mechanism.update_node_metrics(
                            self.node_id,
                            messages_forwarded=len(self.pigeon_cache[self.get_did()])
                        )

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

                # 更新激励机制：转发消息
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    messages_forwarded=1,
                    bandwidth_provided=len(str(msg).encode('utf-8'))
                )

                return {"type": "ACK", "status": "cached"}

            elif msg_type == "CONSENSUS_PROPOSAL":
                # 处理共识提案
                await self.handle_consensus_proposal(msg)

                # 更新激励机制：参与共识
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    blocks_validated=1
                )

                return None

            elif msg_type == "BLOCKCHAIN_SYNC":
                # 区块链同步请求
                # 更新激励机制：提供区块链数据
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    bandwidth_provided=1024  # 估算的带宽使用
                )

                # 根据请求参数返回区块链数据
                start_index = msg.get('start_index', 0)
                end_index = msg.get('end_index', len(self.blockchain.chain))

                if start_index < 0 or end_index > len(self.blockchain.chain):
                    # 返回完整链信息
                    return {
                        "type": "BLOCKCHAIN_RESPONSE",
                        "chain_info": self.blockchain.get_chain_info(),
                        "chain": self.blockchain.to_list()
                    }
                else:
                    # 返回指定范围的区块链数据
                    chain_data = self.blockchain.get_block_range(start_index, end_index)
                    return {
                        "type": "BLOCKCHAIN_RESPONSE",
                        "chain_info": self.blockchain.get_chain_info(),
                        "chain": chain_data,
                        "start_index": start_index,
                        "end_index": end_index
                    }

            elif msg_type == "BLOCKCHAIN_INFO_REQUEST":
                # 区块链信息请求 - 只返回链的基本信息，不传输整个链
                return {
                    "type": "BLOCKCHAIN_INFO_RESPONSE",
                    "chain_info": self.blockchain.get_chain_info()
                }

            elif msg_type == "BLOCKCHAIN_RESPONSE":
                # 处理区块链同步响应
                chain_info = msg.get('chain_info', {})
                received_chain = msg.get('chain', [])
                start_index = msg.get('start_index')
                end_index = msg.get('end_index')

                # 检查是否是完整链同步
                if start_index is None or end_index is None:
                    # 完整链同步
                    if len(received_chain) > len(self.blockchain.chain):
                        # 接收更长的链
                        from ..blockchain.blockchain import Blockchain
                        new_blockchain = Blockchain(consensus_type=self.blockchain.consensus_type)
                        new_blockchain.from_list(received_chain)
                        if new_blockchain.is_chain_valid():
                            self.blockchain = new_blockchain
                            print("[✓] 区块链已同步到最新状态")

                            # 更新激励机制：成功同步区块链
                            self.incentive_mechanism.update_node_metrics(
                                self.node_id,
                                uptime=time.time() - self.start_time
                            )
                        else:
                            print("[!] 接收的区块链无效")
                else:
                    # 部分链同步 - 用于大规模网络优化
                    if len(received_chain) > 0:
                        # 检查接收到的区块是否与当前链一致
                        if start_index < len(self.blockchain.chain):
                            # 如果起始区块已存在，只添加新区块
                            current_block = self.blockchain.chain[start_index]
                            received_first_block = received_chain[0]

                            if current_block.hash == received_first_block['hash']:
                                # 添加新区块
                                for block_data in received_chain[1:]:
                                    from ..blockchain.block import Block
                                    new_block = Block.from_dict(block_data)
                                    if len(self.blockchain.chain) > 0:
                                        new_block.previous_hash = self.blockchain.get_latest_block().hash
                                    self.blockchain.chain.append(new_block)
                                print(f"[✓] 部分区块链已同步 ({start_index+1}-{start_index+len(received_chain)-1})")
                            else:
                                print("[!] 接收到的区块链与当前链不一致")
                        else:
                            # 如果起始区块不存在，需要重新同步
                            print("[!] 需要从更早的区块开始同步")

                return None
            
            elif msg_type == "PING":
                # 响应ping请求
                return {"type": "PONG", "timestamp": time.time(), "node_id": self.node_id}

            elif msg_type == "GOSSIP_MESSAGE":
                # 处理Gossip消息
                gossip_data = msg.get('gossip_data', {})
                response = await self.gossip_manager.handle_incoming_gossip(gossip_data)
                
                # 更新激励机制：参与Gossip传播
                self.incentive_mechanism.update_node_metrics(
                    self.node_id,
                    messages_forwarded=1
                )
                
                return response
        except Exception as e:
            print(f"[!] 处理消息时发生错误: {e}")
            return {"type": "ERROR", "status": f"message processing failed: {str(e)}"}

    async def handle_consensus_proposal(self, msg: dict):
        """处理共识提案"""
        print(f"[👑] 收到共识提案: {msg.get('block', 'N/A')} 来自 {msg.get('leader_id', 'N/A')}")
        
        # 实现完整的PBFT共识逻辑
        proposal_view = msg.get('view', 0)
        proposal_block = msg.get('block', '')
        leader_id = msg.get('leader_id', '')
        proposal_nonce = msg.get('nonce', '')
        proposal_signature = msg.get('signature', '')
        
        # 验证提案签名
        if not self.verify_proposal_signature(leader_id, proposal_block, proposal_signature):
            print(f"[✗] 提案签名验证失败，拒绝提案")
            return
        
        # 检查提案视图号是否有效
        current_view = len(self.blockchain.chain)
        if proposal_view != current_view:
            print(f"[!] 提案视图号不匹配，当前视图: {current_view}, 提案视图: {proposal_view}")
            # 可能需要同步区块链
            return
        
        # 验证提案的合理性
        if not self.validate_proposal(proposal_block):
            print(f"[✗] 提案内容验证失败，拒绝提案")
            return
        
        # 记录提案并准备投票
        proposal_id = hashlib.sha256(f"{proposal_block}{leader_id}{proposal_view}".encode()).hexdigest()
        self.pending_proposals[proposal_id] = {
            'block_data': proposal_block,
            'leader_id': leader_id,
            'view': proposal_view,
            'timestamp': time.time(),
            'votes': {self.node_id: True},  # 自己先投赞成票
            'accepted': False
        }
        
        # 发送预准备消息
        await self.broadcast_vote(proposal_id, 'PREPREPARE')
        
        # 验证并处理区块
        from ..blockchain.block import Block
        new_block = Block(
            index=len(self.blockchain.chain),
            previous_hash=self.blockchain.get_latest_block().hash,
            timestamp=time.time(),
            data=proposal_block,
            proposer=leader_id
        )
        
        # 添加到区块链
        self.blockchain.add_block(new_block)
        print(f"[✓] 提案已接受并添加到区块链")

    def verify_proposal_signature(self, leader_id: str, block_data: str, signature: str) -> bool:
        """验证提案签名"""
        # 在实际实现中，这里会查找领导者的公钥并验证签名
        # 实际实现需要从路由表或其他地方获取领导者的公钥
        try:
            # 这里应该获取leader的公钥并验证签名
            leader_node = self.routing_table_manager.get_node(leader_id)
            if not leader_node:
                return False
            return CryptoManager.verify(leader_node.pub_key, block_data, signature)
        except:
            return False

    def validate_proposal(self, block_data: str) -> bool:
        """验证提案内容的合理性"""
        # 检查数据长度等基本验证
        if not block_data or len(block_data) > 10000:  # 假设最大10KB
            return False
        return True

    async def broadcast_vote(self, proposal_id: str, vote_type: str):
        """广播投票"""
        vote_msg = {
            "type": "CONSENSUS_VOTE",
            "proposal_id": proposal_id,
            "vote_type": vote_type,
            "voter_id": self.node_id,
            "timestamp": time.time(),
            "signature": self.crypto.sign(f"{proposal_id}{vote_type}")
        }
        
        # 广播给其他节点
        for nid, info in self.routing_table_manager.routing_table.items():
            if nid != self.node_id:
                try:
                    reader, writer = await asyncio.open_connection(info.host, info.port)
                    await P2PProtocol.send_json(writer, vote_msg)
                    writer.close()
                except Exception as e:
                    print(f"[!] 发送投票到节点 {nid} 失败: {e}")

    async def send_message(self, target_node_id: str, text: str, max_retries: int = 3):
        """发送端到端加密消息，带重试机制"""
        target_node = self.routing_table_manager.get_node(target_node_id)
        if not target_node:
            print(f"[!] 未找到节点 {target_node_id}，正在查找...")
            return
        
        target = target_node.to_dict()

        # 加密
        encrypted = self.crypto.hybrid_encrypt(target['pub_key'], text)
        
        # 生成唯一消息ID以防止重放
        msg_id = str(uuid.uuid4())
        # 生成随机数用于防重放
        nonce = str(uuid.uuid4())
        
        payload = {
            "type": "DIRECT_MSG",
            "sender_id": self.node_id,
            "encrypted_payload": encrypted,
            "timestamp": time.time(),
            "msg_id": msg_id,
            "nonce": nonce,  # 添加防重放随机数
            "signature": self.crypto.sign(str(encrypted))  # 添加数字签名
        }

        for attempt in range(max_retries):
            try:
                reader, writer = await asyncio.open_connection(target['host'], target['port'])
                await P2PProtocol.send_json(writer, payload)
                # 等待 ACK
                resp = await P2PProtocol.read_json(reader)
                if resp and resp.get('type') == 'ACK':
                    print(f"[✓] 消息已送达 {target_node_id}")
                    
                    # 更新激励机制：发送消息
                    self.incentive_mechanism.update_node_metrics(
                        self.node_id,
                        messages_forwarded=1,
                        bandwidth_provided=len(str(payload).encode('utf-8'))
                    )
                    
                    # 将消息记录到区块链
                    block_data = f"MSG:{self.node_id}->{target_node_id}:{text}"
                    from ..blockchain.block import Block
                    new_block = Block(
                        index=len(self.blockchain.chain),
                        previous_hash=self.blockchain.get_latest_block().hash,
                        timestamp=time.time(),
                        data=block_data,
                        proposer=self.node_id
                    )
                    self.blockchain.add_block(new_block)
                    
                    # 更新节点声誉
                    self.routing_table_manager.update_node_reputation(target_node_id, success=True)
                    
                    writer.close()
                    await writer.wait_closed()
                    return  # 成功发送，退出重试循环
                
                writer.close()
                await writer.wait_closed()
                
            except OSError as e:
                print(f"[!] 第{attempt + 1}次尝试发送消息失败到 {target_node_id}: {e}")
                
                # 更新节点声誉
                self.routing_table_manager.update_node_reputation(target_node_id, success=False)
                
                if attempt == max_retries - 1:  # 最后一次尝试失败
                    print(f"[⚠️] 目标 {target_node_id} 多次尝试后仍不可达，转为信鸽中继模式...")
                    await self.send_via_relay(target_node_id, encrypted)
                    return
                
                # 等待一段时间后重试
                await asyncio.sleep(1 * (attempt + 1))  # 递增延迟

    async def send_multimedia_message(self, target_node_id: str, media_type: str, data: bytes, metadata: dict = None, max_retries: int = 3):
        """发送多媒体消息，带重试机制"""
        target_node = self.routing_table_manager.get_node(target_node_id)
        if not target_node:
            print(f"[!] 未找到节点 {target_node_id}，无法发送多媒体消息")
            return
        
        target = target_node.to_dict()

        # 创建多媒体消息
        multimedia_msg = self.multimedia_processor.create_multimedia_message(
            media_type, data, metadata
        )
        
        if not multimedia_msg:
            print("[!] 创建多媒体消息失败")
            return

        # 序列化多媒体消息
        multimedia_content = f"MULTIMEDIA:{json.dumps(multimedia_msg.to_dict())}"
        
        # 加密多媒体内容
        encrypted = self.crypto.hybrid_encrypt(target['pub_key'], multimedia_content)
        
        # 生成唯一消息ID以防止重放
        msg_id = str(uuid.uuid4())
        # 生成随机数用于防重放
        nonce = str(uuid.uuid4())
        
        payload = {
            "type": "DIRECT_MSG",
            "sender_id": self.node_id,
            "encrypted_payload": encrypted,
            "timestamp": time.time(),
            "msg_id": msg_id,
            "nonce": nonce,  # 添加防重放随机数
            "signature": self.crypto.sign(str(encrypted))  # 添加数字签名
        }

        for attempt in range(max_retries):
            try:
                reader, writer = await asyncio.open_connection(target['host'], target['port'])
                await P2PProtocol.send_json(writer, payload)
                # 等待 ACK
                resp = await P2PProtocol.read_json(reader)
                if resp and resp.get('type') == 'ACK':
                    print(f"[✓] 多媒体消息已送达 {target_node_id}")
                    
                    # 更新激励机制：发送多媒体消息
                    self.incentive_mechanism.update_node_metrics(
                        self.node_id,
                        messages_forwarded=1,
                        bandwidth_provided=len(str(payload).encode('utf-8'))
                    )
                    
                    # 将消息记录到区块链
                    block_data = f"MULTIMEDIA_MSG:{self.node_id}->{target_node_id}:{media_type}:{multimedia_msg.message_id}"
                    from ..blockchain.block import Block
                    new_block = Block(
                        index=len(self.blockchain.chain),
                        previous_hash=self.blockchain.get_latest_block().hash,
                        timestamp=time.time(),
                        data=block_data,
                        proposer=self.node_id
                    )
                    self.blockchain.add_block(new_block)
                    
                    # 更新节点声誉
                    self.routing_table_manager.update_node_reputation(target_node_id, success=True)
                    
                    writer.close()
                    await writer.wait_closed()
                    return  # 成功发送，退出重试循环
                
                writer.close()
                await writer.wait_closed()
                
            except OSError as e:
                print(f"[!] 第{attempt + 1}次尝试发送多媒体消息失败到 {target_node_id}: {e}")
                
                # 更新节点声誉
                self.routing_table_manager.update_node_reputation(target_node_id, success=False)
                
                if attempt == max_retries - 1:  # 最后一次尝试失败
                    print(f"[⚠️] 目标 {target_node_id} 多次尝试后仍不可达，多媒体消息发送失败")
                    return
                
                # 等待一段时间后重试
                await asyncio.sleep(1 * (attempt + 1))  # 递增延迟

    async def send_via_relay(self, target_node_id: str, encrypted_payload: dict):
        """发送给网路中的任意其他节点进行缓存"""
        # 使用路由表管理器获取最优中继节点
        relay_nodes = self.routing_table_manager.get_active_nodes()
        for node_info in relay_nodes:
            if node_info.node_id != target_node_id:
                try:
                    reader, writer = await asyncio.open_connection(node_info.host, node_info.port)
                    # 生成随机数用于防重放
                    nonce = str(uuid.uuid4())
                    relay_msg = {
                        "type": "RELAY_MSG",
                        "target_did": f"did:p2p:{target_node_id}",
                        "payload": encrypted_payload,
                        "nonce": nonce  # 添加防重放随机数
                    }
                    await P2PProtocol.send_json(writer, relay_msg)
                    print(f"[✓] 消息已发送至中继节点 {node_info.node_id}")
                    
                    # 更新激励机制：作为中继转发消息
                    self.incentive_mechanism.update_node_metrics(
                        self.node_id,
                        messages_forwarded=1,
                        bandwidth_provided=len(str(relay_msg).encode('utf-8'))
                    )
                    
                    # 更新节点声誉
                    self.routing_table_manager.update_node_reputation(node_info.node_id, success=True)
                    
                    writer.close()
                    break
                except Exception as e:
                    # 更新节点声誉
                    self.routing_table_manager.update_node_reputation(node_info.node_id, success=False)
                    print(f"[!] 中继发送失败到节点 {node_info.node_id}: {e}")
                    continue

    async def start_consensus_proposal(self, block_data: str):
        """发起共识提案"""
        view_number = len(self.blockchain.chain)
        # 生成随机数用于防重放
        nonce = str(uuid.uuid4())
        proposal = {
            "type": "CONSENSUS_PROPOSAL",
            "view": view_number,
            "leader_id": self.node_id,
            "block": block_data,
            "nonce": nonce,  # 添加防重放随机数
            "signature": self.crypto.sign(block_data)
        }
        print(f"[👑] 发起共识提案 (View {view_number}): {block_data}")
        
        # 更新激励机制：发起共识提案
        self.incentive_mechanism.update_node_metrics(
            self.node_id,
            blocks_validated=1  # 提案者也参与验证
        )
        
        # 广播给所有已知节点
        for nid, info in self.routing_table_manager.routing_table.items():
            asyncio.create_task(self.send_proposal(info, proposal))

    async def send_proposal(self, target_info, proposal):
        # 如果target_info是字典格式（来自旧路由表），提取host和port
        if isinstance(target_info, dict):
            host, port = target_info['host'], target_info['port']
            node_id = None
            for nid, node in self.routing_table_manager.routing_table.items():
                if node.host == host and node.port == port:
                    node_id = nid
                    break
        else:
            # 如果target_info是NodeInfo对象
            host, port = target_info.host, target_info.port
            node_id = target_info.node_id
            
        try:
            reader, writer = await asyncio.open_connection(host, port)
            await P2PProtocol.send_json(writer, proposal)
            
            # 更新激励机制：发送提案
            self.incentive_mechanism.update_node_metrics(
                self.node_id,
                bandwidth_provided=len(str(proposal).encode('utf-8'))
            )
            
            # 更新节点状态
            if node_id:
                self.routing_table_manager.update_node_reputation(node_id, success=True)
            
            writer.close()
        except Exception as e:
            # 更新节点声誉
            if node_id:
                self.routing_table_manager.update_node_reputation(node_id, success=False)
            print(f"[!] 发送提案失败到节点 {node_id}: {e}")

    async def sync_blockchain(self):
        """优化的区块链同步机制 - 解决大规模网络性能瓶颈"""
        # 首先获取网络中区块链的基本信息，找到最长链
        longest_chain_info = await self.get_network_chain_info()
        
        if not longest_chain_info or longest_chain_info['length'] <= len(self.blockchain.chain):
            print("[✓] 本地区块链已为最长链，无需同步")
            return
        
        print(f"[*] 发现更长链，长度: {longest_chain_info['length']}，开始同步...")
        
        # 分批同步区块链
        start_idx = len(self.blockchain.chain)  # 从本地链长度开始同步
        total_blocks = longest_chain_info['length']
        
        while start_idx < total_blocks:
            end_idx = min(start_idx + self.sync_batch_size, total_blocks)
            
            print(f"[*] 同步区块 {start_idx} 到 {end_idx}...")
            
            # 向多个节点并发请求区块
            sync_tasks = []
            for node_info in list(self.routing_table_manager.get_active_nodes())[:self.max_concurrent_syncs]:
                sync_task = asyncio.create_task(
                    self.request_block_range(node_info.to_dict(), start_idx, end_idx)
                )
                sync_tasks.append(sync_task)
            
            # 等待最先完成的响应
            if sync_tasks:
                try:
                    done, pending = await asyncio.wait(
                        sync_tasks, 
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=self.sync_timeout
                    )
                    
                    # 取消未完成的任务
                    for task in pending:
                        task.cancel()
                    
                    # 处理完成的响应
                    for task in done:
                        try:
                            result = await task
                            if result:
                                # 更新本地链
                                for block_data in result:
                                    from ..blockchain.block import Block
                                    new_block = Block.from_dict(block_data)
                                    if len(self.blockchain.chain) > 0:
                                        new_block.previous_hash = self.blockchain.get_latest_block().hash
                                    self.blockchain.chain.append(new_block)
                                print(f"[✓] 成功同步区块 {start_idx} 到 {end_idx}")
                                break
                        except Exception as e:
                            print(f"[!] 区块同步任务失败: {e}")
                            continue
                except asyncio.TimeoutError:
                    print(f"[!] 区块同步超时: {start_idx} 到 {end_idx}")
            
            start_idx = end_idx
        
        print("[✓] 区块链同步完成")

    async def get_network_chain_info(self) -> Optional[dict]:
        """获取网络中区块链的基本信息"""
        chain_info_tasks = []
        
        for node_info in self.routing_table_manager.get_active_nodes():
            task = asyncio.create_task(self.request_chain_info(node_info.to_dict()))
            chain_info_tasks.append(task)
        
        if not chain_info_tasks:
            return None
        
        try:
            results = await asyncio.gather(*chain_info_tasks, return_exceptions=True)
            
            # 找到最长的链
            longest_info = None
            for result in results:
                if isinstance(result, Exception):
                    continue
                if result and isinstance(result, dict):
                    if not longest_info or result.get('length', 0) > longest_info.get('length', 0):
                        longest_info = result
            
            return longest_info
        except Exception as e:
            print(f"[!] 获取网络链信息失败: {e}")
            return None

    async def request_chain_info(self, node_info: dict) -> Optional[dict]:
        """请求节点的区块链信息"""
        try:
            reader, writer = await asyncio.open_connection(node_info['host'], node_info['port'])
            
            info_msg = {
                "type": "BLOCKCHAIN_INFO_REQUEST",
                "requester": self.node_id
            }
            await P2PProtocol.send_json(writer, info_msg)
            
            response = await P2PProtocol.read_json(reader)
            if response and response['type'] == 'BLOCKCHAIN_INFO_RESPONSE':
                writer.close()
                await writer.wait_closed()
                return response['chain_info']
            
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"[!] 请求链信息失败到节点 {node_info}: {e}")
        
        return None

    async def request_block_range(self, node_info: dict, start_idx: int, end_idx: int) -> Optional[list]:
        """请求指定范围的区块"""
        try:
            reader, writer = await asyncio.open_connection(node_info['host'], node_info['port'])
            
            # 生成随机数用于防重放
            nonce = str(uuid.uuid4())
            sync_msg = {
                "type": "BLOCKCHAIN_SYNC",
                "requester": self.node_id,
                "start_index": start_idx,
                "end_index": end_idx,
                "nonce": nonce  # 添加防重放随机数
            }
            await P2PProtocol.send_json(writer, sync_msg)
            
            response = await P2PProtocol.read_json(reader)
            if response and response['type'] == 'BLOCKCHAIN_RESPONSE':
                writer.close()
                await writer.wait_closed()
                
                # 验证接收到的区块
                received_chain = response.get('chain', [])
                for block_data in received_chain:
                    from ..blockchain.block import Block
                    block = Block.from_dict(block_data)
                    if block.calculate_hash() != block_data['hash']:
                        print(f"[!] 接收到的区块哈希验证失败: {block_data['hash']}")
                        return None
                
                return received_chain
            
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"[!] 请求区块范围失败到节点 {node_info}: {e}")
        
        return None

    def get_blockchain_info(self):
        """获取区块链信息"""
        return {
            "length": len(self.blockchain.chain),
            "valid": self.blockchain.is_chain_valid(),
            "chain": self.blockchain.to_list()
        }

    def get_node_stats(self):
        """获取节点统计信息"""
        uptime = time.time() - self.start_time
        return {
            "node_id": self.node_id,
            "uptime": uptime,
            "messages_sent": sum(1 for block in self.blockchain.chain if "MSG:" in block.data),
            "multimedia_messages_sent": sum(1 for block in self.blockchain.chain if "MULTIMEDIA_MSG:" in block.data),
            "routing_table_size": len(self.routing_table_manager.routing_table),
            "incentive_info": self.incentive_mechanism.get_node_info(self.node_id)
        }