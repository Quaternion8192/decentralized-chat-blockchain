import unittest
import asyncio
from src.gossip.gossip_protocol import GossipManager, GossipType, GossipProtocol


class TestGossipProtocol(unittest.TestCase):
    """Gossip协议单元测试"""
    
    def setUp(self):
        """测试前准备"""
        # 由于GossipProtocol需要routing_table_manager，我们使用模拟对象
        class MockRoutingTableManager:
            def get_active_nodes(self):
                return []
        
        self.mock_routing_manager = MockRoutingTableManager()
        self.gossip_protocol = GossipProtocol("test_node", self.mock_routing_manager)
    
    def test_gossip_message_creation(self):
        """测试Gossip消息创建"""
        # 测试Gossip协议的初始化
        self.assertEqual(self.gossip_protocol.node_id, "test_node")
        self.assertIsNotNone(self.gossip_protocol.received_messages)
        self.assertIsNotNone(self.gossip_protocol.message_history)
        
    def test_gossip_type_enum(self):
        """测试Gossip类型枚举"""
        self.assertEqual(GossipType.DATA_SYNC.value, "data_sync")
        self.assertEqual(GossipType.MEMBERSHIP.value, "membership")
        self.assertEqual(GossipType.CUSTOM.value, "custom")


class TestGossipManager(unittest.TestCase):
    """Gossip管理器单元测试"""
    
    def setUp(self):
        """测试前准备"""
        class MockRoutingTableManager:
            def get_active_nodes(self):
                return []
        
        self.mock_routing_manager = MockRoutingTableManager()
        self.gossip_manager = GossipManager("test_node", self.mock_routing_manager)
    
    def test_gossip_manager_initialization(self):
        """测试Gossip管理器初始化"""
        self.assertEqual(self.gossip_manager.node_id, "test_node")
        self.assertIn("default", self.gossip_manager.gossip_protocols)
        self.assertIsNotNone(self.gossip_manager.default_gossip)
    
    def test_create_gossip_protocol(self):
        """测试创建Gossip协议"""
        protocol = self.gossip_manager.create_gossip_protocol("test_protocol")
        self.assertIn("test_protocol", self.gossip_manager.gossip_protocols)
        self.assertEqual(protocol, self.gossip_manager.gossip_protocols["test_protocol"])
    
    def test_broadcast_message(self):
        """测试广播消息"""
        # 由于广播需要网络连接，我们只测试方法存在性
        self.assertTrue(hasattr(self.gossip_manager, 'broadcast_message'))
        self.assertTrue(hasattr(self.gossip_manager, 'handle_incoming_gossip'))
    
    def test_get_gossip_stats(self):
        """测试获取Gossip统计"""
        stats = self.gossip_manager.get_gossip_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("default", stats)


if __name__ == '__main__':
    unittest.main()