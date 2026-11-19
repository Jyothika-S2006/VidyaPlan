"""API routes for reading and updating costs/weights config."""
import logging
import os
import yaml

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")


def _load_yaml(filename: str) -> dict:
    path = os.path.join(CONFIG_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _save_yaml(filename: str, data: dict) -> None:
    path = os.path.join(CONFIG_DIR, filename)
    with open(path, "w") as f:
        yaml.dump(data, f)


@router.get("/config")
async def get_config():
    """Return current costs and weights configuration."""
    return {
        "costs": _load_yaml("costs.yaml"),
        "weights": _load_yaml("weights.yaml"),
        "provenance": "SIMULATED",
    }


class ConfigUpdate(BaseModel):
    costs: Optional[dict] = None
    weights: Optional[dict] = None


@router.put("/config")
async def update_config(update: ConfigUpdate):
    """Update costs and/or weights. All values are SIMULATED."""
    if update.costs:
        _save_yaml("costs.yaml", update.costs)
    if update.weights:
        _save_yaml("weights.yaml", update.weights)
    return {"status": "ok", "provenance": "SIMULATED"}
