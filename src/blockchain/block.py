"""
区块链中的区块类
"""
import hashlib
import time
from typing import Dict


class Block:
    """区块链中的区块类"""
    def __init__(self, index: int, previous_hash: str, timestamp: float, data: str, 
                 nonce: int = 0, hash: str = None, proposer: str = None, vdf_proof: str = None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.proposer = proposer  # 添加区块提议者信息
        self.vdf_proof = vdf_proof  # 添加VDF证明
        self.hash = hash or self.calculate_hash()

    def calculate_hash(self) -> str:
        """计算区块哈希"""
        block_string = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.nonce}{self.proposer or ''}{self.vdf_proof or ''}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "nonce": self.nonce,
            "hash": self.hash,
            "proposer": self.proposer,
            "vdf_proof": self.vdf_proof
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建区块"""
        block = cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            data=data["data"],
            nonce=data["nonce"],
            hash=data["hash"],
            proposer=data.get("proposer"),
            vdf_proof=data.get("vdf_proof")
        )
        return block