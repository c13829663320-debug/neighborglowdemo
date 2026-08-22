<template>
  <div class="followup-page">
    <!-- Header -->
    <header class="top-bar">
      <button class="btn-back" @click="goBack">&#8592; 返回</button>
      <h1>跟进反馈</h1>
      <div class="top-bar-spacer"></div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>正在加载...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchData">重试</button>
    </div>

    <!-- Content -->
    <div v-else class="content">
      <!-- Case Summary Card -->
      <div class="case-summary-card" v-if="caseData">
        <div class="case-summary-header">
          <h3 class="case-title">{{ caseData.title }}</h3>
          <span class="risk-badge" :class="'risk-' + caseData.risk_level">
            {{ riskLabel(caseData.risk_level) }}
          </span>
        </div>
      </div>

      <!-- Escalation Confirmation Banner -->
      <div v-if="escalated" class="escalation-confirmation">
        <div class="confirmation-icon">&#10003;</div>
        <p class="confirmation-text">已成功升级至社区管理者，请耐心等待处理结果</p>
      </div>

      <!-- Follow-up Form -->
      <div class="form-card" v-if="!escalated">
        <h2 class="form-title">记录跟进情况</h2>

        <!-- Action Taken -->
        <div class="form-group">
          <label class="form-label">你采取了什么行动？</label>
          <textarea
            v-model="form.action_taken"
            class="form-textarea"
            placeholder="描述你采取的具体行动..."
            rows="3"
          ></textarea>
        </div>

        <!-- Response Received -->
        <div class="form-group">
          <label class="form-label">对方如何回应？</label>
          <textarea
            v-model="form.response_received"
            class="form-textarea"
            placeholder="描述对方的回应..."
            rows="3"
          ></textarea>
        </div>

        <!-- Improvement Level -->
        <div class="form-group">
          <label class="form-label">情况改善程度</label>
          <div class="improvement-cards">
            <div
              class="improvement-card"
              :class="{ selected: form.improvement_level === 'improved' }"
              @click="selectImprovement('improved')"
            >
              <div class="improvement-icon improved">&#10004;</div>
              <div class="improvement-info">
                <span class="improvement-title">明显改善</span>
                <span class="improvement-desc">情况有了积极变化</span>
              </div>
            </div>

            <div
              class="improvement-card"
              :class="{ selected: form.improvement_level === 'partial' }"
              @click="selectImprovement('partial')"
            >
              <div class="improvement-icon partial">&#9679;</div>
              <div class="improvement-info">
                <span class="improvement-title">部分改善</span>
                <span class="improvement-desc">有一些进展但还需努力</span>
              </div>
            </div>

            <div
              class="improvement-card"
              :class="{ selected: form.improvement_level === 'none' }"
              @click="selectImprovement('none')"
            >
              <div class="improvement-icon none">&#10006;</div>
              <div class="improvement-info">
                <span class="improvement-title">没有改善</span>
                <span class="improvement-desc">情况没有变化</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <button
          class="btn-submit"
          :disabled="!canSubmit || submitting"
          @click="submitFollowup"
        >
          <span v-if="submitting" class="btn-loading"></span>
          {{ submitting ? '提交中...' : '提交反馈' }}
        </button>
      </div>

      <!-- Escalation Section -->
      <div v-if="form.improvement_level === 'none' && !escalated" class="escalation-card">
        <div class="escalation-icon-wrapper">
          <span class="escalation-warning-icon">!</span>
        </div>
        <p class="escalation-text">情况没有改善？你可以申请升级处理</p>
        <p class="escalation-subtext">社区管理者将介入协调，帮助解决邻里纠纷</p>
        <button class="btn-escalate" @click="showEscalateConfirm = true">
          升级至社区管理者
        </button>
      </div>

      <!-- History Section -->
      <div class="history-section" v-if="followups.length > 0">
        <h2 class="section-title">过往跟进记录</h2>
        <div class="timeline">
          <div class="timeline-item" v-for="item in followups" :key="item.id">
            <div class="timeline-dot" :class="'dot-' + item.improvement_level"></div>
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="timeline-date">{{ formatDate(item.created_at) }}</span>
                <span class="improvement-tag" :class="'tag-' + item.improvement_level">
                  {{ improvementLabel(item.improvement_level) }}
                </span>
              </div>
              <div class="timeline-body" v-if="item.action_taken">
                <span class="timeline-label">行动：</span>
                <span>{{ item.action_taken }}</span>
              </div>
              <div class="timeline-body" v-if="item.response_received">
                <span class="timeline-label">回应：</span>
                <span>{{ item.response_received }}</span>
              </div>
              <div class="timeline-escalated" v-if="item.is_escalated">
                <span class="escalated-badge">已升级处理</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty History -->
      <div class="empty-history" v-else-if="!loading">
        <p>暂无跟进记录</p>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="'toast-' + toast.type">
        {{ toast.message }}
      </div>
    </Transition>

    <!-- Escalation Confirm Modal -->
    <Transition name="modal">
      <div v-if="showEscalateConfirm" class="modal-overlay" @click.self="showEscalateConfirm = false">
        <div class="modal-content">
          <h3 class="modal-title">确认升级处理</h3>
          <p class="modal-text">
            升级后，社区管理者将收到通知并介入协调。请确认你已经尝试过直接沟通但未能解决问题。
          </p>
          <div class="modal-actions">
            <button class="btn-modal-cancel" @click="showEscalateConfirm = false">取消</button>
            <button class="btn-modal-confirm" @click="confirmEscalate" :disabled="escalating">
              {{ escalating ? '处理中...' : '确认升级' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'

const route = useRoute()
const router = useRouter()
const caseId = route.params.id

// State
const loading = ref(true)
const error = ref('')
const caseData = ref(null)
const followups = ref([])
const submitting = ref(false)
const escalating = ref(false)
const escalated = ref(false)
const showEscalateConfirm = ref(false)

const form = reactive({
  action_taken: '',
  response_received: '',
  improvement_level: '',
})

const toast = reactive({
  show: false,
  message: '',
  type: 'success',
})

// Computed
const canSubmit = computed(() => {
  return form.action_taken.trim() && form.improvement_level
})

// Methods
function goBack() {
  router.push(`/resident/case/${caseId}`)
}

function riskLabel(level) {
  const map = { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }
  return map[level] || level || '未评估'
}

function improvementLabel(level) {
  const map = { improved: '明显改善', partial: '部分改善', none: '没有改善' }
  return map[level] || level || '未知'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${min}`
}

function selectImprovement(level) {
  form.improvement_level = level
}

function showToast(message, type = 'success') {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => {
    toast.show = false
  }, 3000)
}

async function fetchData() {
  loading.value = true
  error.value = ''
  try {
    const [caseRes, followupsRes] = await Promise.all([
      casesApi.get(caseId),
      casesApi.listFollowups(caseId),
    ])
    caseData.value = caseRes.data
    followups.value = followupsRes.data || []

    // Check if already escalated
    if (caseData.value.status === 'escalated') {
      escalated.value = true
    }
  } catch (e) {
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function submitFollowup() {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    const payload = {
      action_taken: form.action_taken,
      response_received: form.response_received,
      improvement_level: form.improvement_level,
      is_escalated: false,
    }
    const res = await casesApi.createFollowup(caseId, payload)

    // Add to history
    followups.value.unshift(res.data)

    // Reset form
    form.action_taken = ''
    form.response_received = ''
    form.improvement_level = ''

    showToast('反馈提交成功')
  } catch (e) {
    showToast('提交失败，请重试', 'error')
  } finally {
    submitting.value = false
  }
}

async function confirmEscalate() {
  if (escalating.value) return
  escalating.value = true

  try {
    await casesApi.escalate(caseId)
    escalated.value = true
    showEscalateConfirm.value = false
    showToast('已成功升级至社区管理者')
  } catch (e) {
    showToast('升级失败，请重试', 'error')
  } finally {
    escalating.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.followup-page {
  min-height: 100vh;
  background-color: var(--ng-bg-mobile);
  max-width: 480px;
  margin: 0 auto;
  padding-bottom: 40px;
}

/* Header */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
  background: var(--ng-bg-card);
  border-bottom: 1px solid var(--ng-border-strong);
  position: sticky;
  top: 0;
  z-index: 10;
}

.top-bar h1 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}

.btn-back {
  background: none;
  border: none;
  font-size: var(--ng-fs-body);
  color: var(--ng-primary);
  cursor: pointer;
  padding: var(--ng-space-1) var(--ng-space-2);
  border-radius: var(--ng-radius-tag);
  transition: background var(--ng-dur-fast) var(--ng-ease);
}

.btn-back:hover {
  background: var(--ng-primary-tint);
}

.btn-back:active {
  transform: scale(0.98);
}

.top-bar-spacer {
  width: 60px;
}

/* Loading & Error */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px var(--ng-page-margin-mobile);
  gap: var(--ng-space-3);
  color: var(--ng-text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-retry {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  border: none;
  padding: var(--ng-space-2) var(--ng-space-5);
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-body);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}

.btn-retry:hover {
  background: var(--ng-primary-dark);
}

.btn-retry:active {
  transform: scale(0.98);
}

/* Content */
.content {
  padding: var(--ng-card-padding);
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}

/* Case Summary Card */
.case-summary-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding);
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
}

.case-summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ng-space-3);
}

.case-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-badge {
  font-size: var(--ng-fs-small);
  padding: var(--ng-space-1) 10px;
  border-radius: var(--ng-radius-pill);
  font-weight: var(--ng-fw-strong);
  white-space: nowrap;
}

.risk-green {
  background: var(--ng-risk-green);
  color: var(--ng-text-inverse);
}

.risk-yellow {
  background: var(--ng-risk-yellow);
  color: var(--ng-text-main);
}

.risk-orange {
  background: var(--ng-risk-orange);
  color: var(--ng-text-inverse);
}

.risk-red {
  background: var(--ng-risk-red);
  color: var(--ng-text-inverse);
}

/* Escalation Confirmation */
.escalation-confirmation {
  background: var(--ng-risk-green-soft);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-space-6);
  text-align: center;
  border: 1px solid var(--ng-risk-green);
}

.confirmation-icon {
  width: 48px;
  height: 48px;
  background: var(--ng-risk-green);
  color: var(--ng-text-inverse);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin: 0 auto var(--ng-space-3);
}

.confirmation-text {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  font-weight: var(--ng-fw-strong);
  margin: 0;
}

/* Form Card */
.form-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding);
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
}

.form-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-5) 0;
}

.form-group {
  margin-bottom: var(--ng-space-5);
}

.form-label {
  display: block;
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
  margin-bottom: var(--ng-space-2);
}

.form-textarea {
  width: 100%;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-input);
  padding: var(--ng-space-3);
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  background: var(--ng-bg-mobile);
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color var(--ng-dur-fast) var(--ng-ease),
              box-shadow var(--ng-dur-fast) var(--ng-ease);
}

.form-textarea:focus {
  outline: none;
  border-color: var(--ng-primary);
  box-shadow: 0 0 0 3px var(--ng-primary-tint);
}

.form-textarea::placeholder {
  color: var(--ng-text-hint);
}

/* Improvement Cards */
.improvement-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.improvement-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px var(--ng-space-4);
  border: 2px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  background: var(--ng-bg-card);
}

.improvement-card:hover {
  border-color: var(--ng-primary);
  background: var(--ng-primary-soft2);
}

.improvement-card:active {
  transform: scale(0.98);
}

.improvement-card.selected {
  border-color: var(--ng-primary);
  background: var(--ng-primary-soft2);
  box-shadow: 0 0 0 3px var(--ng-primary-tint);
}

.improvement-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.improvement-icon.improved {
  background: var(--ng-risk-green-soft);
  color: var(--ng-risk-green);
}

.improvement-icon.partial {
  background: var(--ng-risk-yellow-soft);
  color: var(--ng-risk-yellow);
}

.improvement-icon.none {
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
}

.improvement-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.improvement-title {
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
}

.improvement-desc {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}

/* Submit Button */
.btn-submit {
  width: 100%;
  padding: 14px;
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--ng-space-2);
}

.btn-submit:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.btn-submit:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-submit:disabled {
  background: var(--ng-border-strong);
  color: var(--ng-text-hint);
  cursor: not-allowed;
  box-shadow: none;
}

.btn-loading {
  width: 16px;
  height: 16px;
  border: 2px solid var(--ng-primary-soft);
  border-top-color: var(--ng-text-inverse);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Escalation Card */
.escalation-card {
  background: linear-gradient(135deg, var(--ng-risk-orange-soft), var(--ng-primary-soft));
  border-radius: var(--ng-radius-card);
  padding: var(--ng-space-6);
  text-align: center;
  border: 1px solid var(--ng-risk-orange);
}

.escalation-icon-wrapper {
  margin-bottom: var(--ng-space-3);
}

.escalation-warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: var(--ng-risk-orange);
  color: var(--ng-text-inverse);
  border-radius: 50%;
  font-size: 22px;
  font-weight: 700;
}

.escalation-text {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-2) 0;
}

.escalation-subtext {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  margin: 0 0 var(--ng-space-4) 0;
}

.btn-escalate {
  background: var(--ng-risk-orange);
  color: var(--ng-text-inverse);
  border: none;
  padding: var(--ng-space-3) var(--ng-space-6);
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}

.btn-escalate:hover {
  filter: brightness(0.92);
  transform: translateY(-1px);
}

.btn-escalate:active {
  transform: scale(0.98);
}

/* History Section */
.history-section {
  margin-top: var(--ng-space-2);
}

.section-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-4) 0;
}

.timeline {
  position: relative;
  padding-left: var(--ng-space-6);
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--ng-border-strong);
}

.timeline-item {
  position: relative;
  padding-bottom: var(--ng-space-5);
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -20px;
  top: 6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
}

.dot-improved {
  background: var(--ng-risk-green);
  border-color: var(--ng-risk-green);
}

.dot-partial {
  background: var(--ng-risk-yellow);
  border-color: var(--ng-risk-yellow);
}

.dot-none {
  background: var(--ng-risk-red);
  border-color: var(--ng-risk-red);
}

.timeline-content {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-btn);
  padding: 14px;
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--ng-space-2);
}

.timeline-date {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
}

.improvement-tag {
  font-size: var(--ng-fs-small);
  padding: 2px var(--ng-space-2);
  border-radius: var(--ng-radius-tag);
  font-weight: var(--ng-fw-strong);
}

.tag-improved {
  background: var(--ng-risk-green-soft);
  color: var(--ng-risk-green);
}

.tag-partial {
  background: var(--ng-risk-yellow-soft);
  color: var(--ng-risk-orange);
}

.tag-none {
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
}

.timeline-body {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-main);
  line-height: 1.5;
  margin-bottom: var(--ng-space-1);
}

.timeline-label {
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-secondary);
  margin-right: var(--ng-space-1);
}

.timeline-escalated {
  margin-top: var(--ng-space-2);
}

.escalated-badge {
  font-size: var(--ng-fs-small);
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
  padding: 3px var(--ng-space-2);
  border-radius: var(--ng-radius-tag);
  font-weight: var(--ng-fw-strong);
}

/* Empty History */
.empty-history {
  text-align: center;
  padding: var(--ng-space-6);
  color: var(--ng-text-hint);
  font-size: var(--ng-fs-body);
}

/* Toast */
.toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: var(--ng-space-3) var(--ng-space-6);
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  z-index: 100;
  box-shadow: var(--ng-shadow-float);
}

.toast-success {
  background: var(--ng-text-main);
  color: var(--ng-text-inverse);
}

.toast-error {
  background: var(--ng-risk-red);
  color: var(--ng-text-inverse);
}

.toast-enter-active,
.toast-leave-active {
  transition: all var(--ng-dur-base) var(--ng-ease);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: color-mix(in srgb, var(--ng-text-main) 45%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: var(--ng-page-margin-mobile);
}

.modal-content {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  padding: 28px var(--ng-space-6);
  max-width: 360px;
  width: 100%;
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-float);
}

.modal-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-3) 0;
}

.modal-text {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  margin: 0 0 var(--ng-space-6) 0;
}

.modal-actions {
  display: flex;
  gap: var(--ng-space-3);
  justify-content: flex-end;
}

.btn-modal-cancel {
  background: var(--ng-bg-card);
  color: var(--ng-text-secondary);
  border: 1px solid var(--ng-border-strong);
  padding: 10px var(--ng-space-5);
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-body);
  cursor: pointer;
  transition: background var(--ng-dur-fast) var(--ng-ease);
}

.btn-modal-cancel:hover {
  background: var(--ng-bg-subtle);
}

.btn-modal-cancel:active {
  transform: scale(0.98);
}

.btn-modal-confirm {
  background: var(--ng-risk-orange);
  color: var(--ng-text-inverse);
  border: none;
  padding: 10px var(--ng-space-5);
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}

.btn-modal-confirm:hover:not(:disabled) {
  filter: brightness(0.92);
}

.btn-modal-confirm:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-modal-confirm:disabled {
  background: var(--ng-border-strong);
  color: var(--ng-text-hint);
  cursor: not-allowed;
  box-shadow: none;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--ng-dur-base) var(--ng-ease);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
