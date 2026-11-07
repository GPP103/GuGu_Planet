export interface Option {
  key: string
  text: string
}

export type QuestionType = 'single' | 'multiple' | 'judge'
export type Difficulty = 'easy' | 'medium' | 'hard'

export interface Question {
  id: string
  type: QuestionType
  stem: string
  options: Option[]
  answer: string[]
  explanation: string
  knowledge_point: string
  difficulty: Difficulty
}

export interface Source {
  title: string
  url: string
}

export interface Quiz {
  quiz_id: string
  title: string
  summary: string
  source_type: string
  user_input: string
  questions: Question[]
  sources: Source[]
  freshness: 'fresh' | 'stale' | 'kb'
}

export interface KnowledgeBase {
  id: number
  name: string
  source_type: string
  source_name: string
  chunk_count: number
  created_at: string
}

export interface AnswerRecord {
  question_id: string
  selected_answers: string[]
  is_correct: boolean
  duration_ms: number
}

export interface Report {
  accuracy: number
  mastered_points: string[]
  weak_points: string[]
  three_line_summary: string[]
  advice: string[]
  share_quote: string
}

export type TabKey = 'home' | 'records' | 'me'

export interface UserProfile {
  id: number
  nickname: string
  avatar_url: string | null
  total_answered: number
  total_correct: number
  current_streak: number
  accuracy: number
  xp: number
  level: number
  next_level_xp: number
}

export interface RecordItem {
  type: string
  stem: string
  options: Option[]
  answer: string[]
  user_answer: string[]
  is_correct: boolean
  explanation: string
  knowledge_point: string
}

export interface HistoryItem {
  id: number
  topic: string
  question_count: number
  answered_count: number
  correct_count: number
  accuracy: number
  created_at: string
  items: RecordItem[]
}

export interface WrongItem {
  id: number
  topic: string
  type: string
  stem: string
  options: Option[]
  answer: string[]
  explanation: string
  knowledge_point: string
  user_answer: string[]
}
