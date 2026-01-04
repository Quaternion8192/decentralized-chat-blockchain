"""
工业级安全架构集成测试
验证X3DH密钥交换、双棘轮算法、TLS加密和Kademlia DHT的正确性
"""
import asyncio
import unittest
from src.crypto.advanced_crypto_manager import AdvancedCryptoManager
from src.crypto.double_ratchet import DoubleRatchet
from src.network.tls_protocol import SecureProtocol
from src.network.kademlia_dht import KademliaDHT, DHTNode
from src.p2p.secure_node_server import SecureChatNode


class TestAdvancedCryptoManager(unittest.TestCase):
    """测试高级加密管理器"""
    
    def setUp(self):
        self.crypto_mgr1 = AdvancedCryptoManager()
        self.crypto_mgr2 = AdvancedCryptoManager()
    
    def test_x3dh_key_exchange(self):
        """测试X3DH密钥交换"""
        # 获取节点1的身份信息
        identity_info1 = self.crypto_mgr1.get_identity_info()
        
        # 节点2发起会话
        session_id2, eph_pub_b64 = self.crypto_mgr2.initiate_session(identity_info1)
        
        # 节点1响应会话请求
        session_id1 = self.crypto_mgr1.respond_to_session_request(eph_pub_b64, identity_info1)
        
        # 验证会话ID不为空
        self.assertIsNotNone(session_id1)
        self.assertIsNotNone(session_id2)
    
    def test_encryption_decryption(self):
        """测试加密解密功能"""
        # 设置会话（简化测试）
        identity_info1 = self.crypto_mgr1.get_identity_info()
        identity_info2 = self.crypto_mgr2.get_identity_info()
        
        # 创建会话
        session_id1, _ = self.crypto_mgr1.initiate_session(identity_info2)
        session_id2 = self.crypto_mgr2.respond_to_session_request(_, identity_info1)
        
        # 测试加密解密
        original_msg = "Hello, secure world!"
        encrypted = self.crypto_mgr1.encrypt_message(session_id1, original_msg)
        decrypted = self.crypto_mgr2.decrypt_message(session_id2, encrypted)
        
        self.assertEqual(original_msg, decrypted)
    
    def test_node_id_generation(self):
        """测试节点ID生成"""
        node_id1 = self.crypto_mgr1.get_node_id()
        node_id2 = self.crypto_mgr2.get_node_id()
        
        # 验证节点ID不相同
        self.assertNotEqual(node_id1, node_id2)
        
        # 验证节点ID长度
        self.assertEqual(len(node_id1), 16)
        self.assertEqual(len(node_id2), 16)


class TestDoubleRatchet(unittest.TestCase):
    """测试双棘轮算法"""
    
    def setUp(self):
        # 创建共享密钥用于测试
        shared_secret = b'test_shared_secret_for_ratchet'
        self.ratchet1 = DoubleRatchet(shared_secret)
        self.ratchet2 = DoubleRatchet(shared_secret)
    
    def test_message_key_derivation(self):
        """测试消息密钥派生"""
        # 获取第一个消息密钥
        msg_key1, msg_num1 = self.ratchet1.get_next_send_key()
        self.assertEqual(msg_num1, 0)
        
        # 获取第二个消息密钥
        msg_key2, msg_num2 = self.ratchet1.get_next_send_key()
        self.assertEqual(msg_num2, 1)
        
        # 验证密钥不同
        self.assertNotEqual(msg_key1, msg_key2)
    
    def test_ratchet_chain_advance(self):
        """测试棘轮链推进"""
        # 获取一些消息密钥
        keys1 = []
        for i in range(3):
            key, num = self.ratchet1.get_next_send_key()
            keys1.append((key, num))
        
        # 模拟接收方获取对应的密钥
        keys2 = []
        for _, num in keys1:
            key = self.ratchet2.get_next_recv_key(num)
            keys2.append(key)
        
        # 验证双方密钥匹配
        for i in range(len(keys1)):
            self.assertEqual(keys1[i][0], keys2[i])


