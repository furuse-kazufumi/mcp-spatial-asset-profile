"""Load and parse cameras.json and scene.json into typed Python objects.

T_world_cam convention (enforced throughout):
  T_world_cam transforms a point from camera frame to world frame.
  p_world = T_world_cam @ p_cam_homogeneous
  T_cam_world = inv(T_world_cam) is used for projection.
"""
from __future__ import annotations

import json
import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Intrinsics ──────────────────────────────────────────────────────────────

@dataclass
class Intrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    distortion_model: str = "none"
    distortion_coeffs: list = field(default_factory=list)

    def project(self, P_cam: np.ndarray) -> tuple[float, float]:
        """Project a camera-frame point to pixel coordinates (pinhole, no distortion)."""
        return self.fx * P_cam[0] / P_cam[2] + self.cx, self.fy * P_cam[1] / P_cam[2] + self.cy

    def unproject(self, x_px: float, y_px: float) -> np.ndarray:
        """Return a unit direction vector in camera frame for the given pixel."""
        d = np.array([(x_px - self.cx) / self.fx, (y_px - self.cy) / self.fy, 1.0])
        return d / np.linalg.norm(d)

    def to_dict(self) -> dict:
        return {"fx": self.fx, "fy": self.fy, "cx": self.cx, "cy": self.cy,
                "distortion_model": self.distortion_model,
                "distortion_coeffs": self.distortion_coeffs}


# ── Camera ──────────────────────────────────────────────────────────────────

@dataclass
class CameraSpec:
    id: str
    resolution: tuple  # (width, height)
    intrinsics: Intrinsics
    T_world_cam: np.ndarray  # 4×4, T_target_source convention
    time_offset_us: int = 0
    contrast_threshold_pos: float = 0.15
    contrast_threshold_neg: float = 0.15

    @property
    def T_cam_world(self) -> np.ndarray:
        return np.linalg.inv(self.T_world_cam)

    @property
    def position_world(self) -> np.ndarray:
        """Camera origin in world frame (column 3 of T_world_cam)."""
        return self.T_world_cam[:3, 3]

    @property
    def R_world_cam(self) -> np.ndarray:
        return self.T_world_cam[:3, :3]

    def project_world(self, P_world: np.ndarray) -> Optional[tuple[float, float]]:
        """Project a world-frame point. Returns (x_px, y_px) or None if not visible."""
        P_h = np.append(P_world, 1.0)
        P_cam = self.T_cam_world @ P_h
        if P_cam[2] <= 0:
            return None
        x, y = self.intrinsics.project(P_cam[:3])
        w, h = self.resolution
        if 0.0 <= x < w and 0.0 <= y < h:
            return float(x), float(y)
        return None


# ── Trajectories ─────────────────────────────────────────────────────────────

@dataclass
class LinearTraj:
    id: str
    start_us: int
    end_us: int
    start_pos: np.ndarray
    end_pos: np.ndarray
    point_radius_m: float
    luminance: float

    def eval(self, t_us: int) -> Optional[np.ndarray]:
        if not (self.start_us <= t_us <= self.end_us):
            return None
        alpha = (t_us - self.start_us) / (self.end_us - self.start_us) if self.end_us != self.start_us else 0.0
        return self.start_pos + alpha * (self.end_pos - self.start_pos)


@dataclass
class CircularTraj:
    id: str
    start_us: int
    end_us: int
    center: np.ndarray
    radius_m: float
    axis: str
    angular_velocity_rad_s: float
    point_radius_m: float
    luminance: float

    def eval(self, t_us: int) -> Optional[np.ndarray]:
        if not (self.start_us <= t_us <= self.end_us):
            return None
        angle = self.angular_velocity_rad_s * (t_us - self.start_us) * 1e-6
        c, s = np.cos(angle), np.sin(angle)
        P = self.center.copy()
        if self.axis == "XY":
            P[0] += self.radius_m * c; P[1] += self.radius_m * s
        elif self.axis == "XZ":
            P[0] += self.radius_m * c; P[2] += self.radius_m * s
        elif self.axis == "YZ":
            P[1] += self.radius_m * c; P[2] += self.radius_m * s
        return P


@dataclass
class ZigzagTraj:
    id: str
    start_us: int
    end_us: int
    waypoints: list
    point_radius_m: float
    luminance: float

    def eval(self, t_us: int) -> Optional[np.ndarray]:
        if not (self.start_us <= t_us <= self.end_us):
            return None
        n = len(self.waypoints) - 1
        alpha = (t_us - self.start_us) / (self.end_us - self.start_us) if self.end_us != self.start_us else 0.0
        pos = alpha * n
        i = min(int(pos), n - 1)
        return self.waypoints[i] + (pos - i) * (self.waypoints[i + 1] - self.waypoints[i])


# ── Scene ────────────────────────────────────────────────────────────────────

@dataclass
class SceneConfig:
    duration_us: int
    seed: int
    background_luminance: float
    trajectories: list


# ── Loaders ──────────────────────────────────────────────────────────────────

def load_cameras(path) -> list[CameraSpec]:
    data = json.loads(Path(path).read_bytes().decode("utf-8"))
    out = []
    for c in data["cameras"]:
        intr = c["intrinsics"]
        out.append(CameraSpec(
            id=c["id"],
            resolution=tuple(c["resolution"]),
            intrinsics=Intrinsics(
                fx=intr["fx"], fy=intr["fy"], cx=intr["cx"], cy=intr["cy"],
                distortion_model=intr.get("distortion_model", "none"),
                distortion_coeffs=intr.get("distortion_coeffs", []),
            ),
            T_world_cam=np.array(c["T_world_cam"], dtype=float),
            time_offset_us=c.get("time_offset_us", 0),
            contrast_threshold_pos=c.get("contrast_threshold_pos", 0.15),
            contrast_threshold_neg=c.get("contrast_threshold_neg", 0.15),
        ))
    return out


def load_scene(path) -> SceneConfig:
    data = json.loads(Path(path).read_bytes().decode("utf-8"))
    trajs = []
    for t in data["trajectories"]:
        base = dict(id=t["id"], start_us=t.get("start_us", 0),
                    end_us=t.get("end_us", data["duration_us"]),
                    point_radius_m=t.get("point_radius_m", 0.02),
                    luminance=t.get("luminance", 1.0))
        if t["type"] == "linear":
            trajs.append(LinearTraj(**base,
                start_pos=np.array(t["start_pos"], dtype=float),
                end_pos=np.array(t["end_pos"], dtype=float)))
        elif t["type"] == "circular":
            trajs.append(CircularTraj(**base,
                center=np.array(t["center"], dtype=float),
                radius_m=t["radius_m"], axis=t["axis"],
                angular_velocity_rad_s=t.get("angular_velocity_rad_s", 1.0)))
        elif t["type"] == "zigzag":
            trajs.append(ZigzagTraj(**base,
                waypoints=[np.array(wp, dtype=float) for wp in t["waypoints"]]))
        else:
            raise ValueError(f"Unknown trajectory type: {t['type']}")
    return SceneConfig(
        duration_us=data["duration_us"],
        seed=data.get("seed", 42),
        background_luminance=data.get("background_luminance", 0.5),
        trajectories=trajs,
    )
