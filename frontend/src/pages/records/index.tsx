import { useEffect, useState } from 'react'
import Taro from '@tarojs/taro'
import { Image, Text, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import TabBar from '../../components/TabBar'
import { getHistory, getWrongList, illustrateQuestion, removeWrong } from '../../utils/api'
import { ensureLogin } from '../../utils/auth'
import { saveQuiz } from '../../utils/store'
import type { HistoryItem, Question, QuestionType, Quiz, RecordItem, WrongItem } from '../../types'
import './index.scss'

const TYPE_LABEL: Record<string, string> = {
  single: '单选题',
  multiple: '多选题',
  judge: '判断题'
}

export default function RecordsPage() {
  const [tab, setTab] = useState<'history' | 'wrong'>('history')
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [wrong, setWrong] = useState<WrongItem[]>([])
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [loggedIn, setLoggedIn] = useState(true)
  const [illustrating, setIllustrating] = useState<string>('')

  const load = async () => {
    setLoading(true)
    const u = await ensureLogin()
    if (!u) {
      setLoggedIn(false)
      setLoading(false)
      return
    }
    setLoggedIn(true)
    try {
      const [h, w] = await Promise.all([getHistory(), getWrongList()])
      setHistory(h)
      setWrong(w)
    } catch {
      // 加载失败静默展示空态
    }
    setLoading(false)
  }

  useEffect(() => {
    const params = Taro.getCurrentInstance().router?.params
    if (params?.tab === 'wrong') setTab('wrong')
    load()
  }, [])

  const retryWrong = () => {
    if (wrong.length === 0) return
    const picked = wrong.slice(0, 10)
    const questions: Question[] = picked.map((w, i) => {
      const type: QuestionType =
        w.type === 'multiple' || w.type === 'judge' || w.type === 'single'
          ? w.type
          : w.options.length === 2
            ? 'judge'
            : w.answer.length > 1
              ? 'multiple'
              : 'single'
      return {
        id: `w_${w.id}_${i}`,
        type,
        stem: w.stem,
        options: w.options,
        answer: w.answer,
        explanation: w.explanation,
        knowledge_point: w.knowledge_point || '',
        difficulty: 'medium'
      }
    })
    const quiz: Quiz = {
      quiz_id: `retry_${Date.now()}`,
      title: `错题重练 · ${picked[0].topic || '综合'}`,
      summary: `共 ${questions.length} 道错题，再来一次巩固`,
      source_type: 'wrong',
      user_input: '错题重练',
      questions,
      sources: [],
      freshness: 'stale'
    }
    saveQuiz(quiz)
    Taro.redirectTo({ url: '/pages/quiz/index' })
  }

  const doIllustrate = async (recordId: number, itemIndex: number, item: RecordItem) => {
    const key = `${recordId}_${itemIndex}`
    if (illustrating) return
    setIllustrating(key)
    Taro.showLoading({ title: '生成配图中，约 1 分钟', mask: true })
    try {
      const res = await illustrateQuestion(item.stem, item.knowledge_point || '', '')
      if (res.hint) {
        Taro.hideLoading()
        Taro.showToast({ title: res.hint, icon: 'none' })
        return
      }
      if (res.url) {
        setHistory((prev) =>
          prev.map((h) =>
            h.id === recordId
              ? { ...h, items: h.items.map((it, i) => (i === itemIndex ? { ...it, image_url: res.url } : it)) }
              : h
          )
        )
        Taro.hideLoading()
        Taro.showToast({ title: res.cached ? '已从图库取回' : '配图已生成', icon: 'none' })
      }
    } catch (e) {
      Taro.hideLoading()
      Taro.showToast({ title: (e as Error)?.message || '配图失败', icon: 'none' })
    } finally {
      setIllustrating('')
    }
  }

  const doRemoveWrong = async (id: number) => {
    try {
      await removeWrong(id)
      setWrong((prev) => prev.filter((w) => w.id !== id))
      Taro.showToast({ title: '已移除', icon: 'none' })
    } catch {
      Taro.showToast({ title: '移除失败', icon: 'none' })
    }
  }

  if (!loggedIn) {
    return (
      <View className='page'>
        <View className='bg-stars' />
        <View className='scroll'>
          <View className='empty'>
            <Mascot variant='empty' />
            <View className='empty-t'>尚未登录</View>
            <View className='empty-s'>在微信小程序端登录后，可查看答题记录与错题本</View>
          </View>
        </View>
        <TabBar active='records' />
      </View>
    )
  }

  return (
    <View className='page'>
      <View className='bg-stars' />
      <View className='scroll'>
        <View className='seg'>
          <View
            className={`seg-item ${tab === 'history' ? 'active' : ''}`}
            onClick={() => setTab('history')}
          >
            答题记录
          </View>
          <View
            className={`seg-item ${tab === 'wrong' ? 'active' : ''}`}
            onClick={() => setTab('wrong')}
          >
            错题本{wrong.length > 0 ? ` (${wrong.length})` : ''}
          </View>
        </View>

        {loading && (
          <View className='loading glass'>
            <Mascot variant='loading' />
            <View className='t'>加载中…</View>
          </View>
        )}

        {!loading && tab === 'history' &&
          (history.length === 0 ? (
            <View className='empty'>
              <Mascot variant='empty' />
              <View className='empty-t'>还没有答题记录</View>
              <View className='empty-s'>完成一次闯关后，记录会出现在这里</View>
            </View>
          ) : (
            <View className='list'>
              {history.map((h) => {
                const expanded = expandedId === h.id
                return (
                  <View key={h.id}>
                    <View
                      className='hist-item glass'
                      onClick={() => setExpandedId(expanded ? null : h.id)}
                    >
                      <View className='hist-main'>
                        <View className='hist-topic'>{h.topic || '未命名主题'}</View>
                        <View className='hist-meta'>
                          {h.created_at} · 已答 {h.answered_count}/{h.question_count} 题 · 答对 {h.correct_count} 题
                        </View>
                      </View>
                      <View className='hist-acc'>{h.accuracy}%</View>
                      <Text className='hist-arrow'>{expanded ? '▾' : '▸'}</Text>
                    </View>
                    {expanded && (
                      <View className='detail'>
                        {h.items.map((item, i) => (
                          <View key={i} className={`detail-item ${item.is_correct ? 'ok' : 'no'}`}>
                            <View className='d-head'>
                              <Text className='d-idx'>{i + 1}</Text>
                              <Text className={`d-flag ${item.is_correct ? 'ok' : 'no'}`}>
                                {item.is_correct ? '✓ 答对' : '✕ 答错'}
                              </Text>
                            </View>
                            <View className='d-stem'>{item.stem}</View>
                            {item.image_url ? (
                              <Image className='d-img' src={item.image_url} mode='widthFix' lazyLoad />
                            ) : (
                              item.type !== 'judge' && (
                                <View
                                  className='d-illustrate'
                                  onClick={() => doIllustrate(h.id, i, item)}
                                >
                                  {illustrating === `${h.id}_${i}` ? '生成中…' : '+ 为这题配图'}
                                </View>
                              )
                            )}
                            {item.options.length > 0 && (
                              <View className='d-opts'>
                                {item.options.map((opt) => {
                                  const isRight = item.answer.includes(opt.key)
                                  const isMine = item.user_answer.includes(opt.key)
                                  let cls = 'd-opt'
                                  if (isRight) cls += ' right'
                                  else if (isMine) cls += ' mine'
                                  return (
                                    <View key={opt.key} className={cls}>
                                      <Text className='d-key'>{opt.key}</Text>
                                      <Text className='d-text'>{opt.text}</Text>
                                    </View>
                                  )
                                })}
                              </View>
                            )}
                            <View className='d-ans'>
                              <Text className={`d-mine ${item.is_correct ? 'ok' : ''}`}>我的答案：{item.user_answer.join('、') || '未作答'}</Text>
                              <Text className='d-right'>正确答案：{item.answer.join('、')}</Text>
                            </View>
                            {item.explanation && (
                              <View className='d-expl'>
                                <Text className='d-label'>讲解</Text>
                                <Text className='d-text'>{item.explanation}</Text>
                              </View>
                            )}
                          </View>
                        ))}
                      </View>
                    )}
                  </View>
                )
              })}
            </View>
          ))}

        {!loading && tab === 'wrong' &&
          (wrong.length === 0 ? (
            <View className='empty'>
              <Mascot variant='celebrate' />
              <View className='empty-t'>暂无错题，太棒了！</View>
              <View className='empty-s'>答错的题会自动收进错题本</View>
            </View>
          ) : (
            <>
              <View className='retry-bar glass' onClick={retryWrong}>
                <View className='retry-main'>
                  <View className='retry-t'>错题重练</View>
                  <View className='retry-s'>把这 {Math.min(wrong.length, 10)} 道错题再来一遍</View>
                </View>
                <View className='retry-btn'>开始</View>
              </View>
              <View className='list'>
                {wrong.map((w) => (
                <View key={w.id} className='wrong-item glass'>
                  <View className='wrong-head'>
                    <Text className='wtype'>{TYPE_LABEL[w.type] || '题目'}</Text>
                    <Text className='wtopic'>{w.topic}</Text>
                  </View>
                  <View className='wstem'>{w.stem}</View>
                  <View className='wrow'>
                    <Text className='wlabel'>我的答案</Text>
                    <Text className='wval wrong-ans'>{w.user_answer.join('、') || '未作答'}</Text>
                  </View>
                  <View className='wrow'>
                    <Text className='wlabel'>正确答案</Text>
                    <Text className='wval right-ans'>{w.answer.join('、')}</Text>
                  </View>
                  {w.explanation && (
                    <View className='wexplain'>
                      <Text className='wlabel'>讲解</Text>
                      <Text className='wtext'>{w.explanation}</Text>
                    </View>
                  )}
                  <View className='wremove' onClick={() => doRemoveWrong(w.id)}>
                    移出错题本
                  </View>
                </View>
                ))}
              </View>
            </>
          ))}
      </View>
      <TabBar active='records' />
    </View>
  )
}
