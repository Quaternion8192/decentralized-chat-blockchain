# 去中心化社交协议

## 概述

本项目旨在实现一个基于双轨混合分层架构的去中心化社交协议。它融合了先进的网络通信、强大的加密机制、简化的HotStuff共识算法、信鸽协议用于离线消息处理，并集成了VDF（可验证延迟函数）作为反垃圾邮件的初步机制。我们的目标是构建一个平衡去中心化、高性能和用户隐私的社交网络基础设施。

## 核心特性

*   **双轨混合分层架构**：
    *   **核心骨干层（Full Nodes）**：由高性能节点组成，负责网络拓扑维护、消息中转、共识投票等。
    *   **边缘接入层（Light Clients）**：以移动端为主，按需连接骨干层，优化弱网络环境下的连接和功耗。
*   **安全通信**：
    *   **端到端加密**：使用混合加密（AES对称加密消息内容，RSA非对称加密AES密钥）确保消息隐私。
    *   **消息签名**：基于RSA算法对消息进行签名，确保消息来源的真实性和完整性。
*   **信鸽协议 (Pigeon Protocol)**：
    *   **离线消息缓存**：当接收方离线时，消息将被加密缓存到网络中的中继节点。
    *   **零知识提取 (简化实现)**：用户上线后，能通过（模拟的）零知识证明向中继节点提取其加密消息，而无需泄露身份。
*   **高性能共识**：
    *   **HotStuff共识算法 (简化实现)**：采用三阶段流水线共识机制，支持高效的提案确认。
    *   **声誉加权 (概念)**：未来的投票权将基于节点声誉积分和持有代币权重进行分配。
*   **反垃圾机制**：
    *   **可验证延迟函数 (VDF)**：通过要求发送方完成少量计算来增加垃圾消息发送成本。
*   **去中心化身份 (DID)**：支持基于W3C DID标准的节点标识符。

## 技术栈

*   **异步框架**: `asyncio`
*   **加密库**: `cryptography`
*   **网络通信**: 基于 `asyncio` 的 TCP 协议，实现消息分包和 JSON 序列化。
*   **共识算法**: 简化的 HotStuff
*   **零知识证明**: 概念性实现 (PigeonRelay 中通过 `_verify_proof` 模拟)
*   **防垃圾机制**: VDF (可验证延迟函数)

## 安装指南

在开始之前，请确保你已安装 Python 3.8+。

```bash
# 1. 克隆仓库 (如果尚未完成)
# git clone <你的仓库地址>
# cd decentralized-social-protocol

# 2. 安装依赖
pip install -r requirements.txt
```

`requirements.txt` 文件内容如下：
```
cryptography>=41.0.0
colorama>=0.4.6
```

## 使用说明

本项目通过命令行界面模拟多个节点间的交互。

### 启动节点

你需要在不同的终端窗口中启动不同的节点。第一个启动的节点通常作为网络的“种子节点”。

**启动种子节点 (例如 NodeA，监听 8001 端口):**

```bash
python main.py NodeA 8001
```

**启动其他节点 (例如 NodeB，监听 8002 端口，连接到 NodeA):**

```bash
python main.py NodeB 8002 127.0.0.1:8001
```

你可以启动更多节点，并指定它们连接到一个或多个已存在的节点（启动参数中的 `127.0.0.1:8001`）。

### 交互命令

节点启动后，你可以在各自的终端中输入命令进行交互：

*   `list`: 查看当前节点已发现的网络邻居节点。
*   `send <TargetNodeID> <Message>`: 向指定的目标节点发送端到端加密消息。如果目标节点离线，消息将尝试通过中继节点缓存。
*   `cons <ProposalData>`: 作为当前节点的 Leader，发起一个共识提案。其他节点会验证并（在简化实现中）打印提案。
*   `exit`: 退出当前节点程序。

**示例：发送消息**

```bash
# 在 NodeA 的终端
send NodeB Hello_from_NodeA
```

**示例：发起共识**

```bash
# 在 NodeA 的终端
cons Important_Network_Update_V3
```

## API 文档

### `src/node.py` 中的 `ProtocolNode` 类

*   `__init__(node_id: str, host: str, port: int, bootstrap_nodes: list = None)`: 初始化节点，包括 ID、网络地址、密钥对和可选的引导节点列表。
*   `get_did() -> str`: 获取节点的去中心化标识符 (DID)，格式为 `did:p2p:{node_id}`。
*   `start()`: 启动节点的网络监听服务，并尝试连接引导节点。
*   `send_message(target_node_id: str, text: str)`: 向目标节点发送加密消息。
*   `update_routing(new_table: dict)`: 更新节点的路由表信息。

### `src/network.py` 中的 `P2PProtocol` 和 `NodeServer`

*   `P2PProtocol.send_json(writer, data)`: 通过 `asyncio.StreamWriter` 发送带长度前缀的 JSON 数据。
*   `P2PProtocol.read_json(reader)`: 通过 `asyncio.StreamReader` 读取带长度前缀的 JSON 数据。
*   `NodeServer(host, port, handler_callback)`: 创建一个 TCP 服务器，用于监听传入连接并调用 `handler_callback` 处理消息。

### `src/crypto_utils.py` 中的 `CryptoManager` 类

*   `__init__()`: 生成节点的 RSA 密钥对。
*   `get_pub_key_pem() -> str`: 获取 PEM 格式的公共密钥字符串。
*   `load_pub_key(pem_str: str)`: 从 PEM 字符串加载公共密钥对象。
*   `sign(message: str) -> str`: 使用节点的私钥对消息进行签名。
*   `verify(pub_key, message: str, signature_b64: str) -> bool`: 使用公共密钥验证消息签名。
*   `encrypt_for(target_pub_key_pem: str, data: str) -> dict`: 对数据进行混合加密（AES + RSA），用于发送给目标。
*   `decrypt_message(encrypted_package: dict) -> str`: 使用节点的私钥解密收到的混合加密消息。

### `src/consensus.py` 中的 `SimplifiedHotStuff` 类

*   `__init__(node)`: 初始化共识模块，绑定到所属节点。
*   `start_proposal(block_data: str)`: 作为 Leader 发起一个包含 `block_data` 的共识提案。
*   `handle_proposal(msg: dict)`: 处理收到的共识提案，进行签名验证（简化处理）。

### `interface.py` 中的辅助类 (概念性接口，未完全集成到当前运行代码)

*   `PigeonRelay`: 离线消息缓存和零知识提取的模拟实现。
    *   `cache_message(receiver_id, encrypted_msg)`
    *   `zkp_extract(receiver_id, proof)`
*   `HotStuffConsensus`: 提供了计算投票权和三阶段提交的概念。
    *   `calculate_voting_power(node)`
    *   `run_three_phase_commit(proposal)`
*   `AntiSpamVDF`: 可验证延迟函数的模拟实现。
    *   `solve(challenge, difficulty)`
    *   `verify(challenge, proof, difficulty)`

## 贡献指南

我们非常欢迎社区的贡献！如果你想为本项目做出贡献，请遵循以下步骤：

1.  **Fork** 本仓库。
2.  创建一个新的特性分支 (`git checkout -b feature/YourFeatureName`)。
3.  提交你的修改 (`git commit -m 'Add new feature'`)。
4.  推送到你的分支 (`git push origin feature/YourFeatureName`)。
5.  创建一个 **Pull Request**，描述你的修改内容。

## 许可证

本项目采用 MIT 许可证。详见 `LICENSE` 文件。
