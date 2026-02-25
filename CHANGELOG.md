# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-25

### Added

- Claude Code Plugin support with marketplace integration
- New `search_paper` MCP tool for searching Semantic Scholar API
- Plugin manifest (`.claude-plugin/plugin.json`)
- Marketplace catalog (`.claude-plugin/marketplace.json`)
- MCP server configuration (`.mcp.json`) with `${CLAUDE_PLUGIN_ROOT}` support
- Skills: `convert-pdf`, `download-paper`, `search-paper`
- Comprehensive test suite achieving 80%+ code coverage
- Plugin install support: `/plugin marketplace add LostSunset/pdf_to_png_converter_mcp`

### Changed

- Updated tool count from 4 to 5 (added `search_paper`)
- Enhanced test fixtures with mock support for httpx, pdf2image, subprocess

## [0.1.3] - 2026-02-02

### Added

- Added PyPI publish workflow for easy installation via `uvx` or `pipx`
- Added project URLs in pyproject.toml
- Updated README with quick installation instructions

## [0.1.2] - 2026-02-02

### Fixed

- Fixed mypy type errors for cross-platform compatibility
- Fixed `subprocess.CREATE_NO_WINDOW` not available on non-Windows platforms
- Fixed lambda type inference issues in converter module
- Added proper type annotations throughout the codebase

## [0.1.1] - 2026-02-02

### Fixed

- CI workflow: use `uv venv` instead of `--system` flag for Ubuntu runners

## [0.1.0] - 2026-02-02

### Added

- Initial release
- MCP server for PDF to PNG conversion
- Support for downloading academic papers from the web
- Automatic folder organization by journal and paper title
- `convert_pdf_to_png` tool for single file conversion
- `download_paper` tool for downloading papers
- `download_and_convert` tool for combined download and conversion
- `batch_convert_pdfs` tool for batch processing
- GUI interface using PySide6
- Support for DPI settings (72-2400, default 1200)
- UTF-8 support for Chinese characters
- GitHub Actions CI/CD pipeline
- Comprehensive documentation
