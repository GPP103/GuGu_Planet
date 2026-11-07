import Taro from '@tarojs/taro'
import type { AnswerRecord, HistoryItem, KnowledgeBase, Question, Quiz, Report, UserProfile, WrongItem } from '../types'
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

function unwrap<T>(body: ApiResponse<T>): T {
  if (body.code !== 0) {
    throw new Error(body.message || '请求失败')
  }
  return body.data as T
}

export function generateQuiz(userInput: string, knowledgeBaseId?: number, withImages?: boolean): Promise<Quiz> {
  return request<Quiz>('/api/v1/quiz/generate', 'POST', {
    user_input: userInput,
    question_count: 3,
    difficulty: 'mixed',
    ...(knowledgeBaseId != null ? { knowledge_base_id: knowledgeBaseId } : {}),
    ...(withImages ? { with_images: true } : {})
  })
}

export interface QuizImagesResult {
  status: 'none' | 'pending' | 'done' | 'failed'
  images: { question_id: string; image_url: string }[]
  hint: string | null
}

export function getQuizImages(quizId: string): Promise<QuizImagesResult> {
  return request<QuizImagesResult>(`/api/v1/quiz/images?quiz_id=${encodeURIComponent(quizId)}`, 'GET')
}

export interface QuestionImageResult {
  url: string | null
  cached: boolean
  hint: string | null
}

export function illustrateQuestion(stem: string, knowledgePoint: string, topic: string): Promise<QuestionImageResult> {
  return request<QuestionImageResult>('/api/v1/quiz/question-image', 'POST', {
    stem,
    knowledge_point: knowledgePoint,
    topic
  })
}

export interface PosterIllustration {
  url: string
  cached: boolean
  prompt: string
}

/** 分享海报插画（需登录） */
export function illustrate(topic: string): Promise<PosterIllustration> {
  return request<PosterIllustration>('/api/v1/illustrate', 'POST', { topic })
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

// ---------- 知识库 ----------

export function listKnowledge(): Promise<KnowledgeBase[]> {
  return request<KnowledgeBase[]>('/api/v1/knowledge/list', 'GET')
}

export function deleteKnowledge(kbId: number): Promise<null> {
  return request<null>(`/api/v1/knowledge/${kbId}`, 'DELETE')
}

export function createKnowledgeLink(url: string, name: string): Promise<KnowledgeBase> {
  return request<KnowledgeBase>('/api/v1/knowledge/link', 'POST', { url, name })
}

/** 小程序端上传（chooseMessageFile 拿到的临时路径） */
export async function uploadKnowledgeFile(filePath: string, name: string): Promise<KnowledgeBase> {
  const token = getToken()
  const res = await Taro.uploadFile({
    url: BASE_URL + '/api/v1/knowledge/upload',
    filePath,
    name: 'file',
    formData: { name },
    header: token ? { Authorization: `Bearer ${token}` } : {},
    timeout: 120000
  })
  return unwrap<KnowledgeBase>(JSON.parse(res.data) as ApiResponse<KnowledgeBase>)
}

/** H5 端上传（fetch + FormData） */
export async function uploadKnowledgeFileH5(file: File, name: string): Promise<KnowledgeBase> {
  const token = getToken()
  const form = new FormData()
  form.append('file', file)
  form.append('name', name)
  const res = await fetch(BASE_URL + '/api/v1/knowledge/upload', {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form
  })
  return unwrap<KnowledgeBase>((await res.json()) as ApiResponse<KnowledgeBase>)
}