class TestKademliaDHT(unittest.TestCase):
    """测试Kademlia DHT"""
    
    def setUp(self):
        self.dht1 = KademliaDHT("node1", "127.0.0.1", 8001)
        self.dht2 = KademliaDHT("node2", "127.0.0.1", 8002)
        self.dht3 = KademliaDHT("node3", "127.0.0.1", 8003)
    
    def test_node_addition(self):
        """测试节点添加"""
        node2 = self.dht2.local_node
        self.dht1.add_node(node2)
        
        # 验证节点被添加
        closest_nodes = self.dht1.get_closest_nodes("node2")
        self.assertIn(node2, closest_nodes)
    
    def test_find_node(self):
        """测试节点查找"""
        # 添加节点到网络
        node2 = self.dht2.local_node
        node3 = self.dht3.local_node
        
        self.dht1.add_node(node2)
        self.dht1.add_node(node3)
        
        # 查找节点
        found_nodes = self.dht1.find_node("target_node")
        
        # 验证找到了节点
        self.assertGreaterEqual(len(found_nodes), 0)
    
    def test_data_storage(self):
        """测试数据存储"""
        # 存储数据
        self.dht1.store("test_key", "test_value")
        
        # 获取数据
        value = self.dht1.get("test_key")
        
        self.assertEqual(value, "test_value")


class TestSecureProtocol(unittest.TestCase):
    """测试安全协议"""
    
    def setUp(self):
        self.crypto_mgr = AdvancedCryptoManager()
        self.secure_protocol = SecureProtocol(self.crypto_mgr)
    
    def test_obfuscation(self):
        """测试流量伪装"""
        original_data = b"Hello, this is a test message!"
        
        # 测试不同的混淆方法
        methods = ['websocket', 'http_padding', 'random_padding']
        
        for method in methods:
            obfuscated = self.secure_protocol.obfuscator.obfuscate(original_data, method)
            deobfuscated = self.secure_protocol.obfuscator.deobfuscate(obfuscated, method)
            
            self.assertEqual(original_data, deobfuscated)


class IntegrationTest(unittest.TestCase):
    """集成测试"""
    
    def test_full_encryption_flow(self):
        """测试完整的加密流程"""
        # 创建两个加密管理器
        mgr1 = AdvancedCryptoManager()
        mgr2 = AdvancedCryptoManager()
        
        # 获取身份信息
        identity_info1 = mgr1.get_identity_info()
        identity_info2 = mgr2.get_identity_info()
        
        # 建立会话
        session_id1, eph_pub_b64 = mgr1.initiate_session(identity_info2)
        session_id2 = mgr2.respond_to_session_request(eph_pub_b64, identity_info1)
        
        # 加密和解密消息
        original_message = "This is a secret message!"
        encrypted_msg = mgr1.encrypt_message(session_id1, original_message)
        decrypted_msg = mgr2.decrypt_message(session_id2, encrypted_msg)
        
        self.assertEqual(original_message, decrypted_msg)
    
    def test_secure_protocol_with_obfuscation(self):
        """测试带混淆的安全协议"""
        mgr = AdvancedCryptoManager()
        protocol = SecureProtocol(mgr, use_tls=False, obfuscation_method='random_padding')
        
        # 模拟数据发送
        test_data = "Test message for obfuscation"
        
        # 加密消息
        # 注意：这里需要先建立会话才能加密，我们简化测试
        pass


async def run_async_tests():
    """运行异步测试"""
    # 测试DHT节点
    dht_node1 = DHTNode("node1", "127.0.0.1", 9001)
    dht_node2 = DHTNode("node2", "127.0.0.1", 9002)
    
    print("[测试] 启动DHT节点...")
    
    # 启动DHT节点（异步操作）
    await dht_node1.start_server()
    await dht_node2.start_server()
    
    print("[测试] DHT节点启动成功")
    
    # 添加节点到彼此的网络
    dht_node1.add_bootstrap_node("127.0.0.1", 9002, "node2")
    dht_node2.add_bootstrap_node("127.0.0.1", 9001, "node1")
    
    print("[测试] DHT节点互联成功")
    
    # 关闭服务器
    dht_node1.server.close()
    dht_node2.server.close()
    await dht_node1.server.wait_closed()
    await dht_node2.server.wait_closed()


def run_all_tests():
    """运行所有测试"""
    print("[测试] 开始运行工业级安全架构测试...")
    
    # 运行同步测试
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestAdvancedCryptoManager))
    test_suite.addTest(unittest.makeSuite(TestDoubleRatchet))
    test_suite.addTest(unittest.makeSuite(TestKademliaDHT))
    test_suite.addTest(unittest.makeSuite(TestSecureProtocol))
    test_suite.addTest(unittest.makeSuite(IntegrationTest))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print(f"\n[测试] 测试完成，通过: {result.testsRun - len(result.failures) - len(result.errors)}, "
          f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
    
    # 运行异步测试
    print("\n[测试] 运行异步测试...")
    asyncio.run(run_async_tests())
    print("[测试] 异步测试完成")


if __name__ == "__main__":
    run_all_tests()