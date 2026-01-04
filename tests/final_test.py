#!/usr/bin/env python3
"""
最终测试，验证所有修改后的功能是否正常工作
"""
from src.zkp.zkp import ZKPManager, ZKPGenerator
from src.blockchain.blockchain import Blockchain
from src.crypto.crypto_manager import CryptoManager, KeyExchangeManager
from cryptography.hazmat.primitives import serialization
import time


def test_zkp():
    """测试 ZKP 功能"""
    print('1. 测试 ZKP 管理器...')
    zkp_manager = ZKPManager()
    proof_id = zkp_manager.create_proof('test_statement', 'test_witness')
    print(f'   证明创建成功: {proof_id[:16]}...')
    verification_result = zkp_manager.verify_proof_by_id(proof_id)
    print(f'   证明验证结果: {verification_result}')
    
    # 测试过期清理功能
    original_count = len(zkp_manager.proof_store)
    zkp_manager.proof_timestamps[proof_id] = time.time() - 2  # 设置为2秒前
    removed = zkp_manager.cleanup_expired_proofs(max_age=1)  # 1秒过期
    print(f'   过期清理结果: {removed} 个证明被清理')
    
    # 测试改进的Schnorr协议
    generator = ZKPGenerator()
    proof = generator.generate_proof('test_statement', 'test_witness')
    is_valid = generator.verify_proof(proof)
    print(f'   改进的Schnorr协议验证: {is_valid}')
    return is_valid


def test_blockchain():
    """测试区块链功能"""
    print('2. 测试区块链功能...')
    blockchain = Blockchain(consensus_type='pbft')
    
    # 测试pbft共识
    from src.blockchain.block import Block
    test_block = Block(
        index=1,
        previous_hash='0' * 64,
        timestamp=time.time(),
        data='test_data',
        proposer='test_proposer'
    )
    hash_result = blockchain.pbft_consensus(test_block)
    print(f'   PBFT共识执行: {hash_result is not None}')
    
    # 测试VDF共识
    blockchain_vdf = Blockchain(consensus_type='vdf_pow')
    challenge = 'integration_test_challenge'
    vdf_result = blockchain_vdf.compute_vdf(challenge)
    vdf_valid = blockchain_vdf.verify_vdf(challenge, vdf_result)
    print(f'   VDF 计算与验证: {vdf_valid}')
    return vdf_valid


def test_crypto():
    """测试加密功能"""
    print('3. 测试加密管理器...')
    crypto = CryptoManager()
    test_data = 'Hello, secure world!'
    encrypted = crypto.hybrid_encrypt(crypto.get_pub_key_pem(), test_data)
    decrypted = crypto.hybrid_decrypt(encrypted)
    success = test_data == decrypted
    print(f'   加密解密成功: {success}')
    return success


def test_key_exchange():
    """测试密钥交换"""
    print('4. 测试密钥交换...')
    kem = KeyExchangeManager()
    private_key, public_key = kem.generate_ephemeral_key_pair()
    peer_public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    shared_key, encrypted_key, salt = kem.derive_shared_secret(private_key, peer_public_key_pem)
    decrypted_shared_key = kem.decrypt_shared_secret(private_key, encrypted_key, salt)
    success = shared_key == decrypted_shared_key
    print(f'   密钥交换成功: {success}')
    return success


def main():
    print('=== 最终测试开始 ===')
    
    results = []
    results.append(test_zkp())
    results.append(test_blockchain())
    results.append(test_crypto())
    results.append(test_key_exchange())
    
    print('=== 最终测试完成 ===')
    print(f'测试结果: {sum(results)}/{len(results)} 项通过')
    
    if all(results):
        print('所有最终测试通过！')
        return True
    else:
        print('部分测试失败！')
        return False


if __name__ == '__main__':
    main()