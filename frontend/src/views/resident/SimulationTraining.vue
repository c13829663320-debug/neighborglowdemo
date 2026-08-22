<template>
  <div class="page">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">&larr; 返回</button>
      <h1>模拟训练</h1>
      <span class="header-spacer"></span>
    </header>

    <!-- Critical-risk safety block -->
    <main v-if="phase === 'blocked'" class="blocked-phase">
      <div class="blocked-card">
        <div class="blocked-hero">
          <span class="blocked-icon">&#x1F6E1;&#xFE0F;</span>
          <h2>模拟训练已暂停</h2>
        </div>
        <p class="blocked-text">
          AI 判断当前案例可能涉及人身安全风险（红色风险）。出于对你的保护，
          系统暂不提供模拟对话与直接沟通建议，请优先查看安全响应指引。
        </p>
        <div class="blocked-actions">
          <button class="btn-danger" @click="$router.replace(`/resident/case/${caseId}/safety`)">
            查看安全响应 &rarr;
          </button>
          <button class="btn-secondary" @click="$router.push(`/resident/case/${caseId}`)">
            返回案例
          </button>
        </div>
      </div>
    </main>

    <!-- Pre-simulation setup -->
    <main v-else-if="phase === 'setup'" class="setup-phase">
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
        <template v-for="(msg, idx) in conversation" :key="idx">
          <!-- 教练反馈卡（PRD 11.6：每轮表达获得具体反馈和优化版本） -->
          <div v-if="msg.role === 'coach'" class="coach-msg">
            <div class="coach-msg-head">
              <span class="coach-msg-icon">&#x1F3AF;</span>
              <span class="coach-msg-title">教练反馈 · 第 {{ msg.round }} 轮</span>
              <span class="coach-score-chip">{{ msg.score }}/10</span>
            </div>
            <ul v-if="msg.suggestions && msg.suggestions.length" class="coach-msg-list">
              <li v-for="(s, i) in msg.suggestions" :key="i">{{ s }}</li>
            </ul>
            <div v-if="msg.improved_version" class="coach-improved">
              <span class="coach-improved-label">&#x2728; 优化参考</span>
              <p>{{ msg.improved_version }}</p>
            </div>
          </div>

          <div v-else class="msg-row" :class="msg.role === 'user' ? 'msg-right' : 'msg-left'">
            <div v-if="msg.role !== 'user'" class="avatar neighbor-avatar">&#x1F9D1;&#x200D;&#x1F91D;&#x200D;&#x1F9D1;</div>
            <div class="bubble-col" :class="msg.role === 'user' ? 'bubble-col-right' : 'bubble-col-left'">
              <div class="bubble" :class="msg.role === 'user' ? 'bubble-user' : 'bubble-neighbor'">
                {{ msg.displayContent || msg.content }}
              </div>
              <span class="msg-time">{{ formatTime(msg.time) }}</span>
            </div>
            <div v-if="msg.role === 'user'" class="avatar user-avatar">&#x1F60A;</div>
          </div>
        </template>

        <div v-if="sending" class="msg-row msg-left">
          <div class="avatar neighbor-avatar">&#x1F9D1;&#x200D;&#x1F91D;&#x200D;&#x1F9D1;</div>
          <div class="bubble-col bubble-col-left">
            <div class="bubble bubble-neighbor typing-indicator">
              <span></span><span></span><span></span>
            </div>
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
          class="btn-mic"
          :class="{ recording: isRecording }"
          @click="toggleVoice"
          :disabled="sending"
          type="button"
          title="语音输入"
        >
          <svg v-if="!isRecording" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
            <path d="M19 10v2a7 7 0 01-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
          <span v-else class="recording-dot"></span>
        </button>
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
              :class="score >= 80 ? 'score-high' : score >= 60 ? 'score-mid' : 'score-low'"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="circumference - (circumference * score) / 100"
            />
          </svg>
          <div class="score-value" :class="score >= 80 ? 'score-high' : score >= 60 ? 'score-mid' : 'score-low'">{{ score }}</div>
        </div>
        <p class="score-label">沟通评分 · 共 {{ rounds }} 轮对话</p>

        <div v-if="feedbackList.length" class="feedback-section">
          <h3>教练反馈</h3>
          <ul class="feedback-list">
            <li v-for="(fb, idx) in feedbackList" :key="idx" class="feedback-item">
              <span class="fb-icon">{{ fb.type === 'positive' ? '&#x2705;' : '&#x1F4CC;' }}</span>
              <span>{{ fb.text }}</span>
            </li>
          </ul>
        </div>

        <div v-if="finalVersion" class="final-section">
          <div class="final-head">
            <h3>最终沟通版本</h3>
            <button class="btn-copy" type="button" @click="copyFinalVersion">
              {{ copied ? '已复制' : '复制' }}
            </button>
          </div>
          <div class="final-text">{{ finalVersion }}</div>
          <p class="final-hint">该版本综合了本次训练要点，可直接用于现实沟通，也可根据当时情境微调。</p>
        </div>

        <div class="result-actions">
          <button class="btn-primary" :disabled="recorded" @click="recordAction">
            {{ recorded ? '已记录现实行动' : '记录现实行动' }}
          </button>
          <button class="btn-secondary" @click="restart">再练一次</button>
          <button class="btn-text" @click="$router.push(`/resident/case/${caseId}`)">
            返回案例 &rarr;
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { cases as casesApi, ai as aiApi } from '../../api'
import { useToast } from '../../composables'

