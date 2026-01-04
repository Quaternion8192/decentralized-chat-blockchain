# Industrial-Grade Secure Decentralized Chat [工业级安全去中心化聊天系统]

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg)](https://github.com/Quaternion8192/decentralized-chat-blockchain)
[![Security](https://img.shields.io/badge/Security-Industrial--Grade-critical.svg)](https://github.com/Quaternion8192/decentralized-chat-blockchain)

</div>

<div align="center">

### 🛡️ An industrial-grade decentralized chat solution with zero-trust architecture and censorship resistance

</div>

---

## English Version

An industrial-grade secure decentralized chat solution featuring zero-trust architecture, end-to-end encryption, and censorship resistance.

### ✨ Features

- **Zero-Trust Architecture**: All communications are encrypted and verified
- **Industrial-Grade Security**: X3DH key exchange + Double Ratchet algorithm for forward/backward secrecy
- **Censorship Resistance**: TLS 1.3 with traffic obfuscation to bypass DPI detection
- **Decentralized Network**: Kademlia DHT for node discovery without single point of failure
- **End-to-End Encryption**: PyNaCl (LibSodium) with X3DH and Double Ratchet for message security
- **Forward Secrecy**: Even if current keys are compromised, historical messages remain secure
- **Backward Secrecy**: Regular key updates limit exposure from key leaks
- **P2P Network**: Decentralized node communication
- **Traffic Obfuscation**: Multiple techniques (WebSocket, HTTP-style, random padding) to hide traffic patterns
- **High Performance**: Async I/O with high concurrency support

### 📦 Installation

```bash
pip install -r requirements.txt
```

### 🚀 Usage

#### Start a Secure Node

```bash
python main.py --host 0.0.0.0 --port 8080
```

#### Connect to Bootstrap Nodes

```bash
python main.py --host 0.0.0.0 --port 8081 --bootstrap 127.0.0.1:8080:node_id
```

### 🏗️ Architecture

#### Security Layer
- **X3DH Key Exchange Protocol**: Extended Triple Diffie-Hellman for secure key establishment
- **Double Ratchet Algorithm**: Ensures forward and backward secrecy
- **PyNaCl (LibSodium)**: State-of-the-art cryptographic library
- **TLS 1.3**: Transport Layer Security with mutual authentication

#### Network Layer
- **Kademlia DHT**: Decentralized node discovery and routing
- **Traffic Obfuscation**: Multiple techniques to bypass censorship
- **Async I/O**: High-performance concurrent communication
- **Node Reputation System**: Quality-based peer selection

#### Encryption Layer
- **X3DH**: Secure key exchange protocol similar to Signal
- **Double Ratchet**: Message key evolution for perfect forward secrecy
- **AES-256-GCM**: Message encryption with authentication
- **Curve25519**: Elliptic curve cryptography for key exchange

### 🔐 Security Features

#### Zero-Trust Architecture
- All communications are encrypted end-to-end
- No trust assumptions about network infrastructure
- Mutual authentication between peers

#### Censorship Resistance
- Traffic obfuscation to avoid DPI detection
- Multiple protocol camouflage techniques
- Resilient to network analysis and blocking

#### Forward Secrecy
- Keys are regularly updated using Double Ratchet
- Past communications remain secure even if current keys are compromised
- Perfect forward secrecy ensures historical message protection

#### Backward Secrecy  
- Key updates limit the impact of key compromises
- Future messages remain secure even if current keys are compromised
- Continuous security evolution

### 📁 Project Structure

```
.
├── main.py                 # Main entry point
├── pyproject.toml          # Build configuration
├── requirements.txt        # Dependencies
├── README.md              # Project documentation
├── LICENSE               # MIT License
├── CODE_OF_CONDUCT.md    # Community guidelines
├── CONTRIBUTING.md       # Contribution guide
├── SECURITY.md           # Security policy
├── webui.py             # Web UI console
├── scripts/             # Utility scripts
├── docs/                # Documentation
├── src/                 # Source code
│   ├── __init__.py
│   ├── blockchain/      # Blockchain implementation
│   ├── config/          # Configuration management
│   ├── core/            # Core application logic
│   ├── crypto/          # Cryptography utilities (X3DH, Double Ratchet)
│   │   ├── __init__.py
│   │   ├── advanced_crypto_manager.py  # Industrial-grade crypto
│   │   ├── double_ratchet.py          # Double Ratchet algorithm
│   │   └── simple_secure_channel.py   # Simplified crypto for testing
│   ├── gossip/          # Gossip protocol
│   ├── incentive/       # Incentive mechanisms
│   ├── ipfs/            # IPFS integration
│   ├── multimedia/      # Multimedia processing
│   ├── network/         # Network protocols (TLS, obfuscation)
│   │   ├── __init__.py
│   │   ├── kademlia_dht.py     # Kademlia DHT implementation
│   │   ├── tls_protocol.py     # TLS 1.3 and obfuscation
│   │   └── protocol.py         # Legacy protocol (deprecated)
│   ├── p2p/             # P2P protocols and secure node server
│   │   ├── __init__.py
│   │   └── secure_node_server.py  # Secure node implementation
│   ├── routing/         # Routing management
│   ├── utils/           # Utility functions
│   ├── vdf/             # Verifiable delay functions
│   └── zkp/             # Zero-knowledge proofs
└── tests/               # Test suite
    ├── __init__.py
    └── test_secure_architecture.py  # Integration tests
```

### 🛡️ Security Architecture

#### X3DH Key Exchange
```
Initiator (Alice)                    Responder (Bob)
     |                                        |
     |-------- [E, signed(E, IK)] ------------>|
     |                                        | Compute shared secrets:
     |<------- [E', signed(E', IK')] ---------|   SK = DH(IK, SPK') || DH(E, IK') || DH(E, OPK')
     |                                        |   SK = DH(SP, IK') || DH(IK, E') || DH(OPK, E')
     |-------- [DH computation] -------------->|
     |                                        |
```

#### Double Ratchet Algorithm
- **Root Chain**: Derived from shared secret and DH ratchet
- **Sending Chain**: Evolves for each outgoing message
- **Receiving Chain**: Evolves for each incoming message
- **Symmetric Design**: Both parties maintain synchronized chains

### 🚀 Performance

- **High Concurrency**: Async I/O supports thousands of concurrent connections
- **Low Latency**: Optimized cryptographic operations
- **Scalable Architecture**: DHT-based node discovery scales to millions of nodes
- **Memory Efficient**: Ratchet chains maintain minimal state

### 🌐 Anti-Censorship

#### Traffic Obfuscation Techniques
1. **WebSocket Style**: Packets mimic WebSocket frames
2. **HTTP Padding**: Traffic looks like HTTP requests with padding
3. **Random Padding**: Random-length random data padding

#### Protocol Mimicry
- Traffic appears as normal HTTPS browsing
- Resists deep packet inspection (DPI)
- Bypasses firewall and censorship systems

### 📄 License

MIT License - See LICENSE file for details.
