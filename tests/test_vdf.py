import unittest
import asyncio
from src.vdf.vdf import VDF, VDFProof, VDFManager, VDFBlockchain


class TestVDF(unittest.TestCase):
    """VDF模块单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.vdf = VDF(difficulty=100)  # 使用较低难度以加快测试
    
    def test_compute_and_verify(self):
        """测试VDF计算和验证"""
        challenge = "test_challenge"
        
        # 计算VDF证明
        proof, computation_time = self.vdf.compute(challenge)
        
        # 验证证明
        is_valid = self.vdf.verify(challenge, proof)
        self.assertTrue(is_valid)
        
        # 验证错误的证明
        is_valid = self.vdf.verify(challenge, "invalid_proof")
        self.assertFalse(is_valid)
    
    def test_async_compute_and_verify(self):
        """测试异步VDF计算和验证"""
        challenge = "async_test_challenge"
        
        # 异步计算VDF证明
        async def async_test():
            return await self.vdf.compute_async(challenge)
        
        proof, computation_time = asyncio.run(async_test())
        
        # 验证证明
        is_valid = self.vdf.verify(challenge, proof)
        self.assertTrue(is_valid)
    
    def test_compute_with_witness(self):
        """测试带见证的VDF计算"""
        challenge = "witness_test_challenge"
        
        # 计算带见证的VDF证明
        proof, witness, computation_time = self.vdf.compute_with_witness(challenge)
        
        # 验证证明
        is_valid = self.vdf.verify(challenge, proof)
        self.assertTrue(is_valid)
        
        # 验证见证不为空
        self.assertIsNotNone(witness)
        self.assertIsInstance(witness, str)


class TestVDFProof(unittest.TestCase):
    """VDFProof类单元测试"""
    
    def test_vdf_proof_creation(self):
        """测试VDFProof创建"""
        challenge = "proof_test_challenge"
        proof = "sample_proof_data"
        witness = "sample_witness_data"
        
        vdf_proof = VDFProof(
            challenge=challenge,
            proof=proof,
            witness=witness,
            computation_time=1.5,
            difficulty=100
        )
        
        self.assertEqual(vdf_proof.challenge, challenge)
        self.assertEqual(vdf_proof.proof, proof)
        self.assertEqual(vdf_proof.witness, witness)
        self.assertEqual(vdf_proof.computation_time, 1.5)
        self.assertEqual(vdf_proof.difficulty, 100)
    
    def test_vdf_proof_serialization(self):
        """测试VDFProof序列化"""
        original_proof = VDFProof(
            challenge="serialization_test",
            proof="serialized_proof",
            witness="serialized_witness",
            computation_time=2.0,
            difficulty=50
        )
        
        # 序列化
        proof_dict = original_proof.to_dict()
        
        # 反序列化
        restored_proof = VDFProof.from_dict(proof_dict)
        
        self.assertEqual(original_proof.challenge, restored_proof.challenge)
        self.assertEqual(original_proof.proof, restored_proof.proof)
        self.assertEqual(original_proof.witness, restored_proof.witness)
        self.assertEqual(original_proof.computation_time, restored_proof.computation_time)
        self.assertEqual(original_proof.difficulty, restored_proof.difficulty)


class TestVDFManager(unittest.TestCase):
    """VDFManager类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.vdf_manager = VDFManager(difficulty=50)
    
    def test_generate_and_verify_proof(self):
        """测试生成和验证证明"""
        challenge = "manager_test_challenge"
        
        # 生成证明
        async def async_generate():
            return await self.vdf_manager.generate_proof(challenge)
        
        vdf_proof = asyncio.run(async_generate())
        
        # 验证证明
        is_valid = self.vdf_manager.verify_proof(vdf_proof)
        self.assertTrue(is_valid)
        
        # 验证缓存功能
        self.vdf_manager.add_proof_to_cache(vdf_proof)
        is_valid_cached = self.vdf_manager.verify_proof(vdf_proof)
        self.assertTrue(is_valid_cached)
    
    def test_cache_cleanup(self):
        """测试缓存清理"""
        challenge = "cleanup_test_challenge"
        
        async def async_generate():
            return await self.vdf_manager.generate_proof(challenge)
        
        vdf_proof = asyncio.run(async_generate())
        self.vdf_manager.add_proof_to_cache(vdf_proof)
        
        # 验证缓存中有证明
        cache_key = __import__('hashlib').sha256(vdf_proof.challenge.encode()).hexdigest()
        self.assertIn(cache_key, self.vdf_manager.proof_cache)
        
        # 手动设置一个过期时间
        vdf_proof.timestamp = 0  # 设置为过去时间
        self.vdf_manager.proof_cache[cache_key] = vdf_proof
        
        # 清理过期缓存
        self.vdf_manager.cleanup_cache(max_age=1)  # 1秒后过期
        
        # 验证缓存已被清理
        self.assertNotIn(cache_key, self.vdf_manager.proof_cache)


class TestVDFBlockchain(unittest.TestCase):
    """VDFBlockchain类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.vdf_blockchain = VDFBlockchain(difficulty=1, vdf_difficulty=10)
    
    def test_add_block_with_vdf(self):
        """测试添加带VDF证明的区块"""
        async def async_add_block():
            return await self.vdf_blockchain.add_block_with_vdf("Test data")
        
        success = asyncio.run(async_add_block())
        self.assertTrue(success)
        
        # 验证区块链长度
        self.assertEqual(len(self.vdf_blockchain.blockchain.chain), 2)  # 包括创世块
        
        # 验证区块链有效性
        is_valid = self.vdf_blockchain.verify_blockchain_with_vdf()
        self.assertTrue(is_valid)
    
    def test_verify_blockchain_with_vdf(self):
        """测试验证带VDF证明的区块链"""
        # 添加几个带VDF证明的区块
        async def async_add_blocks():
            results = []
            for i in range(3):
                result = await self.vdf_blockchain.add_block_with_vdf(f"Test data {i}")
                results.append(result)
            return results
        
        results = asyncio.run(async_add_blocks())
        self.assertTrue(all(results))
        
        # 验证整个区块链
        is_valid = self.vdf_blockchain.verify_blockchain_with_vdf()
        self.assertTrue(is_valid)
        
        # 获取区块链信息
        info = self.vdf_blockchain.get_blockchain_info()
        self.assertEqual(info["length"], 4)  # 包括创世块
        self.assertTrue(info["valid"])


if __name__ == '__main__':
    unittest.main()