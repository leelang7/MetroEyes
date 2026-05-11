"""BEVConfig 설정 + BEVBaseline 추가 회귀 가드 (cycle 508).

BEVConfig 기본값 검증 — 실제 지하철 칸 크기 (19.5m × 2.8m / 0.1m 해상도):
  bev_h=195, bev_w=28, num_cams=4, backbone='resnet18'

추가 forward 케이스 (batch/camera 변형):
  - 단일 카메라 (N=1)
  - 큰 배치 (B=4)
  - 출력 bev_h/bev_w 커스텀
"""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")


def test_bev_config_defaults() -> None:
    """BEVConfig 기본값 — bev_h=195, bev_w=28 (지하철 칸 스케일)."""
    from src.models.bev_baseline import BEVConfig
    cfg = BEVConfig()
    assert cfg.bev_h == 195, f"기본 bev_h {cfg.bev_h} != 195"
    assert cfg.bev_w == 28, f"기본 bev_w {cfg.bev_w} != 28"
    assert cfg.num_cams == 4
    assert cfg.backbone == "resnet18"
    assert cfg.feat_channels == 64


def test_bev_config_custom() -> None:
    """BEVConfig 커스텀 — 작은 해상도."""
    from src.models.bev_baseline import BEVConfig
    cfg = BEVConfig(bev_h=32, bev_w=16, num_cams=2)
    assert cfg.bev_h == 32
    assert cfg.bev_w == 16
    assert cfg.num_cams == 2


def test_bev_backbone_unknown_raises() -> None:
    """지원하지 않는 backbone → ValueError."""
    from src.models.bev_baseline import BEVConfig, BEVBaseline
    cfg = BEVConfig(backbone="vgg16", bev_h=8, bev_w=8)
    with pytest.raises(ValueError, match="unknown backbone"):
        BEVBaseline(cfg)


def test_bev_forward_single_cam() -> None:
    """N=1 단일 카메라 forward — occupancy shape 정상."""
    from src.models.bev_baseline import BEVBaseline, BEVConfig
    cfg = BEVConfig(bev_h=8, bev_w=8)
    model = BEVBaseline(cfg).eval()
    x = torch.randn(1, 1, 3, 32, 32)
    with torch.no_grad():
        out = model(x)
    assert out["occupancy"].shape == (1, 1, 8, 8)


def test_bev_forward_large_batch() -> None:
    """B=4 배치 forward — count shape (4,1)."""
    from src.models.bev_baseline import BEVBaseline, BEVConfig
    cfg = BEVConfig(bev_h=8, bev_w=8)
    model = BEVBaseline(cfg).eval()
    x = torch.randn(4, 2, 3, 32, 32)
    with torch.no_grad():
        out = model(x)
    assert out["count"].shape == (4, 1)


def test_bev_bev_query_shape() -> None:
    """bev_query 파라미터 shape: (1, feat_channels, bev_h, bev_w)."""
    from src.models.bev_baseline import BEVBaseline, BEVConfig
    cfg = BEVConfig(bev_h=16, bev_w=16, feat_channels=32)
    model = BEVBaseline(cfg)
    shape = tuple(model.bev_query.shape)
    assert shape == (1, 32, 16, 16), f"bev_query shape 오류: {shape}"


def test_bev_density_shape_matches_bev_grid() -> None:
    """density 출력 shape이 BEV grid와 일치."""
    from src.models.bev_baseline import BEVBaseline, BEVConfig
    cfg = BEVConfig(bev_h=12, bev_w=10)
    model = BEVBaseline(cfg).eval()
    x = torch.randn(2, 1, 3, 32, 32)
    with torch.no_grad():
        out = model(x)
    assert out["density"].shape == (2, 1, 12, 10)
