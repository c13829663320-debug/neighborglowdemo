<template>
  <div class="page">
    <!-- Header -->
    <header class="top-bar">
      <button class="btn-back" @click="$router.back()">&larr; 返回</button>
      <h1>沟通文案</h1>
      <span class="header-spacer"></span>
    </header>

    <!-- Tone Selector -->
    <div class="tone-scroll">
      <div class="tone-tabs">
        <button
          v-for="t in tones"
          :key="t.key"
          :class="['tone-tab', { active: selectedTone === t.key }]"
          @click="selectTone(t.key)"
        >
          <span class="tone-emoji">{{ t.emoji }}</span>
          <span class="tone-label">{{ t.label }}</span>
        </button>
      </div>
    </div>

    <!-- Generated Message Card -->
    <div v-if="currentMessage" class="message-card">
      <div class="card-header">
        <span class="card-tone-badge">{{ currentToneObj.emoji }} {{ currentToneObj.label }}</span>
        <span class="card-time">{{ formatTime(currentMessage.created_at) }}</span>
      </div>
      <div class="card-body">
        <p class="card-content">{{ currentMessage.content }}</p>
      </div>
      <div class="card-actions">
        <button class="btn-copy" @click="copyContent">复制文案</button>
        <button class="btn-regen" @click="generate">重新生成</button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-card">
      <div class="spinner"></div>
      <span>正在生成文案...</span>
    </div>

    <!-- Empty State (no message yet, not loading) -->
    <div v-if="!currentMessage && !loading" class="empty-hint">
      <p>请选择一种语气风格，系统将自动为您生成沟通文案</p>
    </div>

    <!-- History Section -->
    <div v-if="historyMessages.length" class="history-section">
      <h2 class="section-title">已生成的文案</h2>
      <div
        v-for="msg in historyMessages"
        :key="msg.id"
        class="history-card"
      >
        <button class="history-header" @click="toggleExpand(msg.id)">
          <span class="history-tone-badge">{{ getToneObj(msg.tone)?.emoji }} {{ getToneObj(msg.tone)?.label }}</span>
          <span :class="['expand-icon', { expanded: expandedIds.has(msg.id) }]">&#9662;</span>
        </button>
        <transition name="slide">
          <div v-if="expandedIds.has(msg.id)" class="history-body">
            <p>{{ msg.content }}</p>
            <div class="history-footer">
              <span class="history-time">{{ formatTime(msg.created_at) }}</span>
              <button class="btn-copy-sm" @click="copyText(msg.content)">复制</button>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- Bottom Action -->
    <div class="bottom-action">
      <button class="btn-simulation" @click="goSimulation">前往模拟训练 &rarr;</button>
    </div>

    <!-- Toast -->
    <transition name="fade">
      <div v-if="toastVisible" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'

const route = useRoute()
const router = useRouter()
const caseId = computed(() => route.params.id)

// Tone definitions
const tones = [
  { key: 'wechat_friendly', label: '微信友善', emoji: '💬' },
  { key: 'wechat_direct', label: '微信直接', emoji: '📨' },
  { key: 'face_to_face_outline', label: '面谈提纲', emoji: '🤝' },
  { key: 'door_note', label: '门贴便条', emoji: '📝' },
  { key: 'property_apply', label: '物业申请', emoji: '🏢' },
]

const selectedTone = ref('')
const currentMessage = ref(null)
const historyMessages = ref([])
const loading = ref(false)
const expandedIds = reactive(new Set())

// Toast
const toastVisible = ref(false)
const toastText = ref('')
let toastTimer = null

const currentToneObj = computed(() => tones.find(t => t.key === selectedTone.value) || tones[0])

function getToneObj(toneKey) {
  return tones.find(t => t.key === toneKey) || tones[0]
}

function showToast(text) {
  toastText.value = text
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2000)
}

// Select tone and auto-generate
async function selectTone(key) {
  selectedTone.value = key
  await generate()
}

// Generate message
async function generate() {
  if (!selectedTone.value) return
  loading.value = true
  currentMessage.value = null
  try {
    const res = await casesApi.generateMessage(caseId.value, { tone: selectedTone.value })
    currentMessage.value = res.data
    await loadHistory()
  } catch (e) {
    showToast('生成失败，请重试')
  } finally {
    loading.value = false
  }
}

// Load message history
async function loadHistory() {
  try {
    const res = await casesApi.listMessages(caseId.value)
    historyMessages.value = (res.data || []).filter(m => {
      // exclude current message from history
      return !currentMessage.value || m.id !== currentMessage.value.id
    })
  } catch {
    historyMessages.value = []
  }
}

// Toggle history card expand
function toggleExpand(id) {
  if (expandedIds.has(id)) {
    expandedIds.delete(id)
  } else {
    expandedIds.add(id)
  }
}

// Copy to clipboard
async function copyContent() {
  if (!currentMessage.value) return
  await copyText(currentMessage.value.content)
}

async function copyText(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
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
    showToast('已复制到剪贴板')
  } catch {
    showToast('复制失败')
  }
}

