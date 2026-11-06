import Taro from '@tarojs/taro'
import type { UserProfile } from '../types'
import { getMe, login } from './api'
import { clearToken, getToken, setToken } from './store'

function isWeapp(): boolean {
  return process.env.TARO_ENV === 'weapp'
}

/**
 * 静默登录：微信小程序端用 Taro.login 换 code -> 后端换 token。
 * H5 端不登录，返回 null。
 */
export async function ensureLogin(): Promise<UserProfile | null> {
  if (!isWeapp()) return null

  if (getToken()) {
    try {
      return await getMe()
    } catch {
      clearToken()
    }
  }

  try {
    const loginRes = await Taro.login()
    if (!loginRes.code) return null
    const result = await login(loginRes.code)
    setToken(result.token)
    return result.user
  } catch {
    return null
  }
}

export function logout() {
  clearToken()
}
