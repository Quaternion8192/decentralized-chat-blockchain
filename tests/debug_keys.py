"""
调试密钥生成
"""
from src.crypto.simple_secure_channel import SimpleSecureChannel
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import nacl
from nacl.public import PrivateKey, PublicKey
from nacl.bindings import crypto_scalarmult


def debug_keys():
    # 创建两个节点
    node1 = SimpleSecureChannel()
    node2 = SimpleSecureChannel()
    
    print(f"节点1 ID: {node1.node_id}")
    print(f"节点2 ID: {node2.node_id}")
    
    # 交换公钥信息
    info1 = node1.get_public_info()
    info2 = node2.get_public_info()
    
    print(f"节点1公钥长度: {len(base64.b64decode(info1['pub_key']))}")
    print(f"节点2公钥长度: {len(base64.b64decode(info2['pub_key']))}")
    
    # 建立共享密钥
    shared_key1 = node1.establish_shared_key(info2['pub_key'])
    shared_key2 = node2.establish_shared_key(info1['pub_key'])
    
    print(f"共享密钥1长度: {len(shared_key1)}")
    print(f"共享密钥2长度: {len(shared_key2)}")
    print(f"共享密钥1前8字节: {shared_key1[:8]}")
    print(f"共享密钥2前8字节: {shared_key2[:8]}")
    
    print(f"共享密钥相等: {shared_key1 == shared_key2}")
    
    # 测试直接的DH计算
    pk1 = PrivateKey(node1.identity_private_key.encode())
    pk2 = PublicKey(base64.b64decode(info2['pub_key']))
    
    dh_raw = crypto_scalarmult(pk1.encode(), pk2.encode())
    print(f"原始DH结果长度: {len(dh_raw)}")
    print(f"原始DH结果前8字节: {dh_raw[:8]}")
    
    # 测试HKDF
    hkdf_result = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'simple_secure_channel',
        backend=default_backend()
    ).derive(dh_raw)
    
    print(f"HKDF结果长度: {len(hkdf_result)}")
    print(f"HKDF结果前8字节: {hkdf_result[:8]}")

if __name__ == "__main__":
    import base64
    debug_keys()