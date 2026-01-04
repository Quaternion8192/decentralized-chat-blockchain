"""
主入口文件 - 类区块链聊天节点
"""
import asyncio
import json
import sys
import argparse
from ..config.config import get_config
from .chat_node import ChatNode
from ..blockchain.blockchain import Blockchain


def run_cli(node: ChatNode):
    """运行命令行界面"""
    print(f"""
    =========================================
      类区块链聊天节点启动 | ID: {node.node_id}
      监听端口: {node.addr[1]}
    =========================================
    命令:
    - 'list' 查看邻居
    - 'send <TargetID> <Msg>' 发送消息
    - 'send_media <TargetID> <FilePath>' 发送多媒体文件
    - 'gossip <Type> <Data>' 发送Gossip消息
    - 'gossip_stats' 查看Gossip统计
    - 'cons <Data>' 发起共识
    - 'sync' 同步区块链
    - 'chain' 查看区块链状态
    - 'stats' 查看节点统计
    - 'incentive' 查看激励信息
    - 'exit' 退出
    """)
    
    # 简单的非阻塞输入处理循环
    loop = asyncio.get_running_loop()
    while True:
        try:
            line = input(f"[{node.node_id}]> ")
            line = line.strip()
            if not line: continue
            
            parts = line.split(' ')
            cmd = parts[0]

            if cmd == "list":
                print(f"当前已知节点 ({len(node.routing_table_manager.routing_table)}):")
                for nid, info in node.routing_table_manager.routing_table.items():
                    print(f" - {nid} @ {info['host']}:{info['port']} (URL: {info.get('public_url', 'N/A')})")
            
            elif cmd == "send":
                if len(parts) < 3:
                    print("用法: send <TargetID> <Message>")
                    continue
                target = parts[1]
                msg = " ".join(parts[2:])
                asyncio.run_coroutine_threadsafe(node.send_message(target, msg), loop)
            
            elif cmd == "send_media":
                if len(parts) < 3:
                    print("用法: send_media <TargetID> <FilePath>")
                    continue
                target = parts[1]
                file_path = parts[2]
                
                # 检查文件是否存在
                import os
                if not os.path.exists(file_path):
                    print(f"[!] 文件不存在: {file_path}")
                    continue
                
                # 读取文件内容
                try:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    # 根据文件扩展名确定媒体类型
                    import os.path
                    file_ext = os.path.splitext(file_path)[1].lower()
                    media_types = {
                        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif',
                        '.mp3': 'audio/mp3', '.wav': 'audio/wav',
                        '.mp4': 'video/mp4', '.avi': 'video/avi', '.mov': 'video/mov'
                    }
                    media_type = media_types.get(file_ext, 'file')
                    
                    # 发送多媒体消息
                    asyncio.run_coroutine_threadsafe(
                        node.send_multimedia_message(
                            target, 
                            media_type, 
                            file_data, 
                            {"original_filename": os.path.basename(file_path)}
                        ),
                        loop
                    )
                except Exception as e:
                    print(f"[!] 读取文件失败: {e}")
            
            elif cmd == "cons":
                if len(parts) < 2: 
                    print("用法: cons <ProposalData>")
                    continue
                data = " ".join(parts[1:])
                asyncio.run_coroutine_threadsafe(node.start_consensus_proposal(data), loop)

            elif cmd == "sync":
                print("[*] 正在同步区块链...")
                asyncio.run_coroutine_threadsafe(node.sync_blockchain(), loop)
                print("[✓] 区块链同步完成")

            elif cmd == "chain":
                info = node.get_blockchain_info()
                print(f"区块链长度: {info['length']}")
                print(f"区块链有效性: {'有效' if info['valid'] else '无效'}")
                # 只显示最近几个区块
                recent_blocks = info['chain'][-3:]  # 显示最近3个区块
                print("最近的区块:")
                for block in recent_blocks:
                    print(f"  - #{block['index']}: {block['data'][:50]}...")

            elif cmd == "stats":
                stats = node.get_node_stats()
                print(f"节点统计信息:")
                print(f"  节点ID: {stats['node_id']}")
                print(f"  在线时间: {stats['uptime']:.2f}秒 ({stats['uptime']/3600:.2f}小时)")
                print(f"  发送消息数: {stats['messages_sent']}")
                print(f"  发送多媒体消息数: {stats['multimedia_messages_sent']}")
                print(f"  路由表大小: {stats['routing_table_size']}")
                
            elif cmd == "incentive":
                incentive_info = node.get_node_stats()['incentive_info']
                if incentive_info:
                    print(f"激励机制信息:")
                    print(f"  余额: {incentive_info['balance']}")
                    print(f"  声誉分数: {incentive_info['reputation_score']:.2f}")
                    print(f"  节点类型: {incentive_info['node_type']}")
                    print(f"  提供带宽: {incentive_info['bandwidth_provided']} 字节")
                    print(f"  提供存储: {incentive_info['storage_provided']} 字节")
                    print(f"  转发消息数: {incentive_info['messages_forwarded']}")
                    print(f"  验证区块数: {incentive_info['blocks_validated']}")
                else:
                    print("未找到激励机制信息")
            
            elif cmd == "gossip":
                if len(parts) < 3:
                    print("用法: gossip <Type> <JSON_Data>")
                    print("类型: data_sync, membership, custom")
                    continue
                try:
                    msg_type = parts[1]
                    data_str = ' '.join(parts[2:])
                    content = json.loads(data_str)
                    asyncio.run_coroutine_threadsafe(node.send_gossip_message(msg_type, content), loop)
                except json.JSONDecodeError:
                    print("JSON格式错误，请提供有效的JSON数据")
                except Exception as e:
                    print(f"发送Gossip消息失败: {e}")
            
            elif cmd == "gossip_stats":
                stats = node.get_gossip_stats()
                print("Gossip统计信息:")
                for protocol_name, protocol_stats in stats.items():
                    print(f"  协议 {protocol_name}:")
                    stat_info = protocol_stats["stats"]
                    print(f"    发送消息数: {stat_info['messages_sent']}")
                    print(f"    接收消息数: {stat_info['messages_received']}")
                    print(f"    传播消息数: {stat_info['messages_propagated']}")
                    print(f"    已接收消息数: {protocol_stats['received_messages_count']}")

            elif cmd == "exit":
                print("[*] 正在停止节点...")
                node.running = False
                break
                
        except KeyboardInterrupt:
            print("\n[*] 正在停止节点...")
            node.running = False
            break


def main():
    config = get_config()
    
    parser = argparse.ArgumentParser(description='启动类区块链聊天节点')
    parser.add_argument('node_id', help='节点ID')
    parser.add_argument('port', type=int, help='监听端口')
    parser.add_argument('--bootstrap', help='引导节点地址 (host:port)')
    
    args = parser.parse_args()
    
    # 解析引导节点
    bootstrap_nodes = []
    if args.bootstrap:
        host, port = args.bootstrap.split(':')
        bootstrap_nodes.append((host, int(port)))

    # 创建区块链实例
    blockchain = Blockchain(consensus_type=config.get("blockchain.consensus_type", "vdf_pow"))
    
    # 创建节点
    node = ChatNode(
        args.node_id, 
        "127.0.0.1", 
        args.port, 
        blockchain, 
        bootstrap_nodes
    )
    
    async def run_node():
        await node.start()
        
        # 运行CLI交互
        run_cli(node)
    
    # 运行节点
    try:
        asyncio.run(run_node())
    except KeyboardInterrupt:
        print(f"\n[*] 正在停止节点 {args.node_id}...")


if __name__ == "__main__":
    main()