const route = useRoute()
const caseId = route.params.id
const toast = useToast()

const phase = ref('setup') // setup | chat | result | blocked

// Critical-risk guard: red-risk cases must not enter simulation (PRD safety bottom line)
onMounted(async () => {
  try {
    const res = await casesApi.get(caseId)
    const risk = res.data?.risk_level || res.data?.case?.risk_level
    if (risk === 'red') {
      phase.value = 'blocked'
    }
  } catch (e) {
    console.error('Failed to check case risk level', e)
  }
})

// Style options
const styleOptions = [
  { value: 'friendly', label: '友善型邻居', desc: '态度温和，愿意沟通' },
  { value: 'defensive', label: '防御型邻居', desc: '容易辩解，不太配合' },
  { value: 'avoidant', label: '回避型邻居', desc: '不太想谈，想尽快结束' },
]
const selectedStyle = ref('friendly')
const loading = ref(false)

// System prompt personality descriptions
const stylePersonality = {
  friendly: '态度温和，愿意沟通，能够理解对方的立场，说话友善',
  defensive: '比较固执，容易辩解，不太愿意承认问题，但也有一定的道理，说话带刺但不失理性',
  avoidant: '不太想谈，想尽快结束对话，回答简短敷衍，不太正面回应问题',
}

// Chat state
const simId = ref(null)
const conversation = ref([])
const inputText = ref('')
const sending = ref(false)
const currentTip = ref('')
const chatArea = ref(null)

// Voice input state
const isRecording = ref(false)
let recognition = null

// Result state
const score = ref(0)
const feedbackList = ref([])
const rounds = ref(0)
const finalVersion = ref('')
const recorded = ref(false)
const copied = ref(false)

// Computed
const circumference = 2 * Math.PI * 52
const userMsgCount = computed(() => conversation.value.filter(m => m.role === 'user').length)

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const h = d.getHours().toString().padStart(2, '0')
  const m = d.getMinutes().toString().padStart(2, '0')
  return `${h}:${m}`
}

function buildSystemPrompt() {
  const personality = stylePersonality[selectedStyle.value] || stylePersonality.friendly
  return `你正在模拟训练中扮演对方邻居的角色。你是一位住在隔壁的邻居，最近与对方因为邻里纠纷产生了矛盾。你的性格特点：${personality}。请用口语化的中文回复，就像真实的邻居对话一样自然。每次回复控制在50到100字之间，不要太长也不要太短。不要使用表情符号。`
}

