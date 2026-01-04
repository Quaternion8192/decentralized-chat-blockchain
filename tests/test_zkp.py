import unittest
from src.zkp.zkp import ZKPProof, ZKPGenerator, ZKPManager, ZKPBlockchainIntegration


class TestZKPProof(unittest.TestCase):
    """ZKPProof类单元测试"""
    
    def test_zkp_proof_creation(self):
        """测试ZKPProof创建"""
        proof = ZKPProof(
            statement="test_statement",
            witness="test_witness",
            challenge="test_challenge",
            response="test_response",
            public_data={"key": "value"}
        )
        
        self.assertEqual(proof.statement, "test_statement")
        self.assertEqual(proof.witness, "test_witness")
        self.assertEqual(proof.challenge, "test_challenge")
        self.assertEqual(proof.response, "test_response")
        self.assertEqual(proof.public_data, {"key": "value"})
    
    def test_zkp_proof_serialization(self):
        """测试ZKPProof序列化"""
        original_proof = ZKPProof(
            statement="serialization_test",
            witness="witness_data",
            challenge="challenge_data",
            response="response_data",
            public_data={"test": "data", "number": 123}
        )
        
        # 序列化
        proof_dict = original_proof.to_dict()
        
        # 反序列化
        restored_proof = ZKPProof.from_dict(proof_dict)
        
        self.assertEqual(original_proof.statement, restored_proof.statement)
        self.assertEqual(original_proof.witness, restored_proof.witness)
        self.assertEqual(original_proof.challenge, restored_proof.challenge)
        self.assertEqual(original_proof.response, restored_proof.response)
        self.assertEqual(original_proof.public_data, restored_proof.public_data)


class TestZKPGenerator(unittest.TestCase):
    """ZKPGenerator类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = ZKPGenerator()
    
    def test_generate_and_verify_proof(self):
        """测试生成和验证证明"""
        statement = "I know the secret"
        witness = "secret_value"
        public_data = {"user": "test_user", "action": "access"}
        
        # 生成证明
        proof = self.generator.generate_proof(statement, witness, public_data)
        
        # 验证证明
        is_valid = self.generator.verify_proof(proof)
        self.assertTrue(is_valid)
        
        # 验证无效证明
        invalid_proof = ZKPProof(
            statement="wrong_statement",
            witness="wrong_witness",
            challenge="wrong_challenge",
            response="wrong_response",
            public_data={"wrong": "data"}
        )
        is_valid = self.generator.verify_proof(invalid_proof)
        self.assertFalse(is_valid)


class TestZKPManager(unittest.TestCase):
    """ZKPManager类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = ZKPManager()
    
    def test_create_and_verify_proof(self):
        """测试创建和验证证明"""
        statement = "knowledge_test"
        witness = "test_witness_value"
        public_data = {"test": "data"}
        
        # 创建证明
        proof_id = self.manager.create_proof(statement, witness, public_data)
        self.assertIsNotNone(proof_id)
        self.assertNotEqual(proof_id, "")
        
        # 验证证明
        is_valid = self.manager.verify_proof_by_id(proof_id)
        self.assertTrue(is_valid)
        
        # 获取证明
        proof = self.manager.get_proof(proof_id)
        self.assertIsNotNone(proof)
        self.assertEqual(proof.statement, statement)
        self.assertEqual(proof.public_data, public_data)
    
    def test_verify_proof_data(self):
        """测试验证证明数据"""
        statement = "data_verification_test"
        witness = "another_witness"
        
        # 直接生成证明
        proof = self.manager.zkp_generator.generate_proof(statement, witness)
        
        # 验证证明数据
        is_valid = self.manager.verify_proof_data(proof)
        self.assertTrue(is_valid)
        
        # 验证无效证明数据
        invalid_proof = ZKPProof(
            statement="invalid",
            witness="invalid",
            challenge="invalid",
            response="invalid",
            public_data={}
        )
        is_valid = self.manager.verify_proof_data(invalid_proof)
        self.assertFalse(is_valid)
    
    def test_remove_proof(self):
        """测试移除证明"""
        statement = "removal_test"
        witness = "removal_witness"
        
        # 创建证明
        proof_id = self.manager.create_proof(statement, witness)
        self.assertIsNotNone(proof_id)
        
        # 验证证明存在
        self.assertIn(proof_id, self.manager.proof_store)
        is_valid_before = self.manager.verify_proof_by_id(proof_id)
        self.assertTrue(is_valid_before)
        
        # 移除证明
        removed = self.manager.remove_proof(proof_id)
        self.assertTrue(removed)
        
        # 验证证明已移除
        self.assertNotIn(proof_id, self.manager.proof_store)
        is_valid_after = self.manager.verify_proof_by_id(proof_id)
        self.assertFalse(is_valid_after)
    
    def test_get_nonexistent_proof(self):
        """测试获取不存在的证明"""
        proof = self.manager.get_proof("nonexistent_proof_id")
        self.assertIsNone(proof)


class TestZKPBlockchainIntegration(unittest.TestCase):
    """ZKPBlockchainIntegration类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = ZKPManager()
        self.blockchain_integration = ZKPBlockchainIntegration(self.manager)
    
    def test_add_and_verify_zkp_to_blockchain(self):
        """测试添加和验证区块链零知识证明"""
        statement = "blockchain_proof_test"
        witness = "blockchain_witness"
        public_data = {"user_id": "test_user", "action": "transaction"}
        
        # 添加零知识证明到区块链
        result = self.blockchain_integration.add_zkp_to_blockchain(statement, witness, public_data)
        
        self.assertIn("proof_id", result)
        self.assertIn("verified", result)
        self.assertIn("statement", result)
        self.assertIn("public_data", result)
        
        self.assertTrue(result["verified"])
        self.assertEqual(result["statement"], statement)
        self.assertEqual(result["public_data"], public_data)
        
        # 验证区块链上的证明
        verification_result = self.blockchain_integration.verify_zkp_on_blockchain(result["proof_id"])
        
        self.assertIn("valid", verification_result)
        self.assertTrue(verification_result["valid"])
        self.assertEqual(verification_result["proof_id"], result["proof_id"])
        self.assertEqual(verification_result["statement"], statement)


if __name__ == '__main__':
    unittest.main()