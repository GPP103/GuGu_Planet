import Taro from '@tarojs/taro'
import type { AnswerRecord, Question, Quiz, Report } from '../types'

const BASE_URL = 'http://127.0.0.1:8000'

interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}

async function request<T>(path: string, method: 'GET' | 'POST', data?: unknown): Promise<T> {
  const res = await Taro.request({
    url: BASE_URL + path,
    method,
    data,
    header: { 'content-type': 'application/json' },
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
    question_count: 5,
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
