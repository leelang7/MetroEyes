"""BEV 베이스라인 — multi-view → BEV feature → occupancy/count head.

스켈레톤. BEVFormer / Lift-Splat-Shoot 의 실내용 경량 버전을 채워넣을 자리.
초기에는 카메라별 ResNet feature → 단순 splat → 2D conv head 로 시작해
정확도 baseline을 박은 뒤 deformable attention 으로 교체.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torchvision.models as tvm


@dataclass
class BEVConfig:
    num_cams: int = 4
    backbone: str = "resnet18"
    feat_channels: int = 64
    bev_h: int = 195   # x: 19.5m / 0.1m
    bev_w: int = 28    # y: 2.8m / 0.1m


def _build_backbone(name: str, out_channels: int) -> nn.Module:
    if name == "resnet18":
        net = tvm.resnet18(weights=None)
        # conv1 ~ layer3 만 사용 (stride 16)
        backbone = nn.Sequential(
            net.conv1, net.bn1, net.relu, net.maxpool,
            net.layer1, net.layer2, net.layer3,
        )
        proj = nn.Conv2d(256, out_channels, 1)
        return nn.Sequential(backbone, proj)
    raise ValueError(f"unknown backbone: {name}")


class BEVBaseline(nn.Module):
    """입력: (B, N, 3, H, W) — N=카메라 수.

    출력:
        occupancy: (B, 1, bev_h, bev_w)  — sigmoid 확률
        count:     (B, 1)                — 회귀
        density:   (B, 1, bev_h, bev_w)  — 회귀 (people / m^2)
    """

    def __init__(self, cfg: BEVConfig | None = None) -> None:
        super().__init__()
        self.cfg = cfg or BEVConfig()
        self.backbone = _build_backbone(self.cfg.backbone, self.cfg.feat_channels)

        # 자리표시: 카메라 feature를 BEV grid로 직접 사상하는 학습가능한 query.
        # 실제 구현에서는 calibration 기반 lift 또는 deformable cross-attn으로 대체.
        self.bev_query = nn.Parameter(
            torch.randn(1, self.cfg.feat_channels, self.cfg.bev_h, self.cfg.bev_w) * 0.02
        )
        self.fuse = nn.Sequential(
            nn.Conv2d(self.cfg.feat_channels, self.cfg.feat_channels, 3, padding=1),
            nn.GELU(),
            nn.Conv2d(self.cfg.feat_channels, self.cfg.feat_channels, 3, padding=1),
            nn.GELU(),
        )
        self.head_occ = nn.Conv2d(self.cfg.feat_channels, 1, 1)
        self.head_density = nn.Conv2d(self.cfg.feat_channels, 1, 1)
        self.head_count = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(self.cfg.feat_channels, 1),
        )

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        b, n, c, h, w = x.shape
        feats = self.backbone(x.view(b * n, c, h, w))             # (B*N, C, H', W')
        feats = feats.view(b, n, *feats.shape[1:]).mean(dim=1)    # 카메라 평균 — placeholder
        feats = nn.functional.adaptive_avg_pool2d(
            feats, (self.cfg.bev_h, self.cfg.bev_w)
        )
        bev = self.fuse(feats + self.bev_query)
        return {
            "occupancy": torch.sigmoid(self.head_occ(bev)),
            "density": torch.relu(self.head_density(bev)),
            "count": self.head_count(bev),
        }


if __name__ == "__main__":
    model = BEVBaseline()
    dummy = torch.randn(2, 4, 3, 256, 448)
    out = model(dummy)
    for k, v in out.items():
        print(f"{k:>10}: {tuple(v.shape)}")
