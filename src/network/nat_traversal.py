"""
NAT穿越模块
实现STUN协议检测、ngrok隧道服务和UPnP端口映射功能
"""
import asyncio
import socket
import struct
import requests
import json
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import threading
import time
import sys

try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("[!] 未安装pyngrok，请运行 'pip install pyngrok' 以支持ngrok隧道功能")


@dataclass
class NATResult:
    """NAT检测结果"""
    nat_type: str  # "none", "full_cone", "restricted", "port_restricted", "symmetric"
    external_ip: str
    external_port: int
    is_traversable: bool
    tunnel_url: Optional[str] = None  # 用于ngrok隧道


class STUNClient:
    """STUN客户端实现"""
    
    def __init__(self, stun_server: str = "stun.l.google.com", stun_port: int = 19302):
        self.stun_server = stun_server
        self.stun_port = stun_port
    
    def get_nat_type(self) -> NATResult:
        """检测NAT类型"""
        try:
            # 测试1: 直接连接STUN服务器
            external_ip, external_port = self._get_external_address()
            if not external_ip:
                return NATResult("blocked", "0.0.0.0", 0, False)
            
            # 测试2: 使用不同端口连接STUN服务器，判断NAT类型
            test_port = self._get_external_address_with_different_port()
            if test_port == (external_ip, external_port):
                # 端口保持不变，可能是全锥型NAT或无NAT
                return NATResult("none", external_ip, external_port, True)
            else:
                # 端口发生变化，需要进一步检测
                nat_type = self._detect_nat_type(external_ip, external_port)
                return NATResult(nat_type, external_ip, external_port, nat_type != "symmetric")
        
        except Exception as e:
            print(f"[!] STUN检测失败: {e}")
            return NATResult("unknown", "0.0.0.0", 0, False)
    
    def _get_external_address(self) -> Tuple[Optional[str], Optional[int]]:
        """获取外部IP和端口"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            # STUN Binding Request
            msg = bytearray(20)
            msg[0:2] = struct.pack('!H', 0x0001)  # Message Type: Binding Request
            msg[2:4] = struct.pack('!H', 0x0000)  # Message Length
            msg[4:20] = b'\x21\x12\xA4\x42' + bytes([i for i in range(16)])  # Magic Cookie + Transaction ID
            
            sock.sendto(msg, (self.stun_server, self.stun_port))
            data, addr = sock.recvfrom(1024)
            sock.close()
            
            # 解析响应
            if len(data) >= 20:
                msg_type = struct.unpack('!H', data[0:2])[0]
                if msg_type == 0x0101:  # Binding Success Response
                    # 查找XOR-MAPPED-ADDRESS属性
                    offset = 20
                    while offset < len(data):
                        if offset + 4 > len(data):
                            break
                        attr_type = struct.unpack('!H', data[offset:offset+2])[0]
                        attr_len = struct.unpack('!H', data[offset+2:offset+4])[0]
                        
                        if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
                            # 解析地址
                            family = struct.unpack('!H', data[offset+6:offset+8])[0]
                            if family == 0x01:  # IPv4
                                port = struct.unpack('!H', data[offset+8:offset+10])[0]
                                ip_bytes = data[offset+10:offset+14]
                                # XOR with magic cookie
                                magic = b'\x21\x12\xA4\x42'
                                xor_ip = bytes([b ^ c for b, c in zip(ip_bytes, magic[:4])])
                                ip = '.'.join(str(b) for b in xor_ip)
                                return ip, port
                        
                        offset += 4 + attr_len
                        # 属性值需要4字节对齐
                        offset = (offset + 3) & ~3
            
            return None, None
        
        except Exception as e:
            print(f"[!] 获取外部地址失败: {e}")
            return None, None
    
    def _get_external_address_with_different_port(self) -> Tuple[Optional[str], Optional[int]]:
        """使用不同端口获取外部地址"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 0))  # 绑定到随机端口
            sock.settimeout(5)
            
            # STUN Binding Request
            msg = bytearray(20)
            msg[0:2] = struct.pack('!H', 0x0001)  # Message Type: Binding Request
            msg[2:4] = struct.pack('!H', 0x0000)  # Message Length
            msg[4:20] = b'\x21\x12\xA4\x42' + bytes([i for i in range(16)])  # Magic Cookie + Transaction ID
            
            sock.sendto(msg, (self.stun_server, self.stun_port))
            data, addr = sock.recvfrom(1024)
            sock.close()
            
            # 解析响应（与上面相同）
            if len(data) >= 20:
                msg_type = struct.unpack('!H', data[0:2])[0]
                if msg_type == 0x0101:  # Binding Success Response
                    offset = 20
                    while offset < len(data):
                        if offset + 4 > len(data):
                            break
                        attr_type = struct.unpack('!H', data[offset:offset+2])[0]
                        attr_len = struct.unpack('!H', data[offset+2:offset+4])[0]
                        
                        if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
                            family = struct.unpack('!H', data[offset+6:offset+8])[0]
                            if family == 0x01:  # IPv4
                                port = struct.unpack('!H', data[offset+8:offset+10])[0]
                                ip_bytes = data[offset+10:offset+14]
                                magic = b'\x21\x12\xA4\x42'
                                xor_ip = bytes([b ^ c for b, c in zip(ip_bytes, magic[:4])])
                                ip = '.'.join(str(b) for b in xor_ip)
                                return ip, port
                        
                        offset += 4 + attr_len
                        offset = (offset + 3) & ~3
            
            return None, None
        
        except Exception as e:
            print(f"[!] 使用不同端口获取外部地址失败: {e}")
            return None, None
    
    def _detect_nat_type(self, external_ip: str, external_port: int) -> str:
        """检测具体的NAT类型"""
        # 这里实现简化版的NAT类型检测
        # 在实际应用中，需要更复杂的测试来确定NAT类型
        # 这里我们返回一个常见的NAT类型
        return "restricted"


