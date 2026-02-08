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

## Coding Style Guidelines
- **Prioritize object-oriented design**: Use classes, inheritance, and polymorphism over procedural code
- Favor composition and abstraction to promote code reusability and maintainability
- Apply SOLID principles where appropriate
- Use inheritance chains to share common behavior across agent implementations
- Avoid code duplication by leveraging base classes and method overrides

## Additional Commands
- **Manual pre-commit check**: `pre-commit run --all-files`
- **Fresh setup**: `source ./install.sh` (activates venv and pre-commit at the end)
