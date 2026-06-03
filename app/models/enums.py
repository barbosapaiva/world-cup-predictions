from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    PARTICIPANT = "participant"


class PlayerPosition(StrEnum):
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"


class MatchStage(StrEnum):
    GROUP = "group"
    R32 = "R32"
    R16 = "R16"
    QF = "QF"
    SF = "SF"
    THIRD = "3rd"
    FINAL = "F"


class MatchStatus(StrEnum):
    LOCKED = "locked"
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"


class SpecialCategory(StrEnum):
    CHAMPION = "champion"
    MVP = "mvp"
    GOLDEN_BOOT = "golden_boot"
    YOUNG_PLAYER = "young_player"
    BEST_GK = "best_gk"
