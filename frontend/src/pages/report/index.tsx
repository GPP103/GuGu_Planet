import { useEffect, useState } from 'react'
import Taro from '@tarojs/taro'
import { Canvas, Image, Text, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import { illustrate } from '../../utils/api'
import { ensureLogin } from '../../utils/auth'
import { getQuiz, getReport } from '../../utils/store'
import type { Report } from '../../types'
import './index.scss'

const isWeapp = process.env.TARO_ENV === 'weapp'

function wrapText(ctx: any, text: string, x: number, y: number, maxWidth: number, lineHeight: number, maxLines: number) {
  const chars = Array.from(text || '')
  let line = ''
  let row = 0
  for (let i = 0; i < chars.length; i += 1) {
    const test = line + chars[i]
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, y + row * lineHeight)
      row += 1
      line = chars[i]
      if (row >= maxLines) {
        return y + row * lineHeight
      }
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
  const [posterUrl, setPosterUrl] = useState('')
  const [posterLoading, setPosterLoading] = useState(false)
  const [posterHint, setPosterHint] = useState('')
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

  const openPoster = async () => {
    setPosterOpen(true)
    setPosterHint('')
    if (posterUrl) return
    setPosterLoading(true)
    try {
      await ensureLogin().catch(() => null)
      const res = await illustrate(topic || '学习')
      setPosterUrl(res.url)
    } catch (e) {
      setPosterHint((e as Error)?.message || '插画生成失败，可先保存文字海报')
    } finally {
      setPosterLoading(false)
    }
  }

  const savePoster = () => {
    if (saving) return
    if (!isWeapp) {
      Taro.showToast({ title: '请在微信小程序端保存海报', icon: 'none' })
      return
    }
    setSaving(true)
    const W = Taro.getSystemInfoSync().windowWidth
    const H = Math.round(W * 1.62)
    const ctx = Taro.createCanvasContext('posterCanvas')
    const pad = 18
    const imgSize = W - pad * 2

    ctx.setFillStyle('#0b0a1f')
    ctx.fillRect(0, 0, W, H)

    ctx.setFillStyle('#ffe3a3')
    ctx.setFontSize(13)
    ctx.fillText('咕咕星球 GuGu', pad, 30)

    let y = 44
    if (posterUrl) {
      try {
        ctx.drawImage(posterUrl, pad, y, imgSize, imgSize)
      } catch {
        /* 图片加载失败则跳过 */
      }
      y += imgSize + 34
    } else {
      y += 10
    }

    ctx.setFillStyle('#f5c26b')
    ctx.setFontSize(34)
    ctx.fillText(`${accuracy}%`, pad, y + 26)
    ctx.setFillStyle('#c9c3e8')
    ctx.setFontSize(12)
    ctx.fillText('本次闯关正确率', pad + 78, y + 24)

    y += 46
    ctx.setFillStyle('#f7f5ff')
    ctx.setFontSize(13)
    y = wrapText(ctx, topic || '学习', pad, y + 8, W - pad * 2, 19, 1)

    y += 12
    ctx.setFillStyle('#c9c3e8')
    ctx.setFontSize(12)
    report.three_line_summary.slice(0, 3).forEach((line) => {
      y = wrapText(ctx, `· ${line}`, pad, y + 8, W - pad * 2, 18, 2) + 4
    })

    y += 6
    ctx.setFillStyle('#ffe3a3')
    ctx.setFontSize(12)
    y = wrapText(ctx, `「${report.share_quote}」`, pad, y + 8, W - pad * 2, 18, 2)

    // 底部品牌条 + 小程序码占位
    const boxY = H - 76
    ctx.setFillStyle('rgba(255,255,255,0.06)')
    ctx.fillRect(pad, boxY, W - pad * 2, 56)
    ctx.setFillStyle('#9a93bd')
    ctx.setFontSize(11)
    ctx.fillText('咕咕带你点亮知识', pad + 12, boxY + 24)
    ctx.setFontSize(10)
    ctx.fillText('长按识别小程序码 · 一起闯关', pad + 12, boxY + 42)
    ctx.setFillStyle('rgba(255,255,255,0.12)')
    ctx.fillRect(W - pad - 56, boxY + 8, 40, 40)

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

        <View className='next' onClick={openPoster}>
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
              <Text className='ph-brand'>咕咕星球 GuGu</Text>
              <Text className='ph-close' onClick={() => setPosterOpen(false)}>
                ✕
              </Text>
            </View>

            {posterLoading && (
              <View className='poster-loading'>
                <Mascot variant='loading' />
                <View className='pl-t'>咕咕正在画插画…</View>
                <View className='pl-s'>首次生成约 1 分钟，之后秒出</View>
              </View>
            )}

            {!posterLoading && (
              <>
                {posterUrl ? (
                  <Image className='poster-img' src={posterUrl} mode='widthFix' />
                ) : (
                  <View className='poster-img placeholder-img'>
                    <Text>插画未生成</Text>
                  </View>
                )}
                <View className='poster-body'>
                  <View className='pb-row'>
                    <Text className='pb-pct'>{accuracy}%</Text>
                    <Text className='pb-label'>本次闯关正确率</Text>
                  </View>
                  <View className='pb-topic'>{topic || '学习'}</View>
                  <View className='pb-lines'>
                    {report.three_line_summary.slice(0, 3).map((l, i) => (
                      <View key={i} className='pb-line'>
                        · {l}
                      </View>
                    ))}
                  </View>
                  <View className='pb-quote'>「{report.share_quote}」</View>
                  <View className='pb-foot'>
                    <Text>咕咕带你点亮知识</Text>
                    <View className='qr' />
                  </View>
                </View>
              </>
            )}

            {posterHint && <View className='poster-hint'>{posterHint}</View>}

            <View className='poster-actions'>
              <View
                className={`pa-btn ghost ${posterLoading ? 'disabled' : ''}`}
                onClick={() => setPosterOpen(false)}
              >
                关闭
              </View>
              <View
                className={`pa-btn ${posterLoading || saving ? 'disabled' : ''}`}
                onClick={() => !posterLoading && !saving && savePoster()}
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
