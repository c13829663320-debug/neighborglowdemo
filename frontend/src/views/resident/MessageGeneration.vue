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
  background: var(--ng-bg-mobile);
  padding-bottom: 100px;
  position: relative;
}

/* Header */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
  position: sticky;
  top: 0;
  background: var(--ng-bg-mobile);
  z-index: 10;
}
.btn-back {
  background: none;
  border: none;
  font-size: var(--ng-fs-body);
  color: var(--ng-primary);
  cursor: pointer;
  padding: var(--ng-space-1) 0;
  transition: opacity var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover {
  color: var(--ng-primary-deep);
}
.btn-back:active {
  transform: scale(0.98);
}
.top-bar h1 {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}
.header-spacer {
  width: 50px;
}

/* Tone Selector */
.tone-scroll {
  padding: 0 0 var(--ng-space-3);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.tone-scroll::-webkit-scrollbar {
  display: none;
}
.tone-tabs {
  display: flex;
  gap: 10px;
  padding: 0 var(--ng-page-margin-mobile);
  width: max-content;
}
.tone-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-1);
  padding: 10px var(--ng-space-4);
  border-radius: var(--ng-radius-btn);
  border: 1.5px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  min-width: 76px;
  flex-shrink: 0;
}
.tone-tab:hover {
  border-color: var(--ng-primary);
}
.tone-tab:active {
  transform: scale(0.98);
}
.tone-tab.active {
  background: var(--ng-gradient-btn);
  border-color: var(--ng-primary);
  color: var(--ng-text-inverse);
  box-shadow: var(--ng-shadow-btn);
}
.tone-emoji {
  font-size: 22px;
  line-height: 1;
}
.tone-label {
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
  white-space: nowrap;
}
.tone-tab.active .tone-label {
  color: var(--ng-text-inverse);
}

/* Message Card */
.message-card {
  margin: var(--ng-space-2) var(--ng-page-margin-mobile) var(--ng-space-5);
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
  overflow: hidden;
  animation: cardIn var(--ng-dur-base) var(--ng-ease);
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px var(--ng-card-padding) 0;
}
.card-tone-badge {
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
}
.card-time {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
}
.card-body {
  padding: var(--ng-space-3) var(--ng-card-padding) var(--ng-card-padding);
}
.card-content {
  font-size: var(--ng-fs-body);
  line-height: 1.7;
  color: var(--ng-text-main);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
.card-actions {
  display: flex;
  gap: 10px;
  padding: 0 var(--ng-card-padding) var(--ng-card-padding);
}
.btn-copy {
  flex: 1;
  padding: 10px 0;
  border-radius: var(--ng-radius-btn);
  border: none;
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-copy:hover {
  filter: brightness(1.05);
}
.btn-copy:active {
  transform: scale(0.98);
}
.btn-regen {
  flex: 1;
  padding: 10px 0;
  border-radius: var(--ng-radius-btn);
  border: 1.5px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  color: var(--ng-text-main);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-regen:hover {
  border-color: var(--ng-primary);
  color: var(--ng-primary-deep);
}
.btn-regen:active {
  transform: scale(0.98);
}

/* Loading */
.loading-card {
  margin: var(--ng-space-5) var(--ng-page-margin-mobile);
  padding: var(--ng-space-8);
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-3);
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-body);
  box-shadow: var(--ng-shadow-card);
}
.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty Hint */
.empty-hint {
  margin: var(--ng-space-5) var(--ng-page-margin-mobile);
  padding: 40px var(--ng-space-6);
  text-align: center;
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-body);
  line-height: var(--ng-lh);
}

/* History */
.history-section {
  padding: 0 var(--ng-page-margin-mobile);
}
.section-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: var(--ng-space-6) 0 var(--ng-space-3);
}
.history-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-btn);
  border: 1px solid var(--ng-border);
  margin-bottom: 10px;
  box-shadow: var(--ng-shadow-card);
  overflow: hidden;
}
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: var(--ng-space-3) 14px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background var(--ng-dur-fast) var(--ng-ease);
}
.history-header:hover {
  background: var(--ng-bg-subtle);
}
.history-tone-badge {
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
}
.expand-icon {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  transition: transform var(--ng-dur-base) var(--ng-ease);
  display: inline-block;
}
.expand-icon.expanded {
  transform: rotate(180deg);
}
.history-body {
  padding: 0 14px 14px;
}
.history-body p {
  font-size: var(--ng-fs-body);
  line-height: 1.65;
  color: var(--ng-text-main);
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
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
}
.btn-copy-sm {
  font-size: var(--ng-fs-small);
  color: var(--ng-primary);
  background: none;
  border: 1px solid var(--ng-primary);
  border-radius: var(--ng-radius-tag);
  padding: 3px 10px;
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-copy-sm:hover {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
}
.btn-copy-sm:active {
  transform: scale(0.98);
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: all var(--ng-dur-base) var(--ng-ease);
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
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
  background: linear-gradient(to top, var(--ng-bg-mobile) 80%, transparent);
  z-index: 10;
}
.btn-simulation {
  width: 100%;
  padding: 14px 0;
  border-radius: var(--ng-radius-btn);
  border: none;
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-simulation:hover {
  filter: brightness(1.05);
}
.btn-simulation:active {
  transform: scale(0.98);
}

/* Toast */
.toast {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--ng-text-main);
  color: var(--ng-text-inverse);
  font-size: var(--ng-fs-aux);
  padding: var(--ng-space-2) var(--ng-space-5);
  border-radius: var(--ng-radius-pill);
  z-index: 100;
  pointer-events: none;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--ng-dur-base) var(--ng-ease);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
