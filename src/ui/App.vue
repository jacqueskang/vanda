<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import type { Agent, Message, ChatResponse, AgentResponse } from './types'

const API_BASE = ''

const agents = ref<Agent[]>([])
const messages = ref<Message[]>([])
const inputText = ref('')
const isLoading = ref(false)
const isConnected = ref(false)
const chatAreaRef = ref<HTMLElement>()

async function loadAgents() {
  try {
    const res = await fetch(`${API_BASE}/agents`)
    const data = await res.json()
    agents.value = data.agents || []
  } catch (e) {
    console.error('Failed to load agents:', e)
  }
}

async function checkConnection() {
  try {
    const res = await fetch(`${API_BASE}/health`)
    isConnected.value = res.ok
  } catch {
    isConnected.value = false
  }
  setTimeout(checkConnection, 5000)
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', text })
  inputText.value = ''
  isLoading.value = true

  const payload = { messages: messages.value }

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    const data: AgentResponse | ChatResponse = await res.json()

    if ('responses' in data) {
      for (const resp of data.responses) {
        messages.value.push({
          role: 'assistant',
          text: resp.output,
          agentName: resp.agent_label || resp.agent_meta?.name,
          agentAvatar: resp.agent_avatar || resp.agent_meta?.avatar_url,
          roleType: resp.role,
        })
      }
    } else {
      messages.value.push({
        role: 'assistant',
        text: data.output,
        agentName: data.agent_label || data.agent_meta?.name,
        agentAvatar: data.agent_avatar || data.agent_meta?.avatar_url,
        roleType: data.role,
      })
    }
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      text: `Error: ${e instanceof Error ? e.message : 'Unknown error'}`,
    })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function getRoleClass(role?: string): string {
  if (!role) return ''
  return `role-${role}`
}

onMounted(() => {
  loadAgents()
  checkConnection()
})
</script>

<template>
  <div class="status-indicator">
    <div class="status-badge">
      <span :class="['status-dot', isConnected ? 'connected' : 'disconnected']"></span>
      <span>{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
    </div>
  </div>

  <div class="main-wrapper">
    <div class="team-sidebar">
      <div class="team-header">
        <i class="fas fa-users"></i> Team
      </div>
      <div v-for="agent in agents" :key="agent.key" class="agent-item">
        <img :src="agent.avatar" :alt="agent.name" class="agent-item-avatar">
        <div class="agent-item-info">
          <span class="agent-item-name">{{ agent.name }}</span>
          <span class="agent-item-role">{{ agent.role }}</span>
        </div>
      </div>
    </div>

    <div class="chat-container">
      <div class="chat-header">
        <h1><i class="fas fa-brain"></i> Vanda Team</h1>
        <p>Chat with your expert agents • @mention to select</p>
      </div>

      <div class="chat-messages" ref="chatAreaRef">
        <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
          <div v-if="msg.role === 'assistant' && msg.agentName" class="agent-header">
            <img v-if="msg.agentAvatar" :src="msg.agentAvatar" class="agent-avatar">
            <span>{{ msg.agentName }}</span>
            <span v-if="msg.roleType" :class="['role-badge', msg.roleType]">{{ msg.roleType }}</span>
          </div>
          <div class="message-bubble" v-html="escapeHtml(msg.text).replace(/\n/g, '<br>')"></div>
        </div>

        <div v-if="isLoading" class="message assistant">
          <div class="loading">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <div class="input-section">
        <div class="input-wrapper">
          <input
            v-model="inputText"
            type="text"
            placeholder="Type @ to mention agents, then ask your question..."
            @keydown="handleKeydown"
            :disabled="isLoading"
          >
          <button @click="sendMessage" :disabled="isLoading || !inputText.trim()">
            Send
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}
</script>