function buildAiMessages() {
  return conversation.value
    .filter(m => m.role === 'user' || m.role === 'neighbor')
    .map(m => ({
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.content,
    }))
}

// Speech recognition
function initSpeechRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) return null
  recognition = new SR()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true
  recognition.onresult = (event) => {
    let transcript = ''
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript
    }
    inputText.value = transcript
  }
  recognition.onend = () => { isRecording.value = false }
  recognition.onerror = () => { isRecording.value = false }
  return recognition
}

function toggleVoice() {
  if (!recognition) recognition = initSpeechRecognition()
  if (!recognition) { toast.error('当前浏览器不支持语音识别'); return }
  if (isRecording.value) { recognition.stop() }
  else { recognition.start(); isRecording.value = true }
}

// Typing effect: reveal text character by character
function typeMessage(msgObj, fullText) {
  return new Promise((resolve) => {
    msgObj.displayContent = ''
    let i = 0
    const interval = setInterval(() => {
      if (i < fullText.length) {
        msgObj.displayContent = fullText.slice(0, i + 1)
        i++
        scrollToBottom()
      } else {
        clearInterval(interval)
        msgObj.displayContent = fullText
        resolve()
      }
    }, 30)
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
    // Initialize conversation with timestamps for any initial messages
    conversation.value = (data.conversation || []).map(m => ({
      ...m,
      role: m.role === 'counterpart' ? 'neighbor' : m.role,
      time: m.time || Date.now(),
      displayContent: m.content,
    }))
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

  // Stop voice recording if active
  if (isRecording.value && recognition) {
    recognition.stop()
  }

  inputText.value = ''
  sending.value = true
  currentTip.value = ''

  // Optimistically append user message with timestamp
  const userMsg = { role: 'user', content: text, time: Date.now(), displayContent: text }
  conversation.value.push(userMsg)
  scrollToBottom()

  try {
    // Build AI request
    const aiMessages = buildAiMessages()
    const systemPrompt = buildSystemPrompt()

    const aiRes = await aiApi.chat({
      messages: aiMessages,
      system: systemPrompt,
      context: `这是一个邻里纠纷模拟训练场景。用户正在练习与邻居沟通。邻居风格：${selectedStyle.value}。`,
    })

    const replyText = aiRes.data?.reply || aiRes.data?.content || aiRes.data?.message || ''

    if (replyText) {
      const neighborMsg = { role: 'neighbor', content: replyText, time: Date.now() }
      conversation.value.push(neighborMsg)
      scrollToBottom()

      // Typing effect
      await typeMessage(neighborMsg, replyText)

      // PRD 11.6: 同步本轮到服务端，获取具体反馈和优化版本
      const fb = await logRoundToServer(text, replyText)
      pushCoachMessage(fb)
    } else {
      // Empty AI reply, fallback
      throw new Error('Empty AI response')
    }
  } catch (aiError) {
    console.warn('AI chat failed, falling back to rule engine:', aiError)
    // Fallback to original rule engine
    try {
      const res = await casesApi.sendSimMessage(caseId, simId.value, { content: text })
      const data = res.data
      // 只取服务端对方回复追加，避免覆盖本地已有的教练反馈卡
      const serverConv = data.conversation || []
      const lastNeighbor = [...serverConv].reverse().find(m => m.role === 'counterpart')
      if (lastNeighbor) {
        const neighborMsg = { role: 'neighbor', content: lastNeighbor.content, time: Date.now() }
        conversation.value.push(neighborMsg)
        scrollToBottom()
        await typeMessage(neighborMsg, lastNeighbor.content)
      }

      // PRD 11.6: 展示本轮教练反馈与优化版本
      pushCoachMessage(data.feedback)

      scrollToBottom()
    } catch (fallbackError) {
      console.error('Fallback also failed', fallbackError)
      // Show an error message in the conversation
      conversation.value.push({
        role: 'neighbor',
        content: '抱歉，对方暂时无法回复，请稍后再试。',
        time: Date.now(),
        displayContent: '抱歉，对方暂时无法回复，请稍后再试。',
      })
      scrollToBottom()
    }
  } finally {
    sending.value = false
  }
}

function endSimulation() {
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
  rounds.value = 0
  finalVersion.value = ''
  recorded.value = false
  copied.value = false
  if (isRecording.value && recognition) {
    recognition.stop()
  }
}

// PRD 11.6: 把本轮对话同步到服务端，换取具体反馈与优化版本
async function logRoundToServer(text, counterpartReply) {
  try {
    const res = await casesApi.sendSimMessage(caseId, simId.value, {
      content: text,
      counterpart_reply: counterpartReply,
    })
    return res.data?.feedback || null
  } catch (e) {
    console.warn('Round feedback unavailable', e)
    return null
  }
}

function pushCoachMessage(fb) {
  if (!fb) return
  const hasSuggestions = Array.isArray(fb.suggestions) && fb.suggestions.length > 0
  if (!hasSuggestions && !fb.improved_version) return
  conversation.value.push({
    role: 'coach',
    round: fb.round || userMsgCount.value,
    score: typeof fb.score === 'number' ? fb.score : '-',
    suggestions: fb.suggestions || [],
    improved_version: fb.improved_version || '',
    time: Date.now(),
  })
  scrollToBottom()
}

// PRD 11.6: 记录现实行动 —— 训练成果落到真实跟进记录
async function recordAction() {
  try {
    await casesApi.createFollowup(caseId, {
      action_taken: `完成模拟训练（${rounds.value} 轮，评分 ${score.value}），计划使用最终沟通版本与邻居进行现实沟通`,
      is_escalated: false,
    })
    recorded.value = true
    toast.success('已记录现实行动，沟通后记得回来记录对方回应')
  } catch (e) {
    console.error('Failed to record real action', e)
    toast.error('记录失败，请稍后再试')
  }
}

async function copyFinalVersion() {
  const text = finalVersion.value
  if (!text) return
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    copied.value = true
    toast.success('已复制，可直接发给邻居或当面参考')
    setTimeout(() => { copied.value = false }, 2000)
  } catch (e) {
    toast.error('复制失败，请手动长按选择文本')
  }
}

watch(phase, async (val) => {
  if (val === 'result') {
    try {
      // [END] 不会被写入对话，仅聚合逐轮反馈并产出最终沟通版本
      const res = await casesApi.sendSimMessage(caseId, simId.value, { content: '[END]' })
      const data = res.data
      score.value = Math.round((data.score || 0) * 10)
      rounds.value = data.rounds || userMsgCount.value
      finalVersion.value = data.final_version || ''
      feedbackList.value = parseFeedback(data.feedback)
    } catch (e) {
      score.value = 0
      rounds.value = userMsgCount.value
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
  background: var(--ng-bg-mobile);
  display: flex;
  flex-direction: column;
}

/* Header */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
  background: var(--ng-bg-card);
  border-bottom: 1px solid var(--ng-border);
  flex-shrink: 0;
}
.btn-back {
  background: none;
  border: none;
  font-size: var(--ng-fs-body);
  color: var(--ng-primary);
  cursor: pointer;
  padding: 0;
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover {
  color: var(--ng-primary-dark);
}
.top-bar h1 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}
.header-spacer {
  width: 40px;
}

/* ========== Blocked Phase (red risk) ========== */
.blocked-phase {
  flex: 1;
  padding: var(--ng-space-6) var(--ng-page-margin-mobile);
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.blocked-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: var(--ng-space-8) var(--ng-space-6);
  width: 100%;
  box-shadow: var(--ng-shadow-card);
  text-align: center;
  border-top: 4px solid var(--ng-risk-red);
  animation: ng-fade-in var(--ng-dur-slow) var(--ng-ease) both;
}
.blocked-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-card-gap);
  margin-bottom: var(--ng-space-4);
}
.blocked-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--ng-risk-red-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}
.blocked-card h2 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-risk-red);
  margin: 0;
}
.blocked-text {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  line-height: 1.7;
  margin-bottom: 28px;
}
.blocked-actions {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}
.btn-danger {
  background: var(--ng-risk-red);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-space-3) var(--ng-space-8);
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  width: 100%;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-danger:hover {
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
}
.btn-danger:active {
  transform: scale(0.98);
}

