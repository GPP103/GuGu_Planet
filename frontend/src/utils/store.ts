import Taro from '@tarojs/taro'
import type { Quiz, Report } from '../types'

const QUIZ_KEY = 'gugu_quiz'
const REPORT_KEY = 'gugu_report'
const TOPIC_KEY = 'gugu_topic'

export function saveQuiz(quiz: Quiz) {
  Taro.setStorageSync(QUIZ_KEY, quiz)
  Taro.setStorageSync(TOPIC_KEY, quiz.title)
}

export function getQuiz(): Quiz | null {
  try {
    return (Taro.getStorageSync(QUIZ_KEY) as Quiz) || null
  } catch {
    return null
  }
}

export function getTopic(): string {
  try {
    return (Taro.getStorageSync(TOPIC_KEY) as string) || ''
  } catch {
    return ''
  }
}

export function saveReport(report: Report) {
  Taro.setStorageSync(REPORT_KEY, report)
}

export function getReport(): Report | null {
  try {
    return (Taro.getStorageSync(REPORT_KEY) as Report) || null
  } catch {
    return null
  }
}

export function clearAll() {
  Taro.removeStorageSync(QUIZ_KEY)
  Taro.removeStorageSync(REPORT_KEY)
  Taro.removeStorageSync(TOPIC_KEY)
}

const TOKEN_KEY = 'gugu_token'

export function setToken(token: string) {
  Taro.setStorageSync(TOKEN_KEY, token)
}

export function getToken(): string {
  try {
    return (Taro.getStorageSync(TOKEN_KEY) as string) || ''
  } catch {
    return ''
  }
}

export function clearToken() {
  Taro.removeStorageSync(TOKEN_KEY)
}
