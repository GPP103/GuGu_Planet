import Taro from '@tarojs/taro'
import type { AnswerRecord, HistoryItem, Question, Quiz, Report, UserProfile, WrongItem } from '../types'
import { getToken } from './store'

const BASE_URL = 'http://127.0.0.1:8000'

interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}

async function request<T>(path: string, method: 'GET' | 'POST' | 'PUT' | 'DELETE', data?: unknown): Promise<T> {
  const token = getToken()
  const header: Record<string, string> = { 'content-type': 'application/json' }
  if (token) header['Authorization'] = `Bearer ${token}`
  const res = await Taro.request({
    url: BASE_URL + path,
    method,
    data,
    header,
    timeout: 60000
  })
  const body = res.data as ApiResponse<T>
  if (body.code !== 0) {
    throw new Error(body.message || '请求失败')
  }
  return body.data as T
}

export function generateQuiz(userInput: string): Promise<Quiz> {
  return request<Quiz>('/api/v1/quiz/generate', 'POST', {
    user_input: userInput,
    question_count: 3,
    difficulty: 'mixed'
  })
}

export function generateReport(
  quizId: string,
  topic: string,
  questions: Question[],
  answerRecords: AnswerRecord[]
): Promise<Report> {
  return request<Report>('/api/v1/report/generate', 'POST', {
    quiz_id: quizId,
    topic,
    questions,
    answer_records: answerRecords
  })
}

export interface LoginResult {
  token: string
  user: UserProfile
}

export function login(code: string): Promise<LoginResult> {
  return request<LoginResult>('/api/v1/auth/login', 'POST', { code })
}

export function getMe(): Promise<UserProfile> {
  return request<UserProfile>('/api/v1/users/me', 'GET')
}

export function updateMe(payload: { nickname?: string; avatar_url?: string }): Promise<UserProfile> {
  return request<UserProfile>('/api/v1/users/me', 'PUT', payload)
}

export interface StudyRecordResult {
  total_answered: number
  total_correct: number
  current_streak: number
  accuracy: number
}

export function submitStudyRecord(answered: number, correct: number): Promise<StudyRecordResult> {
  return request<StudyRecordResult>('/api/v1/users/study-record', 'POST', { answered, correct })
}

export function submitRecord(topic: string, questions: Question[], records: AnswerRecord[]): Promise<StudyRecordResult> {
  return request<StudyRecordResult>('/api/v1/records/submit', 'POST', { topic, questions, records })
}

export function getHistory(): Promise<HistoryItem[]> {
  return request<HistoryItem[]>('/api/v1/records/history', 'GET')
}

export function getWrongList(): Promise<WrongItem[]> {
  return request<WrongItem[]>('/api/v1/records/wrong', 'GET')
}

export function removeWrong(wrongId: number): Promise<null> {
  return request<null>(`/api/v1/records/wrong/${wrongId}`, 'DELETE')
}
