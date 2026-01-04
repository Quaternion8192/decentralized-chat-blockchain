# Usage Guide

## Getting Started

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the System

### Starting a Node
```bash
# Start a basic node
python main.py --host 0.0.0.0 --port 8080

# Start a node with specific configuration
python main.py --host 127.0.0.1 --port 8081

# Connect to bootstrap nodes
python main.py --host 0.0.0.0 --port 8082 --bootstrap 127.0.0.1:8080:node_id
```

### Command Line Options
- `--host`: Host address to bind to (default: 0.0.0.0)
- `--port`: Port to listen on (default: 8080)
- `--bootstrap`: Bootstrap nodes in format `ip:port:node_id`

## Security Features

### Encryption
All messages are encrypted using the X3DH + Double Ratchet protocol:
- Initial key exchange uses X3DH for secure key establishment
- Each message uses a unique key derived from the Double Ratchet algorithm
- Forward secrecy: past communications remain secure even if current keys are compromised
- Backward secrecy: future communications remain secure even if current keys are compromised

### Traffic Obfuscation
The system uses multiple techniques to avoid detection:
- WebSocket-style packet formatting
- HTTP-style requests with padding
- Random padding for maximum obfuscation

## Network Architecture

### Node Discovery
The system uses Kademlia DHT for decentralized node discovery:
- No central authority or single point of failure
- Nodes can join and leave the network dynamically
- Efficient O(log n) lookup time for peer discovery

### Message Routing
- Direct P2P connections when possible
- End-to-end encryption ensures message privacy
- Secure channel establishment using X3DH
- Message integrity verification

## Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_secure_architecture.py
```

### Code Structure
```
src/
├── crypto/              # Cryptography implementation
│   ├── advanced_crypto_manager.py  # X3DH + Double Ratchet
│   ├── double_ratchet.py          # Double Ratchet algorithm
│   └── simple_secure_channel.py   # Simplified crypto for testing
├── network/             # Network protocols
│   ├── tls_protocol.py   # TLS 1.3 and obfuscation
│   ├── kademlia_dht.py   # DHT implementation
│   └── protocol.py       # Base protocol (legacy)
├── p2p/                 # P2P node implementation
│   └── secure_node_server.py  # Secure node server
└── core/                # Core application logic
```

## Troubleshooting

### Common Issues
1. **Connection Issues**: Ensure ports are not blocked by firewall
2. **Encryption Failures**: Verify that both nodes support the same cryptographic protocols
3. **Node Discovery**: Check network connectivity and DHT configuration

### Performance Tuning
- Adjust async task limits for high-concurrency scenarios
- Optimize network buffer sizes for your environment
- Monitor memory usage for long-running nodes