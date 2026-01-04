"""
区块链类，支持多种共识机制
"""
import hashlib
import time
from typing import List
from .block import Block


class Blockchain:
    """区块链类，支持多种共识机制"""
    def __init__(self, consensus_type="simple_pow"):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2  # 挖矿难度
        self.consensus_type = consensus_type  # 共识类型
        self.pending_transactions = []  # 待处理交易
        self.validators = {}  # 验证节点列表
        self.votes = {}  # 投票记录
        self.current_view = 0  # 当前视图号

    def create_genesis_block(self) -> Block:
        """创建创世区块"""
        return Block(0, "0", time.time(), "Genesis Block", 0)

    def get_latest_block(self) -> Block:
        """获取最新区块"""
        return self.chain[-1]

    def add_block(self, new_block: Block):
        """添加新区块到链上"""
        new_block.previous_hash = self.get_latest_block().hash
        if self.consensus_type == "simple_pow":
            new_block.hash = self.mine_block(new_block)
        elif self.consensus_type == "pbft":
            new_block.hash = self.pbft_consensus(new_block)
        elif self.consensus_type == "vdf_pow":
            new_block.hash = self.vdf_pow_consensus(new_block)
        else:
            new_block.hash = self.mine_block(new_block)  # 默认使用简单挖矿
        self.chain.append(new_block)

    def mine_block(self, block: Block) -> str:
        """挖矿 - 寻找满足条件的哈希值（旧的工作量证明算法）"""
        while True:
            block.nonce += 1
            hash = block.calculate_hash()
            if hash[:self.difficulty] == "0" * self.difficulty:
                return hash
            # 为避免无限循环，可以添加一些限制
            if block.nonce > 1000000:  # 防止挖矿时间过长
                break
        return block.calculate_hash()

    def pbft_consensus(self, block: Block) -> str:
        """实用拜占庭容错共识算法"""
        # 实现更完整的PBFT共识过程
        # 阶段1：预准备 (Pre-prepare)
        # 验证区块是否有效
        if not self.is_block_valid(block):
            return block.calculate_hash()
        
        # 阶段2：准备 (Prepare) 
        # 模拟收集准备消息的过程
        prepared_messages = self.collect_prepare_messages(block)
        
        # 阶段3：提交 (Commit)
        # 模拟收集提交消息的过程
        commit_messages = self.collect_commit_messages(block, prepared_messages)
        
        # 如果收到足够的提交消息，则接受区块
        if len(commit_messages) >= self.get_required_commit_count():
            # 区块被确认，更新nonce并返回哈希
            block.nonce += 1
            return block.calculate_hash()
        else:
            # 共识失败，返回原始哈希
            return block.calculate_hash()

    def is_block_valid(self, block: Block) -> bool:
        """验证区块是否有效"""
        # 检查区块数据是否完整
        if not block.data:
            return False
        
        # 检查时间戳是否合理
        if block.timestamp > time.time() + 300:  # 5分钟容差
            return False
            
        # 检查索引是否连续
        if block.index != len(self.chain):
            return False
            
        return True

    def collect_prepare_messages(self, block: Block) -> list:
        """收集准备消息"""
        # 在实际实现中，这里会从网络中收集准备消息
        # 为更真实地模拟，我们考虑网络延迟、节点状态等因素
        num_validators = len(self.validators) if self.validators else 10
        required_prepare = (2 * num_validators // 3) + 1  # 三分之二多数
        
        # 模拟更真实的准备消息收集，考虑网络延迟和节点可用性
        prepare_messages = []
        for node_id, node_info in self.validators.items():
            # 检查节点是否在线和健康
            if node_info.get('status') == 'online' and node_info.get('health', True):
                # 模拟网络延迟
                import random
                delay = random.uniform(0.1, 1.0)  # 100ms到1s的延迟
                time.sleep(delay)  # 模拟网络延迟
                
                # 模拟节点处理并返回准备消息
                prepare_messages.append({
                    'node_id': node_id,
                    'block_hash': block.calculate_hash(),
                    'view': len(self.chain),
                    'timestamp': time.time(),
                    'signature': hashlib.sha256(f"{node_id}{block.calculate_hash()}".encode()).hexdigest()  # 模拟签名
                })
                
                # 如果已收集到足够数量的消息，提前退出
                if len(prepare_messages) >= required_prepare:
                    break
        
        # 如果在线节点不足，使用模拟数据补充
        while len(prepare_messages) < required_prepare and len(prepare_messages) < num_validators:
            node_id = f'validator_{len(prepare_messages)}'
            prepare_messages.append({
                'node_id': node_id,
                'block_hash': block.calculate_hash(),
                'view': len(self.chain),
                'timestamp': time.time(),
                'signature': hashlib.sha256(f"{node_id}{block.calculate_hash()}".encode()).hexdigest()
            })
        
        return prepare_messages

    def collect_commit_messages(self, block: Block, prepared_messages: list) -> list:
        """收集提交消息"""
        # 在实际实现中，这里会从网络中收集提交消息
        # 为更真实地模拟，我们考虑网络延迟、节点状态和已收到的准备消息
        num_validators = len(self.validators) if self.validators else 10
        required_commit = (2 * num_validators // 3) + 1  # 三分之二多数
        
        # 基于已收到的准备消息来收集提交消息
        commit_messages = []
        for msg in prepared_messages:
            node_id = msg['node_id']
            # 模拟节点在收到足够准备消息后发送提交消息
            if len([pm for pm in prepared_messages if pm['block_hash'] == msg['block_hash']]) >= (2 * num_validators // 3):
                # 模拟网络延迟
                import random
                delay = random.uniform(0.1, 0.5)  # 100ms到500ms的延迟
                time.sleep(delay)  # 模拟网络延迟
                
                # 模拟节点发送提交消息
                commit_messages.append({
                    'node_id': node_id,
                    'block_hash': block.calculate_hash(),
                    'view': len(self.chain),
                    'timestamp': time.time(),
                    'signature': hashlib.sha256(f"{node_id}COMMIT{block.calculate_hash()}".encode()).hexdigest()  # 模拟签名
                })
                
                # 如果已收集到足够数量的消息，提前退出
                if len(commit_messages) >= required_commit:
                    break
        
        # 如果提交消息不足，使用模拟数据补充
        while len(commit_messages) < required_commit and len(commit_messages) < num_validators:
            node_id = f'validator_{len(commit_messages) + num_validators}'
            commit_messages.append({
                'node_id': node_id,
                'block_hash': block.calculate_hash(),
                'view': len(self.chain),
                'timestamp': time.time(),
                'signature': hashlib.sha256(f"{node_id}COMMIT{block.calculate_hash()}".encode()).hexdigest()
            })
        
        return commit_messages

    def get_required_commit_count(self) -> int:
        """获取所需的提交消息数量"""
        # PBFT中需要 (2f+1) 个提交消息，其中 f 是最大容错节点数
        # 总节点数为 3f+1，所以容错数 f = (n-1)/3
        total_nodes = len(self.validators) if self.validators else 10
        fault_tolerance = (total_nodes - 1) // 3
        return 2 * fault_tolerance + 1

    def vdf_pow_consensus(self, block: Block) -> str:
        """结合VDF的工作量证明共识算法"""
        # 计算VDF证明
        challenge = f"{block.previous_hash}{block.timestamp}{block.data}{block.nonce}"
        vdf_result = self.compute_vdf(challenge)
        # 将VDF证明存储在区块中
        block.vdf_proof = vdf_result
        # 然后进行工作量证明
        while True:
            block.nonce += 1
            hash = block.calculate_hash()
            if hash[:self.difficulty] == "0" * self.difficulty:
                # 验证VDF结果
                if self.verify_vdf(challenge, vdf_result):
                    return hash
            # 防止无限循环
            if block.nonce > 1000000:
                break
        return block.calculate_hash()

    def compute_vdf(self, challenge: str) -> str:
        """计算VDF（可验证延迟函数）"""
        # 改进的VDF计算，使用更复杂的数学运算来确保顺序计算特性
        import hashlib
        import time
        
        start_time = time.time()
        result = challenge
        # 增加计算轮数以增强安全性
        for i in range(50000):  # 增加迭代次数
            # 使用更复杂的计算：不仅哈希，还加入迭代计数
            input_str = f"{result}{i}{challenge}"
            result = hashlib.sha256(input_str.encode()).hexdigest()
        
        computation_time = time.time() - start_time
        print(f"[VDF] 计算耗时: {computation_time:.2f}秒")
        
        return result

    def _hash_string(self, s: str) -> str:
        """辅助函数：对字符串进行哈希"""
        import hashlib
        return hashlib.sha256(s.encode()).hexdigest()

    def verify_vdf(self, challenge: str, proof: str) -> bool:
        """验证VDF结果"""
        # 改进的VDF验证，需要执行相同的计算来验证结果
        import hashlib
        
        # 重新执行相同的计算过程
        result = challenge
        for i in range(50000):  # 必须执行相同数量的计算
            input_str = f"{result}{i}{challenge}"
            result = hashlib.sha256(input_str.encode()).hexdigest()
        
        return result == proof

    def is_chain_valid(self) -> bool:
        """验证区块链是否有效"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # 检查当前区块哈希是否正确
            if current_block.hash != current_block.calculate_hash():
                return False

            # 检查当前区块的前一个哈希是否与上一个区块的哈希匹配
            if current_block.previous_hash != previous_block.hash:
                return False

            # 如果区块使用VDF共识，验证VDF证明
            if self.consensus_type == "vdf_pow" and current_block.vdf_proof:
                challenge = f"{previous_block.hash}{current_block.timestamp}{current_block.data}{current_block.nonce}"
                if not self.verify_vdf(challenge, current_block.vdf_proof):
                    return False

        return True

    def to_list(self) -> List[dict]:
        """将区块链转换为字典列表"""
        return [block.to_dict() for block in self.chain]

    def from_list(self, chain_data: List[dict]):
        """从字典列表恢复区块链"""
        self.chain = [Block.from_dict(data) for data in chain_data]
    
    def get_block_range(self, start_index: int, end_index: int) -> List[dict]:
        """获取指定范围的区块"""
        start = max(0, start_index)
        end = min(len(self.chain), end_index)
        return [block.to_dict() for block in self.chain[start:end]]
    
    def get_chain_info(self) -> dict:
        """获取区块链基本信息"""
        return {
            "length": len(self.chain),
            "valid": self.is_chain_valid(),
            "latest_hash": self.get_latest_block().hash if self.chain else None,
            "oldest_hash": self.chain[0].hash if self.chain else None
        }