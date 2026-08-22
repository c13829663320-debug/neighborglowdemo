<template>
  <div class="submit-page ng-fade-in">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">← 返回</button>
      <h1>描述问题</h1>
      <span></span>
    </header>
    <main class="main-content">
      <div class="chat-area" ref="chatArea">
        <div v-for="(msg, i) in messages" :key="i" :class="['chat-bubble', msg.role]">
          <div v-if="msg.role === 'ai' && msg.html" v-html="msg.html"></div>
          <span v-else>{{ msg.text }}</span>
        </div>
        <div v-if="loading" class="chat-bubble ai">
          <span class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
        </div>
      </div>

      <!-- 案例确认卡片（AI 认为信息足够时显示） -->
      <div v-if="casePending" class="confirm-card ng-card">
        <div class="confirm-header">
          <span class="checkmark">✓</span>
          <h3>信息已收集完毕</h3>
        </div>
        <div class="confirm-body">
          <p class="summary">{{ casePending.summary }}</p>
          <div class="confirm-row">
            <span class="label">问题分类</span>
            <span>{{ categoryLabel(casePending.category) }}</span>
          </div>
        </div>
        <div class="confirm-actions">
          <button @click="confirmCreate" class="ng-btn ng-btn-primary ng-btn-block">确认创建案例 →</button>
          <button @click="continueChat" class="ng-btn ng-btn-secondary ng-btn-block">再补充一些信息</button>
        </div>
      </div>

      <!-- 创建完成后的结果卡片 -->
      <div v-if="createdCase" class="result-card ng-card">
        <div class="result-header">
          <span class="checkmark">✓</span>
          <h3>案例已创建</h3>
        </div>
        <div class="result-body">
          <div class="result-row">
            <span class="label">风险等级</span>
            <span :class="'ng-risk-badge ng-risk-soft-' + createdCase.risk_level">{{ riskLabel(createdCase.risk_level) }}</span>
          </div>
          <div class="result-row">
            <span class="label">问题分类</span>
            <span>{{ categoryLabel(createdCase.category) }}</span>
          </div>
        </div>
        <div class="result-actions">
          <button @click="goToDiagnosis" class="ng-btn ng-btn-primary ng-btn-block">查看 AI 诊断 →</button>
          <button @click="$router.push('/resident')" class="ng-btn ng-btn-secondary ng-btn-block">返回首页</button>
        </div>
      </div>

      <!-- 输入区域 -->
      <div v-if="!createdCase && !casePending" class="form-area">
        <div class="input-with-voice">
          <textarea v-model="input" class="ng-textarea" :placeholder="inputPlaceholder" rows="3" @keydown.enter.ctrl="submit" :disabled="loading"></textarea>
          <button class="btn-voice" :class="{ recording: isRecording }" @click="toggleVoice" type="button">
            <svg v-if="!isRecording" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
              <path d="M19 10v2a7 7 0 01-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
            <span v-else class="recording-dot"></span>
            {{ isRecording ? '录音中...' : '语音输入' }}
          </button>
        </div>

        <div class="image-upload-section">
          <div class="section-label">证据照片（可选）</div>
          <div v-if="imagePreview" class="preview-wrap">
            <img :src="imagePreview" class="preview-img" />
            <button class="btn-remove-img" @click="removeImage" type="button">&#10005;</button>
          </div>
          <label v-else class="upload-trigger">
            <input type="file" accept="image/*" capture="environment" @change="handleImageUpload" hidden />
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#B8AFA3" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
            <span>拍照或选择照片</span>
          </label>
        </div>

        <button @click="submit" :disabled="!input.trim() || loading" class="ng-btn ng-btn-primary btn-send">发送</button>
      </div>
    </main>
  </div>
</template>
<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases } from '../../api'
import api from '../../api'

const route = useRoute()
const router = useRouter()
const input = ref('')
const messages = ref([])
const loading = ref(false)
const createdCase = ref(null)
const casePending = ref(null) // { summary, title, category }
const chatArea = ref(null)

