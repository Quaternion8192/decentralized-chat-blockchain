import unittest
import asyncio
import tempfile
import os
from src.ipfs.ipfs_integration import IPFSClient, IPFSStorage, BlockchainIPFSBridge


class TestIPFSClient(unittest.TestCase):
    """IPFSClient类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        # 使用本地IPFS API端点
        self.client = IPFSClient(api_url="http://localhost:5001")
    
    @unittest.skip("跳过需要真实IPFS节点的测试")
    def test_add_and_get_bytes(self):
        """测试添加和获取字节数据"""
        async def async_test():
            test_data = b"Hello, IPFS!"
            
            # 添加字节数据
            result = await self.client.add_bytes(test_data, "test.txt")
            if result and 'Hash' in result:
                ipfs_hash = result['Hash']
                
                # 获取字节数据
                retrieved_data = await self.client.get_bytes(ipfs_hash)
                self.assertEqual(retrieved_data, test_data)
        
        asyncio.run(async_test())
    
    @unittest.skip("跳过需要真实IPFS节点的测试")
    def test_add_and_get_json(self):
        """测试添加和获取JSON数据"""
        async def async_test():
            test_json = {"message": "Hello, IPFS!", "number": 42}
            
            # 添加JSON数据
            result = await self.client.add_json(test_json)
            if result and 'Hash' in result:
                ipfs_hash = result['Hash']
                
                # 获取JSON数据
                retrieved_json = await self.client.get_json(ipfs_hash)
                self.assertEqual(retrieved_json, test_json)
        
        asyncio.run(async_test())
    
    @unittest.skip("跳过需要真实IPFS节点的测试")
    def test_pin_operations(self):
        """测试固定操作"""
        async def async_test():
            test_data = b"Test data for pinning"
            
            # 添加数据
            result = await self.client.add_bytes(test_data, "pintest.txt")
            if result and 'Hash' in result:
                ipfs_hash = result['Hash']
                
                # 固定对象
                pin_result = await self.client.pin_add(ipfs_hash)
                self.assertTrue(pin_result)
                
                # 取消固定对象
                unpin_result = await self.client.pin_rm(ipfs_hash)
                self.assertTrue(unpin_result)
        
        asyncio.run(async_test())


class TestIPFSStorage(unittest.TestCase):
    """IPFSStorage类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.storage = IPFSStorage(api_url="http://localhost:5001")
    
    @unittest.skip("跳过需要真实IPFS节点的测试")
    def test_store_and_retrieve_data(self):
        """测试存储和检索数据"""
        async def async_test():
            # 测试字符串数据
            test_string = "Hello, IPFS Storage!"
            ipfs_hash = await self.storage.store_data(test_string)
            
            if ipfs_hash:
                retrieved_data = await self.storage.retrieve_data(ipfs_hash)
                self.assertEqual(retrieved_data, test_string)
            
            # 测试JSON数据
            test_json = {"key": "value", "number": 123}
            ipfs_hash = await self.storage.store_data(test_json)
            
            if ipfs_hash:
                retrieved_json = await self.storage.retrieve_data(ipfs_hash)
                self.assertEqual(retrieved_json, test_json)
        
        asyncio.run(async_test())
    
    @unittest.skip("跳过需要真实IPFS节点的测试")
    def test_store_and_retrieve_file(self):
        """测试存储和检索文件"""
        async def async_test():
            # 创建临时文件进行测试
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                temp_file.write("Test file content for IPFS")
                temp_file_path = temp_file.name
            
            try:
                # 存储文件
                ipfs_hash = await self.storage.store_file(temp_file_path)
                
                if ipfs_hash:
                    # 检索文件到新位置
                    with tempfile.NamedTemporaryFile(delete=False, suffix='_retrieved.txt') as output_file:
                        output_path = output_file.name
                    
                    try:
                        success = await self.storage.retrieve_file(ipfs_hash, output_path)
                        self.assertTrue(success)
                        
                        # 验证文件内容
                        with open(output_path, 'r', encoding='utf-8') as f:
                            retrieved_content = f.read()
                        
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            original_content = f.read()
                        
                        self.assertEqual(retrieved_content, original_content)
                        
                    finally:
                        # 清理检索的文件
                        if os.path.exists(output_path):
                            os.remove(output_path)
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        
        asyncio.run(async_test())


