# Contributing to Decentralized Chat with Blockchain

Thank you for your interest in contributing to the Decentralized Chat with Blockchain project! We welcome contributions from everyone, regardless of experience level.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/Quaternion8192/decentralized-chat-blockchain.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Create a new branch for your feature or bug fix: `git checkout -b feature/your-feature-name`

## Development Workflow

1. Make your changes
2. Add tests if applicable
3. Run tests to ensure everything works: `pytest tests/`
4. Update documentation if needed
5. Commit your changes with a descriptive commit message
6. Push your changes to your fork
7. Create a pull request

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Update the README.md if needed with details of changes to the interface
3. Add tests for any new functionality
4. Ensure all tests pass
5. Describe your changes in detail in the pull request description
6. Link any relevant issues in the pull request description

## Style Guidelines

### Python Code Style
- Follow PEP 8 style guide
- Use descriptive variable and function names
- Write docstrings for all functions and classes
- Keep functions and methods focused on a single responsibility

### Commit Messages
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

## Project Architecture

The project follows a modular architecture:

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

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_specific_file.py
```

## Questions?

If you have any questions, feel free to open an issue or contact the maintainers.

Thank you for contributing!