/* ========== Setup Phase ========== */
.setup-phase {
  flex: 1;
  padding: var(--ng-space-6) var(--ng-page-margin-mobile);
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.setup-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: var(--ng-space-8) var(--ng-space-6);
  width: 100%;
  box-shadow: var(--ng-shadow-card);
  text-align: center;
}
.setup-icon {
  font-size: 48px;
  margin-bottom: var(--ng-space-4);
}
.setup-card h2 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-2) 0;
}
.setup-hint {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  margin-bottom: var(--ng-space-6);
  line-height: 1.5;
}

.style-options {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
  margin-bottom: 28px;
}
.style-option {
  display: flex;
  align-items: center;
  gap: var(--ng-card-gap);
  background: var(--ng-bg-mobile);
  border: 2px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-space-3) var(--ng-space-4);
  cursor: pointer;
  transition: border-color var(--ng-dur-fast) var(--ng-ease),
              background var(--ng-dur-fast) var(--ng-ease);
}
.style-option:hover {
  border-color: var(--ng-primary);
}
.style-option input {
  display: none;
}
.style-option.active {
  border-color: var(--ng-primary);
  background: var(--ng-primary-soft2);
}
.style-content {
  flex: 1;
  text-align: left;
}
.style-label {
  display: block;
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin-bottom: 2px;
}
.style-desc {
  display: block;
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
}
.radio-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--ng-border-strong);
  flex-shrink: 0;
  position: relative;
  transition: border-color var(--ng-dur-fast) var(--ng-ease);
}
.style-option.active .radio-dot {
  border-color: var(--ng-primary);
}
.style-option.active .radio-dot::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--ng-primary);
}