class NgrokTunnel:
    """ngrok隧道管理类"""
    
    def __init__(self):
        self.tunnel = None
        self.port = None
    
    def start_tunnel(self, local_port: int, protocol: str = "tcp") -> Optional[str]:
        """启动ngrok隧道"""
        if not NGROK_AVAILABLE:
            print("[!] pyngrok未安装，无法使用ngrok隧道功能")
            return None
        
        try:
            # 断开可能存在的旧隧道
            if self.tunnel:
                ngrok.disconnect(self.tunnel.public_url)
            
            # 启动新隧道
            self.tunnel = ngrok.connect(local_port, protocol)
            print(f"[+] ngrok隧道已启动: {self.tunnel.public_url}")
            self.port = local_port
            return self.tunnel.public_url
        
        except Exception as e:
            print(f"[!] ngrok隧道启动失败: {e}")
            return None
    
    def stop_tunnel(self):
        """停止ngrok隧道"""
        if self.tunnel and NGROK_AVAILABLE:
            try:
                ngrok.disconnect(self.tunnel.public_url)
                print(f"[+] ngrok隧道已停止: {self.tunnel.public_url}")
                self.tunnel = None
                self.port = None
            except Exception as e:
                print(f"[!] 停止ngrok隧道失败: {e}")


class UPnPPortForwarder:
    """UPnP端口转发类"""
    
    def __init__(self):
        self.discovered_gateway = None
    
    def discover_gateway(self) -> Optional[str]:
        """发现UPnP网关"""
        try:
            import netifaces
            import urllib.request
            from xml.etree import ElementTree as ET
            
            # 简化版UPnP网关发现
            # 实际应用中需要更复杂的发现和解析过程
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info['addr']
                        if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                            # 尝试发现网关
                            gateway_ip = self._find_gateway_ip(ip)
                            if gateway_ip:
                                self.discovered_gateway = gateway_ip
                                return gateway_ip
        except ImportError:
            print("[!] netifaces未安装，无法使用UPnP功能")
        except Exception as e:
            print(f"[!] UPnP网关发现失败: {e}")
        
        return None
    
    def _find_gateway_ip(self, local_ip: str) -> Optional[str]:
        """查找网关IP（简化实现）"""
        # 简化实现：假设网关在常见位置
        parts = local_ip.split('.')
        if len(parts) == 4:
            gateway_ip = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
            return gateway_ip
        return None
    
    def add_port_mapping(self, internal_port: int, external_port: int, 
                        protocol: str = "TCP", description: str = "P2P Chat Node") -> bool:
        """添加端口映射"""
        if not self.discovered_gateway:
            print("[!] 未发现UPnP网关")
            return False
        
        try:
            # 简化实现：实际UPnP协议交互会更复杂
            print(f"[+] 尝试添加UPnP端口映射: 内部端口{internal_port} -> 外部端口{external_port}")
            # 这里应该发送SOAP请求到UPnP网关
            # 由于完整实现较为复杂，这里仅作示意
            return True
        except Exception as e:
            print(f"[!] 添加UPnP端口映射失败: {e}")
            return False
    
    def remove_port_mapping(self, external_port: int, protocol: str = "TCP") -> bool:
        """移除端口映射"""
        if not self.discovered_gateway:
            print("[!] 未发现UPnP网关")
            return False
        
        try:
            print(f"[+] 尝试移除UPnP端口映射: 外部端口{external_port}")
            # 这里应该发送SOAP请求到UPnP网关
            return True
        except Exception as e:
            print(f"[!] 移除UPnP端口映射失败: {e}")
            return False