// 对话历史（用于 LLM 多轮对话）
const conversationHistory = ref([])

// Voice input
const isRecording = ref(false)
let recognition = null

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
    input.value = transcript
  }
  recognition.onend = () => { isRecording.value = false }
  recognition.onerror = () => { isRecording.value = false }
  return recognition
}

function toggleVoice() {
  if (!recognition) recognition = initSpeechRecognition()
  if (!recognition) { alert('当前浏览器不支持语音识别'); return }
  if (isRecording.value) { recognition.stop() }
  else { recognition.start(); isRecording.value = true }
}

// Image upload
const imageFile = ref(null)
const imagePreview = ref(null)
const imageAnalysis = ref(null)

function handleImageUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

function removeImage() {
  imageFile.value = null
  imagePreview.value = null
  imageAnalysis.value = null
}

function getImageBase64() {
  return new Promise((resolve) => {
    if (!imageFile.value) { resolve(null); return }
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.readAsDataURL(imageFile.value)
  })
}

const scenarioLabels = {
  noise: '深夜噪音', leak: '漏水纠纷', public_space: '公共区域',
  pet: '宠物问题', garbage: '异味困扰', renovation: '装修施工'
}
const categoryLabels = {
  noise: '噪音问题', parking: '停车问题', pet: '宠物问题', renovation: '装修施工',
  leak: '漏水问题', garbage: '卫生问题', public_space: '公共区域', wechat: '微信群', other: '其他'
}

const inputPlaceholder = ref('描述你遇到的邻里问题...')