.btn-primary {
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-space-3) var(--ng-space-8);
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  width: 100%;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-primary:hover:not(:disabled) {
  background: var(--ng-primary-dark);
}
.btn-primary:active:not(:disabled) {
  transform: scale(0.98);
}
.btn-primary:disabled {
  background: var(--ng-border-strong);
  box-shadow: none;
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
  padding: var(--ng-space-4) var(--ng-space-4) var(--ng-space-2);
  -webkit-overflow-scrolling: touch;
}

.msg-row {
  display: flex;
  align-items: flex-end;
  gap: var(--ng-space-2);
  margin-bottom: var(--ng-space-3);
  animation: fadeSlideUp var(--ng-dur-base) var(--ng-ease) both;
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
  background: var(--ng-bg-subtle);
}
.user-avatar {
  background: var(--ng-primary-soft);
}

/* Bubble with timestamp column */
.bubble-col {
  max-width: 72%;
  display: flex;
  flex-direction: column;
}
.bubble-col-left {
  align-items: flex-start;
}
.bubble-col-right {
  align-items: flex-end;
}

.bubble {
  max-width: 100%;
  padding: 10px 14px;
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-body);
  line-height: 1.5;
  word-break: break-word;
}
.bubble-neighbor {
  background: var(--ng-bg-card);
  color: var(--ng-text-main);
  border: 1px solid var(--ng-border);
  border-bottom-left-radius: var(--ng-space-1);
}
.bubble-user {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  border-bottom-right-radius: var(--ng-space-1);
}

