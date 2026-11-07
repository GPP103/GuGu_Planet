import { useEffect, useState } from 'react'
import Taro from '@tarojs/taro'
import { Button, Form, Input, Text, View } from '@tarojs/components'
import Mascot from '../../components/Mascot'
import TabBar from '../../components/TabBar'
import { cacheUser, ensureLogin, logout } from '../../utils/auth'
import { updateMe } from '../../utils/api'
import type { UserProfile } from '../../types'
import './index.scss'

function readFileAsBase64(filePath: string): Promise<string | null> {
  return new Promise((resolve) => {
    Taro.getFileSystemManager().readFile({
      filePath,
      encoding: 'base64',
      success: (res) => resolve(res.data as string),
      fail: () => resolve(null)
    })
  })
}

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [nickname, setNickname] = useState('')
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const u = await ensureLogin()
    if (u) {
      setUser(u)
      setNickname(u.nickname)
    }
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  const onChooseAvatar = async (e: { detail?: { avatarUrl?: string } }) => {
    const tempPath = e.detail?.avatarUrl
    if (!tempPath) return
    Taro.showLoading({ title: '保存头像…' })
    const base64 = await readFileAsBase64(tempPath)
    Taro.hideLoading()
    if (!base64) {
      Taro.showToast({ title: '头像读取失败', icon: 'none' })
      return
    }
    try {
      const updated = await updateMe({ avatar_url: `data:image/png;base64,${base64}` })
      setUser(updated)
      cacheUser(updated)
      Taro.showToast({ title: '头像已更新', icon: 'none' })
    } catch (err) {
      Taro.showToast({ title: (err as Error).message || '保存失败', icon: 'none' })
    }
  }

  // 微信 type="nickname" 回填是异步的，onBlur 会先于回填触发导致读到旧值，
  // 官方推荐用 form + submit 按钮主动收集，确保拿到最终昵称
  const onNicknameSubmit = async (e: { detail?: { value?: Record<string, string> } }) => {
    const name = (e.detail?.value?.nickname || '').trim()
    setEditing(false)
    if (!name || !user || name === user.nickname) return
    try {
      const updated = await updateMe({ nickname: name })
      setUser(updated)
      setNickname(name)
      cacheUser(updated)
      Taro.showToast({ title: '昵称已保存', icon: 'none' })
    } catch (err) {
      Taro.showToast({ title: (err as Error).message || '保存失败', icon: 'none' })
    }
  }

  const doLogout = () => {
    logout()
    setUser(null)
    Taro.showToast({ title: '已退出登录', icon: 'none' })
  }

  if (loading) {
    return (
      <View className='page'>
        <View className='bg-stars' />
        <View className='scroll'>
          <View className='loading glass'>
            <Mascot variant='loading' />
            <View className='t'>正在进入个人中心…</View>
          </View>
        </View>
        <TabBar active='me' />
      </View>
    )
  }

  if (!user) {
    const isWeapp = process.env.TARO_ENV === 'weapp'
    return (
      <View className='page'>
        <View className='bg-stars' />
        <View className='scroll'>
          <View className='empty'>
            <Mascot variant='empty' />
            <View className='empty-t'>尚未登录</View>
            <View className='empty-s'>
              {isWeapp ? '登录后可累积学习统计' : '请在微信小程序端使用登录功能'}
            </View>
            {isWeapp && (
              <View className='cta' onClick={load}>
                登录
              </View>
            )}
          </View>
        </View>
        <TabBar active='me' />
      </View>
    )
  }

  return (
    <View className='page'>
      <View className='bg-stars' />
      <View className='scroll'>
        <View className='profile-head'>
          <Button
            className='avatar-btn'
            openType='chooseAvatar'
            onChooseAvatar={onChooseAvatar}
          >
            {user.avatar_url ? (
              <View className='avatar' style={{ backgroundImage: `url(${user.avatar_url})` }} />
            ) : (
              <View className='avatar avatar-default'>G</View>
            )}
          </Button>
          <View className='nick-area'>
            {editing ? (
              <Form onSubmit={onNicknameSubmit}>
                <Input
                  className='nick-input'
                  type='nickname'
                  name='nickname'
                  defaultValue={nickname}
                  focus
                  maxlength={32}
                />
                <View className='nick-actions'>
                  <View className='nick-cancel' onClick={() => setEditing(false)}>取消</View>
                  <Button className='nick-save' formType='submit'>保存</Button>
                </View>
              </Form>
            ) : (
              <View className='nick' onClick={() => setEditing(true)}>
                {user.nickname}
                <Text className='edit-tip'>编辑</Text>
              </View>
            )}
            <View className='uid'>咕咕学员 · ID {user.id}</View>
          </View>
        </View>

        <View className='sec-title'>学习统计</View>
        <View className='stats glass'>
          <View className='stat'>
            <View className='num'>{user.total_answered}</View>
            <View className='label'>累计答题</View>
          </View>
          <View className='stat'>
            <View className='num'>{user.accuracy}%</View>
            <View className='label'>正确率</View>
          </View>
          <View className='stat'>
            <View className='num'>{user.current_streak}</View>
            <View className='label'>连续天数</View>
          </View>
        </View>

        <View className='tip glass'>
          <Text>答对 {user.total_correct} 题 / 共答 {user.total_answered} 题</Text>
        </View>

        <View className='logout' onClick={doLogout}>
          退出登录
        </View>
      </View>
      <TabBar active='me' />
    </View>
  )
}
