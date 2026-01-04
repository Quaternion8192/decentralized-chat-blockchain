"""
增强版加密管理器
实现端到端加密协议流程，包括密钥交换、消息加密和数字签名
"""
import os
import base64
import hashlib
import secrets
import time
from typing import Dict, Optional
from cryptography.hazmat.primitives import hashes, serialization, padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json


class KeyExchangeManager:
    """密钥交换管理器"""
    def __init__(self):
        self._ephemeral_keys = {}  # 临时密钥对存储

    def generate_ephemeral_key_pair(self) -> tuple:
        """生成临时密钥对用于密钥交换"""
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        public_key = private_key.public_key()
        
        return private_key, public_key

    def derive_shared_secret(self, private_key, peer_public_key_pem: str) -> tuple:
        """基于ECDH或RSA的密钥交换协议（改进实现）"""
        # 在实际应用中，这里应该使用ECDH进行密钥交换
        # 由于我们使用的是RSA，我们使用RSA加密一个随机值作为共享密钥
        # 但这里我们实现一个更安全的密钥派生过程
        
        # 使用椭圆曲线密钥交换的模拟实现
        # 由于我们使用RSA密钥对，我们使用RSA-OAEP加密一个随机密钥
        # 然后使用KDF（密钥派生函数）生成共享密钥
        
        import os
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        
        peer_public_key = serialization.load_pem_public_key(
            peer_public_key_pem.encode(), 
            backend=default_backend()
        )
        
        # 生成一个随机值作为预主密钥
        pre_shared_secret = secrets.token_bytes(32)  # 256位预共享密钥
        
        # 使用对方公钥加密预共享密钥
        encrypted_pre_shared_secret = peer_public_key.encrypt(
            pre_shared_secret,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 使用KDF从预共享密钥派生实际的共享密钥
        # 这里使用随机盐值来增加安全性
        salt = os.urandom(16)  # 128位盐值
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256位输出
            salt=salt,
            iterations=100000,  # 高迭代次数以防止暴力破解
            backend=default_backend()
        )
        
        shared_key = kdf.derive(pre_shared_secret)
        
        return shared_key, encrypted_pre_shared_secret, salt

    def decrypt_shared_secret(self, private_key, encrypted_pre_shared_secret: bytes, salt: bytes) -> bytes:
        """使用私钥解密共享密钥并使用KDF派生最终密钥"""
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        
        # 使用私钥解密预共享密钥
        pre_shared_secret = private_key.decrypt(
            encrypted_pre_shared_secret,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 使用KDF从预共享密钥派生实际的共享密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256位输出
            salt=salt,
            iterations=100000,  # 高迭代次数以防止暴力破解
            backend=default_backend()
        )
        
        shared_key = kdf.derive(pre_shared_secret)
        
        return shared_key