.msg-time {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
  margin-top: var(--ng-space-1);
  padding: 0 var(--ng-space-1);
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: var(--ng-space-1);
  padding: var(--ng-card-gap) var(--ng-space-4);
  align-items: center;
}
.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ng-text-hint);
  opacity: 0.4;
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
  gap: var(--ng-space-2);
  margin: 0 var(--ng-space-4) var(--ng-space-2);
  padding: 10px 14px;
  background: var(--ng-primary-soft2);
  border: 1px solid var(--ng-primary-soft);
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-aux);
  color: var(--ng-primary-deep);
  line-height: 1.5;
  animation: fadeSlideUp var(--ng-dur-base) var(--ng-ease) both;
}
.coach-tip-icon {
  flex-shrink: 0;
  font-size: var(--ng-fs-card);
}
.coach-tip-text {
  flex: 1;
}

@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 每轮教练反馈卡 */
.coach-msg {
  margin: var(--ng-space-1) var(--ng-space-2) var(--ng-space-3);
  padding: var(--ng-card-gap) var(--ng-space-3);
  background: var(--ng-primary-soft2);
  border: 1px solid var(--ng-primary-soft);
  border-radius: var(--ng-radius-card);
  animation: fadeSlideUp var(--ng-dur-base) var(--ng-ease) both;
}
.coach-msg-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.coach-msg-icon {
  font-size: var(--ng-fs-body);
}
.coach-msg-title {
  flex: 1;
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
}
.coach-score-chip {
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
  background: var(--ng-primary-soft);
  border-radius: var(--ng-radius-pill);
  padding: 2px 10px;
}
.coach-msg-list {
  margin: 0;
  padding-left: 18px;
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
}
.coach-improved {
  margin-top: var(--ng-space-2);
  padding: var(--ng-space-2) 10px;
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-tag);
  border: 1px dashed var(--ng-primary);
}
.coach-improved-label {
  display: block;
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
  margin-bottom: var(--ng-space-1);
}
.coach-improved p {
  margin: 0;
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-main);
  line-height: var(--ng-lh);
}

/* Input bar */
.input-bar {
  display: flex;
  gap: var(--ng-space-2);
  padding: var(--ng-card-gap) var(--ng-space-4);
  background: var(--ng-bg-card);
  border-top: 1px solid var(--ng-border);
  flex-shrink: 0;
  align-items: center;
}
.chat-input {
  flex: 1;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-pill);
  padding: 10px var(--ng-space-4);
  font-size: var(--ng-fs-body);
  outline: none;
  background: var(--ng-bg-mobile);
  color: var(--ng-text-main);
  transition: border-color var(--ng-dur-fast) var(--ng-ease),
              box-shadow var(--ng-dur-fast) var(--ng-ease);
  min-width: 0;
}
.chat-input:focus {
  border-color: var(--ng-primary);
  box-shadow: 0 0 0 3px var(--ng-primary-tint);
}
.chat-input::placeholder {
  color: var(--ng-text-hint);
}

/* Voice button */
.btn-mic {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  color: var(--ng-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-mic:hover:not(:disabled) {
  border-color: var(--ng-primary);
  color: var(--ng-primary);
}
.btn-mic:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-mic.recording {
  border-color: var(--ng-risk-red);
  color: var(--ng-risk-red);
  animation: pulse 1.5s infinite;
}
.recording-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--ng-risk-red);
  animation: blink 1s infinite;
  display: inline-block;
}
@keyframes blink { 50% { opacity: 0.3; } }
@keyframes pulse { 50% { box-shadow: 0 0 0 4px var(--ng-risk-red-soft); } }

