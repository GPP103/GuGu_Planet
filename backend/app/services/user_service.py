"""用户资料与学习统计服务。"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import InputInvalidError
from app.models.user import User
from app.models.user_schemas import StudyRecordResponse, UpdateProfileRequest, UserOut

# 经验值 = 答对题数 × 10；等级按累计经验分档（升到 LV2~LV10 所需累计 XP）
XP_PER_CORRECT = 10
LEVEL_THRESHOLDS = [50, 120, 240, 400, 620, 1000, 1500, 2200, 3000]


def calc_xp(total_correct: int) -> int:
    return total_correct * XP_PER_CORRECT


def calc_level(xp: int) -> int:
    level = 1
    for threshold in LEVEL_THRESHOLDS:
        if xp >= threshold:
            level += 1
    return level


def calc_next_level_xp(xp: int) -> int:
    for threshold in LEVEL_THRESHOLDS:
        if xp < threshold:
            return threshold
    return xp  # 已满级，停在上限


def xp_fields(total_correct: int) -> dict:
    xp = calc_xp(total_correct)
    return {"xp": xp, "level": calc_level(xp), "next_level_xp": calc_next_level_xp(xp)}


def to_user_out(user: User) -> UserOut:
    accuracy = round(user.total_correct / user.total_answered * 100) if user.total_answered > 0 else 0
    return UserOut(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        total_answered=user.total_answered,
        total_correct=user.total_correct,
        current_streak=user.current_streak,
        accuracy=accuracy,
        **xp_fields(user.total_correct),
    )


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user: User) -> UserOut:
        return to_user_out(user)

    def update_profile(self, user: User, req: UpdateProfileRequest) -> UserOut:
        if req.nickname is not None:
            nickname = req.nickname.strip()
            if not nickname:
                raise InputInvalidError("昵称不能为空")
            user.nickname = nickname
        if req.avatar_url is not None:
            user.avatar_url = req.avatar_url
        self.db.commit()
        self.db.refresh(user)
        return to_user_out(user)

    def submit_study_record(self, user: User, answered: int, correct: int) -> StudyRecordResponse:
        if correct > answered:
            raise InputInvalidError("正确数不能大于答题数")

        today = date.today()
        if user.last_study_date == today:
            pass  # 今日已打卡，streak 不变
        elif user.last_study_date == today - timedelta(days=1):
            user.current_streak += 1  # 连续
        else:
            user.current_streak = 1  # 断签，重新起算

        user.last_study_date = today
        user.total_answered += answered
        user.total_correct += correct
        self.db.commit()
        self.db.refresh(user)

        accuracy = round(user.total_correct / user.total_answered * 100) if user.total_answered > 0 else 0
        return StudyRecordResponse(
            total_answered=user.total_answered,
            total_correct=user.total_correct,
            current_streak=user.current_streak,
            accuracy=accuracy,
            **xp_fields(user.total_correct),
        )
