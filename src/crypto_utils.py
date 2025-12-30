import base64
import os
from cryptography.hazmat.primitives import hashes, serialization, padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class CryptoManager:
    def __init__(self):
        # 生成 RSA 密钥对
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_pub_key_pem(self) -> str:
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')

    @staticmethod
    def load_pub_key(pem_str: str):
        return serialization.load_pem_public_key(pem_str.encode(), backend=default_backend())

    def sign(self, message: str) -> str:
        signature = self.private_key.sign(
            message.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()

    @staticmethod
    def verify(pub_key, message: str, signature_b64: str) -> bool:
        try:
            signature = base64.b64decode(signature_b64)
            pub_key.verify(
                signature,
                message.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    # 混合加密：随机生成 AES Key 加密数据，再用接收者公钥加密 AES Key
    @staticmethod
    def encrypt_for(target_pub_key_pem: str, data: str) -> dict:
        target_pub_key = CryptoManager.load_pub_key(target_pub_key_pem)
        
        # 1. 生成 AES 密钥
        aes_key = os.urandom(32)
        iv = os.urandom(16)
        
        # 2. AES 加密数据
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # 3. RSA 加密 AES 密钥
        encrypted_key = target_pub_key.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

        return {
            "enc_key": base64.b64encode(encrypted_key).decode(),
            "iv": base64.b64encode(iv).decode(),
            "ciphertext": base64.b64encode(encrypted_data).decode()
        }

    def decrypt_message(self, encrypted_package: dict) -> str:
        # 1. RSA 解密 AES Key
        encrypted_key = base64.b64decode(encrypted_package['enc_key'])
        aes_key = self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

        # 2. AES 解密数据
        iv = base64.b64decode(encrypted_package['iv'])
        ciphertext = base64.b64decode(encrypted_package['ciphertext'])
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = sym_padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data.decode('utf-8')