<template>
  <div class="case-detail-page ng-fade-in">
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
      <button class="btn-retry ng-btn ng-btn-primary" @click="fetchCase">重试</button>
    </div>

    <!-- Content -->
    <div v-else-if="caseData" class="content">

      <!-- Toast -->
      <transition name="toast-fade">
        <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">{{ toast.msg }}</div>
      </transition>

      <!-- 品牌横幅 + 风险/状态（与首页视觉同风格） -->
      <div class="status-banner ng-card--hero">
        <p class="banner-brand">🌟 邻光｜邻里之光，让善意照进千万人家</p>
        <div class="banner-badges">
          <span class="ng-risk-badge" :class="'ng-risk-' + caseData.risk_level">
            {{ riskLabel(caseData.risk_level) }}
          </span>
          <span class="status-badge" :class="'status-' + caseData.status">
            {{ statusLabel(caseData.status) }}
          </span>
        </div>
        <p v-if="caseData.created_at" class="banner-date">创建于 {{ formatDate(caseData.created_at) }}</p>
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
  const map = { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }
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

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('zh-CN') : ''
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
/* ---- 页面容器（移动端 480px / 奶油白底） ---- */
.case-detail-page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--ng-bg-mobile);
  font-family: var(--ng-font-family);
  color: var(--ng-text-main);
  padding-bottom: var(--ng-space-8);
}

/* ---- 顶栏 ---- */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ng-space-3) var(--ng-space-4);
  background: var(--ng-bg-card);
  border-bottom: 1px solid var(--ng-border-strong);
  position: sticky;
  top: 0;
  z-index: 10;
}
.top-bar h1 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
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
  color: var(--ng-primary-deep);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  padding: var(--ng-space-1) 0;
  white-space: nowrap;
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { color: var(--ng-primary); }
.top-bar-spacer {
  width: 50px;
}

/* ---- 加载 / 错误 ---- */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px var(--ng-page-margin-mobile);
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-body);
  gap: var(--ng-space-3);
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
.error-state {
  text-align: center;
  padding: 80px var(--ng-page-margin-mobile);
  color: var(--ng-text-secondary);
}
.btn-retry {
  margin-top: var(--ng-space-3);
}

/* ---- 内容区 ---- */
.content {
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
}

/* ---- 品牌横幅（渐变底 + 品牌行 + 徽章） ---- */
.status-banner {
  border-radius: var(--ng-radius-card);
  padding: var(--ng-space-4);
  margin-bottom: var(--ng-space-4);
}
.banner-brand {
  font-size: var(--ng-fs-small);
  letter-spacing: 0.05em;
  color: var(--ng-primary-deep);
  opacity: 0.9;
  margin: 0 0 var(--ng-space-3);
}
.banner-badges {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--ng-space-2);
}
.banner-date {
  font-size: var(--ng-fs-small);
  color: var(--ng-primary-deep);
  opacity: 0.7;
  margin: var(--ng-space-2) 0 0;
}
.status-badge {
  display: inline-block;
  padding: 5px 12px;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-strong);
  background: var(--ng-bg-subtle);
  color: var(--ng-text-secondary);
}
.status-resolved {
  background: var(--ng-risk-green-soft);
  color: var(--ng-risk-green);
}
.status-escalated {
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
}

/* ---- 案例信息卡 ---- */
.info-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: var(--ng-card-padding);
  margin-bottom: var(--ng-space-4);
  box-shadow: var(--ng-shadow-card);
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--ng-border);
}
.info-row:last-child {
  border-bottom: none;
}
.info-label {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  flex-shrink: 0;
}
.info-value {
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  text-align: right;
}
.info-desc {
  padding-top: var(--ng-space-3);
}
.info-desc .info-label {
  display: block;
  margin-bottom: 6px;
}
.info-desc p {
  margin: 0;
  font-size: var(--ng-fs-body);
  line-height: var(--ng-lh);
  color: var(--ng-text-main);
}

/* ---- 统计行 ---- */
.stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: var(--ng-card-padding);
  margin-bottom: var(--ng-space-4);
  box-shadow: var(--ng-shadow-card);
  gap: 0;
}
.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-1);
}
.stat-num {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary);
}
.stat-label {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}
.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--ng-border-strong);
}

/* ---- 处理流程步骤器 ---- */
.stepper-section {
  margin-top: var(--ng-space-1);
}
.section-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  margin: 0 0 var(--ng-space-4) 0;
  color: var(--ng-text-main);
}
.stepper {
  display: flex;
  flex-direction: column;
}
.stepper-item {
  display: flex;
  gap: var(--ng-space-3);
  min-height: 90px;
}
.stepper-item:last-child {
  min-height: auto;
}
.stepper-item:last-child .stepper-line {
  display: none;
}

/* 时间轴列 */
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
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  flex-shrink: 0;
  transition: all var(--ng-dur-base) var(--ng-ease);
}
.dot-check {
  font-size: var(--ng-fs-aux);
}
.dot-num {
  font-size: var(--ng-fs-small);
}

/* 已完成 */
.is-completed .stepper-dot {
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  box-shadow: var(--ng-shadow-btn);
}
.is-completed .dot-num {
  display: none;
}
/* 进行中 */
.is-active .stepper-dot {
  background: var(--ng-bg-card);
  border: 2px solid var(--ng-primary);
  color: var(--ng-primary-deep);
  box-shadow: 0 0 0 4px var(--ng-primary-tint);
}
/* 待开始 */
.is-pending .stepper-dot {
  background: var(--ng-bg-subtle);
  color: var(--ng-text-hint);
}

