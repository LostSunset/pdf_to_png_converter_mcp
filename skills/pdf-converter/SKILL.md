---
name: convert-pdf
description: Convert PDF files to high-quality PNG images. Use when the user wants to convert a PDF to PNG, extract pages as images, or batch convert multiple PDFs in a folder.
---

# PDF to PNG Conversion

Use the MCP tools provided by the pdf-to-png server to convert PDF files.

## Single File Conversion
Use the `convert_pdf_to_png` tool with:
- `pdf_path` (required): Full path to the PDF file
- `dpi` (optional): Resolution, default 1200. Range: 72-2400
- `output_dir` (optional): Output directory, defaults to same as PDF

## Batch Conversion
Use the `batch_convert_pdfs` tool with:
- `folder_path` (required): Path to folder containing PDFs
- `dpi` (optional): Resolution, default 1200
- `recursive` (optional): Search subdirectories, default true

Always confirm the PDF path exists before attempting conversion.
Report the number of PNG files generated and their location.
