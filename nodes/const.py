"""노드에서 사용하는 모든 Enum 상수."""
from enum import StrEnum
from midjourney_api.params.types import Quality, SpeedMode, StyleVersion, VisibilityMode

class UpscaleType(StrEnum):
    SUBTLE   = "v7_2x_subtle"
    CREATIVE = "v7_2x_creative"


class PanDirection(StrEnum):
    """순서: DIRECTION_MAP 값 오름차순 (0=down, 1=right, 2=up, 3=left)."""
    DOWN  = "down"   # 0
    RIGHT = "right"  # 1
    UP    = "up"     # 2
    LEFT  = "left"   # 3


class PersonalizeMode(StrEnum):
    OFF     = "off"
    DEFAULT = "default"
    CUSTOM  = "custom"


class VideoResolution(StrEnum):
    R480 = "480"
    R720 = "720"


class MotionIntensity(StrEnum):
    LOW  = "low"
    HIGH = "high"


QUALITY_OPTIONS    = [str(v) for v in Quality._allowed]       # ["1", "2", "4"]
VISIBILITY_OPTIONS = ["default"] + list(VisibilityMode)        # ["default", "stealth", "public"]
SV_OPTIONS         = [str(v) for v in StyleVersion._allowed]   # ["4", "6", "7", "8"] (스타일 버전 옵션)

__all__ = [
    # API에서 재내보내기
    "SpeedMode",
    # 로컬 열거형
    "UpscaleType",
    "PanDirection",
    "PersonalizeMode",
    "VideoResolution",
    "MotionIntensity",
    # 파생 옵션 목록
    "QUALITY_OPTIONS",
    "VISIBILITY_OPTIONS",
    "SV_OPTIONS",
]
