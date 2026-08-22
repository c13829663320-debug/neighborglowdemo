<template>
  <div class="page">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">&larr; 返回</button>
      <h1>模拟训练</h1>
      <span class="header-spacer"></span>
    </header>

    <!-- Pre-simulation setup -->
    <main v-if="phase === 'setup'" class="setup-phase">
      <div class="setup-card">
        <div class="setup-icon">&#x1F3AD;</div>
        <h2>选择对方风格</h2>
        <p class="setup-hint">不同风格的邻居会带来不同的沟通挑战，选择你想练习的类型。</p>

        <div class="style-options">
          <label
            v-for="opt in styleOptions"
            :key="opt.value"
            class="style-option"
            :class="{ active: selectedStyle === opt.value }"
          >
            <input type="radio" :value="opt.value" v-model="selectedStyle" />
            <div class="style-content">
              <span class="style-label">{{ opt.label }}</span>
              <span class="style-desc">{{ opt.desc }}</span>
            </div>
            <span class="radio-dot"></span>
          </label>
        </div>

        <button
          class="btn-primary"
          :disabled="loading"
          @click="startSimulation"
        >
          {{ loading ? '正在准备...' : '开始模拟' }}
        </button>
      </div>
    </main>

    <!-- Chat interface -->
    <main v-else-if="phase === 'chat'" class="chat-phase">
      <div class="chat-area" ref="chatArea">
        <div
          v-for="(msg, idx) in conversation"
          :key="idx"
          class="msg-row"
          :class="msg.role === 'user' ? 'msg-right' : 'msg-left'"
        >
          <div v-if="msg.role !== 'user'" class="avatar neighbor-avatar">&#x1F9D1;&#x200D;&#x1F91D;&#x200D;&#x1F9D1;</div>
          <div class="bubble" :class="msg.role === 'user' ? 'bubble-user' : 'bubble-neighbor'">
            {{ msg.content }}
          </div>
          <div v-if="msg.role === 'user'" class="avatar user-avatar">&#x1F60A;</div>
        </div>

        <div v-if="sending" class="msg-row msg-left">
          <div class="avatar neighbor-avatar">&#x1F9D1;&#x200D;&#x1F91D;&#x200D;&#x1F9D1;</div>
          <div class="bubble bubble-neighbor typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <div v-if="currentTip" class="coach-tip">
        <span class="coach-tip-icon">&#x1F4A1;</span>
        <span class="coach-tip-text">{{ currentTip }}</span>
      </div>

      <div class="input-bar">
        <input
          v-model="inputText"
          @keyup.enter="sendMessage"
          :disabled="sending"
          placeholder="输入你想说的话..."
          class="chat-input"
        />
        <button
          class="btn-send"
          :disabled="!inputText.trim() || sending"
          @click="sendMessage"
        >
          发送
        </button>
      </div>

      <div v-if="userMsgCount >= 6" class="end-bar">
        <button class="btn-end" @click="endSimulation">结束模拟</button>
      </div>
    </main>

    <!-- Post-simulation results -->
    <main v-else-if="phase === 'result'" class="result-phase">
      <div class="result-card">
        <h2>模拟结果</h2>

        <div class="score-ring-wrap">
          <svg class="score-ring" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" class="score-track" />
            <circle
              cx="60" cy="60" r="52"
              class="score-fill"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="circumference - (circumference * score) / 100"
            />
          </svg>
          <div class="score-value">{{ score }}</div>
        </div>
        <p class="score-label">沟通评分</p>

        <div v-if="feedbackList.length" class="feedback-section">
          <h3>教练反馈</h3>
          <ul class="feedback-list">
            <li v-for="(fb, idx) in feedbackList" :key="idx" class="feedback-item">
              <span class="fb-icon">{{ fb.type === 'positive' ? '&#x2705;' : '&#x1F4CC;' }}</span>
              <span>{{ fb.text }}</span>
            </li>
          </ul>
        </div>

        <div class="result-actions">
          <button class="btn-primary" @click="restart">重新开始</button>
          <button class="btn-secondary" @click="$router.push(`/resident/cases/${caseId}`)">
            返回案例 &rarr;
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { cases as casesApi } from '../../api'

const route = useRoute()
const caseId = route.params.id

const phase = ref('setup') // setup | chat | result

