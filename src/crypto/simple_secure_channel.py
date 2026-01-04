"""
简化安全通道实现
用于验证基本加密功能
"""
import nacl
from nacl.public import PrivateKey, PublicKey
from nacl.bindings import crypto_scalarmult
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import nacl.secret
import nacl.utils
import json
import base64
import time
from typing import Dict, Tuple


class SimpleSecureChannel:
    """
    简化安全通道
    使用DH密钥交换和对称加密
    """
    
    def __init__(self):
        # 生成长期密钥对
        self.identity_private_key = PrivateKey.generate()
        self.identity_public_key = self.identity_private_key.public_key
        self.node_id = base64.b64encode(
            self.identity_public_key.encode()[:8]
        ).decode()[:16]
    
    def get_public_info(self) -> Dict:
        """获取公开信息"""
        return {
            'pub_key': base64.b64encode(self.identity_public_key.encode()).decode(),
            'node_id': self.node_id
        }
    
    def establish_shared_key(self, peer_pub_key_b64: str) -> bytes:
        """与对等节点建立共享密钥"""
        peer_pub_key_bytes = base64.b64decode(peer_pub_key_b64)
        peer_pub_key = PublicKey(peer_pub_key_bytes)
        
        # 使用DH计算共享密钥
        shared_secret = crypto_scalarmult(
            self.identity_private_key.encode(),
            peer_pub_key.encode()
        )
        
        # 使用HKDF派生更安全的密钥
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'simple_secure_channel',
            backend=default_backend()
        ).derive(shared_secret)
        
        return derived_key
    
    def encrypt_message(self, shared_key: bytes, message: str) -> Dict:
        """加密消息"""
        # 确保密钥长度正确（32字节）
        if len(shared_key) != 32:
            # 如果密钥长度不正确，截取或填充到32字节
            shared_key = shared_key[:32].ljust(32, b'\x00')
        
        box = nacl.secret.SecretBox(shared_key)
        nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        encrypted = box.encrypt(message.encode(), nonce)
        
        return {
            'ciphertext': base64.b64encode(encrypted).decode(),
            'nonce': base64.b64encode(nonce).decode(),
            'timestamp': int(time.time())
        }
    
    def decrypt_message(self, shared_key: bytes, encrypted_msg: Dict) -> str:
        """解密消息"""
        # 确保密钥长度正确（32字节）
        if len(shared_key) != 32:
            # 如果密钥长度不正确，截取或填充到32字节
            shared_key = shared_key[:32].ljust(32, b'\x00')
        
        ciphertext = base64.b64decode(encrypted_msg['ciphertext'])
        
        box = nacl.secret.SecretBox(shared_key)
        # 解密时不提供nonce，因为加密时没有提供，nonce包含在加密结果中
        decrypted = box.decrypt(ciphertext)
        return decrypted.decode()


def test_simple_channel():
    """测试简化安全通道"""
    print("测试简化安全通道...")
    
    # 创建两个节点
    node1 = SimpleSecureChannel()
    node2 = SimpleSecureChannel()
    
    print(f"节点1 ID: {node1.node_id}")
    print(f"节点2 ID: {node2.node_id}")
    
    # 交换公钥信息
    info1 = node1.get_public_info()
    info2 = node2.get_public_info()
    
    # 建立共享密钥
    shared_key1 = node1.establish_shared_key(info2['pub_key'])
    shared_key2 = node2.establish_shared_key(info1['pub_key'])
    
    # 验证共享密钥相同
    if shared_key1 == shared_key2:
        print("✓ 共享密钥建立成功且匹配")
    else:
        print("✗ 共享密钥不匹配")
        return False
    
    # 测试加密解密
    original_msg = "Hello, secure world!"
    print(f"原始消息: {original_msg}")
    
    encrypted = node1.encrypt_message(shared_key1, original_msg)
    print("消息加密成功")
    
    decrypted = node2.decrypt_message(shared_key2, encrypted)
    print(f"解密消息: {decrypted}")
    
    if original_msg == decrypted:
        print("✓ 加密解密测试成功!")
        return True
    else:
        print("✗ 加密解密测试失败!")
        return False


if __name__ == "__main__":
    test_simple_channel()