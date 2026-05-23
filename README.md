# 🚀 Rebase Overlord

**The Git Feature Flow Assistant** — A powerful CLI tool that simplifies Git feature branch workflows, interactive rebasing, and conflict resolution for developers.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Problem It Solves](#problem-it-solves)
- [Features](#features)
- [Installation](#installation)
  - [Option 1: Download Pre-built Executable (Recommended)](#option-1-download-pre-built-executable-recommended)
  - [Option 2: Build from Source](#option-2-build-from-source)
  - [Option 3: Run with Python](#option-3-run-with-python)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Development](#development)
- [Release Notes](#release-notes)
- [License](#license)

---

## Overview

**Rebase Overlord** is an interactive terminal UI tool that guides developers through Git feature branch workflows with special focus on:

- **Interactive Rebase Management** — Intelligent rebase conflict detection and recovery
- **Feature Branch Operations** — Checkout, create, and sync feature branches with main
- **Commit Optimization** — Squash, reorder, and clean up commit history
- **GitHub Integration** — Direct interaction with GitHub via CLI (optional)
- **Multi-language Support** — Full Vietnamese and English support with customizable emoji modes

The tool provides a **menu-driven interface** that handles complex Git operations that would normally require multiple manual CLI commands.

---

## Problem It Solves

### The Pain Points

Developers working with Git feature branch workflows frequently encounter:

1. **Manual Rebase Complexity** — Interactive rebase (`git rebase -i`) is powerful but requires memorizing commands and manual conflict resolution workflows

2. **Conflict Recovery** — When rebase pauses due to conflicts, recovering the correct state requires understanding Git's internal rebase state machinery

3. **Repetitive Operations** — Checking out feature branches, pulling latest main, rebasing, and pushing is a multi-step process prone to mistakes

4. **History Cleanup** — Squashing commits, reordering, and editing commit messages requires careful manual coordination

### How Rebase Overlord Helps

- **Automated Workflows** — Reduces 5+ Git commands to a single menu selection
- **Intelligent Conflict Handling** — Automatically detects rebase state and provides recovery guidance
- **No Manual Rebasing** — Interactive rebase is orchestrated automatically with conflict pause/resume
- **GitHub-aware** — Optional GitHub CLI integration for pull request operations
- **Cross-platform** — Works on Windows, macOS, and Linux

---

## Features

✅ **Feature Branch Management**
- Create new feature branches from main
- Checkout existing feature branches  
- Delete feature branches locally and on remote
- Sync feature branches with latest main (fetch + rebase)

✅ **Interactive Rebase & History Squashing**
- Automated interactive rebase with conflict detection
- Pause/resume rebase on conflicts
- Commit message editing
- Automatic stash/unstash for uncommitted changes

✅ **Conflict Resolution**
- Real-time conflict detection
- Staged file status tracking
- Rebase recovery with state preservation
- Clear recovery prompts

✅ **GitHub Integration** (optional, requires `gh` CLI)
- List pull requests
- Create pull requests from feature branch
- Create releases
- View repository status

✅ **Configuration**
- No config file needed (works out of the box)
- Language selection (Vietnamese/English)
- Emoji mode toggle
- Command logging for debugging

✅ **Statistics & History**
- Rebase operation tracking
- Command history buffer
- Session statistics

---

## Installation

### Option 1: Download Pre-built Executable (Recommended)

**The easiest way** — no Python installation needed.

1. Go to [Releases](../../releases)
2. Download the latest `rebase-overlord-X.Y.Z.exe` for your version
3. Run the `.exe` file directly:
   ```bash
   rebase-overlord-0.3.5.exe
   ```

**Supported on:** Windows 10/11 (x64)

---

### Option 2: Build from Source

**Requirements:**
- Python 3.11+
- Git (installed and in PATH)
- PyInstaller (for building)

**Steps:**

```bash
# Clone the repository
git clone https://github.com/yourusername/the-git-saver.git
cd the-git-saver

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable (Windows)
pyinstaller --onefile --clean --noconfirm \
  --add-data "config;config" \
  --name rebase-overlord \
  git_feature_flow.py

# The executable will be in dist/rebase-overlord.exe
```

---

### Option 3: Run with Python

**Requirements:**
- Python 3.11+
- Git (installed and in PATH)

**Steps:**

```bash
# Clone the repository
git clone https://github.com/yourusername/the-git-saver.git
cd the-git-saver

# Install dependencies
pip install -r requirements.txt

# Run directly with Python
python git_feature_flow.py
```

---

## Quick Start

### First Run

```bash
# Launch the tool
rebase-overlord

# Or if running from source:
python git_feature_flow.py
```

### Initial Setup

1. **Select Language** — Choose between Vietnamese (vn_pro) or English
2. **Select Repository** — Point to your Git repository (or use current directory)
3. **Main Menu** — Browse available operations

### Common Workflows

**Create and work on a feature branch:**
```
1. Main Menu → Create Feature Branch
2. Enter branch name: feature/new-feature
3. Make changes and commit
4. Main Menu → Rebase Feature on Main
5. Main Menu → Push Feature Branch
```

**Squash commits before merging:**
```
1. Main Menu → Squash Commits
2. Select commits to squash
3. Edit combined commit message
4. Main Menu → Push Feature Branch
```

**Recover from failed rebase:**
```
1. Tool detects rebase in progress
2. Main Menu → Rebase Recovery
3. Resolve conflicts (follow prompts)
4. Tool automatically resumes rebase
```

---

## Requirements

### Runtime Requirements

**Minimum:**
- Windows 10, macOS 10.14+, or Linux (x64)
- Git 2.20+ installed and in PATH

**Optional:**
- GitHub CLI (`gh`) for GitHub integration
  ```bash
  # Install gh (if needed)
  # Windows: https://github.com/cli/cli/releases
  # macOS: brew install gh
  # Linux: https://cli.github.com/
  
  # Then authenticate
  gh auth login
  ```

### Development Requirements

- Python 3.11+
- pip
- PyInstaller (for building executables)

---

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/the-git-saver.git
cd the-git-saver

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pyinstaller flake8 pytest
```

### Project Structure

```
the-git-saver/
├── git_feature_flow.py      # Main application (single file)
├── config/
│   ├── emoji_map.json       # Emoji configuration
│   └── languages.json       # i18n translations (VN + EN)
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Build & release config
├── README.md               # This file
└── .github/workflows/
    ├── release.yml         # Automated release pipeline
    └── pr-check.yml        # PR validation
```

### Running Tests

```bash
# Run linting
flake8 . --select=E9,F63,F7,F82

# Run unit tests
pytest tests/
```

### Building Executable Locally

```bash
# Windows
build_local.bat

# Or manually:
pyinstaller --onefile --clean --noconfirm \
  --add-data "config;config" \
  --name rebase-overlord \
  git_feature_flow.py
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes following PEP 8 style
4. Commit with conventional format: `feat:` or `fix:`
5. Push and open a Pull Request

---

## Release Notes

### Latest Version: [0.3.5](../../releases/tag/ver0.3.5)

See [CHANGELOG.md](CHANGELOG.md) for full release history and upgrade notes.

### Version History

| Version | Release Date | Notes |
|---------|-------------|-------|
| 0.3.5   | 2026-05-23 | Bug fixes, improved conflict recovery |
| 0.3.4   | 2026-05-23 | Release pipeline optimization |
| 0.3.0+  | 2026-05  | Initial feature-complete releases |

---

## Troubleshooting

### "Git not found"
Ensure Git is installed and accessible from PATH:
```bash
git --version
```

### "GitHub CLI not available"
The tool works without GitHub CLI, but some features will be disabled. To enable GitHub integration:
```bash
gh auth login
```

### Rebase conflicts
The tool will pause and prompt you to resolve conflicts. Edit conflicting files in your editor, stage them, then select "Resume Rebase" from the menu.

### Command history buffer
Use the history feature to review all Git commands executed in the current session for debugging.

---

## License

MIT License — See [LICENSE](LICENSE) file for details.

---

## Support

- 📖 **Documentation** — See inline help in the tool menu
- 🐛 **Bug Reports** — [Issues](../../issues)
- 💬 **Questions** — Open a [Discussion](../../discussions)

---

## Author

**Rebase Overlord** — Making Git feature workflows less painful since 2026.

Built with ❤️ for developers who work with Git daily.
