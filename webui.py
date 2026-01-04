"""
去中心化聊天系统 Web UI 控制台
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
from src.core.chat_node import ChatNode
from src.blockchain.blockchain import Blockchain
from src.p2p.node_server import NodeServer
from src.network.nat_traversal import setup_nat_traversal, NATTraverser


class WebUI:
    def __init__(self, chat_node: ChatNode):
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
        # 添加NAT穿越相关的API
        self.app.router.add_get('/api/nat/status', self.get_nat_status)
        self.app.router.add_post('/api/nat/configure', self.configure_nat_traversal)
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

    async def get_nat_status(self, request):
        """获取NAT穿越状态"""
        nat_status = {
            "enabled": getattr(self.chat_node, 'enable_nat_traversal', False),
            "public_url": getattr(self.chat_node, 'public_url', None),
            "nat_type": getattr(self.chat_node, 'nat_type', 'unknown'),
            "external_ip": getattr(self.chat_node, 'external_ip', None),
            "external_port": getattr(self.chat_node, 'external_port', None),
            "is_traversable": getattr(self.chat_node, 'is_nat_traversable', False)
        }
        return web.json_response(nat_status)

    async def configure_nat_traversal(self, request):
        """配置NAT穿越"""
        try:
            data = await request.json()
            enable_nat = data.get('enable', False)
            
            if enable_nat and not getattr(self.chat_node, 'enable_nat_traversal', False):
                # 启用NAT穿越
                from src.config.config import get_config
                config = get_config()
                
                # 获取节点当前监听的端口
                local_port = self.chat_node.addr[1]
                
                success, public_url, nat_result = await setup_nat_traversal(
                    config.config, local_port
                )
                
                if success:
                    self.chat_node.enable_nat_traversal = True
                    self.chat_node.public_url = public_url
                    self.chat_node.nat_type = nat_result.nat_type
                    self.chat_node.external_ip = nat_result.external_ip
                    self.chat_node.external_port = nat_result.external_port
                    self.chat_node.is_nat_traversable = nat_result.is_traversable
                    
                    # 更新节点在路由表中的信息
                    for node_id, node_info in self.chat_node.routing_table_manager.routing_table.items():
                        if node_info.node_id == self.chat_node.node_id:
                            node_info.public_url = public_url
                            break
                    
                    return web.json_response({
                        "status": "success", 
                        "message": "NAT穿越配置成功",
                        "public_url": public_url,
                        "nat_result": {
                            "nat_type": nat_result.nat_type,
                            "external_ip": nat_result.external_ip,
                            "external_port": nat_result.external_port,
                            "is_traversable": nat_result.is_traversable
                        }
                    })
                else:
                    return web.json_response({
                        "status": "error", 
                        "message": "NAT穿越配置失败"
                    }, status=500)
            elif not enable_nat:
                # 禁用NAT穿越
                self.chat_node.enable_nat_traversal = False
                self.chat_node.public_url = None
                
                return web.json_response({
                    "status": "success", 
                    "message": "NAT穿越已禁用"
                })
            else:
                return web.json_response({
                    "status": "success", 
                    "message": "NAT穿越状态未改变"
                })
                
        except Exception as e:
            return web.json_response({
                "status": "error", 
                "message": f"配置NAT穿越时出错: {str(e)}"
            }, status=500)
        
    async def index(self, request):
        """主页"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decentralized Chat Console - 去中心化聊天系统控制台</title>
    <link rel="stylesheet" href="/static/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="glassmorphism-nav">
        <div class="nav-container">
            <h1 class="logo">
                <span class="logo-icon"></span>
                Blockchain Chat Console
            </h1>
            <div class="nav-links">
                <button class="nav-btn active" data-tab="beginner">快速入门</button>
                <button class="nav-btn" data-tab="dashboard">控制台</button>
                <button class="nav-btn" data-tab="messages">消息</button>
                <button class="nav-btn" data-tab="network">网络</button>
                <button class="nav-btn" data-tab="blockchain">区块链</button>
                <button class="nav-btn" data-tab="nat">NAT穿越</button>
                <button class="nav-btn" data-tab="settings">设置</button>
            </div>
        </div>
    </div>

    <main class="main-container">
        <!-- 初学者友好界面 -->
        <section id="beginner" class="tab-content active">
            <div class="beginner-friendly-section">
                <h2>欢迎使用去中心化聊天系统</h2>
                <p>这是一个基于区块链技术的去中心化聊天应用，无需中央服务器，安全可靠。</p>
                
                <div class="quick-start-grid">
                    <div class="quick-action-card" onclick="switchToTab('messages')">
                        <h3>💬 发送消息</h3>
                        <p>向其他节点发送加密消息</p>
                        <button class="beginner-btn">开始发送</button>
                    </div>
                    
                    <div class="quick-action-card" onclick="switchToTab('network')">
                        <h3>🌐 查看网络</h3>
                        <p>了解当前网络中的节点</p>
                        <button class="beginner-btn">查看网络</button>
                    </div>
                    
                    <div class="quick-action-card" onclick="switchToTab('nat')">
                        <h3>🌐 NAT穿越</h3>
                        <p>配置和管理NAT穿越功能</p>
                        <button class="beginner-btn">配置NAT</button>
                    </div>
                    
                    <div class="quick-action-card" onclick="switchToTab('blockchain')">
                        <h3>🔗 区块链</h3>
                        <p>查看消息记录和区块链信息</p>
                        <button class="beginner-btn">查看区块链</button>
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
                        <div class="stat-value" id="chain-length-beginner">-</div>
                        <div class="stat-label">区块链长度</div>
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
                        <button id="sync-btn" class="action-btn">🔄 同步区块链</button>
                        <button id="consensus-btn" class="action-btn">🗳️ 发起共识</button>
                        <button id="refresh-stats" class="action-btn">🔄 刷新状态</button>
                    </div>
                </div>
                
                <div class="card incentive-card">
                    <h3>💰 激励机制</h3>
                    <div class="incentive-stats">
                        <div class="incentive-item">
                            <span class="label">余额:</span>
                            <span class="value" id="balance">-</span>
                        </div>
                        <div class="incentive-item">
                            <span class="label">声誉分数:</span>
                            <span class="value" id="reputation">-</span>
                        </div>
                        <div class="incentive-item">
                            <span class="label">节点类型:</span>
                            <span class="value" id="node-type">-</span>
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
                        <span class="status-label">区块链长度:</span>
                        <span class="status-value" id="chain-length">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">区块链状态:</span>
                        <span class="status-value" id="chain-validity">-</span>
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
                            <input type="text" id="target-node" placeholder="输入目标节点ID (例如: NodeA)">
                        </div>
                        <div class="input-row">
                            <input type="text" id="message-content" placeholder="输入要发送的消息内容...">
                        </div>
                        <button id="send-message-btn" class="send-btn">📤 发送消息</button>
                    </div>
                    
                    <div class="input-group">
                        <label>发送多媒体文件</label>
                        <input type="file" id="media-file" accept="image/*,audio/*,video/*,.pdf,.doc,.docx">
                        <button id="send-media-btn" class="send-btn">📤 发送多媒体</button>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 消息历史</h3>
                    <div id="messages-list" class="messages-list">
                        <p>暂无消息记录。发送第一条消息开始吧！</p>
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
                                    <th>公钥</th>
                                    <th>公共URL</th>
                                    <th>声誉</th>
                                </tr>
                            </thead>
                            <tbody>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="card consensus-section">
                    <h3>🗳️ 共识提案</h3>
                    <div class="input-group">
                        <input type="text" id="consensus-data" placeholder="输入共识提案数据">
                        <button id="propose-btn" class="action-btn">🗳️ 发起提案</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- NAT穿越面板 -->
        <section id="nat" class="tab-content">
            <div class="nat-container">
                <div class="card nat-status">
                    <h3>🌐 NAT穿越状态</h3>
                    <div class="status-grid">
                        <div class="status-item">
                            <span class="status-label">状态:</span>
                            <span class="status-value" id="nat-enabled">未启用</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">公共URL:</span>
                            <span class="status-value url-value" id="nat-public-url">-</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">NAT类型:</span>
                            <span class="status-value" id="nat-type">-</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">外部IP:</span>
                            <span class="status-value" id="nat-external-ip">-</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">外部端口:</span>
                            <span class="status-value" id="nat-external-port">-</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">可穿越:</span>
                            <span class="status-value" id="nat-traversable">-</span>
                        </div>
                    </div>
                    <div class="nat-actions">
                        <button id="toggle-nat-btn" class="action-btn">🔄 切换NAT穿越</button>
                        <button id="refresh-nat-btn" class="action-btn">🔄 刷新状态</button>
                    </div>
                </div>
                
                <div class="card nat-info">
                    <h3>ℹ️ NAT穿越信息</h3>
                    <div class="info-content">
                        <p><strong>STUN协议检测:</strong> 用于检测NAT类型和公网IP地址</p>
                        <p><strong>ngrok隧道:</strong> 当STUN无法穿透时，自动创建TCP隧道</p>
                        <p><strong>UPnP端口转发:</strong> 自动配置路由器端口映射（未来支持）</p>
                        <p><strong>使用说明:</strong> 点击"切换NAT穿越"按钮启用或禁用功能</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- 区块链面板 -->
        <section id="blockchain" class="tab-content">
            <div class="blockchain-container">
                <div class="card chain-info">
                    <h3>🔗 区块链信息</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="label">长度:</span>
                            <span class="value" id="chain-length-info">-</span>
                        </div>
                        <div class="info-item">
                            <span class="label">有效性:</span>
                            <span class="value" id="chain-valid">-</span>
                        </div>
                        <div class="info-item">
                            <span class="label">最新哈希:</span>
                            <span class="value hash-value" id="latest-hash">-</span>
                        </div>
                        <div class="info-item">
                            <span class="label">创世哈希:</span>
                            <span class="value hash-value" id="oldest-hash">-</span>
                        </div>
                    </div>
                </div>
                
                <div class="card chain-blocks">
                    <h3>📦 区块列表</h3>
                    <div class="blocks-container" id="blocks-container">
                        <!-- 区块将通过JavaScript动态添加 -->
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
                        <input type="text" id="node-name" value="NodeA">
                    </div>
                    <div class="form-group">
                        <label for="listen-port">监听端口</label>
                        <input type="number" id="listen-port" value="8001">
                    </div>
                </div>
                
                <div class="setting-card">
                    <h3>🌐 网络配置</h3>
                    <div class="form-group">
                        <label for="bootstrap-node">引导节点</label>
                        <input type="text" id="bootstrap-node" placeholder="host:port">
                    </div>
                </div>
                
                <div class="setting-card">
                    <h3>ℹ️ 系统信息</h3>
                    <div class="system-info">
                        <div class="info-item">
                            <span class="label">系统版本:</span>
                            <span class="value">v1.0.0</span>
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
        stats = self.chat_node.get_node_stats()
        return web.json_response(stats)

    async def get_routing_table(self, request):
        """获取路由表"""
        routing_table = {
            "nodes": []
        }
        for node_id, node_info in self.chat_node.routing_table_manager.routing_table.items():
            routing_table["nodes"].append({
                "node_id": node_id,
                "host": node_info.host,
                "port": node_info.port,
                "pub_key": node_info.pub_key[:50] + "..." if len(node_info.pub_key) > 50 else node_info.pub_key,
                "public_url": node_info.public_url or "N/A",
                "reputation": node_info.reputation_score
            })
        return web.json_response(routing_table)

    async def get_blockchain_info(self, request):
        """获取区块链信息"""
        info = self.chat_node.get_blockchain_info()
        return web.json_response(info)

    async def get_blockchain(self, request):
        """获取区块链完整数据"""
        chain = self.chat_node.get_blockchain_info()
        return web.json_response(chain['chain'])

    async def send_message(self, request):
        """发送消息"""
        data = await request.json()
        target_node_id = data.get('target')
        message = data.get('message')
        
        if not target_node_id or not message:
            return web.json_response({'error': 'Missing target or message'}, status=400)
        
        # 异步发送消息
        asyncio.create_task(self.chat_node.send_message(target_node_id, message))
        
        return web.json_response({'status': 'success'})

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
        asyncio.create_task(self.chat_node.start_consensus_proposal(proposal_data))
        
        return web.json_response({'status': 'success'})

    async def sync_blockchain(self, request):
        """同步区块链"""
        # 异步同步区块链
        asyncio.create_task(self.chat_node.sync_blockchain())
        
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
            "uptime": time.time() - self.chat_node.start_time if hasattr(self.chat_node, 'start_time') else 0,
            "node_id": self.chat_node.node_id,
            "node_addr": self.chat_node.addr,
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
    # 创建区块链实例
    blockchain = Blockchain(consensus_type="vdf_pow")
    
    # 创建聊天节点实例 (使用默认参数)
    # 注意：在实际部署时，需要根据命令行参数或配置来创建节点
    chat_node = ChatNode(
        node_id="WebConsole", 
        addr="127.0.0.1",
        port=9001,  # 使用9001端口，避免与Web UI端口冲突
        blockchain=blockchain,
        bootstrap_nodes=[],
        enable_nat_traversal=False  # 默认不启用NAT穿越
    )
    
    # 设置必要属性
    chat_node.start_time = time.time()  # 设置启动时间
    chat_node.pigeon_cache = {}  # 初始化信鸽缓存
    chat_node.bootstrap_nodes = []  # 初始化引导节点列表
    
    # 创建节点服务器，将消息处理委托给chat_node
    node_server = NodeServer("127.0.0.1", 9001, chat_node.handle_message)
    chat_node.server = node_server
    
    # 创建并运行Web UI
    webui = WebUI(chat_node)

    print("正在启动去中心化聊天系统Web控制台...")
    print("访问 http://localhost:8080 查看控制台")
    
    async def start_services():
        # 启动节点服务器
        await node_server.start()
        print(f"[+] 节点服务器已在 127.0.0.1:9001 启动")
        
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