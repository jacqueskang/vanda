export interface Agent {
  key: string
  name: string
  role: string
  avatar: string
}

export interface AgentMeta {
  key: string
  name: string
  gender: string
  role: string
  avatar_url: string
  model_name: string
}

export interface Message {
  role: 'user' | 'assistant' | 'system'
  text: string
  agentName?: string
  agentAvatar?: string
  roleType?: string
}

export interface ChatResponse {
  output: string
  agent: string
  agent_label: string
  agent_meta?: AgentMeta
  agent_avatar?: string
  tokens_estimated: number
  status: string
  role?: string
  turn?: number
}

export interface AgentResponse {
  responses: ChatResponse[]
  status: string
  agent_count: number
}
