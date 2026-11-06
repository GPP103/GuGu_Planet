import { useState } from 'react'
import Taro from '@tarojs/taro'
import { Text, Textarea, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import TabBar from '../../components/TabBar'
import { generateQuiz } from '../../utils/api'
import { saveQuiz } from '../../utils/store'
import './index.scss'

const HOT_TAGS = ['RAG 入门', '英语单词', '大模型基础']

export default function Index() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [elapsed, setElapsed] = useState('0.0')
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    const text = input.trim()
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
          <View className='cta' onClick={handleGenerate}>
            <View className='rocket' />
            开始远征
          </View>
        )}

        {loading && (
          <View className='loading glass'>
            <Mascot variant='loading' />
            <View className='t'>正在生成题库…</View>
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

        <View className='sec-title'>我的关卡</View>
        <View className='level-item glass'>
          <View className='icon done' />
          <View className='meta'>
            <View className='t'>星图 · 大模型基础</View>
            <View className='s'>5 题 · 已点亮</View>
          </View>
          <Text className='arrow'>›</Text>
        </View>
        <View className='level-item glass'>
          <View className='icon' />
          <View className='meta'>
            <View className='t'>星图 · 网络原理</View>
            <View className='s'>5 题 · 待探索</View>
          </View>
          <Text className='arrow'>›</Text>
        </View>
      </View>
      <TabBar active='home' />
    </View>
  )
}
