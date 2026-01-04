"""
安全协议类 - 支持TLS加密和协议混淆
"""
import asyncio
import json
import struct
import ssl
from typing import Dict, Optional, Callable
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import secrets


class SecureProtocol:
    """安全协议类，支持TLS和混淆"""
    
    def __init__(self, use_tls: bool = True, enable_obfuscation: bool = True):
        self.use_tls = use_tls
        self.enable_obfuscation = enable_obfuscation
        self.backend = default_backend()
        
    @staticmethod
    def create_tls_context(is_server: bool = True, cert_file: str = None, key_file: str = None):
        """创建TLS上下文"""
        if is_server:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            # 为演示目的，生成自签名证书
            # 在生产环境中，应使用有效的证书
            import tempfile
            import subprocess
            import atexit
            import os
            
            # 生成自签名证书（仅用于演示）
            if not cert_file or not key_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as cert_f, \
                     tempfile.NamedTemporaryFile(delete=False, suffix='.key') as key_f:
                    cert_file = cert_f.name
                    key_file = key_f.name
                    
                    # 生成自签名证书
                    subprocess.run([
                        'openssl', 'req', '-x509', '-newkey', 'rsa:2048', 
                        '-keyout', key_file, '-out', cert_file, 
                        '-days', '365', '-nodes', 
                        '-subj', '/C=US/ST=State/L=City/O=Org/CN=localhost'
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # 注册清理函数
                    def cleanup():
                        for f in [cert_file, key_file]:
                            try:
                                os.unlink(f)
                            except:
                                pass
                    atexit.register(cleanup)
            
            context.load_cert_chain(cert_file, key_file)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            # 禁用证书验证（仅用于演示，生产环境应验证证书）
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        return context

    @staticmethod
    async def send_json(writer: asyncio.StreamWriter, data: dict, 
                       use_tls: bool = True, enable_obfuscation: bool = True, 
                       shared_secret: bytes = None):
        """发送 JSON 数据，支持TLS和混淆"""
        try:
            message = json.dumps(data).encode('utf-8')
            
            # 如果启用混淆，对消息进行加密
            if enable_obfuscation and shared_secret:
                message = SecureProtocol._encrypt_message(message, shared_secret)
            
            # 发送长度前缀
            writer.write(struct.pack('>I', len(message)))
            writer.write(message)
            await writer.drain()
        except ConnectionResetError:
            print("[!] 连接被重置")
            raise
        except Exception as e:
            print(f"[!] 发送JSON数据失败: {e}")
            raise

    @staticmethod
    async def read_json(reader: asyncio.StreamReader, 
                       use_tls: bool = True, enable_obfuscation: bool = True,
                       shared_secret: bytes = None):
        """读取带长度前缀的 JSON 数据，支持TLS和混淆"""
        try:
            # 读取 4字节长度
            header = await reader.readexactly(4)
            length = struct.unpack('>I', header)[0]
            
            # 根据长度读取内容
            body = await reader.readexactly(length)
            
            # 如果启用混淆，对消息进行解密
            if enable_obfuscation and shared_secret:
                body = SecureProtocol._decrypt_message(body, shared_secret)
            
            return json.loads(body.decode('utf-8'))
        except (asyncio.IncompleteReadError, ConnectionResetError):
            print("[!] 连接已重置或读取不完整")
            return None
        except json.JSONDecodeError as e:
            print(f"[!] JSON解码错误: {e}")
            return None
        except Exception as e:
            print(f"[!] 读取JSON数据失败: {e}")
            return None

    @staticmethod
    def _encrypt_message(message: bytes, shared_secret: bytes) -> bytes:
        """使用共享密钥加密消息"""
        # 使用PBKDF2派生密钥
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(shared_secret)
        
        # 生成随机IV
        iv = os.urandom(16)
        
        # AES加密
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # 填充消息到16字节的倍数
        from cryptography.hazmat.primitives import padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message) + padder.finalize()
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # 返回: salt + iv + encrypted_data
        return salt + iv + encrypted_data

    @staticmethod
    def _decrypt_message(encrypted_message: bytes, shared_secret: bytes) -> bytes:
        """使用共享密钥解密消息"""
        if len(encrypted_message) < 32:  # 至少需要salt(16) + iv(16)
            raise ValueError("Encrypted message too short")
        
        # 提取salt, iv, encrypted_data
        salt = encrypted_message[:16]
        iv = encrypted_message[16:32]
        encrypted_data = encrypted_message[32:]
        
        # 使用PBKDF2派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(shared_secret)
        
        # AES解密
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 去除填充
        from cryptography.hazmat.primitives import padding
        unpadder = padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data

    @staticmethod
    async def establish_secure_connection(host: str, port: int, 
                                       shared_secret: bytes = None,
                                       use_tls: bool = True,
                                       enable_obfuscation: bool = True):
        """建立安全连接"""
        if use_tls:
            context = SecureProtocol.create_tls_context(is_server=False)
            reader, writer = await asyncio.open_connection(host, port, ssl=context)
        else:
            reader, writer = await asyncio.open_connection(host, port)
        
        return reader, writer

    @staticmethod
    async def start_secure_server(host: str, port: int, 
                                handler_callback: Callable,
                                shared_secret: bytes = None,
                                use_tls: bool = True,
                                enable_obfuscation: bool = True):
        """启动安全服务器"""
        async def handle_client(reader, writer):
            peer_addr = writer.get_extra_info('peername')
            try:
                while True:
                    data = await SecureProtocol.read_json(
                        reader, 
                        use_tls=use_tls, 
                        enable_obfuscation=enable_obfuscation,
                        shared_secret=shared_secret
                    )
                    if data is None: 
                        break
                    # 调用节点逻辑处理消息
                    response = await handler_callback(data, writer)
                    if response:
                        await SecureProtocol.send_json(
                            writer, 
                            response,
                            use_tls=use_tls,
                            enable_obfuscation=enable_obfuscation,
                            shared_secret=shared_secret
                        )
            except Exception as e:
                print(f"[!] 客户端处理错误: {e}")
            finally:
                writer.close()
                await writer.wait_closed()
        
        if use_tls:
            context = SecureProtocol.create_tls_context(is_server=True)
            server = await asyncio.start_server(handle_client, host, port, ssl=context)
        else:
            server = await asyncio.start_server(handle_client, host, port)
        
        print(f"[*] 安全服务监听于 {host}:{port}")
        return server