import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PARTICIPANT = "participant"


class PlayerPosition(str, enum.Enum):
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"


class MatchStage(str, enum.Enum):
    GROUP = "group"
    R32 = "R32"
    R16 = "R16"
    QF = "QF"
    SF = "SF"
    THIRD = "3rd"
    FINAL = "F"


class MatchStatus(str, enum.Enum):
    LOCKED = "locked"
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"


class SpecialCategory(str, enum.Enum):
    CHAMPION = "champion"
    MVP = "mvp"
    GOLDEN_BOOT = "golden_boot"
    YOUNG_PLAYER = "young_player"
    BEST_GK = "best_gk"