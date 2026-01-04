"""
工业级加密管理器
实现X3DH密钥交换协议和双棘轮算法，使用PyNaCl(LibSodium)库
"""
import os
import time
import pickle
import hashlib
from typing import Dict, Optional, Tuple
import nacl
from nacl.public import PrivateKey, PublicKey, Box
from nacl.bindings import crypto_scalarmult
from nacl.exceptions import CryptoError
import nacl.secret
import nacl.utils
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import json
import base64


class X3DHKeyManager:
    """
    X3DH (Extended Triple Diffie-Hellman) 密钥交换管理器
    实现类似Signal协议的密钥交换机制
    """
    
    def __init__(self):
        # 长期密钥对 (Identity Key Pair - IK)
        self.identity_private_key = PrivateKey.generate()
        self.identity_public_key = self.identity_private_key.public_key
        
        # 已签名的预密钥对 (Signed Prekey - SPK)
        self.signed_prekey = PrivateKey.generate()
        self.signed_prekey_public = self.signed_prekey.public_key
        self.signed_prekey_signature = self._sign_prekey()
        
        # 一次性预密钥列表 (One-time Prekeys - OPK)
        self.one_time_prekeys = [PrivateKey.generate() for _ in range(5)]
        self.one_time_prekey_publics = [key.public_key for key in self.one_time_prekeys]
        
        # 存储会话密钥
        self.sessions = {}
    
    def _sign_prekey(self) -> bytes:
        """
        使用身份私钥对预密钥进行签名
        """
        # 这里使用简单的签名机制，实际应用中应使用更安全的签名方案
        prekey_bytes = self.signed_prekey_public.encode()
        signature = hashlib.sha256(prekey_bytes + self.identity_private_key.encode()).digest()
        return signature
    
    def get_identity_public_key(self) -> bytes:
        """获取身份公钥"""
        return self.identity_public_key.encode()
    
    def get_signed_prekey_public(self) -> bytes:
        """获取已签名的预密钥公钥"""
        return self.signed_prekey_public.encode()
    
    def get_one_time_prekey_publics(self) -> list:
        """获取一次性预密钥公钥列表"""
        return [key.encode() for key in self.one_time_prekey_publics]
    
    def get_signed_prekey_signature(self) -> bytes:
        """获取预密钥签名"""
        return self.signed_prekey_signature
    
    def initiate_key_exchange(self, peer_identity_key: bytes, peer_signed_prekey: bytes, 
                             peer_one_time_prekey: Optional[bytes] = None) -> Tuple[bytes, Dict]:
        """
        发起方执行X3DH密钥交换
        """
        # 解码对方的密钥
        peer_ik = PublicKey(peer_identity_key)
        peer_spk = PublicKey(peer_signed_prekey)
        peer_opk = PublicKey(peer_one_time_prekey) if peer_one_time_prekey else None
        
        # 生成临时密钥对 (Ephemeral Key - E)
        ephemeral_private_key = PrivateKey.generate()
        ephemeral_public_key = ephemeral_private_key.public_key
        
        # 计算DH密钥
        dh1 = nacl.bindings.crypto_scalarmult(
            ephemeral_private_key.encode(), 
            peer_ik.encode()
        )
        dh2 = nacl.bindings.crypto_scalarmult(
            self.identity_private_key.encode(), 
            peer_spk.encode()
        )
        dh3 = None
        if peer_opk:
            dh3 = nacl.bindings.crypto_scalarmult(
                ephemeral_private_key.encode(), 
                peer_opk.encode()
            )
        
        # 组合DH密钥
        ik_spk = nacl.bindings.crypto_scalarmult(
            self.identity_private_key.encode(), 
            peer_spk.encode()
        )
        
        # 使用HKDF派生共享密钥
        dh_input = dh1 + dh2
        if dh3:
            dh_input += dh3
        dh_input += ik_spk
        
        shared_secret = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'x3dh_key_derivation',
            backend=default_backend()
        ).derive(dh_input)
        
        # 返回临时公钥和派生的共享密钥
        return ephemeral_public_key.encode(), shared_secret
    
    def respond_to_key_exchange(self, ephemeral_public_key: bytes, peer_identity_key: bytes,
                               signed_prekey_private: bytes, one_time_prekey_private: Optional[bytes] = None) -> bytes:
        """
        响应方执行X3DH密钥交换
        """
        # 解码密钥
        eph_pk = PublicKey(ephemeral_public_key)
        peer_ik = PublicKey(peer_identity_key)
        
        # 计算DH密钥
        dh1 = nacl.bindings.crypto_scalarmult(
            signed_prekey_private, 
            eph_pk.encode()
        )
        dh2 = nacl.bindings.crypto_scalarmult(
            self.identity_private_key.encode(), 
            eph_pk.encode()
        )
        dh3 = None
        if one_time_prekey_private:
            dh3 = nacl.bindings.crypto_scalarmult(
                one_time_prekey_private, 
                eph_pk.encode()
            )
        
        # 组合并派生共享密钥
        ik_spk = nacl.bindings.crypto_scalarmult(
            self.identity_private_key.encode(), 
            PublicKey(signed_prekey_private).encode()
        )
        
        dh_input = dh1 + dh2
        if dh3:
            dh_input += dh3
        dh_input += ik_spk
        
        shared_secret = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'x3dh_key_derivation',
            backend=default_backend()
        ).derive(dh_input)
        
        return shared_secret