onMounted(() => {
  const scenario = route.query.scenario
  let initialMsg = '你好，我是邻光。邻里之光，让善意照进千万人家！请描述你遇到的邻里问题，我会帮你分析情况。'
  if (scenario && scenarioLabels[scenario]) {
    initialMsg = `你选择了「${scenarioLabels[scenario]}」场景。请详细描述一下发生了什么？`
    inputPlaceholder.value = `描述${scenarioLabels[scenario]}的具体情况...`
    conversationHistory.value.push(
      { role: 'assistant', content: initialMsg },
      { role: 'assistant', content: '比如：什么时候发生的？频率如何？对你造成了什么影响？你和对方之前有过沟通吗？' }
    )
    messages.value.push(
      { role: 'ai', text: initialMsg },
      { role: 'ai', text: '比如：什么时候发生的？频率如何？对你造成了什么影响？你和对方之前有过沟通吗？' }
    )
  } else {
    conversationHistory.value.push({ role: 'assistant', content: initialMsg })
    messages.value.push({ role: 'ai', text: initialMsg })
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

// 核心：发送消息 → AI 引导对话，不立即创建案例
async function submit() {
  if (!input.value.trim() || loading.value) return
  const text = input.value.trim()
  input.value = ''
  loading.value = true

  // 显示用户消息
  messages.value.push({ role: 'user', text })
  conversationHistory.value.push({ role: 'user', content: text })
  scrollToBottom()

  try {
    // 调用 AI 引导对话端点
    messages.value.push({ role: 'ai', text: '正在分析...' })
    scrollToBottom()

    const res = await api.post('/ai/chat-submit', {
      messages: conversationHistory.value,
      user_input: text,
    })

    messages.value.pop() // 移除"正在分析"

    const { reply, ready_to_create, case_title, case_summary, category } = res.data

    if (ready_to_create) {
      // AI 认为信息足够，显示确认卡片
      messages.value.push({ role: 'ai', text: reply })
      casePending.value = {
        summary: case_summary || reply,
        title: case_title || text.slice(0, 30),
        category: category || 'other',
      }
      scrollToBottom()
    } else {
      // 继续引导对话
      messages.value.push({ role: 'ai', text: reply })
      conversationHistory.value.push({ role: 'assistant', content: reply })
      scrollToBottom()
    }
  } catch (e) {
    messages.value.push({ role: 'ai', text: '抱歉，分析时遇到了问题，请稍后重试。' })
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

// 用户确认创建案例
async function confirmCreate() {
  if (!casePending.value || loading.value) return
  loading.value = true

  try {
    // 构建完整的问题描述（合并所有用户输入）
    const userMessages = conversationHistory.value
      .filter(m => m.role === 'user')
      .map(m => m.content)
      .join('。')

    const res = await cases.create({
      title: casePending.value.title,
      description: userMessages,
      category: casePending.value.category,
    })

    // 图片分析（如果有）
    if (imageFile.value) {
      const base64 = await getImageBase64()
      try {
        await api.post(`/cases/${res.data.id}/analyze-image`, { image: base64, text: userMessages })
      } catch (e) {
        console.error('图片分析失败', e)
      }
    }

    casePending.value = null
    createdCase.value = res.data

    // 触发诊断
    try {
      await api.post(`/cases/${res.data.id}/diagnose`)
    } catch (e) {
      console.error('诊断失败', e)
    }

    scrollToBottom()
  } catch (e) {
    messages.value.push({ role: 'ai', text: '抱歉，创建案例时遇到了问题，请稍后重试。' })
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

// 用户想再补充信息，回到对话模式
function continueChat() {
  casePending.value = null
  messages.value.push({ role: 'ai', text: '好的，请继续补充。还有什么想说的吗？' })
  conversationHistory.value.push({ role: 'assistant', content: '好的，请继续补充。还有什么想说的吗？' })
  scrollToBottom()
}

function goToDiagnosis() {
  if (createdCase.value) {
    router.push(`/resident/case/${createdCase.value.id}/diagnosis`)
  }
}

function riskLabel(level) {
  return { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }[level] || level
}
function riskColor(level) {
  return { green: '#4CAF50', yellow: '#FFC107', orange: '#FF9800', red: '#F44336' }[level] || '#999'
}
function categoryLabel(cat) {
  return categoryLabels[cat] || categoryLabels.other
}
</script>
<style scoped>
/* ---- 页面容器（移动端 480px / 奶油白底 / 左右 20px） ---- */
.submit-page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: var(--ng-bg-mobile); display: flex; flex-direction: column; font-family: var(--ng-font-family); color: var(--ng-text-main); }

/* ---- 顶栏 ---- */
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: var(--ng-space-4) var(--ng-page-margin-mobile); background: var(--ng-bg-card); border-bottom: 1px solid var(--ng-border); position: sticky; top: 0; z-index: 10; }
.btn-back { background: none; border: none; font-size: var(--ng-fs-body); color: var(--ng-primary-deep); font-weight: var(--ng-fw-strong); cursor: pointer; transition: color var(--ng-dur-fast) var(--ng-ease); }
.btn-back:hover { color: var(--ng-primary); }
.top-bar h1 { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); }
.main-content { flex: 1; display: flex; flex-direction: column; padding: var(--ng-space-4) var(--ng-page-margin-mobile) var(--ng-space-5); }

/* ---- 对话区 ---- */
.chat-area { flex: 1; overflow-y: auto; padding: var(--ng-space-4) 0; }
.chat-bubble { max-width: 85%; padding: var(--ng-space-3) var(--ng-space-4); border-radius: var(--ng-radius-card); margin-bottom: var(--ng-card-gap); font-size: var(--ng-fs-body); line-height: var(--ng-lh); animation: bubble-in var(--ng-dur-base) var(--ng-ease) both; }
@keyframes bubble-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.chat-bubble.ai { background: var(--ng-bg-card); color: var(--ng-text-main); border-bottom-left-radius: var(--ng-radius-tag); border: 1px solid var(--ng-border); box-shadow: var(--ng-shadow-card); }
.chat-bubble.user { background: var(--ng-gradient-btn); color: var(--ng-text-inverse); margin-left: auto; border-bottom-right-radius: var(--ng-radius-tag); box-shadow: var(--ng-shadow-btn); }

.typing { display: inline-flex; gap: var(--ng-space-1); }
.typing .dot { width: 6px; height: 6px; background: var(--ng-primary); border-radius: 50%; animation: bounce 1.4s infinite; }
.typing .dot:nth-child(2) { animation-delay: 0.2s; }
.typing .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-8px); } }

/* ---- 案例确认卡片（.ng-card 基础 + 琥珀强调边） ---- */
.confirm-card { margin-top: var(--ng-space-4); border: 2px solid var(--ng-primary); animation: slide-up var(--ng-dur-slow) var(--ng-ease) both; }
.confirm-header { display: flex; align-items: center; gap: var(--ng-space-3); margin-bottom: var(--ng-space-4); }
.checkmark { width: 32px; height: 32px; border-radius: 50%; background: var(--ng-risk-green); color: var(--ng-text-inverse); display: flex; align-items: center; justify-content: center; font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); }
.confirm-header h3 { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0; }
.confirm-body { margin-bottom: var(--ng-space-5); }
.confirm-body .summary { font-size: var(--ng-fs-body); color: var(--ng-text-main); line-height: var(--ng-lh); margin-bottom: var(--ng-space-3); }
.confirm-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--ng-border); }
.confirm-row .label { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); }
.confirm-actions { display: flex; flex-direction: column; gap: 10px; }

