"""Material properties: density, friction and contact softness for every surface in the cell.

Edit the numbers here (or add materials) and every engine uses them. Friction is the Coulomb
coefficient MuJoCo combines per contact pair (it takes the larger of the two geoms' values,
so give grippy materials the high number). Sources and caveats are in the comments; anything
marked "estimate" should be measured (a tilted-plate slide test is enough).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    density: float          # kg/m^3 of the solid material
    friction: float         # sliding friction coefficient
    torsional: float = 0.005  # m: resistance to spinning about the contact normal
    rolling: float = 0.0001   # m: resistance to rolling
    solref: tuple | None = None  # contact softness override (time constant s, damping ratio)
    stick_kpa: float = 0.0  # default bond to the build plate (prints only)


MATERIALS: dict[str, Material] = {
    # Printed plastics. Densities are datasheet values for the solid; a print's mass is
    # density * volume * fill (prints.yaml). stick_kpa: cooled prints on textured PEI let go
    # easily; a few kPa (a 20 mm cube is then held by ~1 N) is "a little bit of stick".
    # Friction: PLA on PLA 0.12-0.38 static (Santana 2021), PLA on steel 0.2-0.3 (Stoimenov
    # 2024). No published value for TPU 95A on PLA: TPU on steel is only 0.17-0.33 kinetic
    # (Braileanu 2023), and TPU grips plastic better than steel, so 0.6 is an estimate.
    "PLA": Material(density=1240, friction=0.30, stick_kpa=2.5),
    "PETG": Material(density=1270, friction=0.35, stick_kpa=3.5),
    "ABS": Material(density=1040, friction=0.30, stick_kpa=2.0),
    "TPU": Material(density=1210, friction=0.60, torsional=0.01, solref=(0.006, 1.0)),
    # Cell surfaces (estimates: nothing published for these pairs).
    "plywood": Material(density=600, friction=0.40),
    "pei_textured": Material(density=7850, friction=0.30),  # spring steel sheet, PEI coating
    "black_aluminium": Material(density=2700, friction=0.30),
    "abs_plastic": Material(density=1040, friction=0.30),
    "pla": Material(density=1240, friction=0.30),
    "arm": Material(density=1200, friction=0.30),
}


def get(name: str) -> Material:
    try:
        return MATERIALS[name]
    except KeyError:
        raise KeyError(f"unknown material {name!r}; add it to physics/materials.py "
                       f"(known: {', '.join(MATERIALS)})") from None
