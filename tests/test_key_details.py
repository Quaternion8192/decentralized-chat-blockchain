"""
测试密钥细节
"""
import base64
from src.crypto.simple_secure_channel import SimpleSecureChannel
import nacl.secret as secret_box


def test_key_details():
    # 创建两个节点
    node1 = SimpleSecureChannel()
    node2 = SimpleSecureChannel()

    print(f'节点1 ID: {node1.node_id}')
    print(f'节点2 ID: {node2.node_id}')

    # 交换公钥信息
    info1 = node1.get_public_info()
    info2 = node2.get_public_info()

    # 建立共享密钥
    shared_key1 = node1.establish_shared_key(info2['pub_key'])
    shared_key2 = node2.establish_shared_key(info1['pub_key'])

    print(f'共享密钥1长度: {len(shared_key1)}, 前10字节: {shared_key1[:10]}')
    print(f'共享密钥2长度: {len(shared_key2)}, 前10字节: {shared_key2[:10]}')
    print(f'共享密钥匹配: {shared_key1 == shared_key2}')
    
    # 测试直接使用密钥创建box
    key1_ok = shared_key1[:32].ljust(32, b'\x00')
    key2_ok = shared_key2[:32].ljust(32, b'\x00')
    
    print(f'修正后密钥1长度: {len(key1_ok)}, 前10字节: {key1_ok[:10]}')
    print(f'修正后密钥2长度: {len(key2_ok)}, 前10字节: {key2_ok[:10]}')
    
    # 测试加密
    original_msg = 'Hello, secure world!'
    print(f'原始消息: {original_msg}')
    
    box1 = secret_box.SecretBox(key1_ok)
    import nacl.utils
    nonce = nacl.utils.random(secret_box.SecretBox.NONCE_SIZE)
    print(f'Nonce长度: {len(nonce)}, 前10字节: {nonce[:10]}')
    
    encrypted = box1.encrypt(original_msg.encode(), nonce)
    print(f'加密后长度: {len(encrypted)}, 前10字节: {encrypted[:10]}')
    
    # 测试解密
    box2 = secret_box.SecretBox(key2_ok)
    decrypted = box2.decrypt(encrypted, nonce)
    print(f'解密消息: {decrypted.decode()}')


if __name__ == "__main__":
    test_key_details()