<template>
  <div class="submit-page">
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

      <div v-if="createdCase" class="result-card">
        <div class="result-header">
          <span class="checkmark">✓</span>
          <h3>问题已记录</h3>
        </div>
        <div class="result-body">
          <div class="result-row">
            <span class="label">风险等级</span>
            <span :class="'risk-badge risk-' + createdCase.risk_level">{{ riskLabel(createdCase.risk_level) }}</span>
          </div>
          <div class="result-row">
            <span class="label">问题分类</span>
            <span>{{ categoryLabel(createdCase.category) }}</span>
          </div>
        </div>
        <div class="result-actions">
          <button @click="goToDiagnosis" class="btn-primary">查看 AI 诊断 →</button>
          <button @click="$router.push('/resident')" class="btn-secondary">返回首页</button>
        </div>
      </div>

      <div v-if="!createdCase" class="form-area">
        <div class="input-with-voice">
          <textarea v-model="input" :placeholder="inputPlaceholder" rows="3" @keydown.enter.ctrl="submit" :disabled="loading"></textarea>
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

        <button @click="submit" :disabled="!input.trim() || loading" class="btn-send">发送</button>
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
const chatArea = ref(null)

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
  messages.value.push({ role: 'ai', text: '你好，我是邻光。请描述你遇到的邻里问题，我会帮你分析情况。' })
  const scenario = route.query.scenario
  if (scenario && scenarioLabels[scenario]) {
    messages.value.push({ role: 'ai', text: `你选择了「${scenarioLabels[scenario]}」场景，请详细描述一下发生了什么？` })
    messages.value.push({ role: 'ai', text: '比如：什么时候发生的？频率如何？对你造成了什么影响？你和对方之前有过沟通吗？' })
    inputPlaceholder.value = `描述${scenarioLabels[scenario]}的具体情况...`
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

async function submit() {
  if (!input.value.trim() || loading.value) return
  const text = input.value.trim()
  messages.value.push({ role: 'user', text })
  scrollToBottom()
  input.value = ''
  loading.value = true

  try {
    // AI analysis preview before showing result
    messages.value.push({ role: 'ai', text: '正在分析你的描述...' })
    scrollToBottom()

    const res = await cases.create({
      title: text.slice(0, 30),
      description: text,
      category: route.query.scenario || null,
    })
    createdCase.value = res.data

    // Image analysis after case creation (non-blocking)
    if (imageFile.value) {
      const base64 = await getImageBase64()
      try {
        const imgRes = await api.post(`/cases/${res.data.id}/analyze-image`, { image: base64, text: text })
        imageAnalysis.value = imgRes.data.analysis
      } catch (e) {
        console.error('图片分析失败', e)
      }
    }

    messages.value.pop() // remove "正在分析"
    messages.value.push({
      role: 'ai',
      text: null,
      html: `<strong>分析完成！</strong><br/>初步判定风险等级为 <span style="color:${riskColor(res.data.risk_level)};font-weight:600">${riskLabel(res.data.risk_level)}</span>。`
    })
    scrollToBottom()
  } catch (e) {
    messages.value.push({ role: 'ai', text: '抱歉，提交时遇到了问题，请稍后重试。' })
    scrollToBottom()
  } finally {
    loading.value = false
  }
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
.submit-page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; display: flex; flex-direction: column; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; }
.top-bar h1 { font-size: 17px; font-weight: 600; }
.main-content { flex: 1; display: flex; flex-direction: column; padding: 0 20px 20px; }

.chat-area { flex: 1; overflow-y: auto; padding-bottom: 16px; }
.chat-bubble { max-width: 85%; padding: 12px 16px; border-radius: 16px; margin-bottom: 12px; font-size: 14px; line-height: 1.6; animation: fadeIn 0.3s; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.chat-bubble.ai { background: #fff; color: #2D2A26; border-bottom-left-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.chat-bubble.user { background: #E8A33D; color: #fff; margin-left: auto; border-bottom-right-radius: 4px; }

.typing { display: inline-flex; gap: 4px; }
.typing .dot { width: 6px; height: 6px; background: #E8A33D; border-radius: 50%; animation: bounce 1.4s infinite; }
.typing .dot:nth-child(2) { animation-delay: 0.2s; }
.typing .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-8px); } }

.input-area { display: flex; gap: 8px; align-items: flex-end; }
.input-area textarea { flex: 1; padding: 12px 16px; border: 1px solid #E0D8CE; border-radius: 12px; font-size: 14px; resize: none; outline: none; font-family: inherit; transition: border-color 0.2s; }
.input-area textarea:focus { border-color: #E8A33D; }
.btn-send { background: #E8A33D; color: #fff; border: none; border-radius: 12px; padding: 12px 20px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.btn-send:hover { background: #D4922E; }
.btn-send:disabled { background: #ccc; cursor: not-allowed; }

.result-card { background: #fff; border-radius: 16px; padding: 24px; margin-top: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.06); animation: slideUp 0.4s; }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.checkmark { width: 32px; height: 32px; border-radius: 50%; background: #4CAF50; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 600; }
.result-header h3 { font-size: 18px; font-weight: 600; }
.result-body { margin-bottom: 20px; }
.result-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.result-row:last-child { border-bottom: none; }
.result-row .label { font-size: 14px; color: #6B6560; }
.risk-badge { padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 600; }
.risk-badge.risk-green { background: #E8F5E9; color: #4CAF50; }
.risk-badge.risk-yellow { background: #FFF8E1; color: #F9A825; }
.risk-badge.risk-orange { background: #FFF3E0; color: #E65100; }
.risk-badge.risk-red { background: #FFEBEE; color: #C62828; }

.result-actions { display: flex; flex-direction: column; gap: 10px; }
.btn-primary { background: #E8A33D; color: #fff; border: none; border-radius: 12px; padding: 14px 24px; font-size: 15px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: #D4922E; }
.btn-secondary { background: none; border: 1px solid #E0D8CE; border-radius: 12px; padding: 12px 24px; font-size: 14px; color: #6B6560; cursor: pointer; }
.btn-secondary:hover { border-color: #E8A33D; color: #E8A33D; }

/* Form area layout */
.form-area { display: flex; flex-direction: column; gap: 12px; }
.form-area .btn-send { align-self: flex-end; }

/* Voice input */
.input-with-voice { position: relative; }
.input-with-voice textarea { width: 100%; padding: 12px 16px; border: 1px solid #E0D8CE; border-radius: 12px; font-size: 14px; resize: none; outline: none; font-family: inherit; transition: border-color 0.2s; box-sizing: border-box; }
.input-with-voice textarea:focus { border-color: #E8A33D; }
.btn-voice {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border: 1px solid #E0D8CE; border-radius: 20px;
  background: #fff; color: #6B6560; font-size: 13px; cursor: pointer;
  transition: all 0.2s; margin-top: 8px;
}
.btn-voice:hover { border-color: #E8A33D; color: #E8A33D; }
.btn-voice.recording { border-color: #FF3B30; color: #FF3B30; animation: pulse 1.5s infinite; }
.recording-dot { width: 8px; height: 8px; border-radius: 50%; background: #FF3B30; animation: blink 1s infinite; display: inline-block; }
@keyframes blink { 50% { opacity: 0.3; } }
@keyframes pulse { 50% { box-shadow: 0 0 0 4px rgba(255,59,48,0.15); } }

/* Image upload */
.image-upload-section { margin-top: 4px; }
.section-label { font-size: 14px; color: #6B6560; margin-bottom: 8px; }
.preview-wrap { position: relative; display: inline-block; margin-top: 8px; }
.preview-img { max-width: 100%; max-height: 200px; border-radius: 12px; border: 1px solid #E0D8CE; }
.btn-remove-img {
  position: absolute; top: -8px; right: -8px;
  width: 24px; height: 24px; border-radius: 50%;
  background: #FF3B30; color: #fff; border: none;
  font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.upload-trigger {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 24px; border: 2px dashed #E0D8CE; border-radius: 12px;
  cursor: pointer; transition: all 0.2s; color: #B8AFA3; font-size: 14px;
}
.upload-trigger:hover { border-color: #E8A33D; color: #E8A33D; }
</style>
