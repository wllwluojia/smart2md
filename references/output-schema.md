# Output Schema

`*.structured.json` is the canonical downstream artifact.

## Top Level

```json
{
  "source_path": "/abs/path/to/file",
  "source_type": "pptx",
  "created_at": "2026-04-22T11:00:00+08:00",
  "baseline_markdown_path": "/abs/path/to/file.baseline.md",
  "pages": []
}
```

## Page Object

```json
{
  "page_number": 1,
  "title": "系统运行流程",
  "layout_type": "architecture",
  "width": 1280,
  "height": 720,
  "summary": "One-sentence normalized summary.",
  "blocks": [],
  "regions": [],
  "flows": [],
  "table": null,
  "signals": {
    "has_columns": true,
    "has_timeline_keywords": false,
    "has_architecture_keywords": true
  }
}
```

## Block Object

```json
{
  "id": "p1-b3",
  "kind": "text",
  "role": "title|subtitle|body|table-cell|image-placeholder",
  "text": "标签画像中心",
  "bbox": {
    "x": 0.24,
    "y": 0.39,
    "w": 0.11,
    "h": 0.05
  },
  "reading_rank": 8
}
```

## Region Object

```json
{
  "id": "p1-r2",
  "label": "column-2",
  "bbox": {
    "x": 0.32,
    "y": 0.19,
    "w": 0.21,
    "h": 0.54
  },
  "block_ids": ["p1-b8", "p1-b9"]
}
```

## Flow Edge

```json
{
  "from": "客户洞察",
  "to": "营销策略",
  "evidence": "left-to-right region sequence"
}
```

## Downstream Use

For wiki extraction:
- use `title`, `layout_type`, `summary`
- use `regions` to recover modular hierarchy
- use `flows` to recover process and dependency links
- use `table` if present for metrics, budgets, or milestones
- use `bbox` for traceability back to the original page
