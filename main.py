import asyncio
import sys
from src.node import ProtocolNode
from colorama import init, Fore, Style

init(autoreset=True)

async def run_cli(node: ProtocolNode):
    print(Fore.CYAN + f"""
    =========================================
      去中心化社交节点启动 | ID: {node.node_id}
      监听端口: {node.addr[1]}
    =========================================
    输入 'list' 查看邻居
    输入 'send <TargetID> <Msg>' 发送消息
    输入 'cons <Data>' 发起共识
    输入 'exit' 退出
    """)
    
    # 简单的非阻塞输入处理循环
    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            line = line.strip()
            if not line: continue
            
            parts = line.split(' ')
            cmd = parts[0]

            if cmd == "list":
                print(f"当前已知节点 ({len(node.routing_table)}):")
                for nid, info in node.routing_table.items():
                    print(f" - {nid} @ {info['host']}:{info['port']}")
            
            elif cmd == "send":
                if len(parts) < 3:
                    print("用法: send <TargetID> <Message>")
                    continue
                target = parts[1]
                msg = " ".join(parts[2:])
                await node.send_message(target, msg)
            
            elif cmd == "cons":
                if len(parts) < 2: continue
                data = " ".join(parts[1:])
                await node.consensus.start_proposal(data)

            elif cmd == "exit":
                break
                
        except KeyboardInterrupt:
            break

async def main():
    if len(sys.argv) < 3:
        print("用法: python main.py <NodeID> <Port> [BootstrapHost:Port]")
        return

    nid = sys.argv[1]
    port = int(sys.argv[2])
    
    bootstrap_nodes = []
    if len(sys.argv) > 3:
        bh, bp = sys.argv[3].split(':')
        bootstrap_nodes.append((bh, int(bp)))

    node = ProtocolNode(nid, "127.0.0.1", port, bootstrap_nodes)
    
    # 启动服务器
    await node.start()
    
    # 启动 CLI 交互
    await run_cli(node)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass