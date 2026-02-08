# GitHub Copilot Instructions for Vanda Team Project

## Environment Setup
1. **Always activate the virtual environment** before working on tasks:
   ```bash
   source .venv/bin/activate
   ```

## Task Completion Checklist
Before finishing any task:
1. **Run the build script** to verify code quality and type checking:
   ```bash
   ./build.sh
   ```
2. **Fix any issues** reported by the build script (black formatting, mypy type checking, etc.)
3. Ensure all checks pass with no errors before considering the task complete

## Build Script Details
The `build.sh` script performs:
- **Black**: Code formatting validation
- **MyPy**: Type checking validation
- Reports any findings and must pass with "Success: no issues found"
