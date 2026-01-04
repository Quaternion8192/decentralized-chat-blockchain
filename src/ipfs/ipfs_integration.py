"""
IPFS 集成模块
用于分布式存储和内容寻址
"""
import asyncio
import aiohttp
import json
import hashlib
from typing import Optional, Dict, Any, List
import base64
import os
from pathlib import Path


class IPFSClient:
    """
    IPFS客户端，用于与本地IPFS节点交互
    """
    def __init__(self, api_url: str = "http://localhost:5001"):
        self.api_url = api_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def add_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        将文件添加到IPFS
        """
        if not os.path.exists(file_path):
            print(f"[!] 文件不存在: {file_path}")
            return None

        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # 计算文件哈希作为额外验证
            file_hash = hashlib.sha256(data).hexdigest()
            
            # 使用IPFS API添加文件
            url = f"{self.api_url}/api/v0/add"
            form_data = aiohttp.FormData()
            form_data.add_field('file', data, filename=os.path.basename(file_path))
            
            async with self.session.post(url, data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    result['local_hash'] = file_hash  # 添加本地计算的哈希
                    return result
                else:
                    print(f"[!] IPFS添加文件失败: {response.status}")
                    return None
        except Exception as e:
            print(f"[!] 添加文件到IPFS时出错: {e}")
            return None

    async def add_bytes(self, data: bytes, filename: str = "data") -> Optional[Dict[str, Any]]:
        """
        将字节数据添加到IPFS
        """
        try:
            # 计算数据哈希作为额外验证
            data_hash = hashlib.sha256(data).hexdigest()
            
            # 使用IPFS API添加数据
            url = f"{self.api_url}/api/v0/add"
            form_data = aiohttp.FormData()
            form_data.add_field('file', data, filename=filename)
            
            async with self.session.post(url, data=form_data) as response:
                if response.status == 200:
                    result = await response.json()
                    result['local_hash'] = data_hash  # 添加本地计算的哈希
                    return result
                else:
                    print(f"[!] IPFS添加数据失败: {response.status}")
                    return None
        except Exception as e:
            print(f"[!] 添加数据到IPFS时出错: {e}")
            return None

    async def add_json(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        将JSON数据添加到IPFS
        """
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            return await self.add_bytes(json_str.encode('utf-8'), "data.json")
        except Exception as e:
            print(f"[!] 添加JSON到IPFS时出错: {e}")
            return None

    async def get_file(self, ipfs_hash: str, output_path: str) -> bool:
        """
        从IPFS获取文件
        """
        try:
            url = f"{self.api_url}/api/v0/cat?arg={ipfs_hash}"
            
            async with self.session.post(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # 确保输出目录存在
                    output_dir = os.path.dirname(output_path)
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                    
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    
                    return True
                else:
                    print(f"[!] IPFS获取文件失败: {response.status}")
                    return False
        except Exception as e:
            print(f"[!] 从IPFS获取文件时出错: {e}")
            return False

    async def get_bytes(self, ipfs_hash: str) -> Optional[bytes]:
        """
        从IPFS获取字节数据
        """
        try:
            url = f"{self.api_url}/api/v0/cat?arg={ipfs_hash}"
            
            async with self.session.post(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    print(f"[!] IPFS获取数据失败: {response.status}")
                    return None
        except Exception as e:
            print(f"[!] 从IPFS获取数据时出错: {e}")
            return None

    async def get_json(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """
        从IPFS获取JSON数据
        """
        try:
            data = await self.get_bytes(ipfs_hash)
            if data:
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"[!] 从IPFS获取JSON时出错: {e}")
        
        return None

    async def pin_add(self, ipfs_hash: str) -> bool:
        """
        固定IPFS对象以防止被垃圾回收
        """
        try:
            url = f"{self.api_url}/api/v0/pin/add?arg={ipfs_hash}"
            
            async with self.session.post(url) as response:
                if response.status == 200:
                    return True
                else:
                    print(f"[!] IPFS固定失败: {response.status}")
                    return False
        except Exception as e:
            print(f"[!] IPFS固定时出错: {e}")
            return False

    async def pin_rm(self, ipfs_hash: str) -> bool:
        """
        取消固定IPFS对象
        """
        try:
            url = f"{self.api_url}/api/v0/pin/rm?arg={ipfs_hash}"
            
            async with self.session.post(url) as response:
                if response.status == 200:
                    return True
                else:
                    print(f"[!] IPFS取消固定失败: {response.status}")
                    return False
        except Exception as e:
            print(f"[!] IPFS取消固定时出错: {e}")
            return False

    async def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取IPFS节点统计信息
        """
        try:
            url = f"{self.api_url}/api/v0/stats/bw"
            
            async with self.session.post(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"[!] 获取IPFS统计失败: {response.status}")
                    return None
        except Exception as e:
            print(f"[!] 获取IPFS统计时出错: {e}")
            return None


class IPFSStorage:
    """
    IPFS存储管理器
    提供高级存储和检索功能
    """
    def __init__(self, api_url: str = "http://localhost:5001"):
        self.ipfs_client = IPFSClient(api_url)
        self.cache = {}  # 简单的内存缓存

    async def store_data(self, data: Any, filename: str = None) -> Optional[str]:
        """
        存储数据到IPFS并返回哈希
        """
        try:
            # 根据数据类型选择存储方式
            if isinstance(data, dict):
                result = await self.ipfs_client.add_json(data)
            elif isinstance(data, str):
                result = await self.ipfs_client.add_bytes(data.encode('utf-8'), filename or "data.txt")
            elif isinstance(data, bytes):
                result = await self.ipfs_client.add_bytes(data, filename or "data.bin")
            else:
                # 尝试序列化为JSON
                import json
                json_str = json.dumps(data, default=str)
                result = await self.ipfs_client.add_bytes(json_str.encode('utf-8'), filename or "data.json")

            if result and 'Hash' in result:
                ipfs_hash = result['Hash']
                
                # 固定这个对象
                await self.ipfs_client.pin_add(ipfs_hash)
                
                # 添加到缓存
                self.cache[ipfs_hash] = data
                
                return ipfs_hash
            else:
                print("[!] 存储数据到IPFS失败")
                return None
        except Exception as e:
            print(f"[!] 存储数据时出错: {e}")
            return None

    async def retrieve_data(self, ipfs_hash: str) -> Optional[Any]:
        """
        从IPFS检索数据
        """
        # 检查缓存
        if ipfs_hash in self.cache:
            return self.cache[ipfs_hash]

        try:
            data = await self.ipfs_client.get_bytes(ipfs_hash)
            if data:
                try:
                    # 尝试解析为JSON
                    json_data = json.loads(data.decode('utf-8'))
                    # 添加到缓存
                    self.cache[ipfs_hash] = json_data
                    return json_data
                except:
                    # 如果不是JSON，返回原始字节
                    self.cache[ipfs_hash] = data
                    return data
            else:
                print(f"[!] 从IPFS检索数据失败: {ipfs_hash}")
                return None
        except Exception as e:
            print(f"[!] 检索数据时出错: {e}")
            return None

    async def store_file(self, file_path: str) -> Optional[str]:
        """
        存储文件到IPFS
        """
        try:
            result = await self.ipfs_client.add_file(file_path)
            if result and 'Hash' in result:
                ipfs_hash = result['Hash']
                
                # 固定这个对象
                await self.ipfs_client.pin_add(ipfs_hash)
                
                return ipfs_hash
            else:
                print("[!] 存储文件到IPFS失败")
                return None
        except Exception as e:
            print(f"[!] 存储文件时出错: {e}")
            return None

    async def retrieve_file(self, ipfs_hash: str, output_path: str) -> bool:
        """
        从IPFS检索文件
        """
        try:
            success = await self.ipfs_client.get_file(ipfs_hash, output_path)
            return success
        except Exception as e:
            print(f"[!] 检索文件时出错: {e}")
            return False

    async def verify_content(self, ipfs_hash: str, expected_content: bytes) -> bool:
        """
        验证IPFS内容的完整性
        """
        try:
            retrieved_content = await self.ipfs_client.get_bytes(ipfs_hash)
            if retrieved_content is None:
                return False
            
            expected_hash = hashlib.sha256(expected_content).hexdigest()
            retrieved_hash = hashlib.sha256(retrieved_content).hexdigest()
            
            return expected_hash == retrieved_hash
        except Exception as e:
            print(f"[!] 验证内容时出错: {e}")
            return False


class BlockchainIPFSBridge:
    """
    区块链和IPFS之间的桥梁
    用于存储大块数据的引用
    """
    def __init__(self, ipfs_storage: IPFSStorage):
        self.ipfs_storage = ipfs_storage

    async def store_large_data(self, data: Any) -> Optional[Dict[str, str]]:
        """
        存储大型数据到IPFS，并返回引用信息
        """
        ipfs_hash = await self.ipfs_storage.store_data(data)
        if ipfs_hash:
            # 创建引用对象，包含IPFS哈希和数据元信息
            reference_data = {
                "ipfs_hash": ipfs_hash,
                "timestamp": asyncio.get_event_loop().time(),
                "data_type": type(data).__name__,
                "size": len(str(data).encode('utf-8')) if isinstance(data, (str, dict)) else len(data)
            }
            return reference_data
        return None

    async def retrieve_large_data(self, reference_data: Dict[str, str]) -> Optional[Any]:
        """
        从IPFS检索大型数据
        """
        if 'ipfs_hash' in reference_data:
            ipfs_hash = reference_data['ipfs_hash']
            return await self.ipfs_storage.retrieve_data(ipfs_hash)
        return None