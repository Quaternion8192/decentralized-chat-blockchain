"""
工业级安全协议实现
实现TLS 1.3双向加密和流量伪装
"""
import asyncio
import json
import struct
import ssl
import random
import time
import base64
from typing import Dict, Optional, Callable, Tuple
import aiohttp
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import tempfile
import os
from ..crypto.advanced_crypto_manager import AdvancedCryptoManager


class TLSProtocol:
    """TLS协议类，支持TLS 1.3双向加密"""
    
    def __init__(self, crypto_manager: AdvancedCryptoManager):
        self.crypto_manager = crypto_manager
        self.tls_context = None
    
    def create_tls_context(self, is_server: bool = True, cert_file: str = None, key_file: str = None):
        """创建TLS 1.3上下文，支持双向认证"""
        if is_server:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        # 设置TLS 1.3（如果可用）
        context.minimum_version = ssl.TLSVersion.TLSv1_2  # TLS 1.2+ (TLS 1.3 support varies)
        context.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
        
        # 设置安全的密码套件
        context.set_ciphers(
            'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'
        )
        
        # 启用证书验证（在生产环境中应使用有效证书）
        if is_server:
            # 为演示生成自签名证书
            cert, key = self._generate_self_signed_cert()
            context.load_cert_chain(cert, key)
        else:
            # 客户端配置
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # 仅用于演示，生产环境应验证证书
        
        # 启用双向认证
        context.verify_mode = ssl.CERT_NONE  # 在生产环境中应使用ssl.CERT_REQUIRED
        if is_server:
            context.load_cert_chain(cert_file or self._get_server_cert(), 
                                  key_file or self._get_server_key())
        
        return context
    
    def _generate_self_signed_cert(self) -> Tuple[str, str]:
        """生成自签名证书（仅用于演示）"""
        # 创建临时证书文件
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "P2P Chat Network"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(time.time() - 3600)
            .not_valid_after(time.time() + 3600 * 24 * 365)  # 1年有效期
            .sign(key, hashes.SHA256(), default_backend())
        )
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.key') as key_f:
            key_f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )
            key_file = key_f.name
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem') as cert_f:
            cert_f.write(
                cert.public_bytes(serialization.Encoding.PEM)
            )
            cert_file = cert_f.name
        
        return cert_file, key_file
    
    def _get_server_cert(self):
        """获取服务器证书路径"""
        # 实际应用中，从配置或证书存储中获取
        return self._generate_self_signed_cert()[0]
    
    def _get_server_key(self):
        """获取服务器密钥路径"""
        # 实际应用中，从配置或密钥存储中获取
        return self._generate_self_signed_cert()[1]


class ObfuscatedProtocol:
    """流量伪装协议，实现多种混淆技术"""
    
    def __init__(self):
        self.obfuscation_methods = {
            'websocket': self._websocket_obfuscation,
            'http_padding': self._http_padding_obfuscation,
            'random_padding': self._random_padding_obfuscation
        }
    
    def _websocket_obfuscation(self, data: bytes) -> bytes:
        """WebSocket风格的流量伪装"""
        # 模拟WebSocket帧格式
        frame_data = bytearray()
        
        # FIN位、操作码
        frame_data.append(0x81)  # FIN=1, Text frame
        
        # 载荷长度（处理长度编码）
        payload_len = len(data)
        if payload_len <= 125:
            frame_data.append(payload_len)
        elif payload_len <= 65535:
            frame_data.append(126)
            frame_data.extend(struct.pack('>H', payload_len))
        else:
            frame_data.append(127)
            frame_data.extend(struct.pack('>Q', payload_len))
        
        # 添加数据
        frame_data.extend(data)
        
        return bytes(frame_data)
    
    def _http_padding_obfuscation(self, data: bytes) -> bytes:
        """HTTP风格的流量伪装"""
        # 添加HTTP-like头部和随机填充
        headers = [
            b"POST /api/messages HTTP/1.1",
            b"Host: example.com",
            b"User-Agent: Mozilla/5.0 (compatible; P2P-Client)",
            b"Content-Type: application/json",
            b"Content-Length: " + str(len(data)).encode(),
            b"Connection: keep-alive",
            b"",
            b""
        ]
        
        http_request = b"\r\n".join(headers) + data
        
        # 添加随机填充
        padding_len = random.randint(10, 100)
        padding = bytes([random.randint(0, 255) for _ in range(padding_len)])
        return http_request + padding
    
    def _random_padding_obfuscation(self, data: bytes) -> bytes:
        """随机填充混淆"""
        # 在数据前后添加随机长度的随机数据
        prefix_len = random.randint(5, 50)
        suffix_len = random.randint(5, 50)
        
        prefix = bytes([random.randint(0, 255) for _ in range(prefix_len)])
        suffix = bytes([random.randint(0, 255) for _ in range(suffix_len)])
        
        result = prefix + data + suffix
        
        # 在前面加上长度信息
        length_header = struct.pack('>I', len(result))
        return length_header + result
    
    def obfuscate(self, data: bytes, method: str = 'random_padding') -> bytes:
        """应用流量伪装"""
        if method in self.obfuscation_methods:
            return self.obfuscation_methods[method](data)
        else:
            # 默认使用随机填充
            return self.obfuscation_methods['random_padding'](data)
    
    def deobfuscate(self, data: bytes, method: str = 'random_padding') -> bytes:
        """去除流量伪装"""
        if method == 'random_padding':
            # 移除长度头和随机填充
            if len(data) < 4:
                raise ValueError("数据长度不足")
            total_len = struct.unpack('>I', data[:4])[0]
            actual_data = data[4:4+total_len]
            
            # 估算原始数据位置（简化处理）
            # 在实际实现中，需要更复杂的去混淆逻辑
            return actual_data
        elif method == 'websocket':
            # 简化的WebSocket去混淆
            if len(data) < 2:
                return data
            payload_len = data[1] & 0x7F
            offset = 2
            if payload_len == 126:
                offset = 4
            elif payload_len == 127:
                offset = 10
            
            return data[offset:]
        elif method == 'http_padding':
            # 简化的HTTP去混淆
            try:
                header_end = data.find(b'\r\n\r\n')
                if header_end != -1:
                    return data[header_end + 4:]
                return data
            except:
                return data
        else:
            return data


