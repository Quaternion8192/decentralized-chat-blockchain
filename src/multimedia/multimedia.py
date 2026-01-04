"""
多媒体消息处理模块
支持图片、音频、视频等多媒体内容的传输
"""
import asyncio
import base64
import json
import hashlib
import time
import os
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
import tempfile
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets


class MultimediaMessage:
    """
    多媒体消息类
    支持多种媒体类型的封装和传输
    """
    def __init__(self, media_type: str, data: bytes, metadata: Dict[str, Any] = None):
        self.media_type = media_type  # 'image', 'audio', 'file', 'text'
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.message_id = self.generate_message_id()
        
        # 计算数据哈希用于完整性验证
        self.data_hash = hashlib.sha256(data).hexdigest()

    def generate_message_id(self) -> str:
        """生成消息ID"""
        return hashlib.sha256(
            f"{self.media_type}_{len(self.data)}_{self.timestamp}".encode()
        ).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "media_type": self.media_type,
            "data": base64.b64encode(self.data).decode('utf-8'),
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "data_hash": self.data_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建多媒体消息"""
        # 使用字典中的数据创建新实例
        media_type = data["media_type"]
        data_bytes = base64.b64decode(data["data"])
        metadata = data.get("metadata", {})
        
        # 创建实例并设置所有属性
        instance = cls(media_type, data_bytes, metadata)
        instance.message_id = data["message_id"]
        instance.timestamp = data["timestamp"]
        instance.data_hash = data["data_hash"]
        return instance

    def verify_integrity(self) -> bool:
        """验证数据完整性"""
        current_hash = hashlib.sha256(self.data).hexdigest()
        return current_hash == self.data_hash

    def get_file_extension(self) -> str:
        """根据媒体类型获取文件扩展名"""
        extensions = {
            'image': '.jpg',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'audio': '.mp3',
            'audio/mp3': '.mp3',
            'audio/wav': '.wav',
            'video': '.mp4',
            'video/mp4': '.mp4',
            'video/avi': '.avi',
            'text/plain': '.txt',
            'application/pdf': '.pdf',
            'file': '.bin'
        }
        return extensions.get(self.media_type, '.bin')


class MultimediaProcessor:
    """
    多媒体处理器
    负责多媒体内容的编码、解码和压缩
    """
    def __init__(self, max_size: int = 10 * 1024 * 1024):  # 10MB默认最大大小
        self.max_size = max_size

    def compress_image(self, image_data: bytes, quality: int = 80) -> bytes:
        """
        压缩图像数据（模拟实现，实际需要PIL库）
        """
        # 这里是一个模拟实现，实际实现需要使用PIL或其他图像处理库
        if len(image_data) > self.max_size:
            print(f"[!] 图像数据过大: {len(image_data)} bytes，需要压缩")
            # 在实际实现中，这里会使用PIL进行图像压缩
            return image_data[:self.max_size]  # 简单截断作为示例
        return image_data

    def compress_audio(self, audio_data: bytes, quality: int = 80) -> bytes:
        """
        压缩音频数据（模拟实现）
        """
        # 这里是一个模拟实现，实际实现需要使用音频处理库
        if len(audio_data) > self.max_size:
            print(f"[!] 音频数据过大: {len(audio_data)} bytes，需要压缩")
            # 在实际实现中，这里会使用音频压缩算法
            return audio_data[:self.max_size]  # 简单截断作为示例
        return audio_data

    def compress_video(self, video_data: bytes) -> bytes:
        """
        压缩视频数据（模拟实现）
        """
        # 这里是一个模拟实现，实际实现需要使用视频处理库
        if len(video_data) > self.max_size:
            print(f"[!] 视频数据过大: {len(video_data)} bytes，需要压缩")
            # 在实际实现中，这里会使用视频压缩算法
            return video_data[:self.max_size]  # 简单截断作为示例
        return video_data

    def process_media(self, media_type: str, data: bytes) -> bytes:
        """
        根据媒体类型处理数据
        """
        if media_type.startswith('image'):
            return self.compress_image(data)
        elif media_type.startswith('audio'):
            return self.compress_audio(data)
        elif media_type.startswith('video'):
            return self.compress_video(data)
        else:
            # 对于其他类型，检查大小
            if len(data) > self.max_size:
                print(f"[!] 文件过大: {len(data)} bytes，超过了 {self.max_size} bytes 限制")
                return data[:self.max_size]  # 简单截断
            return data

    def create_multimedia_message(self, media_type: str, data: bytes, 
                                metadata: Dict[str, Any] = None) -> Optional[MultimediaMessage]:
        """
        创建多媒体消息
        """
        try:
            # 处理媒体数据
            processed_data = self.process_media(media_type, data)
            
            # 创建多媒体消息
            message = MultimediaMessage(media_type, processed_data, metadata)
            
            # 验证完整性
            if not message.verify_integrity():
                print("[!] 消息完整性验证失败")
                return None
            
            return message
        except Exception as e:
            print(f"[!] 创建多媒体消息时出错: {e}")
            return None

    def save_to_file(self, multimedia_msg: MultimediaMessage, file_path: str) -> bool:
        """
        将多媒体消息保存到文件
        """
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(multimedia_msg.data)
            
            return True
        except Exception as e:
            print(f"[!] 保存文件时出错: {e}")
            return False

    def load_from_file(self, file_path: str, media_type: str = None) -> Optional[MultimediaMessage]:
        """
        从文件加载多媒体消息
        """
        try:
            if not os.path.exists(file_path):
                print(f"[!] 文件不存在: {file_path}")
                return None

            # 如果未指定媒体类型，尝试从文件扩展名推断
            if not media_type:
                suffix = Path(file_path).suffix.lower()
                type_map = {
                    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif',
                    '.mp3': 'audio/mp3', '.wav': 'audio/wav',
                    '.mp4': 'video/mp4', '.avi': 'video/avi', '.mov': 'video/mov'
                }
                media_type = type_map.get(suffix, 'file')

            # 读取文件数据
            with open(file_path, 'rb') as f:
                data = f.read()

            # 创建多媒体消息
            metadata = {
                "original_filename": os.path.basename(file_path),
                "file_size": len(data),
                "file_path": file_path
            }

            return MultimediaMessage(media_type, data, metadata)
        except Exception as e:
            print(f"[!] 从文件加载多媒体消息时出错: {e}")
            return None


class EncryptedMultimediaProcessor(MultimediaProcessor):
    """
    加密多媒体处理器
    在传输前对多媒体数据进行加密
    """
    def __init__(self, max_size: int = 10 * 1024 * 1024):
        super().__init__(max_size)
        self.encryption_key = secrets.token_bytes(32)  # 256位密钥

    def encrypt_data(self, data: bytes) -> Tuple[bytes, bytes]:
        """
        加密数据，返回(加密数据, IV)
        """
        # 生成随机IV
        iv = secrets.token_bytes(16)
        
        # 创建加密器
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # 填充数据到16字节的倍数
        padding_len = 16 - (len(data) % 16)
        padded_data = data + bytes([padding_len] * padding_len)
        
        # 加密数据
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return encrypted_data, iv

    def decrypt_data(self, encrypted_data: bytes, iv: bytes) -> bytes:
        """
        解密数据
        """
        # 创建解密器
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # 解密数据
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 移除填充
        padding_len = padded_data[-1]
        original_data = padded_data[:-padding_len]
        
        return original_data

    def create_multimedia_message(self, media_type: str, data: bytes, 
                                metadata: Dict[str, Any] = None) -> Optional[MultimediaMessage]:
        """
        创建加密的多媒体消息
        """
        try:
            # 处理媒体数据
            processed_data = self.process_media(media_type, data)
            
            # 加密数据
            encrypted_data, iv = self.encrypt_data(processed_data)
            
            # 将IV添加到元数据中
            full_metadata = metadata or {}
            full_metadata['iv'] = base64.b64encode(iv).decode('utf-8')
            full_metadata['encrypted'] = True
            
            # 创建多媒体消息（现在包含加密数据）
            message = MultimediaMessage(media_type, encrypted_data, full_metadata)
            
            # 验证完整性
            if not message.verify_integrity():
                print("[!] 消息完整性验证失败")
                return None
            
            return message
        except Exception as e:
            print(f"[!] 创建加密多媒体消息时出错: {e}")
            return None

    def decrypt_multimedia_message(self, multimedia_msg: MultimediaMessage) -> Optional[MultimediaMessage]:
        """
        解密多媒体消息
        """
        try:
            if not multimedia_msg.metadata.get('encrypted'):
                print("[!] 消息未加密，无需解密")
                return multimedia_msg

            # 从元数据中获取IV
            iv = base64.b64decode(multimedia_msg.metadata['iv'])
            
            # 解密数据
            decrypted_data = self.decrypt_data(multimedia_msg.data, iv)
            
            # 创建新的多媒体消息（包含解密数据）
            decrypted_msg = MultimediaMessage(
                multimedia_msg.media_type,
                decrypted_data,
                multimedia_msg.metadata
            )
            decrypted_msg.message_id = multimedia_msg.message_id
            decrypted_msg.timestamp = multimedia_msg.timestamp
            decrypted_msg.data_hash = hashlib.sha256(decrypted_data).hexdigest()
            
            return decrypted_msg
        except Exception as e:
            print(f"[!] 解密多媒体消息时出错: {e}")
            return None