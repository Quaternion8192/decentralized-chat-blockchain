import unittest
import time
from src.blockchain.block import Block
from src.blockchain.blockchain import Blockchain


class TestBlock(unittest.TestCase):
    """区块单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.block = Block(
            index=0,
            previous_hash="0",
            timestamp=time.time(),
            data="Genesis Block",
            proposer=None,
            vdf_proof=None
        )
    
    def test_block_creation(self):
        """测试区块创建"""
        self.assertEqual(self.block.index, 0)
        self.assertEqual(self.block.previous_hash, "0")
        self.assertEqual(self.block.data, "Genesis Block")
        self.assertIsNotNone(self.block.hash)
        self.assertEqual(self.block.hash, self.block.calculate_hash())
    
    def test_block_hash_changes(self):
        """测试区块哈希变化"""
        original_hash = self.block.calculate_hash()
        
        # 修改数据
        self.block.data = "Modified Data"
        new_hash = self.block.calculate_hash()
        
        self.assertNotEqual(original_hash, new_hash)
    
    def test_block_to_dict(self):
        """测试区块转字典"""
        block_dict = self.block.to_dict()
        self.assertEqual(block_dict["index"], 0)
        self.assertEqual(block_dict["previous_hash"], "0")
        self.assertEqual(block_dict["data"], "Genesis Block")
        self.assertIsNotNone(block_dict["hash"])
    
    def test_block_from_dict(self):
        """测试从字典创建区块"""
        block_dict = self.block.to_dict()
        new_block = Block.from_dict(block_dict)
        
        self.assertEqual(new_block.index, self.block.index)
        self.assertEqual(new_block.previous_hash, self.block.previous_hash)
        self.assertEqual(new_block.data, self.block.data)
        self.assertEqual(new_block.hash, self.block.hash)


class TestBlockchain(unittest.TestCase):
    """区块链单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.blockchain = Blockchain()
    
    def test_blockchain_creation(self):
        """测试区块链创建"""
        self.assertEqual(len(self.blockchain.chain), 1)  # 创世区块
        self.assertTrue(self.blockchain.is_chain_valid())
    
    def test_add_block(self):
        """测试添加区块"""
        original_length = len(self.blockchain.chain)
        
        # 添加新区块
        new_block = Block(
            index=len(self.blockchain.chain),
            previous_hash=self.blockchain.get_latest_block().hash,
            timestamp=time.time(),
            data="Test Block",
            proposer=None,
            vdf_proof=None
        )
        self.blockchain.add_block(new_block)
        
        self.assertEqual(len(self.blockchain.chain), original_length + 1)
        self.assertTrue(self.blockchain.is_chain_valid())
    
    def test_blockchain_validity(self):
        """测试区块链有效性"""
        # 添加几个区块
        for i in range(3):
            new_block = Block(
                index=len(self.blockchain.chain),
                previous_hash=self.blockchain.get_latest_block().hash,
                timestamp=time.time(),
                data=f"Block {i}",
                proposer=None,
                vdf_proof=None
            )
            self.blockchain.add_block(new_block)
        
        self.assertTrue(self.blockchain.is_chain_valid())
        
        # 恶意修改区块链中的一个区块
        self.blockchain.chain[1].data = "Malicious Data"
        self.blockchain.chain[1].hash = self.blockchain.chain[1].calculate_hash()
        
        # 验证区块链无效
        self.assertFalse(self.blockchain.is_chain_valid())
    
    def test_blockchain_serialization(self):
        """测试区块链序列化"""
        # 添加一些区块
        for i in range(2):
            new_block = Block(
                index=len(self.blockchain.chain),
                previous_hash=self.blockchain.get_latest_block().hash,
                timestamp=time.time(),
                data=f"Block {i}",
                proposer=None,
                vdf_proof=None
            )
            self.blockchain.add_block(new_block)
        
        # 序列化
        chain_data = self.blockchain.to_list()
        self.assertEqual(len(chain_data), 3)  # 创世区块 + 2个新区块
        
        # 反序列化
        new_blockchain = Blockchain()
        new_blockchain.from_list(chain_data)
        
        self.assertEqual(len(new_blockchain.chain), 3)
        self.assertTrue(new_blockchain.is_chain_valid())
    
    def test_get_block_range(self):
        """测试获取区块范围"""
        # 添加一些区块
        for i in range(5):
            new_block = Block(
                index=len(self.blockchain.chain),
                previous_hash=self.blockchain.get_latest_block().hash,
                timestamp=time.time(),
                data=f"Block {i}",
                proposer=None,
                vdf_proof=None
            )
            self.blockchain.add_block(new_block)
        
        # 获取范围
        range_data = self.blockchain.get_block_range(1, 3)
        self.assertEqual(len(range_data), 2)  # 从索引1到2（不包括3）
        
        # 测试边界情况
        range_data = self.blockchain.get_block_range(0, 100)  # 超出范围
        self.assertEqual(len(range_data), len(self.blockchain.chain))
    
    def test_blockchain_info(self):
        """测试区块链信息获取"""
        info = self.blockchain.get_chain_info()
        self.assertEqual(info["length"], 1)
        self.assertTrue(info["valid"])
        self.assertIsNotNone(info["latest_hash"])
        self.assertIsNotNone(info["oldest_hash"])


if __name__ == '__main__':
    unittest.main()