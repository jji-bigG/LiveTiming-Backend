#!/bin/bash

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
export PATH="/home/$USER/.local/bin:$PATH"

# Initialize new Poetry project
poetry new livetiming-backend
cd livetiming-backend

# Install dependencies
poetry add fastapi uvicorn redis pika python-dotenv pydantic pydantic-settings
poetry add --group dev pytest httpx black isort flake8 mypy

# Initialize git repository
git init

# Create project structure
mkdir -p src/{api/{routes,models},services} tests docs

# Copy project files
# (You'll need to copy all the source files we created earlier)

# Setup pre-commit hooks
cat > .pre-commit-config.yaml << EOL
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
    -   id: isort

-   repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
    -   id: flake8
EOL

# Install pre-commit hooks
poetry add --group dev pre-commit
poetry run pre-commit install

echo "Setup complete! You can now run:"
echo "poetry shell    # Activate virtual environment"
echo "poetry install  # Install dependencies"
echo "poetry run pytest  # Run tests"