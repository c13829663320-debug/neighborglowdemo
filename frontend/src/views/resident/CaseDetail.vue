<template>
  <div class="case-detail-page">
    <header class="top-bar">
      <button class="btn-back" @click="$router.back()">&#8592; 返回</button>
      <h1>{{ caseData?.title || '案例详情' }}</h1>
      <div class="top-bar-spacer"></div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <span>正在加载...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchCase">重试</button>
    </div>

    <!-- Content -->
    <div v-else-if="caseData" class="content">

      <!-- Toast -->
      <transition name="toast-fade">
        <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">{{ toast.msg }}</div>
      </transition>

      <!-- Risk + Status Banner -->
      <div class="status-banner">
        <span class="risk-badge" :class="'risk-' + caseData.risk_level">
          {{ riskLabel(caseData.risk_level) }}
        </span>
        <span class="status-badge" :class="'status-' + caseData.status">
          {{ statusLabel(caseData.status) }}
        </span>
      </div>

      <!-- Case Info Card -->
      <div class="info-card">
        <div class="info-row" v-if="caseData.category">
          <span class="info-label">类型</span>
          <span class="info-value">{{ categoryLabel(caseData.category) }}</span>
        </div>
        <div class="info-row" v-if="caseData.frequency">
          <span class="info-label">频率</span>
          <span class="info-value">{{ frequencyLabel(caseData.frequency) }}</span>
        </div>
        <div class="info-row" v-if="caseData.relationship_status">
          <span class="info-label">邻里关系</span>
          <span class="info-value">{{ caseData.relationship_status }}</span>
        </div>
        <div class="info-row" v-if="caseData.expected_outcome">
          <span class="info-label">期望结果</span>
          <span class="info-value">{{ caseData.expected_outcome }}</span>
        </div>
        <div class="info-desc" v-if="caseData.description">
          <span class="info-label">问题描述</span>
          <p>{{ caseData.description }}</p>
        </div>
      </div>

      <!-- Stats Row -->
      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-num">{{ caseData.messages_count || 0 }}</span>
          <span class="stat-label">沟通文案</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-num">{{ caseData.followups_count || 0 }}</span>
          <span class="stat-label">跟进记录</span>
        </div>
      </div>

      <!-- Process Stepper -->
      <div class="stepper-section">
        <h3 class="section-title">处理流程</h3>
        <div class="stepper">
          <div
            v-for="(step, idx) in steps"
            :key="step.key"
            class="stepper-item"
            :class="{
              'is-completed': stepStatus(idx) === 'completed',
              'is-active': stepStatus(idx) === 'active',
              'is-pending': stepStatus(idx) === 'pending',
            }"
          >
            <!-- Timeline column -->
            <div class="stepper-timeline">
              <div class="stepper-dot">
                <span v-if="stepStatus(idx) === 'completed'" class="dot-check">&#10003;</span>
                <span v-else class="dot-num">{{ idx + 1 }}</span>
              </div>
              <div v-if="idx < steps.length - 1" class="stepper-line"
                :class="{ 'line-filled': stepStatus(idx) === 'completed' }"></div>
            </div>
            <!-- Content -->
            <div class="stepper-content">
              <div class="stepper-header">
                <span class="stepper-title">{{ step.label }}</span>
                <span class="stepper-status-tag" :class="'tag-' + stepStatus(idx)">
                  {{ stepStatusText(idx) }}
                </span>
              </div>
              <p class="stepper-desc">{{ step.desc }}</p>
              <button
                v-if="step.route"
                class="btn-step"
                :class="'btn-' + stepStatus(idx)"
                @click="navigateTo(step)"
              >
                {{ stepBtnText(idx) }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Danger Zone -->
      <div class="danger-zone">
        <button class="btn-delete-case" :disabled="deleteLoading" @click="showDeleteModal = true">
          <template v-if="deleteLoading">
            <div class="spinner-sm spinner-white"></div>
            删除中...
          </template>
          <template v-else>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
            删除此案例
          </template>
        </button>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <transition name="modal-fade">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
        <div class="modal-box">
          <div class="modal-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <h3 class="modal-title">确认删除</h3>
          <p class="modal-desc">确定删除案例「<strong>{{ caseData?.title }}</strong>」？删除后所有诊断、方案和跟进记录将无法恢复。</p>
          <div class="modal-actions">
            <button class="btn-modal-cancel" @click="showDeleteModal = false">取消</button>
            <button class="btn-modal-confirm" :disabled="deleteLoading" @click="doDelete">确认删除</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'

const route = useRoute()
const router = useRouter()
const caseId = route.params.id

const loading = ref(true)
const error = ref(null)
const caseData = ref(null)
const showDeleteModal = ref(false)
const deleteLoading = ref(false)
const toast = ref({ show: false, msg: '', type: 'success' })
let toastTimer = null

function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

async function doDelete() {
  deleteLoading.value = true
  try {
    await casesApi.remove(caseId)
    showToast('案例已删除')
    setTimeout(() => { router.push('/resident/my-requests') }, 800)
  } catch (e) {
    showToast('删除失败，请重试', 'error')
  } finally {
    deleteLoading.value = false
    showDeleteModal.value = false
  }
}

// --- Step definitions ---
const steps = [
  { key: 'describe', label: '描述问题', desc: '记录你遇到的邻里问题详情', route: null },
  { key: 'diagnosis', label: 'AI诊断', desc: '智能分析问题的严重程度和根源', route: `/resident/case/${caseId}/diagnosis` },
  { key: 'plan', label: '行动方案', desc: '获取个性化的解决方案建议', route: `/resident/case/${caseId}/plan` },
  { key: 'messages', label: '沟通文案', desc: '生成合适的沟通话术', route: `/resident/case/${caseId}/messages` },
  { key: 'simulation', label: '模拟训练', desc: '在安全环境中练习沟通', route: `/resident/case/${caseId}/simulation` },
  { key: 'followup', label: '跟进反馈', desc: '记录进展，持续改善关系', route: null },
]

// --- Map API status to step progress ---
const activeStepIndex = computed(() => {
  const s = caseData.value?.status
  const map = {
    submitted: 0,
    diagnosed: 1,
    planning: 2,
    planned: 2,
    messaging: 3,
    simulating: 4,
    following_up: 5,
    resolved: 5,
    escalated: 5,
  }
  return map[s] ?? 0
})

function stepStatus(idx) {
  if (idx < activeStepIndex.value) return 'completed'
  if (idx === activeStepIndex.value) return 'active'
  return 'pending'
}

function stepStatusText(idx) {
  const s = stepStatus(idx)
  if (s === 'completed') return '已完成'
  if (s === 'active') return '进行中'
  return '待开始'
}

function stepBtnText(idx) {
  const s = stepStatus(idx)
  if (s === 'completed') return '查看'
  if (s === 'active') return '继续'
  return '查看'
}

function navigateTo(step) {
  if (step.route) {
    router.push(step.route)
  }
}

// --- Labels ---
function riskLabel(level) {
  const map = { low: '低风险', medium: '中风险', high: '高风险', critical: '极高风险' }
  return map[level] || '未知'
}

function statusLabel(status) {
  const map = {
    submitted: '已提交',
    diagnosed: '已诊断',
    planning: '规划中',
    planned: '已规划',
    messaging: '沟通中',
    simulating: '训练中',
    following_up: '跟进中',
    resolved: '已解决',
    escalated: '已升级',
  }
  return map[status] || status
}

function categoryLabel(cat) {
  const map = {
    noise: '噪音问题',
    leak: '漏水纠纷',
    public_space: '公共区域',
    pet: '宠物问题',
    garbage: '异味困扰',
    renovation: '装修施工',
    parking: '停车问题',
    other: '其他',
  }
  return map[cat] || cat
}

function frequencyLabel(freq) {
  const map = {
    once: '偶尔一次',
    occasional: '偶尔发生',
    frequent: '经常发生',
    daily: '每天发生',
  }
  return map[freq] || freq
}

// --- Fetch ---
async function fetchCase() {
  loading.value = true
  error.value = null
  try {
    const res = await casesApi.get(caseId)
    caseData.value = res.data
  } catch (e) {
    error.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(fetchCase)
</script>

<style scoped>
.case-detail-page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: #FFF9F0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
  color: #2D2A26;
  padding-bottom: 32px;
}

/* ---- Top Bar ---- */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: #fff;
  border-bottom: 1px solid #E0D8CE;
  position: sticky;
  top: 0;
  z-index: 10;
}
.top-bar h1 {
  font-size: 17px;
  font-weight: 600;
  margin: 0;
  flex: 1;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.btn-back {
  background: none;
  border: none;
  color: #E8A33D;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 0;
  white-space: nowrap;
}
.top-bar-spacer {
  width: 50px;
}

/* ---- Loading / Error ---- */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6B6560;
  font-size: 15px;
  gap: 12px;
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
.error-state {
  text-align: center;
  padding: 80px 20px;
  color: #6B6560;
}
.btn-retry {
  margin-top: 12px;
  padding: 8px 24px;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

/* ---- Content ---- */
.content {
  padding: 16px;
}

/* ---- Status Banner ---- */
.status-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.risk-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}
.risk-low { background: #4CAF50; }
.risk-medium { background: #FFC107; color: #2D2A26; }
.risk-high { background: #FF9800; }
.risk-critical { background: #F44336; }

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: #F5EDE0;
  color: #6B6560;
}
.status-resolved {
  background: #E8F5E9;
  color: #4CAF50;
}
.status-escalated {
  background: #FFEBEE;
  color: #F44336;
}

/* ---- Info Card ---- */
.info-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #E0D8CE;
  padding: 16px;
  margin-bottom: 16px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #F5EDE0;
}
.info-row:last-child {
  border-bottom: none;
}
.info-label {
  font-size: 13px;
  color: #6B6560;
  flex-shrink: 0;
}
.info-value {
  font-size: 14px;
  font-weight: 500;
  text-align: right;
}
.info-desc {
  padding-top: 12px;
  border-top: 1px solid #F5EDE0;
  margin-top: 4px;
}
.info-desc .info-label {
  display: block;
  margin-bottom: 6px;
}
.info-desc p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #2D2A26;
}

/* ---- Stats ---- */
.stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #E0D8CE;
  padding: 16px;
  margin-bottom: 16px;
  gap: 0;
}
.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.stat-num {
  font-size: 22px;
  font-weight: 700;
  color: #E8A33D;
}
.stat-label {
  font-size: 12px;
  color: #6B6560;
}
.stat-divider {
  width: 1px;
  height: 32px;
  background: #E0D8CE;
}

/* ---- Stepper ---- */
.stepper-section {
  margin-top: 4px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
}
.stepper {
  display: flex;
  flex-direction: column;
}
.stepper-item {
  display: flex;
  gap: 14px;
  min-height: 90px;
}
.stepper-item:last-child {
  min-height: auto;
}
.stepper-item:last-child .stepper-line {
  display: none;
}

/* Timeline column */
.stepper-timeline {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 28px;
  flex-shrink: 0;
}
.stepper-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  transition: all 0.3s ease;
}
.dot-check {
  font-size: 13px;
}
.dot-num {
  font-size: 12px;
}

/* Completed */
.is-completed .stepper-dot {
  background: #E8A33D;
  color: #fff;
}
.is-completed .dot-num {
  display: none;
}
/* Active */
.is-active .stepper-dot {
  background: #fff;
  border: 2.5px solid #E8A33D;
  color: #E8A33D;
  box-shadow: 0 0 0 4px rgba(232, 163, 61, 0.15);
}
/* Pending */
.is-pending .stepper-dot {
  background: #F5EDE0;
  color: #BDB5AA;
}

.stepper-line {
  width: 2px;
  flex: 1;
  background: #E0D8CE;
  margin: 4px 0;
  min-height: 16px;
  border-radius: 1px;
}
.line-filled {
  background: #E8A33D;
}

/* Content */
.stepper-content {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #E0D8CE;
  padding: 14px;
  margin-bottom: 12px;
  transition: border-color 0.3s ease;
}
.is-active .stepper-content {
  border-color: #E8A33D;
  box-shadow: 0 2px 12px rgba(232, 163, 61, 0.1);
}
.is-completed .stepper-content {
  border-color: #E8D5B5;
}
.is-pending .stepper-content {
  opacity: 0.7;
}

.stepper-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.stepper-title {
  font-size: 15px;
  font-weight: 600;
}
.stepper-status-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.tag-completed {
  background: #FFF3E0;
  color: #E8A33D;
}
.tag-active {
  background: #E8A33D;
  color: #fff;
}
.tag-pending {
  background: #F5EDE0;
  color: #BDB5AA;
}

.stepper-desc {
  font-size: 13px;
  color: #6B6560;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

/* Step buttons */
.btn-step {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-completed {
  background: #FFF3E0;
  color: #E8A33D;
}
.btn-completed:hover {
  background: #FDEBD0;
}
.btn-active {
  background: #E8A33D;
  color: #fff;
}
.btn-active:hover {
  background: #D4922E;
}
.btn-pending {
  background: #F5EDE0;
  color: #BDB5AA;
  cursor: default;
}

/* ---- Toast ---- */
.toast {
  position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
  z-index: 1000; padding: 10px 24px; border-radius: 24px;
  font-size: 13px; font-weight: 500; box-shadow: 0 4px 16px rgba(0,0,0,0.12); white-space: nowrap;
}
.toast-success { background: #2D2A26; color: #fff; }
.toast-error { background: #FF3B30; color: #fff; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* ---- Danger Zone ---- */
.danger-zone {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #E0D8CE;
}
.btn-delete-case {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #FF3B30;
  background: #fff;
  color: #FF3B30;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}
.btn-delete-case:hover:not(:disabled) {
  background: #FFF5F5;
}
.btn-delete-case:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner-sm {
  width: 14px; height: 14px; border: 2px solid rgba(255,59,48,0.3);
  border-top-color: #FF3B30; border-radius: 50%; animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
.spinner-white { border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; }

/* ---- Modal ---- */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: 24px;
}
.modal-box {
  background: #fff; border-radius: 16px; padding: 28px 24px 20px;
  width: 100%; max-width: 340px; box-shadow: 0 12px 40px rgba(0,0,0,0.15);
  text-align: center;
}
.modal-icon { margin-bottom: 12px; }
.modal-title { font-size: 17px; font-weight: 600; margin: 0 0 10px; }
.modal-desc { font-size: 14px; color: #4A4540; line-height: 1.6; margin: 0 0 20px; }
.modal-actions { display: flex; gap: 10px; }
.btn-modal-cancel {
  flex: 1; padding: 10px; border: 1px solid #E0D8CE; border-radius: 10px;
  background: #fff; font-size: 14px; color: #6B6560; cursor: pointer;
}
.btn-modal-cancel:hover { background: #F5F0E8; }
.btn-modal-confirm {
  flex: 1; padding: 10px; border: none; border-radius: 10px;
  background: #FF3B30; color: #fff; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: background 0.2s;
}
.btn-modal-confirm:hover:not(:disabled) { background: #E0332A; }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all 0.25s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