// Style options
const styleOptions = [
  { value: 'friendly', label: '友善型邻居', desc: '态度温和，愿意沟通' },
  { value: 'defensive', label: '防御型邻居', desc: '容易辩解，不太配合' },
  { value: 'avoidant', label: '回避型邻居', desc: '不太想谈，想尽快结束' },
]
const selectedStyle = ref('friendly')
const loading = ref(false)

// Chat state
const simId = ref(null)
const conversation = ref([])
const inputText = ref('')
const sending = ref(false)
const currentTip = ref('')
const chatArea = ref(null)

// Result state
const score = ref(0)
const feedbackList = ref([])

// Computed
const circumference = 2 * Math.PI * 52 // ~326.73
const userMsgCount = computed(() => conversation.value.filter(m => m.role === 'user').length)

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

async function startSimulation() {
  loading.value = true
  try {
    const res = await casesApi.startSimulation(caseId, {
      role: 'resident',
      counterpart_style: selectedStyle.value,
    })
    const data = res.data
    simId.value = data.id
    conversation.value = data.conversation || []
    currentTip.value = ''
    phase.value = 'chat'
    scrollToBottom()
  } catch (e) {
    console.error('Failed to start simulation', e)
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  inputText.value = ''
  sending.value = true
  currentTip.value = ''

  // Optimistically append user message
  conversation.value.push({ role: 'user', content: text })
  scrollToBottom()

  try {
    const res = await casesApi.sendSimMessage(caseId, simId.value, { content: text })
    const data = res.data
    // Replace conversation with server version (includes neighbor reply)
    conversation.value = data.conversation || conversation.value

    // Extract coach tip from the last neighbor message
    const lastNeighbor = [...(data.conversation || [])].reverse().find(m => m.role === 'neighbor')
    if (lastNeighbor && lastNeighbor.coach_tip) {
      currentTip.value = lastNeighbor.coach_tip
    }

    scrollToBottom()
  } catch (e) {
    console.error('Failed to send message', e)
  } finally {
    sending.value = false
  }
}

function endSimulation() {
  // Use the latest score/feedback from the simulation data
  // The feedback may already be in the last API response
  phase.value = 'result'
}

function restart() {
  phase.value = 'setup'
  conversation.value = []
  simId.value = null
  currentTip.value = ''
  inputText.value = ''
  score.value = 0
  feedbackList.value = []
}

// When we transition to result phase, try to extract score & feedback
// We watch phase changes to result
import { watch } from 'vue'
watch(phase, async (val) => {
  if (val === 'result') {
    // Send a final "end" signal by checking if the API has feedback data
    // The score/feedback should be extracted from the last sendSimMessage response
    // We store them during sendMessage; if not available, show defaults
    if (!score.value) {
      // Attempt to get final state by sending an empty end signal
      try {
        const res = await casesApi.sendSimMessage(caseId, simId.value, { content: '[END]' })
        const data = res.data
        score.value = data.score || 0
        if (data.feedback) {
          feedbackList.value = parseFeedback(data.feedback)
        }
      } catch (e) {
        score.value = 0
      }
    }
  }
})

function parseFeedback(feedback) {
  if (Array.isArray(feedback)) {
    return feedback.map(f => {
      if (typeof f === 'string') return { type: 'positive', text: f }
      return f
    })
  }
  if (typeof feedback === 'string') {
    return feedback.split('\n').filter(Boolean).map(line => {
      if (line.startsWith('-') || line.startsWith('*')) {
        return { type: 'improvement', text: line.replace(/^[-*]\s*/, '') }
      }
      return { type: 'positive', text: line }
    })
  }
  return []
}
</script>

<style scoped>
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #FFF9F0;
  display: flex;
  flex-direction: column;
}

/* Header */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #E0D8CE;
  flex-shrink: 0;
}
.btn-back {
  background: none;
  border: none;
  font-size: 14px;
  color: #E8A33D;
  cursor: pointer;
  padding: 0;
}
.top-bar h1 {
  font-size: 17px;
  font-weight: 600;
  color: #2D2A26;
}
.header-spacer {
  width: 40px;
}

/* ========== Setup Phase ========== */
.setup-phase {
  flex: 1;
  padding: 24px 20px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.setup-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  width: 100%;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  text-align: center;
}
.setup-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.setup-card h2 {
  font-size: 20px;
  font-weight: 600;
  color: #2D2A26;
  margin-bottom: 8px;
}
.setup-hint {
  font-size: 14px;
  color: #6B6560;
  margin-bottom: 24px;
  line-height: 1.5;
}

