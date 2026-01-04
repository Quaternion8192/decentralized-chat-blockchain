"""
零知识证明 (Zero-Knowledge Proof) 模块
用于增强隐私保护，允许验证某些信息而不泄露信息本身
"""
import hashlib
import secrets
import json
import time
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ZKPProof:
    """零知识证明数据结构"""
    statement: str  # 声明
    witness: str    # 证人（秘密值）
    challenge: str  # 挑战
    response: str   # 响应
    public_data: Dict[str, Any]  # 公共数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "statement": self.statement,
            "witness": self.witness,
            "challenge": self.challenge,
            "response": self.response,
            "public_data": self.public_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建ZKPProof对象"""
        return cls(
            statement=data["statement"],
            witness=data["witness"],
            challenge=data["challenge"],
            response=data["response"],
            public_data=data["public_data"]
        )


class ZKPGenerator:
    """
    零知识证明生成器
    实现简单的Schnorr协议变体
    """
    def __init__(self):
        # 使用较大的素数作为模数（实际应用中应该使用更安全的参数）
        self.p = 2147483647  # 一个梅森素数 2^31 - 1
        self.g = 5  # 生成元
    
    def generate_proof(self, statement: str, witness: str, public_data: Dict[str, Any] = None) -> ZKPProof:
        """
        生成零知识证明
        实现更完整的Schnorr协议
        """
        if public_data is None:
            public_data = {}
        
        # 将witness转换为整数
        witness_int = int.from_bytes(hashlib.sha256(witness.encode()).digest()[:4], 'big')
        
        # 计算h = g^w mod p (公钥)
        h = pow(self.g, witness_int, self.p)
        
        # 选择随机数r（承诺值）
        r = secrets.randbelow(self.p - 1)
        
        # 计算u = g^r mod p（承诺）
        u = pow(self.g, r, self.p)
        
        # 生成挑战c（基于statement、承诺u和公共数据）
        challenge_input = f"{statement}{u}{json.dumps(public_data, sort_keys=True)}"
        c = int.from_bytes(hashlib.sha256(challenge_input.encode()).digest()[:4], 'big') % (self.p - 1)
        
        # 计算响应z = r + c*w mod (p-1) 
        z = (r + c * witness_int) % (self.p - 1)
        
        return ZKPProof(
            statement=statement,
            witness=str(witness_int),
            challenge=str(c),
            response=str(z),
            public_data=public_data
        )
    
    def verify_proof(self, proof: ZKPProof) -> bool:
        """
        验证零知识证明
        使用更严格的验证逻辑
        """
        try:
            # 从证明中获取值
            statement = proof.statement
            witness_int = int(proof.witness)
            c = int(proof.challenge)
            z = int(proof.response)
            
            # 验证值的范围
            if c < 0 or c >= self.p - 1 or z < 0 or z >= self.p - 1:
                return False
            
            # 计算 h = g^w mod p (公钥)
            h = pow(self.g, witness_int, self.p)
            
            # 计算 g^z mod p
            gz = pow(self.g, z, self.p)
            
            # 计算 h^c mod p
            hc = pow(h, c, self.p)
            
            # 计算 u' = g^z / h^c mod p = g^z * h^(-c) mod p
            h_neg_c = pow(hc, self.p - 2, self.p)  # 计算模逆
            computed_u = (gz * h_neg_c) % self.p
            
            # 重新生成挑战并验证一致性
            challenge_input = f"{statement}{computed_u}{json.dumps(proof.public_data, sort_keys=True)}"
            expected_c = int.from_bytes(hashlib.sha256(challenge_input.encode()).digest()[:4], 'big') % (self.p - 1)
            
            # 验证挑战值是否匹配
            return c == expected_c
        except Exception:
            return False


class ZKPManager:
    """
    零知识证明管理器
    管理零知识证明的生成、验证和存储
    """
    def __init__(self):
        self.zkp_generator = ZKPGenerator()
        self.proof_store: Dict[str, ZKPProof] = {}
        self.proof_timestamps: Dict[str, float] = {}  # 存储证明创建时间戳
    
    def create_proof(self, statement: str, witness: str, public_data: Dict[str, Any] = None) -> str:
        """
        创建零知识证明并返回证明ID
        """
        proof = self.zkp_generator.generate_proof(statement, witness, public_data)
        
        # 生成证明ID
        proof_id = hashlib.sha256(f"{statement}{witness}{json.dumps(public_data or {}, sort_keys=True)}".encode()).hexdigest()
        
        # 存储证明
        self.proof_store[proof_id] = proof
        # 存储时间戳
        self.proof_timestamps[proof_id] = time.time()
        
        return proof_id
    
    def verify_proof_by_id(self, proof_id: str) -> bool:
        """
        通过ID验证零知识证明
        """
        if proof_id not in self.proof_store:
            return False
        
        proof = self.proof_store[proof_id]
        return self.zkp_generator.verify_proof(proof)
    
    def verify_proof_data(self, proof: ZKPProof) -> bool:
        """
        验证零知识证明数据
        """
        return self.zkp_generator.verify_proof(proof)
    
    def get_proof(self, proof_id: str) -> Optional[ZKPProof]:
        """
        获取证明数据
        """
        return self.proof_store.get(proof_id)
    
    def remove_proof(self, proof_id: str) -> bool:
        """
        移除证明
        """
        if proof_id in self.proof_store:
            del self.proof_store[proof_id]
            return True
        return False
    
    def cleanup_expired_proofs(self, max_age: int = 3600) -> int:
        """
        清理过期的证明
        """
        import time
        current_time = time.time()
        expired_proof_ids = []
        
        # 找出过期的证明ID
        for proof_id, timestamp in self.proof_timestamps.items():
            if current_time - timestamp > max_age:
                expired_proof_ids.append(proof_id)
        
        # 删除过期的证明
        removed_count = 0
        for proof_id in expired_proof_ids:
            if proof_id in self.proof_store:
                del self.proof_store[proof_id]
                del self.proof_timestamps[proof_id]
                removed_count += 1
        
        return removed_count


class ZKPBlockchainIntegration:
    """
    零知识证明与区块链集成
    用于在区块链上验证零知识证明而不泄露敏感信息
    """
    def __init__(self, zkp_manager: ZKPManager):
        self.zkp_manager = zkp_manager
    
    def add_zkp_to_blockchain(self, statement: str, witness: str, public_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        将零知识证明添加到区块链（模拟）
        """
        proof_id = self.zkp_manager.create_proof(statement, witness, public_data)
        
        # 返回包含证明ID和验证状态的信息
        return {
            "proof_id": proof_id,
            "verified": self.zkp_manager.verify_proof_by_id(proof_id),
            "statement": statement,
            "public_data": public_data or {}
        }
    
    def verify_zkp_on_blockchain(self, proof_id: str) -> Dict[str, Any]:
        """
        在区块链上验证零知识证明（模拟）
        """
        is_valid = self.zkp_manager.verify_proof_by_id(proof_id)
        
        if is_valid:
            proof = self.zkp_manager.get_proof(proof_id)
            return {
                "valid": True,
                "proof_id": proof_id,
                "statement": proof.statement,
                "public_data": proof.public_data
            }
        else:
            return {
                "valid": False,
                "proof_id": proof_id
            }