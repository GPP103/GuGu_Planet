import { useEffect, useState } from 'react'
import Taro from '@tarojs/taro'
import { Canvas, Text, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import { getQuiz, getReport } from '../../utils/store'
import type { Report } from '../../types'
import './index.scss'

const isWeapp = process.env.TARO_ENV === 'weapp'

/** canvas 文字自动换行，返回下一行 y 坐标 */
function wrapText(
  ctx: any,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines: number
) {
  const chars = Array.from(text || '')
  let line = ''
  let row = 0
  for (let i = 0; i < chars.length; i += 1) {
    const test = line + chars[i]
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, y + row * lineHeight)
      row += 1
      line = chars[i]
      if (row >= maxLines) return y + row * lineHeight
    } else {
      line = test
    }
  }
  if (line && row < maxLines) {
    ctx.fillText(line, x, y + row * lineHeight)
    row += 1
  }
  return y + row * lineHeight
}

export default function ReportPage() {
  const [report, setReport] = useState<Report | null>(null)
  const [total, setTotal] = useState(5)
  const [topic, setTopic] = useState('')
  const [posterOpen, setPosterOpen] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const r = getReport()
    if (r) setReport(r)
    const q = getQuiz()
    if (q) {
      setTotal(q.questions.length || 5)
      setTopic(q.title || q.user_input || '')
    }
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

  const savePoster = () => {
    if (saving) return
    if (!isWeapp) {
      Taro.showToast({ title: '请在微信小程序端保存海报', icon: 'none' })
      return
    }
    setSaving(true)
    const W = Taro.getSystemInfoSync().windowWidth
    const H = Math.round(W * 1.5)
    const ctx = Taro.createCanvasContext('posterCanvas')
    const pad = 20

    // 背景渐变
    const grd = ctx.createLinearGradient(0, 0, 0, H)
    grd.addColorStop(0, '#1a1440')
    grd.addColorStop(0.55, '#0f0c28')
    grd.addColorStop(1, '#08081f')
    ctx.setFillStyle(grd)
    ctx.fillRect(0, 0, W, H)

    // 星点装饰（固定位置，保证每次一致）
    const seed = [0.12, 0.31, 0.47, 0.63, 0.78, 0.9, 0.22, 0.42, 0.58, 0.71, 0.85, 0.05]
    ctx.setFillStyle('rgba(255,255,255,0.5)')
    seed.forEach((sx, i) => {
      const sy = 0.06 + i * 0.035
      ctx.beginPath()
      ctx.arc(sx * W, sy * H, i % 3 === 0 ? 1.4 : 0.9, 0, Math.PI * 2)
      ctx.fill()
    })

    // 品牌
    ctx.setFillStyle('#ffe3a3')
    ctx.setFontSize(12)
    ctx.fillText('咕咕星球 GuGu', pad, 34)
    ctx.setFillStyle('#9a93bd')
    ctx.setFontSize(10)
    ctx.fillText('远征报告', pad, 52)

    // 正确率圆环
    const cx = W / 2
    const cy = 170
    const r = 56
    ctx.setLineWidth(10)
    ctx.setStrokeStyle('rgba(255,255,255,0.12)')
    ctx.beginPath()
    ctx.arc(cx, cy, r, 0, Math.PI * 2)
    ctx.stroke()
    ctx.setStrokeStyle('#f5c26b')
    ctx.beginPath()
    ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + (Math.PI * 2 * accuracy) / 100)
    ctx.stroke()

    ctx.setTextAlign('center')
    ctx.setFillStyle('#f5c26b')
    ctx.setFontSize(30)
    ctx.fillText(`${accuracy}%`, cx, cy + 8)
    ctx.setFillStyle('#9a93bd')
    ctx.setFontSize(10)
    ctx.fillText('正确率', cx, cy + 26)

    ctx.setFillStyle('#c9c3e8')
    ctx.setFontSize(11)
    ctx.fillText(`咕咕为你点亮了 ${stars} 颗星`, cx, cy + 92)
    ctx.setTextAlign('left')

    // 主题
    let y = cy + 126
    ctx.setFillStyle('#f7f5ff')
    ctx.setFontSize(14)
    y = wrapText(ctx, topic || '学习', pad, y, W - pad * 2, 20, 1)

    // 三句总结
    y += 18
    ctx.setFillStyle('#ffe3a3')
    ctx.setFontSize(11)
    ctx.fillText('三句知识总结', pad, y)
    y += 18
    ctx.setFillStyle('#c9c3e8')
    ctx.setFontSize(11)
    report.three_line_summary.slice(0, 3).forEach((line) => {
      y = wrapText(ctx, `· ${line}`, pad, y, W - pad * 2, 17, 2) + 4
    })

    // 金句
    y += 12
    ctx.setFillStyle('#ffe3a3')
    ctx.setFontSize(11)
    y = wrapText(ctx, `「${report.share_quote}」`, pad, y, W - pad * 2, 17, 2)

    // 底部品牌条
    const boxY = H - 64
    ctx.setFillStyle('rgba(255,255,255,0.06)')
    ctx.fillRect(pad, boxY, W - pad * 2, 44)
    ctx.setFillStyle('#c9c3e8')
    ctx.setFontSize(10)
    ctx.fillText('咕咕带你点亮知识', pad + 12, boxY + 20)
    ctx.setFillStyle('#9a93bd')
    ctx.setFontSize(9)
    ctx.fillText('万物皆可闯关 · 在星海里点亮知识', pad + 12, boxY + 34)

    ctx.draw(false, () => {
      setTimeout(() => {
        Taro.canvasToTempFilePath({
          canvasId: 'posterCanvas',
          success: (res) => {
            Taro.saveImageToPhotosAlbum({ filePath: res.tempFilePath })
              .then(() => {
                setSaving(false)
                Taro.showToast({ title: '已保存到相册', icon: 'success' })
              })
              .catch((err) => {
                setSaving(false)
                const msg = String((err as any)?.errMsg || '')
                if (msg.includes('auth') || msg.includes('deny')) {
                  Taro.showModal({
                    title: '需要相册权限',
                    content: '请在设置中允许保存到相册，然后重试',
                    confirmText: '去设置',
                    success: (m) => {
                      if (m.confirm) Taro.openSetting()
                    }
                  })
                } else {
                  Taro.showToast({ title: '保存失败，请重试', icon: 'none' })
                }
              })
          },
          fail: () => {
            setSaving(false)
            Taro.showToast({ title: '海报生成失败，请重试', icon: 'none' })
          }
        })
      }, 200)
    })
  }

  return (
    <View className='page'>
      <View className='bg-stars' />
      <View className='scroll'>
        <View className='progress'>
          <View className='back' onClick={() => Taro.redirectTo({ url: '/pages/index/index' })}>
            ‹
          </View>
          <View className='stage-t'>远征报告</View>
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

        <View className='quote'>
          {report.share_quote}
          <View className='q'>— 今日学习金句</View>
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

        <View className='next' onClick={() => setPosterOpen(true)}>
          生成分享海报
        </View>
        <View className='home-link' onClick={() => Taro.redirectTo({ url: '/pages/records/index' })}>
          查看答题记录
        </View>
      </View>

      {posterOpen && (
        <View className='poster-mask'>
          <View className='poster-card'>
            <View className='poster-head'>
              <Text className='ph-brand'>咕咕星球 GuGu · 远征报告</Text>
              <Text className='ph-close' onClick={() => setPosterOpen(false)}>
                ✕
              </Text>
            </View>

            <View className='poster-preview'>
              <View className='pv-brand'>咕咕星球 GuGu</View>
              <View className='pv-ring'>
                <View className='pv-pct'>{accuracy}%</View>
                <View className='pv-label'>正确率</View>
              </View>
              <View className='pv-stars'>咕咕为你点亮了 {stars} 颗星</View>
              <View className='pv-topic'>{topic || '学习'}</View>
              <View className='pv-lines'>
                {report.three_line_summary.slice(0, 3).map((l, i) => (
                  <View key={i} className='pv-line'>
                    · {l}
                  </View>
                ))}
              </View>
              <View className='pv-quote'>「{report.share_quote}」</View>
              <View className='pv-foot'>
                <Text>咕咕带你点亮知识</Text>
                <Text className='pv-foot-s'>万物皆可闯关</Text>
              </View>
            </View>

            <View className='poster-actions'>
              <View className='pa-btn ghost' onClick={() => setPosterOpen(false)}>
                关闭
              </View>
              <View
                className={`pa-btn ${saving ? 'disabled' : ''}`}
                onClick={() => !saving && savePoster()}
              >
                {saving ? '保存中…' : '保存到相册'}
              </View>
            </View>
          </View>
        </View>
      )}

      {isWeapp && (
        <View className='canvas-holder'>
          <Canvas canvasId='posterCanvas' id='posterCanvas' className='poster-canvas' />
        </View>
      )}
    </View>
  )
}
