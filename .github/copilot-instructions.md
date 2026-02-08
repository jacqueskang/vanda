# GitHub Copilot Instructions

## Pre-Task Setup
1. **Activate virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Setup pre-commit hooks** (one-time):
   ```bash
   pre-commit install
   ```

## Task Completion Requirements
After completing any task, **ALWAYS**:
1. Run the build script:
   ```bash
   ./build.sh
   ```
2. Fix any errors from **black** (formatting) or **mypy** (type checking)
3. Verify the build passes with: `Success: no issues found`

## Additional Commands
- **Manual pre-commit check**: `pre-commit run --all-files`
- **Fresh setup**: `source ./install.sh` (activates venv and pre-commit at the end)
