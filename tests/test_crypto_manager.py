import unittest
from src.crypto.crypto_manager import CryptoManager


class TestCryptoManager(unittest.TestCase):
    """加密管理器单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.crypto_manager = CryptoManager()
        self.target_crypto_manager = CryptoManager()  # 用于测试加密/解密
    
    def test_key_generation(self):
        """测试密钥生成"""
        self.assertIsNotNone(self.crypto_manager.private_key)
        self.assertIsNotNone(self.crypto_manager.public_key)
        
        # 检查公钥PEM格式
        pem = self.crypto_manager.get_pub_key_pem()
        self.assertTrue(pem.startswith("-----BEGIN PUBLIC KEY-----"))
        self.assertTrue(pem.endswith("-----END PUBLIC KEY-----\n"))
    
    def test_load_pub_key(self):
        """测试加载公钥"""
        pem = self.crypto_manager.get_pub_key_pem()
        loaded_key = CryptoManager.load_pub_key(pem)
        self.assertIsNotNone(loaded_key)
    
    def test_sign_and_verify(self):
        """测试签名和验证"""
        message = "Hello, World!"
        
        # 签名
        signature = self.crypto_manager.sign(message)
        self.assertIsNotNone(signature)
        
        # 验证
        pem = self.crypto_manager.get_pub_key_pem()
        pub_key = CryptoManager.load_pub_key(pem)
        is_valid = CryptoManager.verify(pub_key, message, signature)
        self.assertTrue(is_valid)
        
        # 验证错误消息
        is_valid = CryptoManager.verify(pub_key, "Wrong message", signature)
        self.assertFalse(is_valid)
    
    def test_encrypt_decrypt(self):
        """测试加密和解密"""
        target_pem = self.target_crypto_manager.get_pub_key_pem()
        message = "Secret message"
        
        # 加密
        encrypted_package = self.crypto_manager.hybrid_encrypt(target_pem, message)
        self.assertIn("enc_key", encrypted_package)
        self.assertIn("iv", encrypted_package)
        self.assertIn("ciphertext", encrypted_package)
        
        # 解密
        decrypted_message = self.target_crypto_manager.hybrid_decrypt(encrypted_package)
        self.assertEqual(decrypted_message, message)
    
    def test_invalid_encryption(self):
        """测试无效加密"""
        # 使用无效PEM尝试加密
        with self.assertRaises(Exception):
            CryptoManager.encrypt_for("invalid_pem", "test message")
    
    def test_invalid_decryption(self):
        """测试无效解密"""
        # 尝试解密无效数据
        invalid_package = {
            "enc_key": "invalid_key",
            "iv": "invalid_iv", 
            "ciphertext": "invalid_ciphertext"
        }
        
        with self.assertRaises(Exception):
            self.crypto_manager.decrypt_message(invalid_package)


if __name__ == '__main__':
    unittest.main()