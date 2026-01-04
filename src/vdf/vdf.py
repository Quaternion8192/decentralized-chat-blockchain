"""
可验证延迟函数 (VDF) 模块
用于增加计算延迟以防止垃圾信息和增强安全性
"""
import hashlib
import time
from typing import Tuple, Optional
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.blockchain.block import Block


class VDF:
    """
    可验证延迟函数实现
    使用连续的哈希计算作为延迟函数
    """
    def __init__(self, difficulty: int = 10000):
        self.difficulty = difficulty  # 计算复杂度

    def compute(self, challenge: str) -> Tuple[str, float]:
        """
        计算VDF证明
        返回证明和计算时间
        """
        start_time = time.time()
        result = challenge
        
        # 执行预定义数量的哈希计算
        for i in range(self.difficulty):
            result = hashlib.sha256((result + str(i)).encode()).hexdigest()
        
        computation_time = time.time() - start_time
        return result, computation_time

    async def compute_async(self, challenge: str) -> Tuple[str, float]:
        """
        异步计算VDF证明
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result, computation_time = await loop.run_in_executor(
                executor, self.compute, challenge
            )
        return result, computation_time

    def verify(self, challenge: str, proof: str, expected_iterations: Optional[int] = None) -> bool:
        """
        验证VDF证明
        验证速度应该远快于计算速度
        """
        if expected_iterations is None:
            expected_iterations = self.difficulty
            
        # 重新计算相同的迭代次数来验证证明
        result = challenge
        for i in range(expected_iterations):
            result = hashlib.sha256((result + str(i)).encode()).hexdigest()
        
        return result == proof

    def compute_with_witness(self, challenge: str) -> Tuple[str, str, float]:
        """
        计算VDF证明并生成见证（用于快速验证）
        """
        start_time = time.time()
        result = challenge
        
        # 执行预定义数量的哈希计算
        for i in range(self.difficulty):
            result = hashlib.sha256((result + str(i)).encode()).hexdigest()
        
        computation_time = time.time() - start_time
        
        # 生成见证 - 使用中间值
        witness = hashlib.sha256((challenge + result).encode()).hexdigest()
        
        return result, witness, computation_time


class VDFProof:
    """
    VDF证明对象
    """
    def __init__(self, challenge: str, proof: str, witness: str = None, 
                 computation_time: float = 0.0, difficulty: int = 10000):
        self.challenge = challenge
        self.proof = proof
        self.witness = witness
        self.computation_time = computation_time
        self.difficulty = difficulty
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "challenge": self.challenge,
            "proof": self.proof,
            "witness": self.witness,
            "computation_time": self.computation_time,
            "difficulty": self.difficulty,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建VDFProof对象"""
        return cls(
            challenge=data["challenge"],
            proof=data["proof"],
            witness=data.get("witness"),
            computation_time=data.get("computation_time", 0.0),
            difficulty=data.get("difficulty", 10000)
        )


class VDFManager:
    """
    VDF管理器
    用于管理VDF计算和验证
    """
    def __init__(self, difficulty: int = 10000):
        self.vdf = VDF(difficulty)
        self.difficulty = difficulty
        self.proof_cache = {}  # 缓存证明以避免重复计算

    async def generate_proof(self, challenge: str) -> VDFProof:
        """
        生成VDF证明
        """
        proof, witness, computation_time = self.vdf.compute_with_witness(challenge)
        
        vdf_proof = VDFProof(
            challenge=challenge,
            proof=proof,
            witness=witness,
            computation_time=computation_time,
            difficulty=self.difficulty
        )
        
        # 缓存证明
        cache_key = hashlib.sha256(challenge.encode()).hexdigest()
        self.proof_cache[cache_key] = vdf_proof
        
        return vdf_proof

    def verify_proof(self, vdf_proof: VDFProof) -> bool:
        """
        验证VDF证明
        """
        # 检查是否在缓存中
        cache_key = hashlib.sha256(vdf_proof.challenge.encode()).hexdigest()
        if cache_key in self.proof_cache:
            cached_proof = self.proof_cache[cache_key]
            if cached_proof.proof == vdf_proof.proof:
                return True
        
        # 验证证明
        return self.vdf.verify(
            vdf_proof.challenge, 
            vdf_proof.proof, 
            vdf_proof.difficulty
        )

    def add_proof_to_cache(self, vdf_proof: VDFProof):
        """
        将证明添加到缓存
        """
        cache_key = hashlib.sha256(vdf_proof.challenge.encode()).hexdigest()
        self.proof_cache[cache_key] = vdf_proof

    def cleanup_cache(self, max_age: float = 3600):
        """
        清理过期的缓存证明
        """
        current_time = time.time()
        stale_keys = [
            key for key, proof in self.proof_cache.items()
            if current_time - proof.timestamp > max_age
        ]
        
        for key in stale_keys:
            del self.proof_cache[key]


