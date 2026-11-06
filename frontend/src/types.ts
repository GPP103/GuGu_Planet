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

export interface Quiz {
  quiz_id: string
  title: string
  summary: string
  source_type: string
  user_input: string
  questions: Question[]
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

export type TabKey = 'home' | 'map' | 'me'
