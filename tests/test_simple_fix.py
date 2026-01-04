"""
测试加密修复
"""
import nacl.secret
import nacl.utils
from nacl.public import PrivateKey, PublicKey
from nacl.bindings import crypto_scalarmult
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64


def test_encryption_fix():
    # 创建两个密钥对
    private1 = PrivateKey.generate()
    public1 = private1.public_key
    
    private2 = PrivateKey.generate()
    public2 = private2.public_key
    
    # 计算共享密钥
    shared_secret = crypto_scalarmult(private1.encode(), public2.encode())
    shared_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'test_key',
        backend=default_backend()
    ).derive(shared_secret)
    
    print(f"共享密钥长度: {len(shared_key)}")
    
    # 创建加密box
    box = nacl.secret.SecretBox(shared_key)
    
    # 生成随机nonce
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    print(f"Nonce长度: {len(nonce)}")
    
    # 加密消息
    message = b"Hello, secure world!"
    encrypted = box.encrypt(message, nonce)
    print(f"加密后数据长度: {len(encrypted)}")
    
    # 正确的解密方式：直接使用加密函数返回的结果
    decrypted = box.decrypt(encrypted)
    print(f"解密消息: {decrypted.decode()}")
    
    # 测试完整的加密解密流程
    print("\n--- 测试完整流程 ---")
    message2 = "Test message for full flow"
    encrypted2 = box.encrypt(message2.encode())
    decrypted2 = box.decrypt(encrypted2)
    print(f"完整流程解密: {decrypted2.decode()}")


if __name__ == "__main__":
    test_encryption_fix()