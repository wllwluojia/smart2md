from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_config(config_path: Path | None) -> dict[str, Any]:
    if config_path is None:
        config_path = (
            Path(__file__).resolve().parent.parent.parent / "config" / "defaults.toml"
        )
    with config_path.open("rb") as handle:
        return tomllib.load(handle)


def adapter_settings(config: dict[str, Any], name: str) -> dict[str, Any]:
    return config.get("adapters", {}).get(name, {})


def route_chain(config: dict[str, Any], file_type: str) -> list[str]:
    routing = config.get("routing", {})
    chain = routing.get(file_type) or routing.get("default") or []
    return list(chain)

