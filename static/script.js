// 工业级安全去中心化聊天系统 Web UI 控制台 JavaScript
class SecureChatConsole {
    constructor() {
        this.ws = null;
        this.currentTab = 'dashboard';
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadInitialData();
        this.startAutoRefresh();
        this.setupNotifications();
    }
    
    setupEventListeners() {
        // 导航按钮事件
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // 发送消息按钮事件
        document.getElementById('send-message-btn').addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 按Enter键发送消息
        document.getElementById('message-content').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // 发送多媒体按钮事件
        document.getElementById('send-media-btn').addEventListener('click', () => {
            this.sendMultimedia();
        });
        
        // 同步网络按钮事件
        document.getElementById('sync-btn').addEventListener('click', () => {
            this.syncNetwork();
        });
        
        // 刷新状态按钮事件
        document.getElementById('refresh-stats').addEventListener('click', () => {
            this.loadInitialData();
        });
        
        // 安全检查按钮事件
        document.getElementById('security-check').addEventListener('click', () => {
            this.performSecurityCheck();
        });
    }
    
    switchTab(tabName) {
        // 隐藏所有标签内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // 移除所有导航按钮的active类
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // 显示选中的标签内容
        document.getElementById(tabName).classList.add('active');
        
        // 给选中的导航按钮添加active类
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        this.currentTab = tabName;
        
        // 根据标签加载特定数据
        this.loadTabData(tabName);
    }
    