.style-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 28px;
}
.style-option {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #FFF9F0;
  border: 2px solid #E0D8CE;
  border-radius: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.style-option input {
  display: none;
}
.style-option.active {
  border-color: #E8A33D;
  background: #FFF3E0;
}
.style-content {
  flex: 1;
  text-align: left;
}
.style-label {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #2D2A26;
  margin-bottom: 2px;
}
.style-desc {
  display: block;
  font-size: 13px;
  color: #6B6560;
}
.radio-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #E0D8CE;
  flex-shrink: 0;
  position: relative;
  transition: border-color 0.2s;
}
.style-option.active .radio-dot {
  border-color: #E8A33D;
}
.style-option.active .radio-dot::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #E8A33D;
}

.btn-primary {
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 14px 32px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}
.btn-primary:hover {
  background: #D4922E;
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ========== Chat Phase ========== */
.chat-phase {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 16px 8px;
  -webkit-overflow-scrolling: touch;
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-bottom: 14px;
}
.msg-right {
  justify-content: flex-end;
}
.msg-left {
  justify-content: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.neighbor-avatar {
  background: #F0E6D6;
}
.user-avatar {
  background: #FDE8C8;
}

.bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
  word-break: break-word;
}
.bubble-neighbor {
  background: #fff;
  color: #2D2A26;
  border: 1px solid #E0D8CE;
  border-bottom-left-radius: 4px;
}
.bubble-user {
  background: #E8A33D;
  color: #fff;
  border-bottom-right-radius: 4px;
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 18px;
  align-items: center;
}
.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #BFB8AE;
  animation: typingBounce 1.2s infinite;
}
.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* Coach tip */
.coach-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0 16px 8px;
  padding: 10px 14px;
  background: #FFF3E0;
  border: 1px solid #F5D9A8;
  border-radius: 10px;
  font-size: 13px;
  color: #8B6914;
  line-height: 1.5;
  animation: fadeSlideUp 0.3s ease;
}
.coach-tip-icon {
  flex-shrink: 0;
  font-size: 16px;
}
.coach-tip-text {
  flex: 1;
}

@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Input bar */
.input-bar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #E0D8CE;
  flex-shrink: 0;
}
.chat-input {
  flex: 1;
  border: 1px solid #E0D8CE;
  border-radius: 20px;
  padding: 10px 16px;
  font-size: 15px;
  outline: none;
  background: #FFF9F0;
  color: #2D2A26;
  transition: border-color 0.2s;
}
.chat-input:focus {
  border-color: #E8A33D;
}
.chat-input::placeholder {
  color: #BFB8AE;
}
.btn-send {
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s;
}
.btn-send:hover {
  background: #D4922E;
}
.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* End bar */
.end-bar {
  padding: 8px 16px 12px;
  background: #fff;
  flex-shrink: 0;
}
.btn-end {
  width: 100%;
  background: #fff;
  color: #E8A33D;
  border: 2px solid #E8A33D;
  border-radius: 12px;
  padding: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.btn-end:hover {
  background: #E8A33D;
  color: #fff;
}

/* ========== Result Phase ========== */
.result-phase {
  flex: 1;
  padding: 24px 20px;
  overflow-y: auto;
}
.result-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  text-align: center;
}
.result-card h2 {
  font-size: 20px;
  font-weight: 600;
  color: #2D2A26;
  margin-bottom: 24px;
}

.score-ring-wrap {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 8px;
}
.score-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.score-track {
  fill: none;
  stroke: #E0D8CE;
  stroke-width: 8;
}
.score-fill {
  fill: none;
  stroke: #E8A33D;
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s ease;
}
.score-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 32px;
  font-weight: 700;
  color: #E8A33D;
}
.score-label {
  font-size: 14px;
  color: #6B6560;
  margin-bottom: 28px;
}

.feedback-section {
  text-align: left;
  margin-bottom: 28px;
}
.feedback-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin-bottom: 12px;
}
.feedback-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.feedback-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #F0EBE4;
  font-size: 14px;
  color: #2D2A26;
  line-height: 1.5;
}
.feedback-item:last-child {
  border-bottom: none;
}
.fb-icon {
  flex-shrink: 0;
  font-size: 16px;
}

.result-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.btn-secondary {
  background: none;
  color: #E8A33D;
  border: 2px solid #E8A33D;
  border-radius: 12px;
  padding: 14px 32px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.btn-secondary:hover {
  background: #E8A33D;
  color: #fff;
}
</style>
