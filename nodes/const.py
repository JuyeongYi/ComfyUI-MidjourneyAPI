"""노드에서 사용하는 모든 Enum 상수."""
from enum import StrEnum
from midjourney_api.params.types import Quality, SpeedMode, VisibilityMode

class UpscaleType(StrEnum):
    SUBTLE   = "v7_2x_subtle"
    CREATIVE = "v7_2x_creative"


class PanDirection(StrEnum):
    """순서: DIRECTION_MAP value 오름차순 (0=down, 1=right, 2=up, 3=left)."""
    DOWN  = "down"   # 0
    RIGHT = "right"  # 1
    UP    = "up"     # 2
    LEFT  = "left"   # 3


class PersonalizeMode(StrEnum):
    OFF     = "off"
    DEFAULT = "default"
    CUSTOM  = "custom"


QUALITY_OPTIONS    = [str(v) for v in Quality._allowed]       # ["1", "2", "4"]
VISIBILITY_OPTIONS = ["default"] + list(VisibilityMode)        # ["default", "stealth", "public"]

__all__ = [
    # re-exported from API
    "SpeedMode",
    # local enums
    "UpscaleType",
    "PanDirection",
    "PersonalizeMode",
    # derived option lists
    "QUALITY_OPTIONS",
    "VISIBILITY_OPTIONS",
]