// Navigate to simulation
function goSimulation() {
  router.push(`/resident/case/${caseId.value}/simulation`)
}

// Format time
function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// Load history on mount
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #FFF9F0;
  padding-bottom: 100px;
  position: relative;
}

/* Header */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  position: sticky;
  top: 0;
  background: #FFF9F0;
  z-index: 10;
}
.btn-back {
  background: none;
  border: none;
  font-size: 14px;
  color: #E8A33D;
  cursor: pointer;
  padding: 4px 0;
}
.top-bar h1 {
  font-size: 17px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0;
}
.header-spacer {
  width: 50px;
}

/* Tone Selector */
.tone-scroll {
  padding: 0 0 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.tone-scroll::-webkit-scrollbar {
  display: none;
}
.tone-tabs {
  display: flex;
  gap: 10px;
  padding: 0 20px;
  width: max-content;
}
.tone-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 16px;
  border-radius: 12px;
  border: 1.5px solid #E0D8CE;
  background: #fff;
  cursor: pointer;
  transition: all 0.25s ease;
  min-width: 76px;
  flex-shrink: 0;
}
.tone-tab:hover {
  border-color: #E8A33D;
}
.tone-tab.active {
  background: linear-gradient(135deg, #E8A33D, #D4922E);
  border-color: #E8A33D;
  color: #fff;
  box-shadow: 0 4px 12px rgba(232, 163, 61, 0.3);
}
.tone-emoji {
  font-size: 22px;
  line-height: 1;
}
.tone-label {
  font-size: 12px;
  font-weight: 500;
  color: #2D2A26;
  white-space: nowrap;
}
.tone-tab.active .tone-label {
  color: #fff;
}

/* Message Card */
.message-card {
  margin: 8px 20px 20px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(45, 42, 38, 0.06);
  overflow: hidden;
  animation: cardIn 0.3s ease;
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px 0;
}
.card-tone-badge {
  font-size: 13px;
  font-weight: 600;
  color: #E8A33D;
}
.card-time {
  font-size: 11px;
  color: #6B6560;
}
.card-body {
  padding: 12px 16px 16px;
}
.card-content {
  font-size: 15px;
  line-height: 1.7;
  color: #2D2A26;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
.card-actions {
  display: flex;
  gap: 10px;
  padding: 0 16px 16px;
}
.btn-copy {
  flex: 1;
  padding: 10px 0;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #E8A33D, #D4922E);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-copy:active {
  opacity: 0.85;
}
.btn-regen {
  flex: 1;
  padding: 10px 0;
  border-radius: 10px;
  border: 1.5px solid #E0D8CE;
  background: #fff;
  color: #2D2A26;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.2s;
}
.btn-regen:hover {
  border-color: #E8A33D;
}

/* Loading */
.loading-card {
  margin: 20px;
  padding: 32px;
  background: #fff;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #6B6560;
  font-size: 14px;
  box-shadow: 0 2px 12px rgba(45, 42, 38, 0.06);
}
.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #E0D8CE;
  border-top-color: #E8A33D;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty Hint */
.empty-hint {
  margin: 20px;
  padding: 40px 24px;
  text-align: center;
  color: #6B6560;
  font-size: 14px;
  line-height: 1.6;
}

/* History */
.history-section {
  padding: 0 20px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #2D2A26;
  margin: 24px 0 12px;
}
.history-card {
  background: #fff;
  border-radius: 12px;
  margin-bottom: 10px;
  box-shadow: 0 1px 6px rgba(45, 42, 38, 0.05);
  overflow: hidden;
}
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 12px 14px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
}
.history-tone-badge {
  font-size: 13px;
  font-weight: 500;
  color: #2D2A26;
}
.expand-icon {
  font-size: 12px;
  color: #6B6560;
  transition: transform 0.25s ease;
  display: inline-block;
}
.expand-icon.expanded {
  transform: rotate(180deg);
}
.history-body {
  padding: 0 14px 14px;
}
.history-body p {
  font-size: 14px;
  line-height: 1.65;
  color: #2D2A26;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0 0 10px;
}
.history-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.history-time {
  font-size: 11px;
  color: #6B6560;
}
.btn-copy-sm {
  font-size: 12px;
  color: #E8A33D;
  background: none;
  border: 1px solid #E8A33D;
  border-radius: 6px;
  padding: 3px 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-copy-sm:hover {
  background: #E8A33D;
  color: #fff;
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* Bottom Action */
.bottom-action {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  padding: 16px 20px;
  background: linear-gradient(to top, #FFF9F0 80%, transparent);
  z-index: 10;
}
.btn-simulation {
  width: 100%;
  padding: 14px 0;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #E8A33D, #D4922E);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(232, 163, 61, 0.3);
  transition: opacity 0.2s;
}
.btn-simulation:active {
  opacity: 0.88;
}

/* Toast */
.toast {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(45, 42, 38, 0.85);
  color: #fff;
  font-size: 13px;
  padding: 8px 20px;
  border-radius: 20px;
  z-index: 100;
  pointer-events: none;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