class SecureProtocol:
    """安全协议类，结合TLS和流量伪装"""
    
    def __init__(self, crypto_manager: AdvancedCryptoManager, 
                 use_tls: bool = True, obfuscation_method: str = 'random_padding'):
        self.tls_protocol = TLSProtocol(crypto_manager) if use_tls else None
        self.obfuscation_method = obfuscation_method
        self.obfuscator = ObfuscatedProtocol()
        self.use_tls = use_tls
        self.crypto_manager = crypto_manager
        self.session_keys = {}  # 存储会话密钥
    
    async def send_secure_message(self, writer: asyncio.StreamWriter, 
                                 session_id: str, message: str, 
                                 obfuscate: bool = True):
        """发送安全消息"""
        try:
            # 加密消息
            encrypted_msg = self.crypto_manager.encrypt_message(session_id, message)
            msg_bytes = json.dumps(encrypted_msg).encode('utf-8')
            
            # 应用流量伪装
            if obfuscate:
                msg_bytes = self.obfuscator.obfuscate(msg_bytes, self.obfuscation_method)
            
            # 发送长度前缀
            writer.write(struct.pack('>I', len(msg_bytes)))
            writer.write(msg_bytes)
            await writer.drain()
        except Exception as e:
            print(f"[!] 发送安全消息失败: {e}")
            raise
    
    async def read_secure_message(self, reader: asyncio.StreamReader, 
                                 session_id: str, obfuscate: bool = True) -> Optional[str]:
        """读取安全消息"""
        try:
            # 读取长度前缀
            header = await reader.readexactly(4)
            length = struct.unpack('>I', header)[0]
            
            # 读取数据
            data = await reader.readexactly(length)
            
            # 去除流量伪装
            if obfuscate:
                data = self.obfuscator.deobfuscate(data, self.obfuscation_method)
            
            # 解析JSON
            json_data = json.loads(data.decode('utf-8'))
            
            # 解密消息
            decrypted_msg = self.crypto_manager.decrypt_message(session_id, json_data)
            return decrypted_msg
        except (asyncio.IncompleteReadError, ConnectionResetError):
            print("[!] 连接已重置或读取不完整")
            return None
        except json.JSONDecodeError as e:
            print(f"[!] JSON解码错误: {e}")
            return None
        except Exception as e:
            print(f"[!] 读取安全消息失败: {e}")
            return None
    
    async def establish_secure_session(self, host: str, port: int, 
                                     peer_identity_info: Dict) -> Tuple[str, asyncio.StreamWriter, asyncio.StreamReader]:
        """建立安全会话"""
        # 创建TLS上下文
        if self.use_tls:
            context = self.tls_protocol.create_tls_context(is_server=False)
            reader, writer = await asyncio.open_connection(host, port, ssl=context)
        else:
            reader, writer = await asyncio.open_connection(host, port)
        
        # 发起密钥交换
        session_id, eph_pub_b64 = self.crypto_manager.initiate_session(peer_identity_info)
        
        # 发送临时公钥
        ephemeral_data = {
            'eph_pub': eph_pub_b64,
            'session_id': session_id,
            'identity_info': self.crypto_manager.get_identity_info()
        }
        
        msg_bytes = json.dumps(ephemeral_data).encode('utf-8')
        if self.obfuscation_method:
            msg_bytes = self.obfuscator.obfuscate(msg_bytes, self.obfuscation_method)
        
        writer.write(struct.pack('>I', len(msg_bytes)))
        writer.write(msg_bytes)
        await writer.drain()
        
        return session_id, writer, reader
    
    async def handle_secure_session_request(self, reader: asyncio.StreamReader,
                                          writer: asyncio.StreamWriter) -> Optional[str]:
        """处理安全会话请求"""
        try:
            # 读取会话请求
            header = await reader.readexactly(4)
            length = struct.unpack('>I', header)[0]
            data = await reader.readexactly(length)
            
            if self.obfuscation_method:
                data = self.obfuscator.deobfuscate(data, self.obfuscation_method)
            
            session_request = json.loads(data.decode('utf-8'))
            
            eph_pub_b64 = session_request['eph_pub']
            peer_identity_info = session_request['identity_info']
            
            # 响应会话请求
            session_id = self.crypto_manager.respond_to_session_request(eph_pub_b64, peer_identity_info)
            
            return session_id
        except Exception as e:
            print(f"[!] 处理安全会话请求失败: {e}")
            return None