# UV Project Management

## Overview

UV is a high-performance Python package and project manager that provides an all-in-one solution for dependency management, virtual environments, and project lifecycle management. This MCP RDF Memory project leverages UV for its speed, reliability, and modern Python tooling approach.

## Why UV for This Project

- **Performance**: UV is written in Rust and significantly faster than pip/poetry
- **Unified Tool**: Combines package management, virtual environments, and project scaffolding
- **Lock Files**: Provides deterministic, cross-platform dependency resolution via `uv.lock`
- **Python Version Management**: Handles Python installation and version switching
- **MCP Integration**: Works seamlessly with FastMCP development workflows

## Project Structure

```
mcp-rdf-memory/
├── pyproject.toml      # Project metadata and dependencies
├── uv.lock            # Locked dependency versions
├── .python-version    # Python version specification
├── src/               # Source code
│   └── mcp_rdf_memory/
├── tests/             # Test suite
└── docs/              # Documentation
```

## Key Files

### `pyproject.toml`
Central configuration file containing:
- Project metadata (name, version, description)
- Dependencies and optional dependencies
- Build system configuration
- Tool-specific settings (pytest, ruff, etc.)

### `uv.lock`
- Cross-platform lockfile with exact dependency versions
- Ensures reproducible environments across development and deployment
- Should be committed to version control
- Automatically updated when dependencies change

### `.python-version`
- Specifies the Python version for this project
- UV automatically uses this version when creating virtual environments

## Dependency Management

### Adding Dependencies
```bash
# Add runtime dependency
uv add oxigraph

# Add development dependency
uv add pytest --dev

# Add optional dependency group
uv add --optional docs sphinx
```

### Managing Dependencies
```bash
# Remove dependency
uv remove package-name

# Upgrade specific package
uv lock --upgrade-package oxigraph

# Upgrade all packages
uv lock --upgrade

# Sync environment with lockfile
uv sync
```

### Dependency Groups
The project uses dependency groups for different purposes:
- **Runtime**: Core dependencies (oxigraph, fastmcp, pydantic)
- **Development**: Testing and development tools (pytest, ruff)
- **Documentation**: Docs generation tools (optional)

## Development Workflow

### Environment Management
```bash
# UV automatically manages virtual environments
# No need to manually create/activate venvs

# Run commands in project environment
uv run python -m mcp_rdf_memory
uv run pytest
uv run fastmcp dev src/mcp_rdf_memory/server.py:mcp
```

### Common Development Tasks
```bash
# Install project and dependencies
uv sync

# Run the MCP server
uv run python -m mcp_rdf_memory

# Run tests
uv run pytest

# Run with FastMCP dev server
uv run fastmcp dev src/mcp_rdf_memory/server.py:mcp

# Install for Claude Desktop
uv run fastmcp install src/mcp_rdf_memory/server.py:mcp --name "RDF Memory"
```

## Advanced Features

### Python Version Management
```bash
# Install specific Python version
uv python install 3.11

# Use specific Python version for project
uv python pin 3.11
```

### Build and Distribution
```bash
# Build source and wheel distributions
uv build

# Build outputs to dist/ directory
# Ready for publishing to PyPI
```

### Environment Inspection
```bash
# Show project info
uv show

# List dependencies
uv tree

# Show outdated packages
uv show --outdated
```

## Best Practices for This Project

### 1. Lockfile Management
- Always commit `uv.lock` to version control
- Run `uv sync` after pulling changes
- Use `uv lock --upgrade` periodically to update dependencies

### 2. Dependency Hygiene
- Keep runtime dependencies minimal
- Use development groups for tooling
- Pin versions for critical dependencies in pyproject.toml

### 3. Environment Consistency
- Use `uv run` for all project commands
- Avoid manual virtual environment activation
- Let UV handle Python version management

### 4. CI/CD Integration
- Use `uv sync --frozen` in CI to ensure exact lockfile compliance
- Cache `.venv` directory for faster builds
- Run `uv lock --check` to verify lockfile is up-to-date

### 5. MCP-Specific Workflow
- Use `fastmcp dev` for development with hot reloading
- Test installations with `fastmcp install` before deployment
- Leverage UV's speed for rapid iteration cycles

## Troubleshooting

### Common Issues
1. **Lockfile conflicts**: Run `uv lock` to regenerate
2. **Environment inconsistency**: Use `uv sync --force` to rebuild
3. **Python version issues**: Check `.python-version` and use `uv python install`

### Performance Tips
- UV caches downloads globally - first install may be slow, subsequent ones are fast
- Use `uv add --no-sync` when adding multiple dependencies to avoid repeated syncs
- Leverage UV's parallel installation for large dependency trees

## Migration Notes

If migrating from other tools:
- **From pip**: `requirements.txt` → `pyproject.toml` dependencies
- **From poetry**: Most `pyproject.toml` sections are compatible
- **From pipenv**: `Pipfile` → `pyproject.toml` with dependency groups

UV provides a modern, fast, and reliable foundation for Python project management, perfectly suited for the iterative development cycles common in MCP server development.