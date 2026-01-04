"""
工业级安全去中心化聊天系统 - 主入口点

此模块提供系统的主入口点，用于启动安全聊天节点。
"""
import asyncio
import argparse
from src.p2p.secure_node_server import SecureChatNode


async def run_node(host: str, port: int, bootstrap_nodes: list = None):
    """运行安全聊天节点"""
    node = SecureChatNode(host, port)
    
    print(f"[*] 节点ID: {node.get_identity_info()['node_id']}")
    print(f"[*] 身份公钥: {node.get_identity_info()['identity_key'][:32]}...")
    
    try:
        await node.start_node(bootstrap_nodes)
    except KeyboardInterrupt:
        print("\n[停止] 节点正在关闭...")
        node.node_server.stop()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='工业级安全去中心化聊天节点')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='监听主机地址')
    parser.add_argument('--port', type=int, default=8080, help='监听端口')
    parser.add_argument('--bootstrap', type=str, nargs='*', 
                       help='引导节点地址 (格式: ip:port:node_id)')
    
    args = parser.parse_args()
    
    bootstrap_nodes = []
    if args.bootstrap:
        for bs in args.bootstrap:
            parts = bs.split(':')
            if len(parts) == 3:
                bootstrap_nodes.append((parts[0], int(parts[1]), parts[2]))
    
    print("[*] 启动工业级安全去中心化聊天节点...")
    print(f"[*] 监听地址: {args.host}:{args.port}")
    if bootstrap_nodes:
        print(f"[*] 引导节点: {bootstrap_nodes}")
    
    # 运行节点
    asyncio.run(run_node(args.host, args.port, bootstrap_nodes))


if __name__ == "__main__":
    main()