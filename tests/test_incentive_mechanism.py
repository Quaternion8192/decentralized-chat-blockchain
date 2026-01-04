import unittest
import time
from src.incentive.incentive_mechanism import IncentiveMechanism, NodeType, NodeMetrics, RewardPool


class TestIncentiveMechanism(unittest.TestCase):
    """激励机制单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.incentive_mechanism = IncentiveMechanism()
    
    def test_node_metrics_creation(self):
        """测试节点指标创建"""
        # 由于NodeMetrics现在需要参数，使用默认值创建
        metrics = NodeMetrics(
            node_id="test_node",
            uptime=0,
            bandwidth_provided=0,
            storage_provided=0,
            messages_forwarded=0,
            blocks_validated=0,
            last_updated=time.time(),
            reputation_score=50.0
        )
        
        self.assertEqual(metrics.messages_forwarded, 0)
        self.assertEqual(metrics.blocks_validated, 0)
        self.assertEqual(metrics.bandwidth_provided, 0)
        self.assertEqual(metrics.storage_provided, 0)
        self.assertEqual(metrics.reputation_score, 50.0)  # 默认声誉分数
        self.assertEqual(metrics.uptime, 0)
    
    def test_reward_pool_creation(self):
        """测试奖励池创建"""
        reward_pool = RewardPool(initial_supply=1000)
        
        self.assertEqual(reward_pool.total_supply, 1000)
        self.assertEqual(reward_pool.distributed_tokens, 0)
        self.assertEqual(reward_pool.remaining_tokens, 1000)
    
    def test_register_node(self):
        """测试注册节点"""
        node_id = "test_node_123"
        
        # 注册节点
        self.incentive_mechanism.register_node(node_id, NodeType.FULL)
        
        # 检查节点是否已注册
        self.assertIn(node_id, self.incentive_mechanism.node_types)
        self.assertEqual(self.incentive_mechanism.node_types[node_id], NodeType.FULL)
        self.assertIn(node_id, self.incentive_mechanism.node_metrics)
        self.assertIn(node_id, self.incentive_mechanism.node_balances)
        self.assertEqual(self.incentive_mechanism.node_balances[node_id], 0)
    
    def test_update_node_metrics(self):
        """测试更新节点指标"""
        node_id = "test_node_456"
        self.incentive_mechanism.register_node(node_id, NodeType.LIGHT)
        
        # 更新指标
        self.incentive_mechanism.update_node_metrics(
            node_id,
            messages_forwarded=5,
            blocks_validated=2,
            bandwidth_provided=1024*1024,  # 1MB
            storage_provided=100*1024*1024  # 100MB
        )
        
        metrics = self.incentive_mechanism.node_metrics[node_id]
        self.assertEqual(metrics.messages_forwarded, 5)
        self.assertEqual(metrics.blocks_validated, 2)
        self.assertEqual(metrics.bandwidth_provided, 1024*1024)
        self.assertEqual(metrics.storage_provided, 100*1024*1024)
    
    def test_calculate_reputation_score(self):
        """测试计算声誉分数"""
        node_id = "test_node_789"
        self.incentive_mechanism.register_node(node_id, NodeType.RELAY)
        
        # 更新一些指标
        self.incentive_mechanism.update_node_metrics(
            node_id,
            messages_forwarded=1000,
            blocks_validated=50,
            uptime=86400  # 1天
        )
        
        # 计算声誉分数
        reputation = self.incentive_mechanism.calculate_reputation_score(node_id)
        self.assertGreaterEqual(reputation, 0)
        self.assertLessEqual(reputation, 100)
        
        # 验证指标中的声誉分数也被更新
        metrics = self.incentive_mechanism.node_metrics[node_id]
        self.assertEqual(metrics.reputation_score, reputation)
    
    def test_calculate_reward(self):
        """测试计算奖励"""
        # 注册不同类型节点
        self.incentive_mechanism.register_node("full_node", NodeType.FULL)
        self.incentive_mechanism.register_node("relay_node", NodeType.RELAY)
        self.incentive_mechanism.register_node("light_node", NodeType.LIGHT)
        
        # 更新指标
        self.incentive_mechanism.update_node_metrics("full_node", blocks_validated=10, storage_provided=1000*1024*1024)
        self.incentive_mechanism.update_node_metrics("relay_node", messages_forwarded=500, bandwidth_provided=100*1024*1024)
        self.incentive_mechanism.update_node_metrics("light_node", messages_forwarded=10)
        
        # 计算奖励
        full_reward = self.incentive_mechanism.calculate_reward("full_node")
        relay_reward = self.incentive_mechanism.calculate_reward("relay_node")
        light_reward = self.incentive_mechanism.calculate_reward("light_node")
        
        # 验证奖励计算
        self.assertGreaterEqual(full_reward, 0)
        self.assertGreaterEqual(relay_reward, 0)
        self.assertGreaterEqual(light_reward, 0)
        
        # 完整节点应该获得更高奖励
        self.assertGreaterEqual(full_reward, light_reward)
    
    def test_distribute_rewards(self):
        """测试分配奖励"""
        node_id = "test_node_999"
        self.incentive_mechanism.register_node(node_id, NodeType.FULL)
        
        # 更新指标
        self.incentive_mechanism.update_node_metrics(node_id, blocks_validated=5)
        
        # 分配奖励前的余额
        original_balance = self.incentive_mechanism.node_balances[node_id]
        
        # 分发奖励
        reward_details, total_reward = self.incentive_mechanism.distribute_rewards()
        
        # 验证奖励已分配
        new_balance = self.incentive_mechanism.node_balances[node_id]
        self.assertGreater(new_balance, original_balance)
        self.assertGreater(total_reward, 0)
    
    def test_get_node_info(self):
        """测试获取节点信息"""
        node_id = "info_test_node"
        self.incentive_mechanism.register_node(node_id, NodeType.FULL)
        
        # 更新指标
        self.incentive_mechanism.update_node_metrics(
            node_id,
            messages_forwarded=10,
            blocks_validated=5,
            bandwidth_provided=1024*1024
        )
        
        # 获取节点信息
        node_info = self.incentive_mechanism.get_node_info(node_id)
        
        self.assertIsNotNone(node_info)
        self.assertEqual(node_info["node_id"], node_id)
        self.assertEqual(node_info["node_type"], NodeType.FULL.value)
        self.assertEqual(node_info["messages_forwarded"], 10)
        self.assertEqual(node_info["blocks_validated"], 5)
        self.assertEqual(node_info["bandwidth_provided"], 1024*1024)
        
        # 测试获取不存在节点的信息
        nonexistent_info = self.incentive_mechanism.get_node_info("nonexistent")
        self.assertIsNone(nonexistent_info)


if __name__ == '__main__':
    unittest.main()