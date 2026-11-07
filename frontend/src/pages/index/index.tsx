import { useEffect, useState } from 'react'
import Taro from '@tarojs/taro'
import { Text, Textarea, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import TabBar from '../../components/TabBar'
import { generateQuiz, getHistory, getWrongList } from '../../utils/api'
import { ensureLogin } from '../../utils/auth'
import { saveQuiz } from '../../utils/store'
import './index.scss'

const HOT_TAGS = ['RAG 入门', '英语单词', '大模型基础']

// 学习提醒依赖微信登录，仅小程序端展示；H5 保持原有功能不变
const isWeapp = process.env.TARO_ENV === 'weapp'

interface Tip {
  text: string
  action: string
  type: 'wrong' | 'start' | 'again'
}

export default function Index() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [elapsed, setElapsed] = useState('0.0')
  const [error, setError] = useState('')
  const [tip, setTip] = useState<Tip | null>(null)

  useEffect(() => {
    ;(async () => {
      if (!isWeapp) return
      const user = await ensureLogin().catch(() => null)
      if (!user) return
      try {
        const [wrong, history] = await Promise.all([getWrongList(), getHistory()])
        const d = new Date()
        const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
          d.getDate()
        ).padStart(2, '0')}`
        const todayCount = (history || []).filter((h) => (h.created_at || '').startsWith(today)).length
        if ((wrong || []).length > 0) {
          setTip({ text: `你有 ${wrong.length} 道错题待重练`, action: '去重练', type: 'wrong' })
        } else if (todayCount === 0) {
          setTip({ text: '今天还没闯关，3 题热身一下', action: '开始', type: 'start' })
        } else {
          setTip({ text: `今天已完成 ${todayCount} 次闯关，保持节奏`, action: '再来一组', type: 'again' })
        }
      } catch {
        setTip(null)
      }
    })()
  }, [])

  const onTipAction = () => {
    if (!tip) return
    if (tip.type === 'wrong') {
      Taro.navigateTo({ url: '/pages/records/index?tab=wrong' })
      return
    }
    const topic = HOT_TAGS[Math.floor(Math.random() * HOT_TAGS.length)]
    setInput(topic)
    handleGenerate(topic)
  }

  const handleGenerate = async (preset?: string) => {
    const text = (preset ?? input).trim()
    if (!text) {
      setError('先输入想学的知识，再开始远征')
      return
    }
    setError('')
    setLoading(true)
    const start = Date.now()
    const timer = setInterval(() => {
      setElapsed(((Date.now() - start) / 1000).toFixed(1))
    }, 100)
    try {
      const quiz = await generateQuiz(text)
      saveQuiz(quiz)
      clearInterval(timer)
      Taro.redirectTo({ url: '/pages/quiz/index' })
    } catch (e) {
      clearInterval(timer)
      setLoading(false)
      setError((e as Error)?.message || '题库生成失败，请稍后重试')
    }
  }

  return (
    <View className='page'>
      <View className='bg-stars' />
      <View className='scroll'>
        <View className='hero'>
          <Mascot variant='hero' />
          <View className='hero-text'>
            <View className='slogan'>
              <View>万物皆可闯关，</View>
              <View>在星海里<Text className='em'>点亮知识</Text></View>
            </View>
          </View>
        </View>

        <View className='input-card glass'>
          <Textarea
            className='textarea'
            value={input}
            placeholder='输入想学内容，AI生成闯关题库'
            placeholderClass='placeholder'
            onInput={(e) => setInput(e.detail.value)}
            maxlength={2000}
          />
        </View>

        <View className='sec-title'>热门主题</View>
        <View className='tags'>
          {HOT_TAGS.map((t) => (
            <Text
              key={t}
              className='tag'
              onClick={() => {
                setInput(t)
                setError('')
              }}
            >
              {t}
            </Text>
          ))}
        </View>

        {!loading && (
          <View className='cta' onClick={() => handleGenerate()}>
            <View className='rocket' />
            开始远征
          </View>
        )}

        {loading && (
          <View className='loading glass'>
            <Mascot variant='loading' />
            <View className='t'>正在联网检索最新资料…</View>
            <View className='elapsed'>耗时 {elapsed}s</View>
          </View>
        )}

        {error && (
          <View className='empty'>
            <Mascot variant='empty' />
            <View className='t'>生成失败</View>
            <View className='s'>{error}</View>
          </View>
        )}

        {isWeapp && tip && (
          <View className='tip-bar glass'>
            <View className='tip-text'>{tip.text}</View>
            <View className='tip-btn' onClick={onTipAction}>
              {tip.action}
            </View>
          </View>
        )}
      </View>
      <TabBar active='home' />
    </View>
  )
}
