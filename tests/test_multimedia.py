import unittest
import os
from src.multimedia.multimedia import MultimediaMessage, MultimediaProcessor, EncryptedMultimediaProcessor


class TestMultimedia(unittest.TestCase):
    """多媒体处理单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = MultimediaProcessor()
        self.encrypted_processor = EncryptedMultimediaProcessor()
    
    def test_multimedia_message_creation(self):
        """测试多媒体消息创建"""
        message_id = "test_msg_123"
        media_type = "image/jpeg"
        data = b"fake image data"
        metadata = {"filename": "test.jpg", "size": 1024}
        
        multimedia_msg = self.processor.create_multimedia_message(
            media_type, data, metadata
        )
        
        # 确保消息创建成功
        self.assertIsNotNone(multimedia_msg)
        multimedia_msg.message_id = message_id
        
        self.assertEqual(multimedia_msg.message_id, message_id)
        self.assertEqual(multimedia_msg.media_type, media_type)
        self.assertEqual(multimedia_msg.data, data)
        self.assertEqual(multimedia_msg.metadata, metadata)
    
    def test_multimedia_message_default_id(self):
        """测试多媒体消息默认ID生成"""
        media_type = "text/plain"
        data = b"test data"
        
        multimedia_msg = self.processor.create_multimedia_message(
            media_type, data
        )
        
        # 确保消息创建成功
        self.assertIsNotNone(multimedia_msg)
        self.assertIsNotNone(multimedia_msg.message_id)
        self.assertEqual(multimedia_msg.media_type, media_type)
        self.assertEqual(multimedia_msg.data, data)
    
    def test_multimedia_message_serialization(self):
        """测试多媒体消息序列化"""
        media_type = "video/mp4"
        data = b"fake video data"
        metadata = {"duration": 30, "resolution": "1920x1080"}
        
        original_msg = self.processor.create_multimedia_message(
            media_type, data, metadata
        )
        
        # 确保消息创建成功
        self.assertIsNotNone(original_msg)
        
        # 序列化
        msg_dict = original_msg.to_dict()
        
        # 反序列化
        restored_msg = MultimediaMessage.from_dict(msg_dict)
        
        self.assertEqual(original_msg.message_id, restored_msg.message_id)
        self.assertEqual(original_msg.media_type, restored_msg.media_type)
        self.assertEqual(original_msg.data, restored_msg.data)
        self.assertEqual(original_msg.metadata, restored_msg.metadata)
    
    def test_file_extension(self):
        """测试文件扩展名获取"""
        test_cases = [
            ("image/jpeg", ".jpg"),
            ("image/png", ".png"),
            ("video/mp4", ".mp4"),
            ("audio/mp3", ".mp3"),
            ("text/plain", ".txt"),
            ("application/pdf", ".pdf"),
            ("unknown/type", ".bin")
        ]
        
        for media_type, expected_ext in test_cases:
            msg = self.processor.create_multimedia_message(
                media_type, b"test data"
            )
            # 确保消息创建成功
            self.assertIsNotNone(msg)
            self.assertEqual(msg.get_file_extension(), expected_ext)
    
    def test_save_and_load_file(self):
        """测试保存和加载文件"""
        media_type = "text/plain"
        data = b"Hello, World!"
        msg = self.processor.create_multimedia_message(
            media_type, data
        )
        
        # 确保消息创建成功
        self.assertIsNotNone(msg)
        
        # 保存到文件
        filename = f"test_{msg.message_id}.txt"
        success = self.processor.save_to_file(msg, filename)
        self.assertTrue(success)
        
        # 检查文件是否存在
        self.assertTrue(os.path.exists(filename))
        
        # 从文件加载
        loaded_msg = self.processor.load_from_file(filename, media_type)
        self.assertIsNotNone(loaded_msg)
        self.assertEqual(loaded_msg.data, data)
        self.assertEqual(loaded_msg.media_type, media_type)
        
        # 清理测试文件
        if os.path.exists(filename):
            os.remove(filename)
    
    def test_encrypted_multimedia_processing(self):
        """测试加密多媒体处理"""
        media_type = "text/plain"
        data = b"Secret message"
        metadata = {"encrypted": True}
        
        # 创建加密多媒体消息
        original_msg = self.encrypted_processor.create_multimedia_message(
            media_type, data, metadata
        )
        
        # 确保消息创建成功
        self.assertIsNotNone(original_msg)
        
        # 解密消息
        decrypted_msg = self.encrypted_processor.decrypt_multimedia_message(original_msg)
        self.assertIsNotNone(decrypted_msg)
        self.assertEqual(decrypted_msg.data, data)
        self.assertEqual(decrypted_msg.media_type, media_type)
        self.assertEqual(decrypted_msg.metadata, metadata)


if __name__ == '__main__':
    unittest.main()