import { useEffect, useRef, useState } from 'react'
import Taro from '@tarojs/taro'
import { Text, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import { generateReport, submitRecord } from '../../utils/api'
import { ensureLogin } from '../../utils/auth'
import { getQuiz, saveReport } from '../../utils/store'
import type { AnswerRecord, Question, Quiz, UserProfile } from '../../types'
import './index.scss'

const TYPE_LABEL: Record<string, string> = {
  single: '单选题',
  multiple: '多选题',
  judge: '判断题'
}

function sameAnswer(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false
  return [...a].sort().join(',') === [...b].sort().join(',')
}

export default function QuizPage() {
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [idx, setIdx] = useState(0)
  const [selected, setSelected] = useState<string[]>([])
  const [answered, setAnswered] = useState(false)
  const [answers, setAnswers] = useState<Record<string, { selected: string[]; answered: boolean }>>({})
  const [submitting, setSubmitting] = useState(false)
  const [user, setUser] = useState<UserProfile | null>(null)
  const recordsRef = useRef<AnswerRecord[]>([])
  const startRef = useRef(0)

  useEffect(() => {
    const q = getQuiz()
    if (q) {
      setQuiz(q)
      startRef.current = Date.now()
    }
  }, [])

  useEffect(() => {
    ensureLogin().then((u) => u && setUser(u)).catch(() => null)
  }, [])

  const question: Question | undefined = quiz?.questions[idx]
  const total = quiz?.questions.length || 0
  const isCorrect = answered && sameAnswer(selected, question?.answer || [])
  const xp = user?.xp ?? 0
  const level = user?.level ?? 1
  const nextLevelXp = user?.next_level_xp ?? 50
  const xpProgress = nextLevelXp > 0 ? Math.min(100, Math.round((xp / nextLevelXp) * 100)) : 0

  const submit = (sel: string[]) => {
    if (!question) return
    const correct = sameAnswer(sel, question.answer)
    const record = {
      question_id: question.id,
      selected_answers: sel,
      is_correct: correct,
      duration_ms: Date.now() - startRef.current
    }
    // 回退重答时按题目去重，保留最后一次作答
    recordsRef.current = recordsRef.current.filter((r) => r.question_id !== question.id)
    recordsRef.current.push(record)
    setAnswered(true)
    setAnswers((prev) => ({ ...prev, [question.id]: { selected: sel, answered: true } }))
  }

  const tapOption = (key: string) => {
    if (answered) return
    if (question?.type === 'multiple') {
      setSelected((prev) =>
        prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
      )
    } else {
      const sel = [key]
      setSelected(sel)
      submit(sel)
    }
  }

  const switchTo = (newIdx: number) => {
    setIdx(newIdx)
    const q = quiz?.questions[newIdx]
    const a = q ? answers[q.id] : undefined
    setSelected(a ? a.selected : [])
    setAnswered(a ? a.answered : false)
    startRef.current = Date.now()
  }

  const next = async () => {
    if (idx + 1 < total) {
      switchTo(idx + 1)
    } else {
      await finish()
    }
  }

  const prev = () => {
    if (idx > 0) {
      switchTo(idx - 1)
    }
  }

  const copyUrl = (url: string) => {
    if (!url) return
    Taro.setClipboardData({ data: url }).then(() =>
      Taro.showToast({ title: '已复制来源链接', icon: 'none' })
    )
  }

  const finish = async () => {
    if (!quiz || submitting) return
    setSubmitting(true)
    try {
      // 先静默登录（仅小程序端，H5 直接跳过），再提交完整答题记录；失败不阻断主流程
      await ensureLogin().catch(() => null)
      await submitRecord(quiz.title, quiz.questions, recordsRef.current).catch(() => {})
      const report = await generateReport(
        quiz.quiz_id,
        quiz.title,
        quiz.questions,
        recordsRef.current
      )
      saveReport(report)
      Taro.redirectTo({ url: '/pages/report/index' })
    } catch {
      setSubmitting(false)
      Taro.showToast({ title: '报告生成失败，请重试', icon: 'none' })
    }
  }

  if (!quiz || !question) {
    return (
      <View className='page'>
        <View className='bg-stars' />
        <View className='scroll'>
          <View className='empty'>
            <Mascot variant='empty' />
            <View className='empty-t'>还没有进行中的关卡</View>
            <View className='empty-s'>去首页输入知识，生成你的闯关题库</View>
            <View
              className='cta'
              onClick={() => Taro.redirectTo({ url: '/pages/index/index' })}
            >
              去首页
            </View>
          </View>
        </View>
      </View>
    )
  }

  return (
    <View className='page'>
      <View className='bg-stars' />
      <View className='scroll'>
        <View className='progress'>
          <View className='back' onClick={() => Taro.redirectTo({ url: '/pages/index/index' })}>
            ‹
          </View>
          <View className='stage-t'>第 {idx + 1} / {total} 关</View>
        </View>

        {quiz.freshness === 'fresh' && quiz.sources.length > 0 && (
          <View className='src-bar'>
            <Text className='src-tag'>联网最新</Text>
            <View className='src-titles'>
              {quiz.sources.slice(0, 2).map((s, i) => (
                <Text key={i} className='src-title' onClick={() => copyUrl(s.url)}>
                  {s.title}
                </Text>
              ))}
            </View>
          </View>
        )}
        {quiz.freshness === 'kb' && (
          <View className='src-bar kb'>
            <Text className='src-tag'>基于我的文档</Text>
            <Text className='src-tip'>{quiz.sources[0]?.title || '个人知识库'}</Text>
          </View>
        )}
        {quiz.freshness === 'stale' && (
          <View className='src-bar stale'>
            <Text className='src-tag'>知识可能过时</Text>
            <Text className='src-tip'>基于模型知识生成，建议输入最新资料</Text>
          </View>
        )}

        <View className='xp-wrap'>
          <View className='xp-row'>
            <Text>远征经验</Text>
            <Text>LV.{level} · {xp} / {nextLevelXp}</Text>
          </View>
          <View className='xp-bar'>
            <View className='xp-fill' style={{ width: `${xpProgress}%` }} />
          </View>
        </View>

        <View className='orbit'>
          {Array.from({ length: total }).map((_, i) => (
            <View
              key={i}
              className={`node ${i < idx ? 'done' : ''} ${i === idx ? 'cur' : ''}`}
            />
          ))}
        </View>

        <View className='qcard glass'>
          <Text className='qtype'>{TYPE_LABEL[question.type] || '单选题'}</Text>
          <View className='qstem'>{question.stem}</View>
        </View>

        <View className='opts'>
          {question.options.map((opt) => {
            const picked = selected.includes(opt.key)
            const isAnswer = question.answer.includes(opt.key)
            let cls = 'opt'
            if (picked) cls += ' picked'
            if (answered && isAnswer) cls += ' correct'
            if (answered && picked && !isAnswer) cls += ' wrong'
            return (
              <View key={opt.key} className={cls} onClick={() => tapOption(opt.key)}>
                <View className='k'>{opt.key}</View>
                <View className='opt-text'>{opt.text}</View>
              </View>
            )
          })}
        </View>

        {question.type === 'multiple' && !answered && (
          <View
            className={`confirm ${selected.length ? '' : 'disabled'}`}
            onClick={() => selected.length && submit(selected)}
          >
            确认答案
          </View>
        )}

        {answered && (
          <>
            <View className={`feedback ${isCorrect ? 'ok' : 'no'}`}>
              <View className='ic'>{isCorrect ? '✓' : '✕'}</View>
              <Text className='txt'>{isCorrect ? '答对了！' : '答错了'}</Text>
              {isCorrect && <Text className='xp'>+10 XP</Text>}
            </View>
            <View className='explain glass'>
              <View className='h'>
                <View className='ai' />
                AI 知识讲解
              </View>
              <Text className='p'>{question.explanation}</Text>
            </View>
            <View className='btn-row'>
              {idx > 0 && (
                <View className='prev' onClick={prev}>
                  ‹ 上一关
                </View>
              )}
              <View className='next' onClick={next}>
                {idx + 1 < total ? '下一关 ›' : submitting ? '生成中…' : '生成报告'}
              </View>
            </View>
          </>
        )}
      </View>
    </View>
  )
}
