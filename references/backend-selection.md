# Backend Selection

## Intent

Choose the most faithful extractor available for the source document.

## Preferred Routing

1. `pptx`:
   - Use native PPTX XML parsing.
   - Do not rasterize unless the file is damaged.

2. `pdf`:
   - If optional PDF geometry libraries are available, extract positioned text blocks.
   - Classify each page as `ppt-like`, `doc-like`, `sheet-like`, or `mixed`.
   - Use `markitdown` as baseline text, not as the only structural source.

3. `docx`:
   - Keep as future extension.
   - Fall back to baseline markdown when no native extractor is available.

4. `xlsx`:
   - Keep as future extension.
   - Prefer CSV-like table reconstruction over plain paragraphs.

## Optional Dependencies

- `PyMuPDF` / `fitz`: high-value for PDF block extraction
- `python-pptx`: optional helper library, but not required by the current implementation
- `markitdown`: baseline conversion tool

The current skill is deliberately written to work without `python-pptx` by parsing Office XML directly.
