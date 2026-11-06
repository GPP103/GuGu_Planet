import { useEffect, useState } from 'react'
import Taro from '@tarojs/taro'
import { Text, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import { getQuiz, getReport } from '../../utils/store'
import type { Report } from '../../types'
import './index.scss'

export default function ReportPage() {
  const [report, setReport] = useState<Report | null>(null)
  const [total, setTotal] = useState(5)

  useEffect(() => {
    const r = getReport()
    if (r) setReport(r)
    const q = getQuiz()
    if (q) setTotal(q.questions.length || 5)
  }, [])

  if (!report) {
    return (
      <View className='page'>
        <View className='bg-stars' />
        <View className='scroll'>
          <View className='empty'>
            <Mascot variant='empty' />
            <View className='empty-t'>还没有学习报告</View>
            <View className='empty-s'>完成一次闯关，咕咕会为你生成复盘报告</View>
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

  const accuracy = report.accuracy
  const stars = Math.max(1, Math.min(total, Math.round((accuracy * total) / 100)))

  return (
    <View className='page'>
      <View className='bg-stars' />
      <View className='scroll'>
        <View className='progress'>
          <View className='back' onClick={() => Taro.redirectTo({ url: '/pages/index/index' })}>
            ‹
          </View>
          <View className='stage-t'>远征报告</View>
          <View className='coin'>
            <View className='c' />
            +50
          </View>
        </View>

        <View className='ring-wrap'>
          <View
            className='ring'
            style={{
              background: `conic-gradient(#8b83e8 0%, #f5c26b ${accuracy}%, rgba(255,255,255,0.1) ${accuracy}% 100%)`
            }}
          >
            <View className='ring-inner'>
              <View className='pct'>{accuracy}%</View>
              <View className='label'>正确率</View>
            </View>
          </View>
          <View className='celebrate'>
            <Mascot variant='celebrate' />
            <View className='msg'>咕咕为你点亮了 {stars} 颗星！</View>
          </View>
        </View>

        <View className='sum-card glass'>
          <View className='h'>三句知识总结</View>
          {report.three_line_summary.map((line, i) => (
            <View key={i} className='line'>
              <Text className='star'>✦</Text>
              {line}
            </View>
          ))}
        </View>

        <View className='sec-title'>掌握 / 薄弱</View>
        <View className='pill-row'>
          {report.mastered_points.map((p, i) => (
            <Text key={`g${i}`} className='pill good'>
              ✓ {p}
            </Text>
          ))}
          {report.weak_points.map((p, i) => (
            <Text key={`b${i}`} className='pill bad'>
              ✕ {p}
            </Text>
          ))}
        </View>

        <View className='sec-title'>复习建议</View>
        <View className='explain glass'>
          <Text className='p'>{report.advice.join(' ')}</Text>
        </View>

        <View className='quote'>
          {report.share_quote}
          <View className='q'>— 今日学习金句</View>
        </View>

        <View
          className='next'
          onClick={() => Taro.showToast({ title: '分享海报开发中', icon: 'none' })}
        >
          生成分享海报
        </View>
        <View className='home-link' onClick={() => Taro.redirectTo({ url: '/pages/records/index' })}>
          查看答题记录
        </View>
      </View>
    </View>
  )
}