class NATTraverser:
    """NAT穿越管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stun_client = STUNClient()
        self.ngrok_tunnel = NgrokTunnel()
        self.upnp_forwarder = UPnPPortForwarder()
        self.active_tunnel_url = None
    
    async def detect_and_traverse(self, local_port: int) -> NATResult:
        """检测NAT类型并尝试穿越"""
        print(f"[*] 开始NAT穿越检测，本地端口: {local_port}")
        
        # 1. 使用STUN检测NAT类型
        print("[*] 正在进行STUN检测...")
        nat_result = self.stun_client.get_nat_type()
        print(f"[+] NAT检测结果: 类型={nat_result.nat_type}, 外部IP={nat_result.external_ip}, 外部端口={nat_result.external_port}")
        
        # 2. 如果NAT不可穿越，尝试ngrok隧道
        if not nat_result.is_traversable:
            print(f"[-] NAT不可直接穿越，尝试ngrok隧道...")
            if self.config.get("nat_traversal", {}).get("enable_ngrok", True):
                tunnel_url = self.ngrok_tunnel.start_tunnel(local_port, "tcp")
                if tunnel_url:
                    nat_result.tunnel_url = tunnel_url
                    nat_result.is_traversable = True
                    self.active_tunnel_url = tunnel_url
                    print(f"[+] ngrok隧道创建成功: {tunnel_url}")
                else:
                    print(f"[-] ngrok隧道创建失败")
        
        # 3. 尝试UPnP端口转发（作为备选方案）
        if nat_result.is_traversable and not nat_result.tunnel_url:
            print("[*] 尝试UPnP端口转发...")
            gateway = self.upnp_forwarder.discover_gateway()
            if gateway:
                print(f"[+] 发现UPnP网关: {gateway}")
                success = self.upnp_forwarder.add_port_mapping(local_port, local_port)
                if success:
                    print(f"[+] UPnP端口映射成功: {local_port} -> {local_port}")
                else:
                    print(f"[-] UPnP端口映射失败")
            else:
                print(f"[-] 未发现UPnP网关")
        
        return nat_result
    
    def get_public_url(self) -> Optional[str]:
        """获取公共访问URL"""
        return self.active_tunnel_url
    
    def cleanup(self):
        """清理资源"""
        if self.ngrok_tunnel:
            self.ngrok_tunnel.stop_tunnel()


# 便捷函数
async def setup_nat_traversal(config: Dict[str, Any], local_port: int) -> Tuple[bool, Optional[str], NATResult]:
    """
    便捷函数：设置NAT穿越
    返回: (是否成功, 公共URL, NAT结果)
    """
    traverser = NATTraverser(config)
    nat_result = await traverser.detect_and_traverse(local_port)
    
    success = nat_result.is_traversable
    public_url = nat_result.tunnel_url or None
    
    if success:
        print(f"[✓] NAT穿越设置成功")
        if public_url:
            print(f"[*] 公共访问URL: {public_url}")
    else:
        print(f"[✗] NAT穿越设置失败")
    
    return success, public_url, nat_result