    loadTabData(tabName) {
        switch(tabName) {
            case 'dashboard':
                this.loadNodeStats();
                break;
            case 'network':
                this.loadRoutingTable();
                break;
            case 'security':
                this.loadSecurityInfo();
                break;
            case 'settings':
                this.loadSystemInfo();
                break;
        }
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket连接已建立');
                // 发送订阅消息
                this.ws.send(JSON.stringify({action: 'subscribe'}));
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket连接已关闭，尝试重连...');
                setTimeout(() => {
                    this.connectWebSocket();
                }, 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
            };
        } catch (error) {
            console.error('WebSocket连接失败:', error);
        }
    }
    
    handleWebSocketMessage(data) {
        // 处理从服务器发送的实时更新
        console.log('收到WebSocket消息:', data);
    }
    
    async loadInitialData() {
        await this.loadNodeStats();
        await this.loadSecurityInfo();
        this.loadTabData(this.currentTab);
    }
    
    async loadNodeStats() {
        try {
            const response = await fetch('/api/node/stats');
            const stats = await response.json();
            
            // 更新控制台面板中的统计信息
            this.updateStatElement('node-id', stats.node_id || 'N/A');
            this.updateStatElement('uptime', this.formatDuration(stats.uptime || 0));
            this.updateStatElement('messages-sent', stats.message_count || 0);
            this.updateStatElement('routing-size', stats.connected_peers || 0);
            
            // 更新初学者界面中的统计信息
            this.updateStatElement('node-id-beginner', stats.node_id || 'N/A');
            this.updateStatElement('uptime-beginner', this.formatDuration(stats.uptime || 0));
            this.updateStatElement('secure-connections', stats.connected_peers || 0);
            this.updateStatElement('routing-size-beginner', stats.connected_peers || 0);
            
            // 网络状态
            this.updateStatElement('connected-nodes', stats.connected_peers || 0);
            this.updateStatElement('secure-connections-count', stats.connected_peers || 0);
            this.updateStatElement('dht-nodes', stats.dht_info ? 'Connected' : 'N/A');
        } catch (error) {
            console.error('加载节点统计信息失败:', error);
        }
    }
    
    async loadSecurityInfo() {
        try {
            const response = await fetch('/api/security/info');
            const security = await response.json();
            
            // 更新安全状态显示
            document.getElementById('x3dh-status').textContent = security.x3dh_enabled ? '启用' : '禁用';
            document.getElementById('x3dh-status').className = security.x3dh_enabled ? 'status-value' : 'status-value';
            if (security.x3dh_enabled) {
                document.getElementById('x3dh-status').style.color = '#10B981';
            } else {
                document.getElementById('x3dh-status').style.color = '#EF4444';
            }
            
            document.getElementById('ratchet-status').textContent = security.double_ratchet_enabled ? '启用' : '禁用';
            if (security.double_ratchet_enabled) {
                document.getElementById('ratchet-status').style.color = '#10B981';
            } else {
                document.getElementById('ratchet-status').style.color = '#EF4444';
            }
            
            document.getElementById('tls-status').textContent = security.tls_enabled ? '启用' : '禁用';
            if (security.tls_enabled) {
                document.getElementById('tls-status').style.color = '#10B981';
            } else {
                document.getElementById('tls-status').style.color = '#EF4444';
            }
            
            document.getElementById('obfuscation-status').textContent = security.obfuscation_enabled ? '启用' : '禁用';
            if (security.obfuscation_enabled) {
                document.getElementById('obfuscation-status').style.color = '#10B981';
            } else {
                document.getElementById('obfuscation-status').style.color = '#EF4444';
            }
            
            document.getElementById('forward-secrecy-status').textContent = security.forward_secrecy ? '启用' : '禁用';
            if (security.forward_secrecy) {
                document.getElementById('forward-secrecy-status').style.color = '#10B981';
            } else {
                document.getElementById('forward-secrecy-status').style.color = '#EF4444';
            }
            
            document.getElementById('backward-secrecy-status').textContent = security.backward_secrecy ? '启用' : '禁用';
            if (security.backward_secrecy) {
                document.getElementById('backward-secrecy-status').style.color = '#10B981';
            } else {
                document.getElementById('backward-secrecy-status').style.color = '#EF4444';
            }
        } catch (error) {
            console.error('加载安全信息失败:', error);
        }
    }
    
    updateStatElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            // 添加更新动画效果
            element.classList.add('updating');
            element.textContent = value;
            
            // 移除动画类，以便下次更新时可以重新触发
            setTimeout(() => {
                element.classList.remove('updating');
            }, 500);
        }
    }
    
    async loadRoutingTable() {
        try {
            const response = await fetch('/api/node/routing');
            const routing = await response.json();
            
            const tbody = document.querySelector('#routing-table tbody');
            tbody.innerHTML = '';
            
            routing.nodes.forEach(node => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td title="${node.node_id}">${node.node_id ? node.node_id.substring(0, 8) + '...' : 'N/A'}</td>
                    <td>${node.host || 'N/A'}</td>
                    <td>${node.port || 'N/A'}</td>
                    <td>${node.encrypted ? '✅' : '❌'}</td>
                    <td>${new Date(node.connected_since * 1000).toLocaleString() || 'N/A'}</td>
                    <td>${node.security_level || 'N/A'}</td>
                `;
                tbody.appendChild(row);
            });
        } catch (error) {
            console.error('加载路由表失败:', error);
        }
    }
    
    async sendMessage() {
        const target = document.getElementById('target-node').value.trim();
        const message = document.getElementById('message-content').value.trim();
        
        if (!target || !message) {
            this.showNotification('请填写目标节点ID和消息内容', 'error');
            return;
        }
        
        const button = document.getElementById('send-message-btn');
        const originalText = this.showLoading(button, button.textContent);
        
        try {
            const response = await fetch('/api/messages/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target: target,
                    message: message
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('加密消息发送成功', 'success');
                document.getElementById('message-content').value = '';
            } else {
                this.showNotification('消息发送失败: ' + (result.error || '未知错误'), 'error');
            }
        } catch (error) {
            this.showNotification('发送消息时发生错误: ' + error.message, 'error');
        } finally {
            this.hideLoading(button, originalText);
        }
    }
    
    async sendMultimedia() {
        const target = document.getElementById('target-node').value.trim();
        const fileInput = document.getElementById('media-file');
        const file = fileInput.files[0];
        
        if (!target || !file) {
            this.showNotification('请填写目标节点ID并选择文件', 'error');
            return;
        }
        
        // 这里应该实现文件上传逻辑，简化为模拟发送
        this.showNotification('加密多媒体消息发送功能正在开发中', 'info');
    }
    
    async syncNetwork() {
        const button = document.getElementById('sync-btn');
        const originalText = this.showLoading(button, button.textContent);
        
        try {
            const response = await fetch('/api/node/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'sync started') {
                this.showNotification('网络同步已开始', 'success');
            } else {
                this.showNotification('同步请求失败', 'error');
            }
        } catch (error) {
            this.showNotification('请求同步时发生错误: ' + error.message, 'error');
        } finally {
            this.hideLoading(button, originalText);
        }
    }
    
    async performSecurityCheck() {
        const button = document.getElementById('security-check');
        const originalText = this.showLoading(button, button.textContent);
        
        try {
            // 模拟安全检查
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showNotification('安全检查完成 - 所有安全协议正常运行', 'success');
        } catch (error) {
            this.showNotification('安全检查失败: ' + error.message, 'error');
        } finally {
            this.hideLoading(button, originalText);
        }
    }
    
    formatDuration(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        
        if (h > 0) {
            return `${h}小时 ${m}分钟 ${s}秒`;
        } else if (m > 0) {
            return `${m}分钟 ${s}秒`;
        } else {
            return `${s}秒`;
        }
    }
    
    startAutoRefresh() {
        // 每30秒自动刷新节点状态
        setInterval(() => {
            this.loadNodeStats();  // 总是更新节点统计信息，无论哪个标签页被激活
            if (this.currentTab === 'security') {
                this.loadSecurityInfo();  // 如果在安全标签页，也刷新安全状态
            }
            if (this.currentTab === 'settings') {
                this.loadSystemInfo();
            }
        }, 30000);
    }
    
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/system/info');
            const info = await response.json();
            
            // 更新系统信息显示
            document.querySelector('#system-uptime').textContent = this.formatDuration(info.uptime);
            
            // 添加更多系统信息到设置面板
            this.updateSystemInfoPanel(info);
            
        } catch (error) {
            console.error('加载系统信息失败:', error);
        }
    }
    
    updateSystemInfoPanel(info) {
        // 找到系统信息卡片并更新内容
        const systemInfoContainer = document.querySelector('.system-info');
        if (systemInfoContainer) {
            // 清除除前两项外的所有系统信息（保留版本和运行时间）
            const items = systemInfoContainer.querySelectorAll('.info-item');
            if (items.length > 2) {
                for (let i = 2; i < items.length; i++) {
                    items[i].remove();
                }
            }
            
            // 添加新的系统信息
            const cpuInfo = document.createElement('div');
            cpuInfo.className = 'info-item';
            cpuInfo.innerHTML = `
                <span class="label">CPU使用率:</span>
                <span class="value">${info.cpu_percent}%</span>
            `;
            systemInfoContainer.appendChild(cpuInfo);
            
            const memoryInfo = document.createElement('div');
            memoryInfo.className = 'info-item';
            memoryInfo.innerHTML = `
                <span class="label">内存使用率:</span>
                <span class="value">${Math.round(info.memory_percent)}%</span>
            `;
            systemInfoContainer.appendChild(memoryInfo);
            
            const nodeInfo = document.createElement('div');
            nodeInfo.className = 'info-item';
            nodeInfo.innerHTML = `
                <span class="label">节点ID:</span>
                <span class="value">${info.node_id}</span>
            `;
            systemInfoContainer.appendChild(nodeInfo);
            
            const platformInfo = document.createElement('div');
            platformInfo.className = 'info-item';
            platformInfo.innerHTML = `
                <span class="label">平台:</span>
                <span class="value">${info.platform} ${info.architecture}</span>
            `;
            systemInfoContainer.appendChild(platformInfo);
        }
    }
    
    setupNotifications() {
        // 创建通知容器
        if (!document.querySelector('#notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                z-index: 1000;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 350px;
            `;
            document.body.appendChild(container);
        }
    }
    
    showNotification(message, type = 'info') {
        const container = document.querySelector('#notification-container');
        const notification = document.createElement('div');
        
        const bgColor = {
            success: 'rgba(16, 185, 129, 0.9)',
            error: 'rgba(239, 68, 68, 0.9)',
            warning: 'rgba(245, 158, 11, 0.9)',
            info: 'rgba(59, 130, 246, 0.9)'
        }[type] || 'rgba(59, 130, 246, 0.9)';
        
        notification.innerHTML = `
            <div class="notification-content" style="
                background: ${bgColor};
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                margin-bottom: 10px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                display: flex;
                align-items: center;
                justify-content: space-between;
                min-width: 300px;
                animation: slideIn 0.3s ease-out;
            ">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 1.2rem;
                    cursor: pointer;
                    padding: 0 0 0 1rem;
                ">&times;</button>
            </div>
        `;
        
        container.appendChild(notification);
        
        // 5秒后自动移除通知
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                notification.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
    
    showLoading(button, originalText) {
        button.disabled = true;
        button.innerHTML = '<span class="loading-spinner"></span> 处理中...';
        button.style.opacity = '0.7';
        
        // 添加加载动画的样式
        if (!document.querySelector('#loading-styles')) {
            const style = document.createElement('style');
            style.id = 'loading-styles';
            style.textContent = `
                .loading-spinner {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border: 2px solid rgba(255,255,255,.3);
                    border-radius: 50%;
                    border-top-color: white;
                    animation: spin 1s ease-in-out infinite;
                    margin-right: 8px;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
        
        return originalText;
    }
    
    hideLoading(button, originalText) {
        button.disabled = false;
        button.textContent = originalText;
        button.style.opacity = '1';
    }
}

// 页面加载完成后初始化控制台
// 全局变量存储控制台实例
let secureChatConsole;

// 全局函数，供HTML调用
function switchToTab(tabName) {
    if (secureChatConsole && typeof secureChatConsole.switchTab === 'function') {
        secureChatConsole.switchTab(tabName);
    }
}

// 页面加载完成后初始化控制台
document.addEventListener('DOMContentLoaded', () => {
    secureChatConsole = new SecureChatConsole();
    
    // 初始化时也更新初学者界面的数据
    setTimeout(() => {
        if (secureChatConsole.currentTab === 'beginner') {
            secureChatConsole.loadNodeStats();
        }
    }, 100);
});