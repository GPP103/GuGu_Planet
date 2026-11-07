import Taro from '@tarojs/taro'
import type { UserProfile } from '../types'
import { getMe, login } from './api'
import { clearToken, getToken, setToken } from './store'

function isWeapp(): boolean {
  return process.env.TARO_ENV === 'weapp'
}

// 内存缓存：登录成功后缓存 user，避免每次 ensureLogin 都重新 getMe
let cachedUser: UserProfile | null = null

export function cacheUser(u: UserProfile | null) {
  cachedUser = u
}

/**
 * 静默登录：微信小程序端用 Taro.login 换 code -> 后端换 token。
 * H5 端不登录，返回 null。
 */
export async function ensureLogin(): Promise<UserProfile | null> {
  if (!isWeapp()) return null

  if (cachedUser) return cachedUser

  if (getToken()) {
    try {
      cachedUser = await getMe()
      return cachedUser
    } catch {
      clearToken()
    }
  }

  try {
    const loginRes = await Taro.login()
    if (!loginRes.code) return null
    const result = await login(loginRes.code)
    setToken(result.token)
    cachedUser = result.user
    return result.user
  } catch {
    return null
  }
}

export function logout() {
  clearToken()
  cachedUser = null
}
