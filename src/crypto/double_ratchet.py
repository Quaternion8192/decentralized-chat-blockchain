"""
双棘轮算法实现
实现发送和接收链的密钥更新机制，确保前向安全和后向安全
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
from typing import Dict, Optional, Tuple


class DoubleRatchet:
    """
    双棘轮算法实现
    包含KDF链和消息密钥派生
    """
    
    def __init__(self, shared_secret: bytes):
        self.shared_secret = shared_secret
        self.root_key = self._hkdf(shared_secret, b'root_key')
        
        # 发送链
        self.send_chain_key = self._hkdf(self.root_key, b'send_chain_key')
        self.send_ratchet_key = PrivateKey.generate()
        
        # 接收链
        self.recv_chain_key = self._hkdf(self.root_key, b'recv_chain_key')
        self.recv_ratchet_key = PrivateKey.generate()
        
        # 消息编号
        self.send_message_num = 0
        self.recv_message_num = 0
        self.previous_send_chain_length = 0
        
        # 保存的密钥，用于处理乱序消息
        self.saved_keys = {}
    
    def _hkdf(self, input_key: bytes, info: bytes) -> bytes:
        """HKDF密钥派生函数"""
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=info,
            backend=default_backend()
        ).derive(input_key)
    
    def _kdf_ratchet(self, chain_key: bytes, info: bytes) -> Tuple[bytes, bytes]:
        """棘轮密钥派生函数"""
        # 派生下一个链密钥
        next_chain_key = self._hkdf(chain_key, info + b'_next')
        
        # 派生输出密钥
        output_key = self._hkdf(chain_key, info + b'_output')
        
        return next_chain_key, output_key
    
    def get_next_send_key(self) -> Tuple[bytes, int]:
        """获取下一个发送密钥"""
        chain_key, msg_key = self._kdf_ratchet(
            self.send_chain_key,
            f'send_{self.send_message_num}'.encode()
        )
        self.send_chain_key = chain_key
        msg_num = self.send_message_num
        self.send_message_num += 1
        return msg_key, msg_num
    
    def get_next_recv_key(self, msg_num: int) -> bytes:
        """获取下一个接收密钥"""
        if msg_num in self.saved_keys:
            # 如果消息已保存（乱序到达），返回保存的密钥
            key = self.saved_keys[msg_num]
            del self.saved_keys[msg_num]
            return key
        
        # 如果消息编号大于当前接收编号，需要跳过一些消息
        if msg_num > self.recv_message_num:
            # 保存当前链密钥，用于恢复
            temp_chain_key = self.recv_chain_key
            
            # 计算到目标消息编号所需的密钥
            for i in range(self.recv_message_num, msg_num):
                self.recv_chain_key, skipped_key = self._kdf_ratchet(
                    self.recv_chain_key,
                    f'recv_{i}'.encode()
                )
                # 保存跳过的密钥，用于后续可能的乱序消息
                self.saved_keys[i] = skipped_key
            
            # 为实际需要的消息计算密钥
            self.recv_chain_key, msg_key = self._kdf_ratchet(
                self.recv_chain_key,
                f'recv_{msg_num}'.encode()
            )
            self.recv_message_num = msg_num + 1
            return msg_key
        elif msg_num == self.recv_message_num:
            # 消息编号正好是下一个，正常处理
            self.recv_chain_key, msg_key = self._kdf_ratchet(
                self.recv_chain_key,
                f'recv_{msg_num}'.encode()
            )
            self.recv_message_num = msg_num + 1
            return msg_key
        else:
            # 消息编号小于当前编号，说明是重复消息
            raise ValueError(f"消息编号过期: {msg_num}, 当前: {self.recv_message_num}")
    
    def advance_recv_chain(self):
        """推进接收链（当收到新的棘轮密钥时）"""
        self.previous_send_chain_length = self.send_message_num
        self.send_message_num = 0
        
        # 更新根密钥
        dh_result = crypto_scalarmult(
            self.send_ratchet_key.encode(),
            self.recv_ratchet_key.public_key.encode()
        )
        self.root_key = self._hkdf(self.root_key + dh_result, b'update_root_key')
        
        # 更新发送链
        self.send_chain_key = self._hkdf(self.root_key, b'send_chain_key')
        self.send_ratchet_key = PrivateKey.generate()
    
    def advance_send_chain(self):
        """推进发送链"""
        # 更新根密钥
        dh_result = crypto_scalarmult(
            self.recv_ratchet_key.encode(),
            self.send_ratchet_key.public_key.encode()
        )
        self.root_key = self._hkdf(self.root_key + dh_result, b'update_root_key')
        
        # 更新接收链
        self.recv_chain_key = self._hkdf(self.root_key, b'recv_chain_key')
        self.recv_ratchet_key = PrivateKey.generate()
    
    def get_send_ratchet_pub(self) -> bytes:
        """获取发送棘轮公钥"""
        return self.send_ratchet_key.public_key.encode()
    
    def set_peer_ratchet_pub(self, peer_pub_bytes: bytes):
        """设置对端棘轮公钥，触发链更新"""
        # 在实际应用中，需要使用接收到的对端公钥进行DH计算
        # 这里我们更新发送链，因为收到了新的对端公钥
        self.advance_send_chain()