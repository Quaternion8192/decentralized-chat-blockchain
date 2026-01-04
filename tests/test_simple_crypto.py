"""
简单测试加密功能
"""
from src.crypto.advanced_crypto_manager import AdvancedCryptoManager

def test_simple_crypto():
    # 创建两个加密管理器
    mgr1 = AdvancedCryptoManager()
    mgr2 = AdvancedCryptoManager()
    
    print("节点1 ID:", mgr1.get_node_id())
    print("节点2 ID:", mgr2.get_node_id())
    
    # 获取身份信息
    identity_info1 = mgr1.get_identity_info()
    identity_info2 = mgr2.get_identity_info()
    
    print("节点1身份公钥:", identity_info1['identity_key'][:32])
    print("节点2身份公钥:", identity_info2['identity_key'][:32])
    
    # 节点1发起会话
    session_id1, eph_pub_b64 = mgr1.initiate_session(identity_info2)
    print(f"节点1创建会话: {session_id1}")
    
    # 节点2响应会话
    session_id2 = mgr2.respond_to_session_request(eph_pub_b64, identity_info1)
    print(f"节点2创建会话: {session_id2}")
    
    # 测试加密解密
    original_msg = "Hello, secure world!"
    print(f"原始消息: {original_msg}")
    
    try:
        encrypted = mgr1.encrypt_message(session_id1, original_msg)
        print("消息加密成功")
        print("加密数据:", {k: (str(v)[:50] + "..." if isinstance(v, (str, bytes)) else v) for k, v in encrypted.items()})
        
        decrypted = mgr2.decrypt_message(session_id2, encrypted)
        print(f"解密消息: {decrypted}")
        
        if original_msg == decrypted:
            print("✓ 加密解密测试成功!")
        else:
            print("✗ 加密解密测试失败!")
            print(f"  原始: {original_msg}")
            print(f"  解密: {decrypted}")
    except Exception as e:
        print(f"✗ 加密解密测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_crypto()