/* ---- 结果卡片 ---- */
.result-card { margin-top: var(--ng-space-4); animation: slide-up var(--ng-dur-slow) var(--ng-ease) both; }
@keyframes slide-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.result-header { display: flex; align-items: center; gap: var(--ng-space-3); margin-bottom: var(--ng-space-4); }
.result-header h3 { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0; }
.result-body { margin-bottom: var(--ng-space-5); }
.result-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--ng-border); }
.result-row:last-child { border-bottom: none; }
.result-row .label { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); }
.result-actions { display: flex; flex-direction: column; gap: 10px; }

/* ---- 输入区 ---- */
.form-area { display: flex; flex-direction: column; gap: var(--ng-card-gap); }
.form-area .btn-send { align-self: flex-end; }
.input-with-voice { position: relative; }
.input-with-voice textarea { resize: none; box-sizing: border-box; }

/* ---- 语音输入 ---- */
.btn-voice {
  display: flex; align-items: center; gap: 6px;
  padding: var(--ng-space-2) var(--ng-space-4); border: 1px solid var(--ng-border-strong); border-radius: var(--ng-radius-pill);
  background: var(--ng-bg-card); color: var(--ng-text-secondary); font-size: var(--ng-fs-aux); cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease); margin-top: var(--ng-space-2); font-family: var(--ng-font-family);
}
.btn-voice:hover { border-color: var(--ng-primary); color: var(--ng-primary-deep); }
.btn-voice.recording { border-color: var(--ng-risk-red); color: var(--ng-risk-red); animation: pulse 1.5s infinite; }
.recording-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ng-risk-red); animation: blink 1s infinite; display: inline-block; }
@keyframes blink { 50% { opacity: 0.3; } }
@keyframes pulse { 50% { box-shadow: 0 0 0 4px var(--ng-risk-red-soft); } }

/* ---- 图片上传 ---- */
.image-upload-section { margin-top: var(--ng-space-1); }
.section-label { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); margin-bottom: var(--ng-space-2); }
.preview-wrap { position: relative; display: inline-block; margin-top: var(--ng-space-2); }
.preview-img { max-width: 100%; max-height: 200px; border-radius: var(--ng-radius-btn); border: 1px solid var(--ng-border-strong); }
.btn-remove-img {
  position: absolute; top: -8px; right: -8px;
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--ng-risk-red); color: var(--ng-text-inverse); border: none;
  font-size: var(--ng-fs-small); cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: transform var(--ng-dur-fast) var(--ng-ease);
}
.btn-remove-img:hover { transform: scale(1.1); }
.upload-trigger {
  display: flex; flex-direction: column; align-items: center; gap: var(--ng-space-2);
  padding: var(--ng-space-6); border: 2px dashed var(--ng-border-strong); border-radius: var(--ng-radius-btn);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease); color: var(--ng-text-hint); font-size: var(--ng-fs-body);
}
.upload-trigger:hover { border-color: var(--ng-primary); color: var(--ng-primary-deep); }
</style>
