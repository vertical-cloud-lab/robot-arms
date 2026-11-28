"""Loads the YAML files in config/ (the only place numbers live).

    cfg = load_config()                  # Digital Twin/config/*.yaml
    cfg = load_config("my_configs/")     # another folder with the same five files
    cfg.robot["gripper"]["max_force_n"]  # plain dicts, as written in the YAML

The YAML files use mm and degrees because that is what people measure and what piper_sdk
uses. Code converts with mm() and deg() at the point of use, so SI never leaks into YAML.
"""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field

import numpy as np
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # "Digital Twin/"
CONFIG_DIR = os.path.join(ROOT, "config")
FILES = {"robot": "robot_piper.yaml", "cell": "cell_layout.yaml", "tags": "apriltags.yaml",
         "prints": "prints.yaml", "sim": "sim.yaml"}


def mm(v):
    """mm -> m, for scalars or lists."""
    return np.asarray(v, float) / 1000.0


def deg(v):
    """degrees -> radians, for scalars or lists."""
    return np.radians(np.asarray(v, float))


@dataclass
class Config:
    robot: dict
    cell: dict
    tags: dict
    prints: dict
    sim: dict
    root: str = ROOT
    overrides: dict = field(default_factory=dict)

    def path(self, rel: str) -> str:
        """A path relative to the Digital Twin folder (for meshes and outputs)."""
        return rel if os.path.isabs(rel) else os.path.join(self.root, rel)

    def copy(self) -> "Config":
        return copy.deepcopy(self)


def load_config(config_dir: str | None = None) -> Config:
    config_dir = config_dir or CONFIG_DIR
    data = {}
    for key, fname in FILES.items():
        with open(os.path.join(config_dir, fname)) as fh:
            data[key] = yaml.safe_load(fh)
    return Config(**data)
