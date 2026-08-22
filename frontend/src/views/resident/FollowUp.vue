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
  background-color: #FFF9F0;
  max-width: 480px;
  margin: 0 auto;
  padding-bottom: 40px;
}

/* Header */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #E0D8CE;
  position: sticky;
  top: 0;
  z-index: 10;
}

.top-bar h1 {
  font-size: 18px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0;
}

.btn-back {
  background: none;
  border: none;
  font-size: 15px;
  color: #E8A33D;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.btn-back:hover {
  background: rgba(232, 163, 61, 0.1);
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
  padding: 60px 20px;
  gap: 12px;
  color: #6B6560;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #E0D8CE;
  border-top-color: #E8A33D;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.btn-retry {
  background: #E8A33D;
  color: #fff;
  border: none;
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

/* Content */
.content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Case Summary Card */
.case-summary-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #E0D8CE;
}

.case-summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.case-title {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 500;
  white-space: nowrap;
}

.risk-green {
  background: rgba(76, 175, 80, 0.12);
  color: #2E7D32;
}

.risk-yellow {
  background: rgba(255, 193, 7, 0.18);
  color: #A66A00;
}

.risk-orange {
  background: rgba(255, 152, 0, 0.15);
  color: #C75B00;
}

.risk-red {
  background: rgba(244, 67, 54, 0.12);
  color: #C62828;
}

/* Escalation Confirmation */
.escalation-confirmation {
  background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  border: 1px solid #A5D6A7;
}

.confirmation-icon {
  width: 48px;
  height: 48px;
  background: #4CAF50;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin: 0 auto 12px;
}

.confirmation-text {
  font-size: 15px;
  color: #2D2A26;
  font-weight: 500;
  margin: 0;
}

/* Form Card */
.form-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #E0D8CE;
}

.form-title {
  font-size: 17px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 20px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #2D2A26;
  margin-bottom: 8px;
}

.form-textarea {
  width: 100%;
  border: 1px solid #E0D8CE;
  border-radius: 10px;
  padding: 12px;
  font-size: 14px;
  color: #2D2A26;
  background: #FFF9F0;
  resize: vertical;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-textarea:focus {
  outline: none;
  border-color: #E8A33D;
  box-shadow: 0 0 0 3px rgba(232, 163, 61, 0.15);
}

.form-textarea::placeholder {
  color: #A09A94;
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
  padding: 14px 16px;
  border: 2px solid #E0D8CE;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.improvement-card:hover {
  border-color: #E8A33D;
  background: rgba(232, 163, 61, 0.03);
}

.improvement-card.selected {
  border-color: #E8A33D;
  background: rgba(232, 163, 61, 0.06);
  box-shadow: 0 0 0 3px rgba(232, 163, 61, 0.12);
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
  background: #E8F5E9;
  color: #4CAF50;
}

.improvement-icon.partial {
  background: #FFF8E1;
  color: #F9A825;
}

.improvement-icon.none {
  background: #FFEBEE;
  color: #E53935;
}

.improvement-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.improvement-title {
  font-size: 15px;
  font-weight: 500;
  color: #2D2A26;
}

.improvement-desc {
  font-size: 12px;
  color: #6B6560;
}

/* Submit Button */
.btn-submit {
  width: 100%;
  padding: 14px;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-submit:hover:not(:disabled) {
  background: #D4922F;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(232, 163, 61, 0.3);
}

.btn-submit:disabled {
  background: #E0D8CE;
  color: #A09A94;
  cursor: not-allowed;
}

.btn-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Escalation Card */
.escalation-card {
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  border: 1px solid #FFCC80;
}

.escalation-icon-wrapper {
  margin-bottom: 12px;
}

.escalation-warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: #FF9800;
  color: #fff;
  border-radius: 50%;
  font-size: 22px;
  font-weight: 700;
}

.escalation-text {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 8px 0;
}

.escalation-subtext {
  font-size: 13px;
  color: #6B6560;
  margin: 0 0 16px 0;
}

.btn-escalate {
  background: #E65100;
  color: #fff;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-escalate:hover {
  background: #BF360C;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(230, 81, 0, 0.3);
}

/* History Section */
.history-section {
  margin-top: 8px;
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 16px 0;
}

.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: #E0D8CE;
}

.timeline-item {
  position: relative;
  padding-bottom: 20px;
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
  border: 2px solid #E0D8CE;
  background: #fff;
}

.dot-improved {
  background: #4CAF50;
  border-color: #4CAF50;
}

.dot-partial {
  background: #F9A825;
  border-color: #F9A825;
}

.dot-none {
  background: #E53935;
  border-color: #E53935;
}

.timeline-content {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  border: 1px solid #E0D8CE;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.timeline-date {
  font-size: 12px;
  color: #6B6560;
}

.improvement-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.tag-improved {
  background: #E8F5E9;
  color: #2E7D32;
}

.tag-partial {
  background: #FFF8E1;
  color: #F57F17;
}

.tag-none {
  background: #FFEBEE;
  color: #C62828;
}

.timeline-body {
  font-size: 13px;
  color: #2D2A26;
  line-height: 1.5;
  margin-bottom: 4px;
}

.timeline-label {
  font-weight: 600;
  color: #6B6560;
  margin-right: 4px;
}

.timeline-escalated {
  margin-top: 8px;
}

.escalated-badge {
  font-size: 11px;
  background: #FFEBEE;
  color: #C62828;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
}

/* Empty History */
.empty-history {
  text-align: center;
  padding: 24px;
  color: #A09A94;
  font-size: 14px;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  z-index: 100;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.toast-success {
  background: #2D2A26;
  color: #fff;
}

.toast-error {
  background: #C62828;
  color: #fff;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
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
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 20px;
}

.modal-content {
  background: #fff;
  border-radius: 16px;
  padding: 28px 24px;
  max-width: 360px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 12px 0;
}

.modal-text {
  font-size: 14px;
  color: #6B6560;
  line-height: 1.6;
  margin: 0 0 24px 0;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-modal-cancel {
  background: #fff;
  color: #6B6560;
  border: 1px solid #E0D8CE;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-modal-cancel:hover {
  background: #F5F0EA;
}

.btn-modal-confirm {
  background: #E65100;
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-modal-confirm:hover:not(:disabled) {
  background: #BF360C;
}

.btn-modal-confirm:disabled {
  background: #E0D8CE;
  color: #A09A94;
  cursor: not-allowed;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
