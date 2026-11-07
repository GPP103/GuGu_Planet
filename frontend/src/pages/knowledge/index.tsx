import { useEffect, useState } from 'react'
import Taro from '@tarojs/taro'
import { Input, Text, View } from '@tarojs/components'
import {
  createKnowledgeLink,
  deleteKnowledge,
  generateQuiz,
  listKnowledge,
  uploadKnowledgeFile,
  uploadKnowledgeFileH5
} from '../../utils/api'
import { ensureLogin } from '../../utils/auth'
import { getToken, saveQuiz } from '../../utils/store'
import type { KnowledgeBase } from '../../types'
import './index.scss'

const TYPE_LABEL: Record<string, string> = {
  pdf: 'PDF',
  docx: 'Word',
  txt: 'TXT',
  md: 'MD',
  link: '网页'
}

function isWeapp(): boolean {
  return process.env.TARO_ENV === 'weapp'
}

export default function Knowledge() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([])
  const [ready, setReady] = useState(false)
  const [loggedIn, setLoggedIn] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [generatingId, setGeneratingId] = useState<number | null>(null)
  const [topic, setTopic] = useState('')
  const [linkUrl, setLinkUrl] = useState('')
  const [error, setError] = useState('')

  const refresh = async () => {
    try {
      const list = await listKnowledge()
      setKbs(list || [])
    } catch (e) {
      setError((e as Error)?.message || '加载失败')
    }
  }

  useEffect(() => {
    ;(async () => {
      if (!isWeapp()) {
        setReady(true)
        setLoggedIn(!!getToken())
        return
      }
      try {
        const user = await ensureLogin()
        setLoggedIn(!!user)
        if (user) await refresh()
      } catch {
        setLoggedIn(false)
      } finally {
        setReady(true)
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleUpload = async () => {
    setError('')
    if (!isWeapp()) {
      // H5：动态创建 input[type=file]
      const el = document.createElement('input')
      el.type = 'file'
      el.accept = '.pdf,.docx,.txt,.md'
      el.onchange = async () => {
        const file = el.files && el.files[0]
        if (!file) return
        setUploading(true)
        try {
          await uploadKnowledgeFileH5(file, file.name.replace(/\.[^.]+$/, ''))
          await refresh()
          Taro.showToast({ title: '上传成功', icon: 'success' })
        } catch (e) {
          setError((e as Error)?.message || '上传失败')
        } finally {
          setUploading(false)
        }
      }
      el.click()
      return
    }
    try {
      const res = await Taro.chooseMessageFile({ count: 1, type: 'file' })
      const file = res.tempFiles && res.tempFiles[0]
      if (!file) return
      setUploading(true)
      try {
        await uploadKnowledgeFile(file.path, file.name.replace(/\.[^.]+$/, ''))
        await refresh()
        Taro.showToast({ title: '上传成功', icon: 'success' })
      } catch (e) {
        setError((e as Error)?.message || '上传失败')
      } finally {
        setUploading(false)
      }
    } catch {
      /* 用户取消选择 */
    }
  }

  const handleLink = async () => {
    const url = linkUrl.trim()
    if (!url) {
      setError('先输入网页链接')
      return
    }
    setError('')
    setUploading(true)
    try {
      await createKnowledgeLink(url, '')
      setLinkUrl('')
      await refresh()
      Taro.showToast({ title: '已入库', icon: 'success' })
    } catch (e) {
      setError((e as Error)?.message || '链接入库失败')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (kb: KnowledgeBase) => {
    const res = await Taro.showModal({ title: '删除知识库', content: `确定删除「${kb.name}」？` })
    if (!res.confirm) return
    try {
      await deleteKnowledge(kb.id)
      await refresh()
    } catch (e) {
      setError((e as Error)?.message || '删除失败')
    }
  }

  const handleGenerate = async (kb: KnowledgeBase) => {
    const input = topic.trim() || kb.name
    setError('')
    setGeneratingId(kb.id)
    try {
      const quiz = await generateQuiz(input, kb.id)
      saveQuiz(quiz)
      Taro.redirectTo({ url: '/pages/quiz/index' })
    } catch (e) {
      setError((e as Error)?.message || '出题失败')
      setGeneratingId(null)
    }
  }

  return (
    <View className='page'>
      <View className='bg-stars' />
      <View className='scroll'>
        <View className='progress'>
          <View className='back' onClick={() => Taro.redirectTo({ url: '/pages/index/index' })}>
            ‹
          </View>
          <View className='stage-t'>知识库</View>
        </View>

        {ready && !loggedIn && (
          <View className='empty glass'>
            <View className='t'>登录后可使用知识库</View>
            <View className='s'>{isWeapp() ? '请重新进入小程序尝试登录' : '请在微信小程序端使用知识库功能'}</View>
          </View>
        )}

        {loggedIn && (
          <>
            <View className='upload-card glass'>
              <View className='u-title'>上传文档建库</View>
              <View className='u-tip'>支持 PDF / Word / TXT / MD，不超过 5MB</View>
              <View
                className={`u-btn ${uploading ? 'disabled' : ''}`}
                onClick={() => !uploading && handleUpload()}
              >
                {uploading ? '正在入库…' : '选择文档上传'}
              </View>
            </View>

            <View className='upload-card glass'>
              <View className='u-title'>网页链接入库</View>
              <Input
                className='u-input'
                value={linkUrl}
                placeholder='粘贴网页链接'
                placeholderClass='placeholder'
                onInput={(e) => setLinkUrl(e.detail.value)}
              />
              <View
                className={`u-btn ghost ${uploading ? 'disabled' : ''}`}
                onClick={() => !uploading && handleLink()}
              >
                抓取正文入库
              </View>
            </View>

            <View className='sec-title'>我的知识库（{kbs.length}）</View>

            {kbs.length === 0 && (
              <View className='empty glass'>
                <View className='t'>还没有知识库</View>
                <View className='s'>上传文档后，即可基于自己的资料出题</View>
              </View>
            )}

            {kbs.map((kb) => (
              <View key={kb.id} className='kb-item glass'>
                <View className='kb-head'>
                  <View className='kb-name'>{kb.name}</View>
                  <Text className='kb-type'>{TYPE_LABEL[kb.source_type] || kb.source_type}</Text>
                </View>
                <View className='kb-meta'>
                  {kb.chunk_count} 个片段 · {kb.created_at?.slice(0, 10)}
                </View>
                <View className='kb-actions'>
                  <View className='kb-del' onClick={() => handleDelete(kb)}>
                    删除
                  </View>
                  <View
                    className={`kb-gen ${generatingId === kb.id ? 'disabled' : ''}`}
                    onClick={() => generatingId !== kb.id && handleGenerate(kb)}
                  >
                    {generatingId === kb.id ? '出题中…' : '出题'}
                  </View>
                </View>
              </View>
            ))}

            {kbs.length > 0 && (
              <View className='topic-card glass'>
                <View className='u-title'>出题方向（可选）</View>
                <Input
                  className='u-input'
                  value={topic}
                  placeholder='想重点考察什么？默认按文档名出题'
                  placeholderClass='placeholder'
                  onInput={(e) => setTopic(e.detail.value)}
                />
              </View>
            )}
          </>
        )}

        {error && (
          <View className='error-tip'>{error}</View>
        )}
      </View>
    </View>
  )
}