.stepper-line {
  width: 2px;
  flex: 1;
  background: var(--ng-border-strong);
  margin: var(--ng-space-1) 0;
  min-height: 16px;
  border-radius: var(--ng-radius-pill);
}
.line-filled {
  background: var(--ng-primary);
}

/* 步骤内容卡 */
.stepper-content {
  flex: 1;
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: var(--ng-card-padding);
  margin-bottom: var(--ng-card-gap);
  transition: border-color var(--ng-dur-base) var(--ng-ease),
              box-shadow var(--ng-dur-base) var(--ng-ease);
}
.is-active .stepper-content {
  border-color: var(--ng-primary);
  box-shadow: var(--ng-shadow-card-hover);
}
.is-completed .stepper-content {
  border-color: var(--ng-border-strong);
}
.is-pending .stepper-content {
  opacity: 0.7;
}

.stepper-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--ng-space-1);
}
.stepper-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
}
.stepper-status-tag {
  font-size: var(--ng-fs-small);
  padding: 2px 8px;
  border-radius: var(--ng-radius-tag);
  font-weight: var(--ng-fw-strong);
}
.tag-completed {
  background: var(--ng-primary-soft2);
  color: var(--ng-primary-deep);
}
.tag-active {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
}
.tag-pending {
  background: var(--ng-bg-subtle);
  color: var(--ng-text-hint);
}

.stepper-desc {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  margin: 0 0 10px 0;
  line-height: 1.5;
}

/* 步骤按钮 */
.btn-step {
  display: inline-block;
  padding: 6px var(--ng-space-4);
  border-radius: var(--ng-radius-tag);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  border: none;
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  font-family: var(--ng-font-family);
}
.btn-completed {
  background: var(--ng-primary-soft2);
  color: var(--ng-primary-deep);
}
.btn-completed:hover {
  background: var(--ng-primary-soft);
}
.btn-active {
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  box-shadow: var(--ng-shadow-btn);
}
.btn-active:hover {
  filter: brightness(0.95);
}
.btn-active:active {
  transform: scale(0.98);
}
.btn-pending {
  background: var(--ng-bg-subtle);
  color: var(--ng-text-hint);
  cursor: default;
}

/* ---- Toast ---- */
.toast {
  position: fixed; top: var(--ng-space-4); left: 50%; transform: translateX(-50%);
  z-index: 1000; padding: 10px var(--ng-space-6); border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-strong); box-shadow: var(--ng-shadow-float); white-space: nowrap;
}
.toast-success { background: var(--ng-text-main); color: var(--ng-text-inverse); }
.toast-error { background: var(--ng-risk-red); color: var(--ng-text-inverse); }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* ---- 危险区 ---- */
.danger-zone {
  margin-top: var(--ng-space-6);
  padding-top: var(--ng-space-4);
  border-top: 1px solid var(--ng-border-strong);
}
.btn-delete-case {
  width: 100%;
  padding: var(--ng-space-3);
  border-radius: var(--ng-radius-btn);
  border: 1px solid var(--ng-risk-red);
  background: var(--ng-bg-card);
  color: var(--ng-risk-red);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--ng-space-2);
  transition: all var(--ng-dur-fast) var(--ng-ease);
  font-family: var(--ng-font-family);
}
.btn-delete-case:hover:not(:disabled) {
  background: var(--ng-risk-red-soft);
}
.btn-delete-case:active:not(:disabled) {
  transform: scale(0.98);
}
.btn-delete-case:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner-sm {
  width: 14px; height: 14px; border: 2px solid var(--ng-risk-red-soft);
  border-top-color: var(--ng-risk-red); border-radius: 50%; animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
.spinner-white { border: 2px solid var(--ng-risk-red-soft); border-top-color: var(--ng-risk-red); }

/* ---- 删除确认弹窗 ---- */
.modal-overlay {
  position: fixed; inset: 0; background: color-mix(in srgb, var(--ng-text-main) 40%, transparent); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: var(--ng-space-6);
}
.modal-box {
  background: var(--ng-bg-card); border-radius: var(--ng-radius-card); padding: 28px var(--ng-space-6) var(--ng-space-5);
  width: 100%; max-width: 340px; box-shadow: var(--ng-shadow-float);
  border: 1px solid var(--ng-border);
  text-align: center;
}
.modal-icon { margin-bottom: var(--ng-space-3); }
.modal-title { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0 0 10px; }
.modal-desc { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); line-height: var(--ng-lh); margin: 0 0 var(--ng-space-5); }
.modal-actions { display: flex; gap: 10px; }
.btn-modal-cancel {
  flex: 1; padding: 10px; border: 1px solid var(--ng-border-strong); border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card); font-size: var(--ng-fs-body); color: var(--ng-text-secondary); cursor: pointer;
  transition: background var(--ng-dur-fast) var(--ng-ease); font-family: var(--ng-font-family);
}
.btn-modal-cancel:hover { background: var(--ng-bg-subtle); }
.btn-modal-confirm {
  flex: 1; padding: 10px; border: none; border-radius: var(--ng-radius-btn);
  background: var(--ng-risk-red); color: var(--ng-text-inverse); font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease); font-family: var(--ng-font-family);
}
.btn-modal-confirm:hover:not(:disabled) { filter: brightness(0.9); }
.btn-modal-confirm:active:not(:disabled) { transform: scale(0.98); }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
