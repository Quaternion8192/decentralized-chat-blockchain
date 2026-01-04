# Decentralized Chat with Blockchain [去中心化区块链聊天系统]

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Status-Beta-green.svg)](https://github.com/Quaternion8192/decentralized-chat-blockchain)
[![Stars](https://img.shields.io/github/stars/Quaternion8192/decentralized-chat-blockchain.svg?style=social)](https://github.com/Quaternion8192/decentralized-chat-blockchain)
[![Forks](https://img.shields.io/github/forks/Quaternion8192/decentralized-chat-blockchain.svg?style=social)](https://github.com/Quaternion8192/decentralized-chat-blockchain)
[![Issues](https://img.shields.io/github/issues/Quaternion8192/decentralized-chat-blockchain)](https://github.com/Quaternion8192/decentralized-chat-blockchain/issues)

</div>

<div align="center">

### 🚀 A decentralized chat solution based on P2P networks, blockchain technology, and NAT traversal

</div>

---

## English Version

A decentralized chat solution based on P2P networks, blockchain technology, and NAT traversal.

### ✨ Features

- **Blockchain Technology**: Uses blockchain to record messages and consensus events
- **End-to-End Encryption**: RSA+AES hybrid encryption for message security
- **P2P Network**: Decentralized node communication
- **NAT Traversal**: Supports STUN, ngrok, and UPnP for NAT penetration
- **Pigeon Protocol**: Offline message caching and retrieval
- **Consensus Mechanism**: Simplified HotStuff consensus algorithm
- **Multimedia Support**: Image, audio, and video transmission
- **Incentive Mechanism**: Token rewards based on node contributions
- **Gossip Protocol**: Efficient message propagation
- **VDF (Verifiable Delay Function)**: Computational delay for spam prevention
- **Zero-Knowledge Proofs**: Privacy-preserving verification
- **IPFS Integration**: Distributed storage
- **Web UI Console**: Modern web-based control panel with real-time monitoring

### 📦 Installation

```bash
pip install -r requirements.txt
```

### 🚀 Usage

#### Start Bootstrap Node (Seed Node)

```bash
python -m src.core.node NodeA 8001
```

#### Start Other Nodes and Connect to Bootstrap Node

```bash
python -m src.core.node NodeB 8002 --bootstrap 127.0.0.1:8001
```

#### Enable NAT Traversal

```bash
python -m src.core.node NodeC 8003 --bootstrap 127.0.0.1:8001 --nat
```

#### Start Web UI Console

```bash
python webui.py
```

System will automatically:
- Start node server (default port 9001)
- Start web server (default port 8080)
- Open browser to access console at `http://localhost:8080`

### 🏗️ Architecture

#### Blockchain Layer
- Each message and consensus event is recorded on the blockchain
- Mining using proof of work (simplified version)
- Blockchain synchronization ensures data consistency across all nodes

#### Network Layer
- P2P protocol for direct communication between nodes
- Routing table maintains network topology
- Message length prefix prevents packet sticking
- Node health checks with ping/pong mechanism
- Advanced reputation system based on node reliability

#### Encryption Layer
- RSA for key exchange and signatures
- AES for message content encryption
- Hybrid encryption scheme ensures security

#### NAT Traversal Layer
- STUN protocol for public mapping detection
- ngrok for TCP tunnel
- UPnP for automatic port forwarding

### ⚠️ Ngrok Configuration Note

**Important**: Starting from October 2023, ngrok requires a verified account and authentication token to function. If you encounter an authentication error, you have two options:

1. **Register for ngrok account** (Recommended for production use):
   - Sign up at: https://dashboard.ngrok.com/signup
   - Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
   - Install the authtoken: `ngrok config add-authtoken YOUR_AUTHTOKEN`

2. **Disable ngrok** (Recommended for local testing):
   - Create a `config.json` file in the project root directory with the following content:
   ```json
   {
     "nat_traversal": {
       "enable_ngrok": false,
       "stun_servers": [
         "stun.l.google.com:19302",
         "stun1.l.google.com:19302"
       ],
       "upnp_enabled": true
     }
   }
   ```
   - Then start your nodes with the `--nat` flag: `python -m src.core.node NodeA 8001 --nat`

#### Web UI Console Features

- **Beginner-friendly interface** - Simplified getting started interface for new users
- **Dashboard panel** - Real-time display of node statistics
- **Message management** - Send and receive messages
- **Network management** - View and manage routing table
- **Blockchain browser** - View blockchain information and block details
- **Consensus management** - Initiate consensus proposals
- **System settings** - Node configuration management

### 📋 Protocol Design

#### Pigeon Protocol
- When the target node is offline, messages are cached in relay nodes in the network
- Nodes can retrieve messages after coming online using zero-knowledge proofs

#### Gossip Protocol
- Efficient message propagation using configurable fanout and TTL
- Support for data synchronization, membership changes, and custom messages
- Advanced message processing with different content types

#### Consensus Mechanism
- Simplified HotStuff three-phase commit
- Voting rights allocation based on node reputation
- Enhanced incentive mechanisms with uptime and reputation bonuses

### 🔐 Security

- All messages are end-to-End encrypted
- Message integrity verified using digital signatures
- Blockchain ensures data immutability
- Anti-replay attack mechanism

### 📁 Project Structure

```
src/
├── blockchain/          # Blockchain implementation
├── crypto/              # Cryptography utilities
├── network/             # Network communication
├── p2p/                 # P2P protocols
├── multimedia/          # Multimedia processing
├── incentive/           # Incentive mechanisms
├── routing/             # Routing management
├── gossip/              # Gossip protocol
├── vdf/                 # Verifiable delay functions
├── zkp/                 # Zero-knowledge proofs
├── ipfs/                # IPFS integration
├── config/              # Configuration management
├── utils/               # Utility functions
└── core/                # Core application logic
```

### 🎨 Web UI Design Style

- **Minimalist and Rational**: Clean and neat page, large area of white space, emphasizing structural presentation of content
- **Modern**: No unnecessary decoration, flat design, clear visual hierarchy
- **High Contrast**: Supports dark/light theme mode
- **Responsive Layout**: Adapted to different screen sizes
- **User-friendly**: Simplified beginner interface, reducing learning curve

### 🌐 API Endpoints

- `GET /api/node/stats` - Get node statistics
- `GET /api/node/routing` - Get routing table
- `GET /api/blockchain/info` - Get blockchain information
- `GET /api/blockchain/chain` - Get full blockchain data
- `POST /api/messages/send` - Send message
- `POST /api/messages/send_multimedia` - Send multimedia message
- `POST /api/consensus/propose` - Initiate consensus proposal
- `POST /api/node/sync` - Synchronize blockchain

---

## 中文版 README

基于P2P网络、区块链技术和NAT穿越的去中心化聊天解决方案。

### ✨ 功能特性

- **区块链技术**: 使用区块链记录消息和共识事件
- **端到端加密**: RSA+AES混合加密保障消息安全
- **P2P网络**: 去中心化节点通信
- **NAT穿越**: 支持STUN、ngrok和UPnP进行NAT穿透
- **信鸽协议**: 离线消息缓存和获取
- **共识机制**: 简化版HotStuff共识算法
- **多媒体支持**: 图片、音频和视频传输
- **激励机制**: 基于节点贡献的代币奖励
- **Gossip协议**: 高效消息传播
- **VDF (可验证延迟函数)**: 计算延迟防垃圾
- **零知识证明**: 隐私保护验证
- **IPFS集成**: 分布式存储
- **Web UI控制台**: 现代化网页控制面板，实时监控

### 📦 安装

```bash
pip install -r requirements.txt
```

### 🚀 使用方法

#### 启动引导节点（种子节点）

```bash
python -m src.core.node NodeA 8001
```

#### 启动其他节点并连接到引导节点

```bash
python -m src.core.node NodeB 8002 --bootstrap 127.0.0.1:8001
```

#### 启用NAT穿越

```bash
python -m src.core.node NodeC 8003 --bootstrap 127.0.0.1:8001 --nat
```

#### 启动Web UI控制台

```bash
python webui.py
```

系统将自动：
- 启动节点服务器（默认端口9001）
- 启动Web服务器（默认端口8080）
- 自动打开浏览器访问控制台 `http://localhost:8080`

### 🏗️ 架构设计

#### 区块链层
- 每条消息和共识事件都记录在区块链上
- 使用工作量证明进行挖矿（简化版）
- 区块链同步确保所有节点数据一致性

#### 网络层
- P2P协议实现节点间直接通信
- 路由表维护网络拓扑
- 消息长度前缀防止粘包
- 节点健康检查通过ping/pong机制
- 基于节点可靠性的高级信誉系统

#### 加密层
- RSA用于密钥交换和签名
- AES用于消息内容加密
- 混合加密方案确保安全性

#### NAT穿越层
- STUN协议用于公网映射检测
- ngrok提供TCP隧道
- UPnP自动端口转发

### ⚠️ Ngrok配置注意事项

**重要**: 从2023年10月开始，ngrok需要验证账户和认证令牌才能使用。如果您遇到认证错误，有两种选择：

1. **注册ngrok账户** (推荐用于生产环境):
   - 注册地址: https://dashboard.ngrok.com/signup
   - 获取认证令牌: https://dashboard.ngrok.com/get-started/your-authtoken
   - 安装认证令牌: `ngrok config add-authtoken 您的认证令牌`

2. **禁用ngrok** (推荐用于本地测试):
   - 在项目根目录创建 `config.json` 文件，内容如下:
   ```json
   {
     "nat_traversal": {
       "enable_ngrok": false,
       "stun_servers": [
         "stun.l.google.com:19302",
         "stun1.l.google.com:19302"
       ],
       "upnp_enabled": true
     }
   }
   ```
   - 然后使用 `--nat` 参数启动节点: `python -m src.core.node NodeA 8001 --nat`

#### Web UI控制台功能

- **初学者友好界面** - 简化的入门界面，方便新手使用
- **控制台面板** - 实时显示节点统计信息
- **消息管理** - 发送和接收消息
- **网络管理** - 查看和管理路由表
- **区块链浏览器** - 查看区块链信息和区块详情
- **共识管理** - 发起共识提案
- **系统设置** - 节点配置管理

### 📋 协议设计

#### 信鸽协议
- 当目标节点离线时，消息在网络中的中继节点中缓存
- 节点上线后可以使用零知识证明检索消息

#### Gossip协议
- 使用可配置的fanout和TTL进行高效消息传播
- 支持数据同步、成员变更和自定义消息
- 不同内容类型的高级消息处理

#### 共识机制
- 简化版HotStuff三阶段提交
- 基于节点信誉的投票权分配
- 增强的激励机制，包含在线时间和信誉奖励

### 🔐 安全性

- 所有消息均端到端加密
- 使用数字签名验证消息完整性
- 区块链确保数据不可篡改
- 防重放攻击机制

### 📁 项目结构

```
src/
├── blockchain/          # 区块链实现
├── crypto/              # 加密工具
├── network/             # 网络通信
├── p2p/                 # P2P协议
├── multimedia/          # 多媒体处理
├── incentive/           # 激励机制
├── routing/             # 路由管理
├── gossip/              # Gossip协议
├── vdf/                 # 可验证延迟函数
├── zkp/                 # 零知识证明
├── ipfs/                # IPFS集成
├── config/              # 配置管理
├── utils/               # 工具函数
└── core/                # 核心应用逻辑
```

### 🎨 Web UI设计风格

- **极简主义与理性**: 页面干净利落，大面积留白，强调内容的结构化呈现
- **现代化**: 无多余装饰，扁平化设计，采用清晰的视觉层级
- **高对比度**: 支持深色/浅色主题模式
- **响应式布局**: 适配不同屏幕尺寸
- **用户友好**: 简化的初学者界面，降低上手难度

### 🌐 API端点

- `GET /api/node/stats` - 获取节点统计信息
- `GET /api/node/routing` - 获取路由表
- `GET /api/blockchain/info` - 获取区块链信息
- `GET /api/blockchain/chain` - 获取区块链完整数据
- `POST /api/messages/send` - 发送消息
- `POST /api/messages/send_multimedia` - 发送多媒体消息
- `POST /api/consensus/propose` - 发起共识提案
- `POST /api/node/sync` - 同步区块链

### 📄 许可证

MIT