class TestBlockchainIPFSBridge(unittest.TestCase):
    """BlockchainIPFSBridge类单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.storage = IPFSStorage(api_url="http://localhost:5001")
        self.bridge = BlockchainIPFSBridge(self.storage)
    
    @unittest.skip("跳过需要真实IPFS节点的测试")
    def test_store_and_retrieve_large_data(self):
        """测试存储和检索大型数据"""
        async def async_test():
            large_data = {
                "block_data": "A" * 1000,  # 模拟大块数据
                "transactions": [{"from": f"node_{i}", "to": f"node_{i+1}", "amount": i} for i in range(10)],
                "metadata": {"version": "1.0", "type": "block_data"}
            }
            
            # 存储大型数据
            reference = await self.bridge.store_large_data(large_data)
            
            if reference:
                self.assertIn('ipfs_hash', reference)
                self.assertIn('timestamp', reference)
                
                # 检索大型数据
                retrieved_data = await self.bridge.retrieve_large_data(reference)
                self.assertEqual(retrieved_data, large_data)
        
        asyncio.run(async_test())


# 创建一个模拟IPFS客户端用于单元测试，避免依赖真实IPFS节点
class MockIPFSClient:
    """模拟IPFS客户端，用于单元测试"""
    
    def __init__(self, api_url: str = "http://localhost:5001"):
        self.api_url = api_url
        self.storage = {}  # 模拟存储
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def add_bytes(self, data: bytes, filename: str = "data") -> dict:
        """模拟添加字节数据"""
        import hashlib
        ipfs_hash = hashlib.sha256(data).hexdigest()[:16]  # 简化的哈希
        self.storage[ipfs_hash] = data
        return {"Hash": ipfs_hash, "Name": filename}
    
    async def get_bytes(self, ipfs_hash: str) -> bytes:
        """模拟获取字节数据"""
        return self.storage.get(ipfs_hash)
    
    async def add_json(self, data) -> dict:
        """模拟添加JSON数据"""
        import json
        json_str = json.dumps(data, ensure_ascii=False)
        return await self.add_bytes(json_str.encode('utf-8'), "data.json")
    
    async def get_json(self, ipfs_hash: str):
        """模拟获取JSON数据"""
        import json
        data = await self.get_bytes(ipfs_hash)
        if data:
            return json.loads(data.decode('utf-8'))
        return None
    
    async def pin_add(self, ipfs_hash: str) -> bool:
        """模拟固定操作"""
        return ipfs_hash in self.storage
    
    async def pin_rm(self, ipfs_hash: str) -> bool:
        """模拟取消固定操作"""
        return ipfs_hash in self.storage
    
    async def get_stats(self) -> dict:
        """模拟获取统计信息"""
        return {"totalIn": 100, "totalOut": 100, "rateIn": 10, "rateOut": 10}


class TestIPFSStorageWithMock(unittest.TestCase):
    """使用模拟客户端的IPFSStorage单元测试"""
    
    def setUp(self):
        """测试前准备"""
        from unittest.mock import patch
        self.patcher = patch('src.ipfs.ipfs_integration.IPFSClient', MockIPFSClient)
        self.MockIPFSClient = self.patcher.start()
        self.storage = IPFSStorage(api_url="http://localhost:5001")
    
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    def test_store_and_retrieve_data_with_mock(self):
        """使用模拟客户端测试存储和检索数据"""
        async def async_test():
            # 测试字符串数据
            test_string = "Hello, Mock IPFS!"
            ipfs_hash = await self.storage.store_data(test_string)
            
            self.assertIsNotNone(ipfs_hash)
            retrieved_data = await self.storage.retrieve_data(ipfs_hash)
            self.assertEqual(retrieved_data, test_string)
            
            # 测试JSON数据
            test_json = {"key": "value", "number": 123}
            ipfs_hash = await self.storage.store_data(test_json)
            
            self.assertIsNotNone(ipfs_hash)
            retrieved_json = await self.storage.retrieve_data(ipfs_hash)
            self.assertEqual(retrieved_json, test_json)
        
        asyncio.run(async_test())
    
    def test_store_and_retrieve_bytes_with_mock(self):
        """使用模拟客户端测试存储和检索字节数据"""
        async def async_test():
            test_bytes = b"Hello, Mock IPFS Bytes!"
            ipfs_hash = await self.storage.store_data(test_bytes)
            
            self.assertIsNotNone(ipfs_hash)
            retrieved_bytes = await self.storage.retrieve_data(ipfs_hash)
            self.assertEqual(retrieved_bytes, test_bytes)
        
        asyncio.run(async_test())


class TestBlockchainIPFSBridgeWithMock(unittest.TestCase):
    """使用模拟客户端的BlockchainIPFSBridge单元测试"""
    
    def setUp(self):
        """测试前准备"""
        from unittest.mock import patch
        self.patcher = patch('src.ipfs.ipfs_integration.IPFSClient', MockIPFSClient)
        self.patcher.start()
        
        mock_storage = IPFSStorage(api_url="http://localhost:5001")
        self.bridge = BlockchainIPFSBridge(mock_storage)
    
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    def test_store_and_retrieve_large_data_with_mock(self):
        """使用模拟客户端测试存储和检索大型数据"""
        async def async_test():
            large_data = {
                "block_data": "A" * 100,  # 较小的数据用于测试
                "transactions": [{"from": f"node_{i}", "to": f"node_{i+1}", "amount": i} for i in range(5)],
                "metadata": {"version": "1.0", "type": "block_data"}
            }
            
            # 存储大型数据
            reference = await self.bridge.store_large_data(large_data)
            
            self.assertIsNotNone(reference)
            self.assertIn('ipfs_hash', reference)
            self.assertIn('timestamp', reference)
            
            # 检索大型数据
            retrieved_data = await self.bridge.retrieve_large_data(reference)
            self.assertEqual(retrieved_data, large_data)
        
        asyncio.run(async_test())


if __name__ == '__main__':
    unittest.main()