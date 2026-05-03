"""스모크 — 기본 모듈 import 가능한지만 빠르게 확인."""
from __future__ import annotations


def test_import_settings() -> None:
    from src.utils.settings import load_config

    cfg = load_config("default")
    assert cfg.project.name == "subwaybev"
    assert cfg.bev.resolution == 0.1


def test_import_api() -> None:
    from src.api.main import app  # noqa: F401


def test_bev_forward() -> None:
    import torch

    from src.models.bev_baseline import BEVBaseline

    model = BEVBaseline().eval()
    x = torch.randn(1, 4, 3, 128, 224)
    with torch.no_grad():
        out = model(x)
    assert out["occupancy"].shape[-2:] == (model.cfg.bev_h, model.cfg.bev_w)
    assert out["count"].shape == (1, 1)
