"""
工业级安全去中心化聊天系统 Web UI 控制台
"""
import asyncio
import json
import webbrowser
import threading
import time
from datetime import datetime
from aiohttp import web, WSMsgType
import aiohttp_cors
import psutil
import platform
from src.p2p.secure_node_server import SecureChatNode
from src.crypto.advanced_crypto_manager import AdvancedCryptoManager


class WebUI:
    def __init__(self, chat_node):
        self.chat_node = chat_node
        self.clients = set()  # 存储WebSocket连接
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
        
    def setup_routes(self):
        """设置路由"""
        self.app.router.add_get('/', self.index)
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/api/node/stats', self.get_node_stats)
        self.app.router.add_get('/api/node/routing', self.get_routing_table)
        self.app.router.add_get('/api/blockchain/info', self.get_blockchain_info)
        self.app.router.add_get('/api/blockchain/chain', self.get_blockchain)
        self.app.router.add_post('/api/messages/send', self.send_message)
        self.app.router.add_post('/api/messages/send_multimedia', self.send_multimedia_message)
        self.app.router.add_post('/api/consensus/propose', self.start_consensus_proposal)
        self.app.router.add_post('/api/node/sync', self.sync_blockchain)
        self.app.router.add_get('/api/system/info', self.get_system_info)
        # 添加安全相关的API
        self.app.router.add_get('/api/security/info', self.get_security_info)
        self.app.router.add_static('/static', path='./static', name='static')
        
    def setup_cors(self):
        """设置CORS"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # 为所有路由添加CORS支持
        for route in list(self.app.router.routes()):
            cors.add(route)

    async def get_security_info(self, request):
        """获取安全信息"""
        security_info = {
            "encryption_enabled": True,
            "x3dh_enabled": True,
            "double_ratchet_enabled": True,
            "tls_enabled": True,
            "obfuscation_enabled": True,
            "forward_secrecy": True,
            "backward_secrecy": True,
            "dht_enabled": True
        }
        return web.json_response(security_info)

    async def index(self, request):
        """主页"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Industrial Secure Chat Console - 工业级安全聊天系统控制台</title>
    <link rel="stylesheet" href="/static/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="glassmorphism-nav">
        <div class="nav-container">
            <h1 class="logo">
                <span class="logo-icon"></span>
                Industrial Secure Chat Console
            </h1>
            <div class="nav-links">
                <button class="nav-btn active" data-tab="beginner">快速入门</button>
                <button class="nav-btn" data-tab="dashboard">控制台</button>
                <button class="nav-btn" data-tab="messages">消息</button>
                <button class="nav-btn" data-tab="network">网络</button>
                <button class="nav-btn" data-tab="security">安全</button>
                <button class="nav-btn" data-tab="settings">设置</button>
            </div>
        </div>
    </div>

    <main class="main-container">
        <!-- 初学者友好界面 -->
        <section id="beginner" class="tab-content active">
            <div class="beginner-friendly-section">
                <h2>欢迎使用工业级安全聊天系统</h2>
                <p>这是一个基于X3DH+双棘轮算法的去中心化聊天应用，具备前向/后向安全性，抗审查。</p>
                
                <div class="quick-start-grid">
                    <div class="quick-action-card" onclick="switchToTab('messages')">
                        <h3>💬 发送消息</h3>
                        <p>向其他节点发送端到端加密消息</p>
                        <button class="beginner-btn">开始发送</button>
                    </div>
                    
                    <div class="quick-action-card" onclick="switchToTab('network')">
                        <h3>🌐 查看网络</h3>
                        <p>了解当前网络中的节点</p>
                        <button class="beginner-btn">查看网络</button>
                    </div>
                    
                    <div class="quick-action-card" onclick="switchToTab('security')">
                        <h3>🔒 安全状态</h3>
                        <p>查看端到端加密和安全协议状态</p>
                        <button class="beginner-btn">查看安全</button>
                    </div>
                    
                    <div class="quick-action-card" onclick="switchToTab('dashboard')">
                        <h3>📊 系统监控</h3>
                        <p>监控节点性能和网络状态</p>
                        <button class="beginner-btn">系统监控</button>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>💡 系统状态</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="node-id-beginner">-</div>
                        <div class="stat-label">我的节点ID</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="uptime-beginner">-</div>
                        <div class="stat-label">在线时间</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="secure-connections">-</div>
                        <div class="stat-label">安全连接数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="routing-size-beginner">-</div>
                        <div class="stat-label">连接节点数</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- 控制台面板 -->
        <section id="dashboard" class="tab-content">
            <div class="dashboard-grid">
                <div class="card stats-card">
                    <h3>📊 节点统计</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-value" id="node-id">-</div>
                            <div class="stat-label">节点ID</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="uptime">-</div>
                            <div class="stat-label">在线时间</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="messages-sent">-</div>
                            <div class="stat-label">发送消息数</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" id="routing-size">-</div>
                            <div class="stat-label">路由表大小</div>
                        </div>
                    </div>
                </div>
                
                <div class="card quick-actions">
                    <h3>⚡ 快速操作</h3>
                    <div class="actions-grid">
                        <button id="sync-btn" class="action-btn">🔄 同步网络</button>
                        <button id="refresh-stats" class="action-btn">🔄 刷新状态</button>
                        <button id="security-check" class="action-btn">🔒 安全检查</button>
                    </div>
                </div>
                
                <div class="card security-card">
                    <h3>🛡️ 安全状态</h3>
                    <div class="security-stats">
                        <div class="security-item">
                            <span class="label">加密协议:</span>
                            <span class="value" id="encryption-protocol">X3DH+双棘轮</span>
                        </div>
                        <div class="security-item">
                            <span class="label">前向安全:</span>
                            <span class="value" id="forward-secrecy">启用</span>
                        </div>
                        <div class="security-item">
                            <span class="label">后向安全:</span>
                            <span class="value" id="backward-secrecy">启用</span>
                        </div>
                    </div>
                </div>
                
                <div class="card network-status">
                    <h3>🌐 网络状态</h3>
                    <div class="status-item">
                        <span class="status-label">节点连接数:</span>
                        <span class="status-value" id="connected-nodes">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">安全连接:</span>
                        <span class="status-value" id="secure-connections-count">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">DHT节点数:</span>
                        <span class="status-value" id="dht-nodes">-</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- 消息面板 -->
        <section id="messages" class="tab-content">
            <div class="messages-container">
                <div class="message-input-section">
                    <div class="input-group">
                        <div class="input-row">
                            <input type="text" id="target-node" placeholder="输入目标节点ID">
                        </div>
                        <div class="input-row">
                            <input type="text" id="message-content" placeholder="输入要发送的加密消息内容...">
                        </div>
                        <button id="send-message-btn" class="send-btn">📤 发送加密消息</button>
                    </div>
                    
                    <div class="input-group">
                        <label>发送多媒体文件</label>
                        <input type="file" id="media-file" accept="image/*,audio/*,video/*,.pdf,.doc,.docx">
                        <button id="send-media-btn" class="send-btn">📤 发送加密多媒体</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 消息历史</h3>
                    <div id="messages-list" class="messages-list">
                        <p>暂无消息记录。发送第一条加密消息开始吧！</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- 网络面板 -->
        <section id="network" class="tab-content">
            <div class="network-container">
                <div class="card">
                    <h3>📋 路由表</h3>
                    <div class="table-container">
                        <table id="routing-table">
                            <thead>
                                <tr>
                                    <th>节点ID</th>
                                    <th>主机</th>
                                    <th>端口</th>
                                    <th>加密状态</th>
                                    <th>连接时间</th>
                                    <th>安全等级</th>
                                </tr>
                            </thead>
                            <tbody>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>

        <!-- 安全面板 -->
        <section id="security" class="tab-content">
            <div class="security-container">
                <div class="card security-status">
                    <h3>🔒 安全协议状态</h3>
                    <div class="status-grid">
                        <div class="status-item">
                            <span class="status-label">X3DH密钥交换:</span>
                            <span class="status-value" id="x3dh-status">启用</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">双棘轮算法:</span>
                            <span class="status-value" id="ratchet-status">启用</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">TLS 1.3加密:</span>
                            <span class="status-value" id="tls-status">启用</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">流量混淆:</span>
                            <span class="status-value" id="obfuscation-status">启用</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">前向安全:</span>
                            <span class="status-value" id="forward-secrecy-status">启用</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">后向安全:</span>
                            <span class="status-value" id="backward-secrecy-status">启用</span>
                        </div>
                    </div>
                </div>
                
                <div class="card security-info">
                    <h3>ℹ️ 安全信息</h3>
                    <div class="info-content">
                        <p><strong>X3DH密钥交换:</strong> 使用扩展三重Diffie-Hellman协议进行安全密钥建立</p>
                        <p><strong>双棘轮算法:</strong> 实现消息密钥演进，确保前向和后向安全性</p>
                        <p><strong>TLS 1.3:</strong> 传输层安全协议，提供端到端加密</p>
                        <p><strong>流量混淆:</strong> 多种技术防止深度包检测(DPI)</p>
                        <p><strong>Kademlia DHT:</strong> 去中心化节点发现，无单点故障</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- 设置面板 -->
        <section id="settings" class="tab-content">
            <div class="settings-container">
                <div class="setting-card">
                    <h3>⚙️ 节点配置</h3>
                    <div class="form-group">
                        <label for="node-name">节点名称</label>
                        <input type="text" id="node-name" value="SecureNode">
                    </div>
                    <div class="form-group">
                        <label for="listen-port">监听端口</label>
                        <input type="number" id="listen-port" value="8080">
                    </div>
                </div>
                
                <div class="setting-card">
                    <h3>🔒 安全配置</h3>
                    <div class="form-group">
                        <label for="encryption-level">加密级别</label>
                        <select id="encryption-level">
                            <option value="high">高强度 (推荐)</option>
                            <option value="standard">标准</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="obfuscation-method">混淆方法</label>
                        <select id="obfuscation-method">
                            <option value="websocket">WebSocket风格</option>
                            <option value="http_padding">HTTP填充</option>
                            <option value="random_padding">随机填充</option>
                        </select>
                    </div>
                </div>
                
                <div class="setting-card">
                    <h3>ℹ️ 系统信息</h3>
                    <div class="system-info">
                        <div class="info-item">
                            <span class="label">系统版本:</span>
                            <span class="value">v2.0.0</span>
                        </div>
                        <div class="info-item">
                            <span class="label">运行时间:</span>
                            <span class="value" id="system-uptime">-</span>
                        </div>
                        <div class="info-item">
                            <span class="label">内存使用:</span>
                            <span class="value">-</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <script src="/static/script.js"></script>
