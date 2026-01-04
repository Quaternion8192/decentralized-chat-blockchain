"""
测试工作加密功能
"""
import base64
from src.crypto.simple_secure_channel import SimpleSecureChannel


def test_working_crypto():
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

    print(f'共享密钥匹配: {shared_key1 == shared_key2}')

    # 测试加密解密
    original_msg = 'Hello, secure world!'
    print(f'原始消息: {original_msg}')

    encrypted = node1.encrypt_message(shared_key1, original_msg)
    print('消息加密成功')

    decrypted = node2.decrypt_message(shared_key2, encrypted)
    print(f'解密消息: {decrypted}')

    if original_msg == decrypted:
        print('✓ 加密解密测试成功!')
        return True
    else:
        print('✗ 加密解密测试失败!')
        return False


if __name__ == "__main__":
    test_working_crypto()