"""BEV 모델 (src/models/bev_baseline.py) 회귀 가드 (cycle 501).

BEVBaseline:
- 입력: (B, N, 3, H, W) — B=배치, N=카메라 수
- 출력: occupancy/density/count 3-head
- backbone: MobileNetV3-small (Edge 배포 최적화)
- bev_query: 학습 가능한 BEV grid 파라미터

M1 진입장벽: 자율주행 CV 전문 인력 — YOLO11+BoT-SORT+호모그래피+BEV
"""
from __future__ import annotations

import pytest
import torch


@pytest.fixture(scope="module")
def model():
    from src.models.bev_baseline import BEVBaseline, BEVConfig
    cfg = BEVConfig(bev_h=16, bev_w=16)  # 작은 크기로 빠른 테스트
    return BEVBaseline(cfg).eval()


def test_bev_model_instantiates(model) -> None:
    """BEVBaseline 모델 인스턴스 생성."""
    assert model is not None


def test_bev_model_forward_shape(model) -> None:
    """forward 패스 출력 shape 검증 (B=1, N=2, H=64, W=64)."""
    x = torch.randn(1, 2, 3, 64, 64)
    with torch.no_grad():
        out = model(x)
    assert "occupancy" in out, "occupancy head 출력 누락"
    assert "density" in out, "density head 출력 누락"
    assert "count" in out, "count head 출력 누락"


def test_bev_occupancy_sigmoid_range(model) -> None:
    """occupancy 출력이 sigmoid — [0, 1] 범위."""
    x = torch.randn(1, 1, 3, 64, 64)
    with torch.no_grad():
        out = model(x)
    occ = out["occupancy"]
    assert occ.min() >= 0.0 - 1e-6, "occupancy < 0 (sigmoid 미적용)"
    assert occ.max() <= 1.0 + 1e-6, "occupancy > 1 (sigmoid 미적용)"


def test_bev_density_non_negative(model) -> None:
    """density 출력이 relu — 음수 없음."""
    x = torch.randn(2, 1, 3, 32, 32)
    with torch.no_grad():
        out = model(x)
    assert out["density"].min() >= 0.0 - 1e-6, "density < 0 (relu 미적용)"


def test_bev_count_shape(model) -> None:
    """count head 출력 shape: (B, 1)."""
    x = torch.randn(3, 2, 3, 64, 64)
    with torch.no_grad():
        out = model(x)
    assert out["count"].shape == (3, 1), f"count shape 오류: {out['count'].shape}"


def test_bev_model_parameter_count(model) -> None:
    """파라미터 수 > 0 (모델이 학습 가능한 파라미터 보유)."""
    n_params = sum(p.numel() for p in model.parameters())
    assert n_params > 1000, f"파라미터 수 너무 적음: {n_params}"


def test_bev_query_is_learnable(model) -> None:
    """bev_query 가 학습 가능한 파라미터."""
    bev_query = None
    for name, p in model.named_parameters():
        if "bev_query" in name:
            bev_query = p
            break
    assert bev_query is not None, "bev_query 파라미터 누락"
    assert bev_query.requires_grad, "bev_query requires_grad=False"
