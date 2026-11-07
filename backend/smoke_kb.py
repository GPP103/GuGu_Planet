"""RAG 知识库真实链路冒烟：真 embedding + 真 DeepSeek。

用法：cd backend && ./.venv/Scripts/python.exe smoke_kb.py
"""
from app.db import SessionLocal, init_db
from app.models.knowledge_base import KnowledgeBase
from app.models.question_bank import QuestionBank
from app.models.user import User
from app.services.knowledge_service import KnowledgeService
from app.services.quiz_service import QuizService

DOC = """量子计算入门笔记

一、量子比特
量子比特（qubit）是量子计算的基本单元。与只能处于 0 或 1 的经典比特不同，量子比特可以同时处于 0 和 1 的叠加态。

二、量子门
量子门是对量子比特进行的基本操作，类似经典计算中的逻辑门。常见的单量子比特门有 X 门、H 门，双量子比特门有 CNOT 门。

三、量子纠缠
两个或多个量子比特可以形成纠缠态，测量其中一个会瞬间影响另一个的状态。

四、量子纠错
量子计算工程化的核心难题是退相干与噪声。表面码（surface code）是目前主流的量子纠错方案。
"""


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.openid == "smoke_kb_user").first()
        if user is None:
            user = User(openid="smoke_kb_user", nickname="冒烟用户")
            db.add(user)
            db.commit()
            db.refresh(user)

        svc = KnowledgeService(db)
        kb = svc.create_from_text(user.id, "量子计算笔记", "txt", "quantum.txt", DOC)
        print(f"[1] 建库成功 id={kb.id} chunks={kb.chunk_count}")

        chunks = svc.retrieve(user.id, kb.id, "量子纠错用什么方案")
        print(f"[2] 检索到 {len(chunks)} 段，首段：{chunks[0][:60]}...")

        quiz = QuizService(db=db).generate("量子比特和量子门", knowledge_base_id=kb.id, user_id=user.id)
        print(f"[3] 出题成功 title={quiz.title} freshness={quiz.freshness} 题数={len(quiz.questions)}")
        for q in quiz.questions:
            print(f"    - [{q.type}] {q.stem[:40]}")

        cache_count = db.query(QuestionBank).count()
        print(f"[4] 全局缓存条数={cache_count}（知识库出题不应写入）")

        svc.delete(user.id, kb.id)
        db.query(User).filter(User.openid == "smoke_kb_user").delete()
        db.commit()
        print("[5] 清理完成")
    finally:
        db.close()


if __name__ == "__main__":
    main()
