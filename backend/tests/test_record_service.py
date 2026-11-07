"""答题记录与错题本服务测试。"""
import pytest

from app.core.exceptions import InputInvalidError
from app.models.user import User
from app.services.record_service import RecordService


def _make_user(db_session, openid="openid_rec"):
    u = User(openid=openid, nickname="测试")
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def _make_question(qid="q1", stem="题干1"):
    return {
        "id": qid,
        "type": "single",
        "stem": stem,
        "options": [{"key": "A", "text": "选项A"}, {"key": "B", "text": "选项B"}],
        "answer": ["A"],
        "explanation": "讲解",
        "knowledge_point": "知识点",
        "difficulty": "easy",
    }


def test_submit_records_history_and_wrong(db_session):
    u = _make_user(db_session)
    svc = RecordService(db_session)
    questions = [_make_question("q1", "题干A"), _make_question("q2", "题干B")]
    records = [
        {"question_id": "q1", "selected_answers": ["A"], "is_correct": True},
        {"question_id": "q2", "selected_answers": ["B"], "is_correct": False},
    ]
    result = svc.submit(u, "测试主题", questions, records)
    assert result.total_answered == 2
    assert result.total_correct == 1
    assert result.accuracy == 50

    history = svc.history(u)
    assert len(history) == 1
    assert history[0].correct_count == 1
    assert history[0].topic == "测试主题"
    assert history[0].answered_count == 2
    assert len(history[0].items) == 2
    assert history[0].items[0].is_correct is True
    assert history[0].items[1].is_correct is False
    assert history[0].items[1].user_answer == ["B"]
    assert history[0].items[1].answer == ["A"]

    wrong = svc.wrong_list(u)
    assert len(wrong) == 1
    assert wrong[0].stem == "题干B"
    assert wrong[0].user_answer == ["B"]
    assert wrong[0].answer == ["A"]


def test_partial_answer_accuracy_by_answered(db_session):
    u = _make_user(db_session)
    svc = RecordService(db_session)
    questions = [_make_question("q1", "题A"), _make_question("q2", "题B"), _make_question("q3", "题C")]
    # 只答了 2 题（跳过 q3），全对
    records = [
        {"question_id": "q1", "selected_answers": ["A"], "is_correct": True},
        {"question_id": "q2", "selected_answers": ["A"], "is_correct": True},
    ]
    result = svc.submit(u, "t", questions, records)
    assert result.total_answered == 2  # 只算实际作答，跳过的不计入
    assert result.accuracy == 100  # 2/2=100%，而非 2/3
    history = svc.history(u)
    assert history[0].answered_count == 2
    assert history[0].question_count == 3
    assert len(history[0].items) == 2  # 只记录作答的题


def test_wrong_dedup_by_stem(db_session):
    u = _make_user(db_session)
    svc = RecordService(db_session)
    questions = [_make_question("q1", "题干X")]
    records = [{"question_id": "q1", "selected_answers": ["B"], "is_correct": False}]
    svc.submit(u, "t1", questions, records)
    svc.submit(u, "t2", questions, records)
    assert len(svc.wrong_list(u)) == 1


def test_submit_empty_questions_raises(db_session):
    u = _make_user(db_session)
    svc = RecordService(db_session)
    with pytest.raises(InputInvalidError):
        svc.submit(u, "t", [], [])


def test_remove_wrong(db_session):
    u = _make_user(db_session)
    svc = RecordService(db_session)
    questions = [_make_question("q1", "题干Y")]
    records = [{"question_id": "q1", "selected_answers": ["B"], "is_correct": False}]
    svc.submit(u, "t", questions, records)
    wrong = svc.wrong_list(u)
    assert len(wrong) == 1
    assert svc.remove_wrong(u, wrong[0].id) is True
    assert svc.wrong_list(u) == []


def test_remove_wrong_wrong_owner(db_session):
    u = _make_user(db_session, "openid_u")
    other = _make_user(db_session, "openid_other")
    svc = RecordService(db_session)
    questions = [_make_question("q1", "题干Z")]
    records = [{"question_id": "q1", "selected_answers": ["B"], "is_correct": False}]
    svc.submit(u, "t", questions, records)
    wrong = svc.wrong_list(u)[0]
    # 别的用户删除该错题应失败
    assert svc.remove_wrong(other, wrong.id) is False


def test_items_keep_image_url(db_session):
    from app.models.user import User
    from app.services.record_service import RecordService

    user = User(openid="img_record_user", nickname="带图用户")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    questions = [
        {
            "id": "q1",
            "type": "single",
            "stem": "苹果是什么颜色",
            "options": [{"key": "A", "text": "红色"}],
            "answer": ["A"],
            "explanation": "苹果多为红色",
            "knowledge_point": "apple",
            "image_url": "https://cos/apple.png",
        }
    ]
    records = [{"question_id": "q1", "selected_answers": ["A"], "is_correct": True}]
    RecordService(db_session).submit(user, "英语单词", questions, records)

    hist = RecordService(db_session).history(user)
    assert hist[0].items[0].image_url == "https://cos/apple.png"


def test_items_keep_image_url(db_session):
    from app.models.user import User
    from app.services.record_service import RecordService

    user = User(openid="img_record_user", nickname="带图用户")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    questions = [
        {
            "id": "q1",
            "type": "single",
            "stem": "苹果是什么颜色",
            "options": [{"key": "A", "text": "红色"}],
            "answer": ["A"],
            "explanation": "苹果多为红色",
            "knowledge_point": "apple",
            "image_url": "https://cos/apple.png",
        }
    ]
    records = [{"question_id": "q1", "selected_answers": ["A"], "is_correct": True}]
    RecordService(db_session).submit(user, "英语单词", questions, records)

    hist = RecordService(db_session).history(user)
    assert hist[0].items[0].image_url == "https://cos/apple.png"
