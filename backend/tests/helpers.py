"""测试辅助：假链与样例数据。"""
from app.llm.output_schemas import LLMOption, LLMQuestion, LLMQuiz, LLMReport
from app.models.quiz import Option, Question


class FakeChain:
    """可注入的假链，返回预设结果或抛出预设异常。"""

    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc
        self.last_payload = None

    def invoke(self, payload):
        self.last_payload = payload
        if self.exc:
            raise self.exc
        return self.result


def make_llm_quiz():
    return LLMQuiz(
        title="RAG 入门",
        summary="围绕 RAG 基础概念与应用场景生成的题库",
        keywords=["RAG", "检索增强生成"],
        questions=[
            LLMQuestion(
                id="q1",
                type="single",
                stem="RAG 的核心思想是？",
                options=[
                    LLMOption(key="A", text="检索增强生成"),
                    LLMOption(key="B", text="生成式对抗网络"),
                ],
                answer=["A"],
                explanation="RAG = 检索 + 生成，先查后答。",
                knowledge_point="RAG 定义",
                difficulty="easy",
            )
        ],
    )


def make_llm_report():
    return LLMReport(
        accuracy=80,
        mastered_points=["RAG 定义"],
        weak_points=["与搜索的边界"],
        three_line_summary=["s1", "s2", "s3"],
        advice=["a1"],
        share_quote="把知识做成关卡，记忆会更深。",
    )


def make_question(qid="q1", point="RAG 定义", qtype="single"):
    return Question(
        id=qid,
        type=qtype,
        stem="题干",
        options=[Option(key="A", text="选项A"), Option(key="B", text="选项B")],
        answer=["A"],
        explanation="讲解",
        knowledge_point=point,
        difficulty="easy",
    )