class CryptoManager:
    """增强版加密管理类"""
    def __init__(self):
        # 生成 RSA 密钥对
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        # 生成节点ID（基于公钥的哈希）
        self.node_id = self._generate_node_id()
        
        # 密钥交换管理器
        self.key_exchange_manager = KeyExchangeManager()

    def _generate_node_id(self) -> str:
        """基于公钥生成节点ID"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return hashlib.sha256(pem).hexdigest()[:16]  # 取前16个字符作为节点ID

    def get_pub_key_pem(self) -> str:
        """获取公钥PEM格式"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')

    def get_node_id(self) -> str:
        """获取节点ID"""
        return self.node_id

    @staticmethod
    def load_pub_key(pem_str: str):
        """从PEM格式加载公钥"""
        return serialization.load_pem_public_key(pem_str.encode(), backend=default_backend())

    def sign(self, message: str) -> str:
        """对消息进行数字签名"""
        signature = self.private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), 
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()

    @staticmethod
    def verify(pub_key, message: str, signature_b64: str) -> bool:
        """验证数字签名"""
        try:
            signature = base64.b64decode(signature_b64)
            pub_key.verify(
                signature,
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()), 
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def hybrid_encrypt(self, target_pub_key_pem: str, data: str) -> dict:
        """
        混合加密：使用RSA加密AES密钥，AES加密数据
        这是端到端加密协议的核心部分
        """
        target_pub_key = CryptoManager.load_pub_key(target_pub_key_pem)
        
        # 1. 生成随机AES密钥和IV
        aes_key = os.urandom(32)  # 256位密钥
        iv = os.urandom(16)      # 128位IV
        
        # 2. 使用AES-CBC模式加密数据
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # 对数据进行PKCS7填充
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # 3. 使用接收方公钥加密AES密钥
        encrypted_key = target_pub_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                algorithm=hashes.SHA256(), 
                label=None
            )
        )

        return {
            "enc_key": base64.b64encode(encrypted_key).decode(),
            "iv": base64.b64encode(iv).decode(),
            "ciphertext": base64.b64encode(encrypted_data).decode(),
            "timestamp": int(time.time())
        }

    def hybrid_decrypt(self, encrypted_package: dict) -> str:
        """
        混合解密：使用私钥解密AES密钥，AES解密数据
        """
        # 1. 解密AES密钥
        encrypted_key = base64.b64decode(encrypted_package['enc_key'])
        aes_key = self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                algorithm=hashes.SHA256(), 
                label=None
            )
        )

        # 2. 解密数据
        iv = base64.b64decode(encrypted_package['iv'])
        ciphertext = base64.b64decode(encrypted_package['ciphertext'])
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # 移除PKCS7填充
        unpadder = sym_padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data.decode('utf-8')

    def encrypt_for_broadcast(self, data: str, recipient_pub_keys: list) -> dict:
        """
        为广播加密消息（每个接收者使用不同的密钥加密）
        """
        # 生成一个一次性密钥
        session_key = os.urandom(32)
        iv = os.urandom(16)
        
        # 使用会话密钥加密数据
        cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # 为每个接收者加密会话密钥
        encrypted_keys = []
        for pub_key_pem in recipient_pub_keys:
            target_pub_key = CryptoManager.load_pub_key(pub_key_pem)
            encrypted_session_key = target_pub_key.encrypt(
                session_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                    algorithm=hashes.SHA256(), 
                    label=None
                )
            )
            encrypted_keys.append(base64.b64encode(encrypted_session_key).decode())
        
        return {
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "iv": base64.b64encode(iv).decode(),
            "encrypted_keys": encrypted_keys,
            "timestamp": int(time.time())
        }

    def decrypt_broadcast(self, encrypted_package: dict) -> Optional[str]:
        """
        解密广播消息
        """
        try:
            # 尝试使用我们的私钥解密会话密钥
            encrypted_keys = encrypted_package['encrypted_keys']
            session_key = None
            
            for enc_key in encrypted_keys:
                try:
                    encrypted_key = base64.b64decode(enc_key)
                    session_key = self.private_key.decrypt(
                        encrypted_key,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                            algorithm=hashes.SHA256(), 
                            label=None
                        )
                    )
                    break  # 成功解密，退出循环
                except:
                    continue  # 尝试下一个密钥
            
            if session_key is None:
                return None  # 无法解密
            
            # 使用会话密钥解密数据
            iv = base64.b64decode(encrypted_package['iv'])
            ciphertext = base64.b64decode(encrypted_package['encrypted_data'])
            
            cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            unpadder = sym_padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            return data.decode('utf-8')
        except Exception as e:
            print(f"[!] 广播消息解密失败: {e}")
            return None

    def create_secure_message(self, target_pub_key_pem: str, data: str, metadata: dict = None) -> dict:
        """
        创建安全消息，包含加密数据、签名和元数据
        """
        # 加密数据
        encrypted_data = self.hybrid_encrypt(target_pub_key_pem, data)
        
        # 创建消息内容
        message_content = {
            "encrypted_data": encrypted_data,
            "sender_id": self.node_id,
            "timestamp": int(time.time()),
            "metadata": metadata or {}
        }
        
        # 对消息内容进行签名
        message_json = json.dumps(message_content, sort_keys=True)
        signature = self.sign(message_json)
        
        return {
            "message": message_content,
            "signature": signature,
            "message_id": hashlib.sha256((message_json + signature).encode()).hexdigest()[:16]
        }

    def verify_secure_message(self, secure_message: dict, sender_pub_key_pem: str) -> Optional[dict]:
        """
        验证安全消息的完整性和真实性
        """
        try:
            # 验证签名
            message_json = json.dumps(secure_message["message"], sort_keys=True)
            sender_pub_key = self.load_pub_key(sender_pub_key_pem)
            
            if not self.verify(sender_pub_key, message_json, secure_message["signature"]):
                print("[!] 消息签名验证失败")
                return None
            
            # 验证消息ID
            expected_msg_id = hashlib.sha256(
                (message_json + secure_message["signature"]).encode()
            ).hexdigest()[:16]
            
            if secure_message["message_id"] != expected_msg_id:
                print("[!] 消息ID验证失败")
                return None
            
            return secure_message["message"]
        except Exception as e:
            print(f"[!] 安全消息验证失败: {e}")
            return None