class VDFBlockchain:
    """
    集成VDF的区块链类
    """
    def __init__(self, difficulty: int = 2, vdf_difficulty: int = 1000):
        from ..blockchain.blockchain import Blockchain
        from ..blockchain.block import Block
        self.blockchain = Blockchain()
        self.vdf_manager = VDFManager(vdf_difficulty)
        self.blockchain.difficulty = difficulty

    async def add_block_with_vdf(self, data: str, proposer: str = None) -> bool:
        """
        使用VDF证明添加区块
        """
        # 获取前一个区块的哈希
        previous_hash = self.blockchain.get_latest_block().hash
        timestamp = time.time()
        
        # 生成挑战
        challenge = f"{previous_hash}{timestamp}{data}"
        
        # 生成VDF证明
        vdf_proof = await self.vdf_manager.generate_proof(challenge)
        
        # 创建新区块，包含VDF证明
        new_block = Block(
            index=len(self.blockchain.chain),
            previous_hash=previous_hash,
            timestamp=timestamp,
            data=data,
            proposer=proposer
        )
        
        # 将VDF证明添加到区块数据中，但保留原始数据供验证
        new_block.data = f"VDF:{vdf_proof.proof}:{data}"
        
        # 验证VDF证明
        if not self.vdf_manager.verify_proof(vdf_proof):
            print("[!] VDF证明验证失败")
            return False
        
        # 添加区块到链
        self.blockchain.add_block(new_block)
        return True

    def verify_blockchain_with_vdf(self) -> bool:
        """
        验证包含VDF证明的区块链
        """
        from ..blockchain.block import Block
        
        for i in range(1, len(self.blockchain.chain)):
            current_block = self.blockchain.chain[i]
            previous_block = self.blockchain.chain[i-1]

            # 检查当前区块哈希是否正确
            if current_block.hash != current_block.calculate_hash():
                return False

            # 检查当前区块的前一个哈希是否与上一个区块的哈希匹配
            if current_block.previous_hash != previous_block.hash:
                return False

            # 如果区块数据包含VDF证明，验证它
            if current_block.data.startswith("VDF:"):
                try:
                    parts = current_block.data.split(":", 2)
                    if len(parts) >= 3:
                        vdf_proof_str = parts[1]
                        original_data = parts[2]
                        
                        # 重建挑战 - 使用原始数据和之前区块的哈希
                        # 生成VDF证明时，挑战是基于 previous_hash, timestamp, data
                        challenge = f"{previous_block.hash}{current_block.timestamp}{original_data}"
                        
                        # 验证VDF证明
                        if not self.vdf_manager.vdf.verify(challenge, vdf_proof_str):
                            print(f"[!] 区块 {i} 的VDF证明验证失败")
                            return False
                except Exception as e:
                    print(f"[!] 区块 {i} 的VDF证明验证出错: {e}")
                    # 如果解析失败，继续验证其他部分
                    continue

        return True

    def get_blockchain_info(self):
        """
        获取区块链信息
        """
        return {
            "length": len(self.blockchain.chain),
            "valid": self.verify_blockchain_with_vdf(),
            "chain": [block.to_dict() for block in self.blockchain.chain]
        }