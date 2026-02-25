---
name: download-paper
description: Download academic papers from the web and optionally convert them to PNG. Use when the user wants to download a paper PDF, organize it by journal and title, or download and convert in one step.
---

# Paper Download and Organization

Use the MCP tools provided by the pdf-to-png server to download papers.

## Download Only
Use the `download_paper` tool with:
- `url` (required): Direct URL to the PDF
- `journal` (required): Journal name for folder organization
- `title` (required): Paper title for naming
- `base_dir` (optional): Base directory, defaults to current

## Download and Convert
Use the `download_and_convert` tool with:
- `url` (required): Direct URL to the PDF
- `journal` (required): Journal name
- `title` (required): Paper title
- `base_dir` (optional): Base directory
- `dpi` (optional): Resolution for PNG conversion, default 1200

Papers are organized as: `base_dir/journal/title/title.pdf`
