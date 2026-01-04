"""
测试类区块链聊天解决方案的所有组件
"""
import asyncio
import unittest
from src.blockchain.blockchain import Blockchain
from src.crypto.crypto_manager import CryptoManager
from src.core.chat_node import ChatNode


class TestSystem(unittest.TestCase):
    """系统级测试"""
    
    def test_blockchain_functionality(self):
        """测试区块链功能"""
        blockchain = Blockchain()
        
        # 添加一些测试区块
        for i in range(3):
            from src.blockchain.block import Block
            new_block = Block(
                index=len(blockchain.chain),
                previous_hash=blockchain.get_latest_block().hash,
                timestamp=1234567890.0 + i,
                data=f"Test data {i}",
                proposer=None,
                vdf_proof=None
            )
            new_block.hash = new_block.calculate_hash()
            blockchain.chain.append(new_block)
            print(f"添加区块 #{new_block.index}: {new_block.data}")
        
        self.assertEqual(len(blockchain.chain), 4)  # 创世区块 + 3个新区块
        self.assertTrue(blockchain.is_chain_valid())
    
    def test_crypto_functionality(self):
        """测试加密功能"""
        crypto1 = CryptoManager()
        crypto2 = CryptoManager()
        
        original_message = "Hello, this is a secret message!"
        print(f"原始消息: {original_message}")
        
        # 加密
        encrypted = crypto1.hybrid_encrypt(crypto2.get_pub_key_pem(), original_message)
        print(f"加密完成，密文长度: {len(str(encrypted))}")
        
        # 解密
        decrypted = crypto2.hybrid_decrypt(encrypted)
        print(f"解密消息: {decrypted}")
        self.assertEqual(original_message, decrypted)
        
        # 签名和验证
        signature = crypto1.sign(original_message)
        print(f"签名长度: {len(signature)}")
        
        is_valid = CryptoManager.verify(
            crypto1.public_key, 
            original_message, 
            signature
        )
        self.assertTrue(is_valid)
        print(f"签名验证: {is_valid}")
    
    def test_node_functionality(self):
        """测试节点功能"""
        blockchain = Blockchain()
        node = ChatNode("TestNode", "127.0.0.1", 8001, blockchain)
        
        self.assertEqual(node.node_id, "TestNode")
        self.assertEqual(node.addr, ("127.0.0.1", 8001))
        self.assertIsNotNone(node.crypto)
        self.assertIsNotNone(node.routing_table_manager)
    
    def test_full_system_integration(self):
        """测试完整系统集成"""
        # 创建区块链
        blockchain = Blockchain()
        print(f"创世区块: #{blockchain.chain[0].index} - {blockchain.chain[0].data[:20]}...")
        
        # 创建两个节点
        node1 = ChatNode("Alice", "127.0.0.1", 8001, blockchain)
        node2 = ChatNode("Bob", "127.0.0.1", 8002, blockchain)
        
        print(f"节点1: {node1.node_id} - DID: {node1.get_did()}")
        print(f"节点2: {node2.node_id} - DID: {node2.get_did()}")
        
        # 模拟节点发现
        node1.routing_table_manager.add_node(
            node_id=node2.node_id,
            host="127.0.0.1", 
            port=8002, 
            pub_key=node2.crypto.get_pub_key_pem()
        )
        
        print(f"节点1路由表: {list(node1.routing_table_manager.routing_table.keys())}")
        
        # 验证节点能够互相找到
        found_node = node1.routing_table_manager.get_node(node2.node_id)
        self.assertIsNotNone(found_node)
        self.assertEqual(found_node.node_id, node2.node_id)
        
        print("系统集成测试通过")


class TestAllModules(unittest.TestCase):
    """测试所有模块的导入和基本功能"""
    
    def test_blockchain_module(self):
        """测试区块链模块"""
        from src.blockchain import block, blockchain
        self.assertIsNotNone(block)
        self.assertIsNotNone(blockchain)
        
    def test_crypto_module(self):
        """测试加密模块"""
        from src.crypto import crypto_manager
        self.assertIsNotNone(crypto_manager)
        
    def test_network_module(self):
        """测试网络模块"""
        from src.network import protocol
        self.assertIsNotNone(protocol)
        
    def test_p2p_module(self):
        """测试P2P模块"""
        from src.p2p import node_server
        self.assertIsNotNone(node_server)
        
    def test_multimedia_module(self):
        """测试多媒体模块"""
        from src.multimedia import multimedia
        self.assertIsNotNone(multimedia)
        
    def test_incentive_module(self):
        """测试激励模块"""
        from src.incentive import incentive_mechanism
        self.assertIsNotNone(incentive_mechanism)
        
    def test_routing_module(self):
        """测试路由模块"""
        from src.routing import routing_manager
        self.assertIsNotNone(routing_manager)
        
    def test_gossip_module(self):
        """测试Gossip模块"""
        from src.gossip import gossip_protocol
        self.assertIsNotNone(gossip_protocol)
        
    def test_vdf_module(self):
        """测试VDF模块"""
        from src.vdf import vdf
        self.assertIsNotNone(vdf)
        
    def test_zkp_module(self):
        """测试零知识证明模块"""
        from src.zkp import zkp
        self.assertIsNotNone(zkp)
        
    def test_ipfs_module(self):
        """测试IPFS模块"""
        from src.ipfs import ipfs_integration
        self.assertIsNotNone(ipfs_integration)
        
    def test_config_module(self):
        """测试配置模块"""
        from src.config import config
        self.assertIsNotNone(config)
        
    def test_core_module(self):
        """测试核心模块"""
        from src.core import chat_node, node
        self.assertIsNotNone(chat_node)
        self.assertIsNotNone(node)


def run_system_tests():
    """运行系统测试"""
    print("开始运行系统测试...")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestAllModules))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n测试结果:")
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"成功: {result.wasSuccessful()}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_system_tests()
    if success:
        print("\n所有系统测试通过！")
    else:
        print("\n部分测试失败，请检查错误信息。")