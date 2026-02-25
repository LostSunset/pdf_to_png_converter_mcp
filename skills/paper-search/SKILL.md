---
name: search-paper
description: Search for academic papers using Semantic Scholar. Use when the user wants to find papers by keyword, look up a specific paper, or find open-access PDFs for academic topics.
---

# Academic Paper Search

Use the `search_paper` MCP tool to search Semantic Scholar:
- `query` (required): Search keywords
- `max_results` (optional): Number of results, default 5, max 20

Results include title, authors, year, venue, and PDF URL (if open access).

After searching, offer to download papers that have available PDF URLs
using the `download_paper` or `download_and_convert` tools.
