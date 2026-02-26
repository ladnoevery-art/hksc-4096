# Contributing to HKSC-4096

Thank you for your interest in contributing to HKSC-4096! This document provides guidelines for contributing.

## 🎯 Ways to Contribute

- **Bug Reports**: Report issues you encounter
- **Feature Requests**: Suggest new features
- **Code Contributions**: Submit PRs for bug fixes or features
- **Documentation**: Improve docs and examples
- **Security Audits**: Help identify vulnerabilities

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/hksc-4096.git`
3. Create a branch: `git checkout -b feature/amazing-feature`
4. Make your changes
5. Test thoroughly
6. Commit: `git commit -m "Add amazing feature"`
7. Push: `git push origin feature/amazing-feature`
8. Create a Pull Request

## 📋 Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/hksc-4096.git
cd hksc-4096

# Install Python dependencies
cd hksc-python
pip install -r requirements.txt

# Install Node dependencies
cd ../hksc-electron
npm install

# Install contract dependencies
cd ../hksc-verifier-contract
npm install
```

## 🧪 Testing

### Python Tests

```bash
cd hksc-python
python -m pytest
```

### Contract Tests

```bash
cd hksc-verifier-contract
npx hardhat test
```

### ZK Circuit Tests

```bash
cd zk-circuit
bash setup.sh
snarkjs groth16 verify keys/verification_key.json build/public.json build/proof.json
```

## 📝 Code Style

### Python

- Follow PEP 8
- Use type hints
- Add docstrings for functions
- Maximum line length: 120 characters

```python
def example_function(param: str) -> bool:
    """
    Brief description.
    
    Args:
        param: Description of param
        
    Returns:
        Description of return value
    """
    return True
```

### JavaScript/Solidity

- Use ESLint/Prettier
- Follow existing code patterns
- Add JSDoc comments

```javascript
/**
 * Brief description
 * @param {string} param - Description
 * @returns {boolean} Description
 */
function exampleFunction(param) {
    return true;
}
```

## 🔒 Security

- Never commit private keys or secrets
- Report security issues privately
- Follow secure coding practices
- All PRs must pass security checks

## 📊 Pull Request Process

1. **Before Submitting**:
   - All tests pass
   - Code follows style guidelines
   - Documentation is updated
   - Commit messages are clear

2. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation
   - [ ] Breaking change
   
   ## Testing
   Describe testing performed
   
   ## Checklist
   - [ ] Tests pass
   - [ ] Code follows style
   - [ ] Documentation updated
   ```

3. **Review Process**:
   - At least one approval required
   - All CI checks must pass
   - Security audit for contract changes

## 🏷️ Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

Examples:
```
feat(crypto): add VDF time-lock
fix(contract): resolve reentrancy issue
docs(readme): update installation guide
```

## 🐛 Reporting Bugs

Use GitHub Issues with template:

```markdown
**Description**
Clear bug description

**Steps to Reproduce**
1. Step 1
2. Step 2

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: 
- Python version:
- Node version:
```

## 💡 Feature Requests

Use GitHub Discussions for feature requests:

```markdown
**Feature Description**
Clear description

**Use Case**
Why is this needed?

**Proposed Solution**
How should it work?

**Alternatives**
Other approaches considered
```

## 📜 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## 📞 Contact

- General: security@hksc-4096.eth
- Security: security@hksc-4096.eth (PGP encrypted)

---

Thank you for contributing to HKSC-4096! 🔐
