# Contributing to VoxDub

Thank you for considering contributing to VoxDub! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)

### Suggesting Features

Feature requests are welcome! Please include:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
git checkout -b feature/AmazingFeature

text
3. **Make your changes**
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

4. **Test your changes**
Backend tests
cd backend
pytest

Frontend tests
cd frontend
npm test

text

5. **Commit your changes**
git commit -m "feat: Add amazing feature"

text

6. **Push to your fork**
git push origin feature/AmazingFeature

text

7. **Open a Pull Request**
- Clear title and description
- Reference any related issues

## Development Setup

### Backend
cd backend
python -m venv venv
venv\Scripts\activate # Windows
pip install -r requirements.txt
pip install pytest # For testing

text

### Frontend
cd frontend
npm install
npm run dev

text

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions small and focused

### JavaScript/React
- Use ES6+ syntax
- Follow React best practices
- Use functional components
- Add PropTypes or TypeScript

## Commit Convention

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## Questions?

Feel free to open an issue for any questions or discussions!

Thank you for your contribution! 🙏