.btn-send {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-pill);
  padding: 10px var(--ng-space-5);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  flex-shrink: 0;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-send:hover:not(:disabled) {
  background: var(--ng-primary-dark);
}
.btn-send:active:not(:disabled) {
  transform: scale(0.98);
}
.btn-send:disabled {
  background: var(--ng-border-strong);
  box-shadow: none;
  opacity: 0.6;
  cursor: not-allowed;
}

/* End bar */
.end-bar {
  padding: var(--ng-space-2) var(--ng-space-4) var(--ng-card-gap);
  background: var(--ng-bg-card);
  flex-shrink: 0;
}
.btn-end {
  width: 100%;
  background: var(--ng-bg-card);
  color: var(--ng-primary);
  border: 2px solid var(--ng-primary);
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-card-gap);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-end:hover {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
}
.btn-end:active {
  transform: scale(0.98);
}

/* ========== Result Phase ========== */
.result-phase {
  flex: 1;
  padding: var(--ng-space-6) var(--ng-page-margin-mobile);
  overflow-y: auto;
}
.result-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: var(--ng-space-8) var(--ng-space-6);
  box-shadow: var(--ng-shadow-card);
  text-align: center;
}
.result-card h2 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-6) 0;
}

.score-ring-wrap {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto var(--ng-space-2);
}
.score-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.score-track {
  fill: none;
  stroke: var(--ng-bg-subtle);
  stroke-width: 8;
}
.score-fill {
  fill: none;
  stroke: var(--ng-primary);
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dashoffset var(--ng-dur-slow) var(--ng-ease);
}
/* 评分分级色：高分绿 / 中黄 / 低橙 */
.score-fill.score-high { stroke: var(--ng-risk-green); }
.score-fill.score-mid { stroke: var(--ng-risk-yellow); }
.score-fill.score-low { stroke: var(--ng-risk-orange); }
.score-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 32px;
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
}
.score-value.score-high { color: var(--ng-risk-green); }
.score-value.score-mid { color: var(--ng-risk-yellow); }
.score-value.score-low { color: var(--ng-risk-orange); }
.score-label {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  margin-bottom: 28px;
}

.feedback-section {
  text-align: left;
  margin-bottom: 28px;
}
.feedback-section h3 {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-card-gap) 0;
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
  border-bottom: 1px solid var(--ng-border);
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  line-height: 1.5;
}
.feedback-item:last-child {
  border-bottom: none;
}
.fb-icon {
  flex-shrink: 0;
  font-size: var(--ng-fs-card);
}

/* 最终沟通版本 */
.final-section {
  text-align: left;
  margin-bottom: var(--ng-space-6);
  background: var(--ng-primary-soft2);
  border: 1px solid var(--ng-primary-soft);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding);
}
.final-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.final-head h3 {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}
.btn-copy {
  border: 1px solid var(--ng-primary);
  background: var(--ng-bg-card);
  color: var(--ng-primary-deep);
  border-radius: var(--ng-radius-tag);
  font-size: var(--ng-fs-small);
  padding: var(--ng-space-1) var(--ng-card-gap);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-copy:hover {
  background: var(--ng-primary-soft);
}
.btn-copy:active {
  transform: scale(0.98);
}
.final-text {
  white-space: pre-line;
  font-size: var(--ng-fs-body);
  line-height: 1.8;
  color: var(--ng-text-main);
}
.final-hint {
  margin-top: 10px;
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
  line-height: 1.5;
}

.result-actions {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}
.btn-secondary {
  background: var(--ng-bg-card);
  color: var(--ng-primary);
  border: 1.5px solid var(--ng-primary);
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-space-3) var(--ng-space-8);
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-secondary:hover {
  background: var(--ng-primary-soft2);
}
.btn-secondary:active {
  transform: scale(0.98);
}
.btn-text {
  background: none;
  border: none;
  color: var(--ng-primary-deep);
  font-size: var(--ng-fs-body);
  cursor: pointer;
  padding: var(--ng-space-2);
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.btn-text:hover {
  color: var(--ng-primary);
}
</style>