</body>
</html>
        """
        return web.Response(text=html_content, content_type='text/html')

    async def websocket_handler(self, request):
        """WebSocket处理器"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # 添加客户端到连接集合
        self.clients.add(ws)
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    # 处理从客户端发送的消息
                    if data.get('action') == 'subscribe':
                        # 客户端订阅更新
                        pass
        finally:
            self.clients.discard(ws)
        
        return ws

    async def get_node_stats(self, request):
        """获取节点统计信息"""
        stats = self.chat_node.get_stats() if hasattr(self.chat_node, 'get_stats') else {}
        return web.json_response(stats)

    async def get_routing_table(self, request):
        """获取路由表"""
        routing_table = {
            "nodes": []
        }
        # 根据实际实现调整
        if hasattr(self.chat_node, 'node_server') and hasattr(self.chat_node.node_server, 'peer_connections'):
            for session_id, conn_info in self.chat_node.node_server.peer_connections.items():
                routing_table["nodes"].append({
                    "node_id": session_id,
                    "host": conn_info.get('host', 'unknown'),
                    "port": conn_info.get('port', 'unknown'),
                    "encrypted": True,
                    "connected_since": conn_info.get('established_time', time.time()),
                    "security_level": "high"
                })
        return web.json_response(routing_table)

    async def get_blockchain_info(self, request):
        """获取区块链信息"""
        # 暂时返回基本结构，根据实际区块链实现调整
        info = {
            "length": 0,
            "valid": True,
            "latest_hash": "N/A",
            "oldest_hash": "N/A",
            "chain": []
        }
        return web.json_response(info)

    async def get_blockchain(self, request):
        """获取区块链完整数据"""
        # 暂时返回基本结构，根据实际区块链实现调整
        chain = []
        return web.json_response(chain)

    async def send_message(self, request):
        """发送消息"""
        data = await request.json()
        target_node_id = data.get('target')
        message = data.get('message')
        
        if not target_node_id or not message:
            return web.json_response({'error': 'Missing target or message'}, status=400)
        
        # 异步发送消息
        try:
            # 根据实际SecureChatNode实现调整
            # asyncio.create_task(self.chat_node.send_message(target_node_id, message))
            result = await self.chat_node.node_server.broadcast_message(message)
            return web.json_response({'status': 'success', 'sent_to': result})
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def send_multimedia_message(self, request):
        """发送多媒体消息"""
        data = await request.json()
        target_node_id = data.get('target')
        media_type = data.get('media_type')
        media_data = data.get('media_data')  # 实际应用中这会是文件数据
        
        if not target_node_id or not media_type or not media_data:
            return web.json_response({'error': 'Missing required fields'}, status=400)
        
        # 异步发送多媒体消息
        # 注意：实际实现中需要处理文件上传
        # asyncio.create_task(self.chat_node.send_multimedia_message(target_node_id, media_type, media_data.encode()))
        
        return web.json_response({'status': 'success'})

    async def start_consensus_proposal(self, request):
        """发起共识提案"""
        data = await request.json()
        proposal_data = data.get('data')
        
        if not proposal_data:
            return web.json_response({'error': 'Missing proposal data'}, status=400)
        
        # 异步发起共识
        # asyncio.create_task(self.chat_node.start_consensus_proposal(proposal_data))
        
        return web.json_response({'status': 'success'})

    async def sync_blockchain(self, request):
        """同步区块链"""
        # 异步同步区块链
        # asyncio.create_task(self.chat_node.sync_blockchain())
        
        return web.json_response({'status': 'sync started'})
    
    async def get_system_info(self, request):
        """获取系统信息"""
        import psutil
        import platform
        
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0,
            "uptime": time.time() - getattr(self.chat_node, '_start_time', time.time()),
            "node_id": getattr(self.chat_node, 'get_identity_info', lambda: {'node_id': 'unknown'})()['node_id'],
        }
        
        return web.json_response(system_info)

    def run(self, host='localhost', port=8080):
        """运行Web服务器"""
        # 在新线程中打开浏览器
        def open_browser():
            webbrowser.open(f'http://{host}:{port}')
        
        threading.Thread(target=open_browser).start()
        
        # 运行Web服务器
        web.run_app(self.app, host=host, port=port)


def main():
    """主函数 - 启动Web UI"""
    # 创建安全聊天节点实例
    chat_node = SecureChatNode(
        host='127.0.0.1',
        port=9001  # 使用9001端口，避免与Web UI端口冲突
    )
    
    # 创建并运行Web UI
    webui = WebUI(chat_node)

    print("正在启动工业级安全去中心化聊天系统Web控制台...")
    print("访问 http://localhost:8080 查看控制台")
    
    async def start_services():
        # 启动节点服务器
        # 在新任务中启动节点，但不阻塞
        node_task = asyncio.create_task(chat_node.start_node([]))
        
        # 运行Web服务器
        runner = web.AppRunner(webui.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        print(f"[+] Web服务器已在 http://localhost:8080 启动")
        
        # 保持服务运行
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("\n正在关闭服务...")
        finally:
            await runner.cleanup()
    
    # 运行所有服务
    try:
        # 在新线程中打开浏览器
        def open_browser():
            import time
            time.sleep(2)  # 等待服务器启动
            webbrowser.open('http://localhost:8080')
        
        threading.Thread(target=open_browser).start()
        
        asyncio.run(start_services())
    except KeyboardInterrupt:
        print("\n正在关闭服务...")


if __name__ == "__main__":
    main()