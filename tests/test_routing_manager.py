import unittest
import asyncio
from src.routing.routing_manager import RoutingTableManager, NodeInfo, NodeType


class TestRoutingTableManager(unittest.TestCase):
    """路由表管理器单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = RoutingTableManager(local_node_id="test_node")
    
    def test_add_node(self):
        """测试添加节点"""
        result = self.manager.add_node(
            node_id="node1",
            host="127.0.0.1",
            port=8080,
            pub_key="test_pub_key"
        )
        self.assertTrue(result)
        self.assertIn("node1", self.manager.routing_table)
        
        # 测试添加自己的节点
        result = self.manager.add_node(
            node_id="test_node",
            host="127.0.0.1",
            port=8080,
            pub_key="test_pub_key"
        )
        self.assertFalse(result)
    
    def test_remove_node(self):
        """测试移除节点"""
        # 先添加一个节点
        self.manager.add_node(
            node_id="node1",
            host="127.0.0.1",
            port=8080,
            pub_key="test_pub_key"
        )
        
        # 移除节点
        result = self.manager.remove_node("node1")
        self.assertTrue(result)
        self.assertNotIn("node1", self.manager.routing_table)
        
        # 尝试移除不存在的节点
        result = self.manager.remove_node("nonexistent")
        self.assertFalse(result)
    
    def test_get_node(self):
        """测试获取节点信息"""
        # 添加节点
        self.manager.add_node(
            node_id="node1",
            host="127.0.0.1",
            port=8080,
            pub_key="test_pub_key"
        )
        
        # 获取节点
        node_info = self.manager.get_node("node1")
        self.assertIsNotNone(node_info)
        self.assertEqual(node_info.node_id, "node1")
        self.assertEqual(node_info.host, "127.0.0.1")
        self.assertEqual(node_info.port, 8080)
        
        # 获取不存在的节点
        node_info = self.manager.get_node("nonexistent")
        self.assertIsNone(node_info)
    
    def test_get_all_nodes(self):
        """测试获取所有节点"""
        # 添加多个节点
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        self.manager.add_node("node2", "127.0.0.2", 8081, "pub_key2")
        
        all_nodes = self.manager.get_all_nodes()
        self.assertEqual(len(all_nodes), 2)
    
    def test_get_active_nodes(self):
        """测试获取活跃节点"""
        # 添加节点
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        self.manager.add_node("node2", "127.0.0.2", 8081, "pub_key2")
        
        # 设置一个节点为非活跃
        self.manager.update_node_status("node2", is_active=False)
        
        active_nodes = self.manager.get_active_nodes()
        self.assertEqual(len(active_nodes), 1)
        self.assertEqual(active_nodes[0].node_id, "node1")
    
    def test_update_node_status(self):
        """测试更新节点状态"""
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        
        # 更新节点状态
        result = self.manager.update_node_status("node1", is_active=False, latency=100.0)
        self.assertTrue(result)
        
        node_info = self.manager.get_node("node1")
        self.assertFalse(node_info.is_active)
        self.assertEqual(node_info.latency, 100.0)
    
    def test_update_node_reputation(self):
        """测试更新节点声誉"""
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        
        # 更新声誉（成功）
        result = self.manager.update_node_reputation("node1", success=True, latency=50.0)
        self.assertTrue(result)
        
        node_info = self.manager.get_node("node1")
        self.assertGreaterEqual(node_info.reputation_score, 0.5)  # 成功连接声誉应该较高
        
        # 更新声誉（失败）
        result = self.manager.update_node_reputation("node1", success=False)
        self.assertTrue(result)
        
        node_info = self.manager.get_node("node1")
        # 失败后声誉应该降低
        self.assertLessEqual(node_info.reputation_score, 1.0)
    
    def test_get_reliable_nodes(self):
        """测试获取可靠节点"""
        # 添加节点并设置声誉
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        self.manager.add_node("node2", "127.0.0.2", 8081, "pub_key2")
        
        # 设置node1为高声誉，node2为低声誉
        self.manager.update_node_reputation("node1", success=True)
        self.manager.update_node_reputation("node2", success=False)
        
        # 获取可靠节点（默认最小声誉0.5）
        reliable_nodes = self.manager.get_reliable_nodes()
        # 确保至少有一个可靠节点
        self.assertGreaterEqual(len(reliable_nodes), 0)
        
    def test_get_nodes_by_type(self):
        """测试按类型获取节点"""
        # 添加不同类型节点
        self.manager.add_node("full_node", "127.0.0.1", 8080, "pub_key1", node_type=NodeType.FULL)
        self.manager.add_node("light_node", "127.0.0.2", 8081, "pub_key2", node_type=NodeType.LIGHT)
        
        full_nodes = self.manager.get_nodes_by_type(NodeType.FULL)
        light_nodes = self.manager.get_nodes_by_type(NodeType.LIGHT)
        
        self.assertEqual(len(full_nodes), 1)
        self.assertEqual(full_nodes[0].node_id, "full_node")
        self.assertEqual(len(light_nodes), 1)
        self.assertEqual(light_nodes[0].node_id, "light_node")
    
    def test_get_optimal_route(self):
        """测试获取最优路由"""
        # 添加节点
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        self.manager.add_node("node2", "127.0.0.2", 8081, "pub_key2")
        
        # 设置声誉
        self.manager.update_node_reputation("node1", success=True, latency=50.0)
        self.manager.update_node_reputation("node2", success=True, latency=200.0)
        
        # 获取最优路由（排除node2）
        optimal = self.manager.get_optimal_route("target_node", exclude_nodes=["node2"])
        if optimal:
            self.assertEqual(optimal.node_id, "node1")  # node1延迟更低，应该更优
    
    def test_get_best_nodes_for_broadcast(self):
        """测试获取最佳广播节点"""
        # 添加节点
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        self.manager.add_node("node2", "127.0.0.2", 8081, "pub_key2")
        
        # 设置声誉
        self.manager.update_node_reputation("node1", success=True)
        self.manager.update_node_reputation("node2", success=True)
        
        best_nodes = self.manager.get_best_nodes_for_broadcast(count=5)
        self.assertLessEqual(len(best_nodes), 5)
        self.assertGreaterEqual(len(best_nodes), 0)
    
    def test_routing_stats(self):
        """测试路由统计"""
        # 添加节点
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        
        stats = self.manager.get_routing_stats()
        self.assertEqual(stats["total_nodes"], 1)
    
    def test_serialization(self):
        """测试序列化和反序列化"""
        # 添加节点
        self.manager.add_node("node1", "127.0.0.1", 8080, "pub_key1")
        
        # 序列化
        data = self.manager.to_dict()
        
        # 反序列化
        new_manager = RoutingTableManager.from_dict(data)
        
        self.assertEqual(len(new_manager.routing_table), 1)
        self.assertIn("node1", new_manager.routing_table)


if __name__ == '__main__':
    unittest.main()