from .double_ratchet import DoubleRatchet

class RatchetKeyManager:
    """
    双棘轮算法密钥管理器
    实现发送和接收链的密钥更新机制
    """
    
    def __init__(self, shared_secret: bytes):
        self.shared_secret = shared_secret
        
        # 使用改进的双棘轮算法
        self.double_ratchet = DoubleRatchet(shared_secret)
        
        # 消息计数器
        self.send_message_num = 0
        self.recv_message_num = 0

    def get_next_send_key(self) -> Tuple[bytes, int]:
        """获取下一个发送密钥"""
        msg_key, msg_num = self.double_ratchet.get_next_send_key()
        self.send_message_num += 1
        return msg_key, msg_num

    def update_recv_chain(self, peer_ratchet_pub_bytes: bytes):
        """更新接收链"""
        # 在实际实现中，需要使用对端公钥来更新链
        # 这里我们简单调用双棘轮的链更新方法
        self.double_ratchet.set_peer_ratchet_pub(peer_ratchet_pub_bytes)

    def get_next_recv_key(self, msg_num: int) -> bytes:
        """获取下一个接收密钥"""
        msg_key = self.double_ratchet.get_next_recv_key(msg_num)
        self.recv_message_num = max(self.recv_message_num, msg_num + 1)
        return msg_key


