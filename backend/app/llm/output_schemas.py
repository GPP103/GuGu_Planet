"""LLM 结构化输出 Schema（供 with_structured_output 使用）。

字段类型保持宽松（type/difficulty 用 str），由服务层归一化兜底，
避免 LLM 输出非标准枚举时整体解析失败。
"""
from pydantic import BaseModel, Field


class LLMOption(BaseModel):
    key: str = Field(description="选项标识，如 A/B/C/D")
    text: str = Field(description="选项内容")


class LLMQuestion(BaseModel):
    id: str = Field(description="题目编号，如 q1")
    type: str = Field(description="题型：single 单选 / multiple 多选 / judge 判断")
    stem: str = Field(description="题干")
    options: list[LLMOption] = Field(description="选项列表")
    answer: list[str] = Field(description="正确答案的 key 列表")
    explanation: str = Field(description="详细讲解")
    knowledge_point: str = Field(description="知识点标签")
    difficulty: str = Field(description="难度：easy / medium / hard")


class LLMQuiz(BaseModel):
    title: str = Field(description="学习主题标题")
    summary: str = Field(description="题库主题摘要")
    questions: list[LLMQuestion] = Field(description="题目列表")


class LLMReport(BaseModel):
    accuracy: int = Field(description="正确率百分比，0-100")
    mastered_points: list[str] = Field(description="掌握较好的知识点")
    weak_points: list[str] = Field(description="薄弱知识点")
    three_line_summary: list[str] = Field(description="三句知识总结")
    advice: list[str] = Field(description="后续学习建议")
    share_quote: str = Field(description="一句可分享的学习金句")
