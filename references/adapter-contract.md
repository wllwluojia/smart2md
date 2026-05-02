# Adapter Contract

Each backend adapter should live under `scripts/any2md/adapters/`.

## Discovery

The router auto-discovers adapter modules in that directory. Each module must expose:

```python
ADAPTERS = [MyAdapter]
```

## Required Methods

Each adapter class must provide:

- `name`
- `check(context) -> AdapterStatus`
- `supports(file_type) -> bool`
- `extract(context) -> AdapterResult`

## Design Rules

- `check()` must be cheap and side-effect free.
- `extract()` may shell out or call external APIs.
- Always return one normalized `document` object.
- Preserve raw backend outputs in `raw_outputs` when useful.
- Do not make Hermes depend on vendor-specific schemas.

## Upgrade Path

When a stronger backend appears:

1. Add a new adapter module.
2. Export it via `ADAPTERS = [...]`.
3. Put it into the routing order in `config/defaults.toml`.
4. Run `doctor` and a sample `extract`.