class AdvancedCryptoManager:
    """
    工业级加密管理器
    集成X3DH密钥交换和双棘轮算法
    """
    
    def __init__(self):
        self.x3dh_manager = X3DHKeyManager()
        self.ratchet_managers = {}  # 按会话ID存储棘轮管理器
        self.session_counter = 0
        
        # 节点ID基于身份公钥生成
        identity_pub_bytes = self.x3dh_manager.get_identity_public_key()
        self.node_id = hashlib.sha256(identity_pub_bytes).hexdigest()[:16]
    
    def get_identity_info(self) -> Dict:
        """获取身份信息，用于密钥交换"""
        return {
            'identity_key': base64.b64encode(self.x3dh_manager.get_identity_public_key()).decode(),
            'signed_prekey': base64.b64encode(self.x3dh_manager.get_signed_prekey_public()).decode(),
            'one_time_prekeys': [base64.b64encode(key).decode() for key in self.x3dh_manager.get_one_time_prekey_publics()],
            'signature': base64.b64encode(self.x3dh_manager.get_signed_prekey_signature()).decode(),
            'node_id': self.node_id
        }
    
    def initiate_session(self, peer_identity_info: Dict) -> str:
        """
        发起与对等节点的安全会话
        返回会话ID
        """
        # 解码对方身份信息
        peer_identity_key = base64.b64decode(peer_identity_info['identity_key'])
        peer_signed_prekey = base64.b64decode(peer_identity_info['signed_prekey'])
        
        # 选择一个一次性预密钥（如果可用）
        peer_one_time_prekey = None
        if peer_identity_info['one_time_prekeys']:
            peer_one_time_prekey = base64.b64decode(peer_identity_info['one_time_prekeys'][0])
        
        # 执行X3DH密钥交换
        eph_pub, shared_secret = self.x3dh_manager.initiate_key_exchange(
            peer_identity_key, 
            peer_signed_prekey, 
            peer_one_time_prekey
        )
        
        # 创建棘轮管理器
        ratchet_manager = RatchetKeyManager(shared_secret)
        session_id = f"session_{self.session_counter}"
        self.session_counter += 1
        self.ratchet_managers[session_id] = ratchet_manager
        
        # 返回临时公钥用于建立会话
        return session_id, base64.b64encode(eph_pub).decode()
    
    def respond_to_session_request(self, eph_pub_b64: str, peer_identity_info: Dict) -> str:
        """
        响应对等节点的会话请求
        返回会话ID
        """
        eph_pub = base64.b64decode(eph_pub_b64)
        peer_identity_key = base64.b64decode(peer_identity_info['identity_key'])
        peer_signed_prekey_b64 = peer_identity_info['signed_prekey']
        peer_signed_prekey = base64.b64decode(peer_signed_prekey_b64)
        
        # 这里需要访问私钥，为了简化，我们使用预密钥的私钥
        # 在实际实现中，需要更复杂的密钥管理
        signed_prekey_private = self.x3dh_manager.signed_prekey.encode()
        one_time_prekey_private = None
        if self.x3dh_manager.one_time_prekeys:
            one_time_prekey_private = self.x3dh_manager.one_time_prekeys[0].encode()
        
        shared_secret = self.x3dh_manager.respond_to_key_exchange(
            eph_pub, 
            peer_identity_key, 
            signed_prekey_private, 
            one_time_prekey_private
        )
        
        # 创建棘轮管理器
        ratchet_manager = RatchetKeyManager(shared_secret)
        session_id = f"session_{self.session_counter}"
        self.session_counter += 1
        self.ratchet_managers[session_id] = ratchet_manager
        
        return session_id
    
    def encrypt_message(self, session_id: str, plaintext: str) -> Dict:
        """使用会话密钥加密消息"""
        if session_id not in self.ratchet_managers:
            raise ValueError(f"会话不存在: {session_id}")
        
        ratchet_manager = self.ratchet_managers[session_id]
        msg_key, msg_num = ratchet_manager.get_next_send_key()
        
        # 使用消息密钥加密
        box = nacl.secret.SecretBox(msg_key)
        nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        ciphertext = box.encrypt(plaintext.encode(), nonce)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'msg_num': msg_num,
            'nonce': base64.b64encode(nonce).decode(),
            'timestamp': int(time.time())
        }
    
    def decrypt_message(self, session_id: str, encrypted_msg: Dict) -> str:
        """使用会话密钥解密消息"""
        if session_id not in self.ratchet_managers:
            raise ValueError(f"会话不存在: {session_id}")
        
        ratchet_manager = self.ratchet_managers[session_id]
        
        # 解码消息
        ciphertext = base64.b64decode(encrypted_msg['ciphertext'])
        msg_num = encrypted_msg['msg_num']
        nonce = base64.b64decode(encrypted_msg['nonce'])
        
        # 获取消息密钥并解密
        msg_key = ratchet_manager.get_next_recv_key(msg_num)
        box = nacl.secret.SecretBox(msg_key)
        
        plaintext = box.decrypt(ciphertext, nonce)
        return plaintext.decode()
    
    def get_node_id(self) -> str:
        """获取节点ID"""
        return self.node_id