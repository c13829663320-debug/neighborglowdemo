<template>
  <div class="action-plan-page">
    <header class="top-bar">
      <button class="btn-back" @click="router.back()">
        <span class="arrow">&larr;</span> 返回
      </button>
      <h1>行动方案</h1>
      <div style="width: 52px"></div>
    </header>

    <main v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在生成行动方案...</p>
    </main>

    <main v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn-primary" @click="loadPlan">重试</button>
    </main>

    <main v-else-if="plan" class="main-content">
      <!-- Target Card -->
      <section class="target-card">
        <span class="target-label">目标</span>
        <h2 class="target-text">{{ plan.target }}</h2>
      </section>

      <!-- Next Step (PRD 5.6: 可立即执行的下一步) -->
      <section v-if="plan.next_step" class="nextstep-card">
        <div class="nextstep-head">
          <span class="nextstep-icon">👣</span>
          <span class="nextstep-label">现在就可以做的下一步</span>
        </div>
        <p class="nextstep-text">{{ plan.next_step }}</p>
      </section>

      <!-- Safety Reminder (orange/red risk only) -->
      <section v-if="showSafety && plan.safety_reminder" class="safety-banner">
        <span class="safety-icon">&#9888;</span>
        <div class="safety-body">
          <strong>安全提醒</strong>
          <p>{{ plan.safety_reminder }}</p>
        </div>
      </section>

      <!-- Steps List -->
      <section class="steps-section">
        <h3 class="section-title">行动步骤</h3>
        <div
          v-for="step in plan.steps"
          :key="step.order"
          class="step-card"
          :class="{ 'step-done': step.done }"
        >
          <div class="step-number" :class="{ done: step.done }">{{ step.order }}</div>
          <div class="step-content">
            <p :class="{ 'text-done': step.done }">{{ step.content }}</p>
          </div>
          <label class="step-check">
            <input type="checkbox" :checked="step.done" @change="toggleStep(step)" />
            <span class="checkmark"></span>
          </label>
        </div>
      </section>

      <!-- Don't Do Section -->
      <section v-if="plan.dont_do && plan.dont_do.length" class="dont-section">
        <h3 class="section-title dont-title">不要做的事</h3>
        <div v-for="(item, idx) in plan.dont_do" :key="idx" class="dont-card">
          <span class="dont-icon">&#10060;</span>
          <span class="dont-text">{{ item }}</span>
        </div>
      </section>

      <!-- Escalation Condition -->
      <section v-if="plan.escalation_condition" class="info-card">
        <h3 class="section-title">升级条件</h3>
        <p class="info-text">{{ plan.escalation_condition }}</p>
      </section>

      <!-- Fact Record Hint (PRD 5.6: 事实记录建议) -->
      <section v-if="plan.fact_record" class="info-card fact-card">
        <h3 class="section-title">事实记录建议</h3>
        <p class="info-text">{{ plan.fact_record }}</p>
      </section>

      <!-- Communication Method -->
      <section v-if="plan.communication_method" class="comm-section">
        <h3 class="section-title">沟通方式</h3>
        <span class="comm-badge">{{ plan.communication_method }}</span>
      </section>

      <!-- Bottom Action -->
      <div class="bottom-action">
        <button class="btn-primary" @click="goMessages">
          前往沟通文案 &rarr;
        </button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'

const route = useRoute()
const router = useRouter()

const plan = ref(null)
const loading = ref(true)
const error = ref('')

const caseId = computed(() => route.params.id)

const HIGH_RISK_LEVELS = ['orange', 'red']
const showSafety = computed(() => {
  if (!plan.value) return false
  const level = plan.value.risk_level || plan.value.status || ''
  return HIGH_RISK_LEVELS.includes(level) || !!plan.value.safety_reminder
})

function toggleStep(step) {
  step.done = !step.done
}

function goMessages() {
  router.push(`/resident/case/${caseId.value}/messages`)
}

async function loadPlan() {
  loading.value = true
  error.value = ''
  try {
    const caseRes = await casesApi.get(caseId.value)
    const caseData = caseRes.data
    if (caseData.action_plan) {
      plan.value = normalizePlan(caseData.action_plan)
    } else {
      const planRes = await casesApi.generatePlan(caseId.value, {})
      plan.value = normalizePlan(planRes.data)
    }
  } catch (e) {
    console.error('Failed to load action plan', e)
    error.value = '加载行动方案失败，请重试。'
  } finally {
    loading.value = false
  }
}

function normalizePlan(raw) {
  if (!raw) return null
  return {
    ...raw,
    steps: Array.isArray(raw.steps)
      ? raw.steps.map((s, i) => ({
          order: s.order ?? i + 1,
          content: s.content || '',
          done: !!s.done,
        }))
      : [],
    dont_do: raw["don't_do"] || raw.dont_do || [],
  }
}

onMounted(loadPlan)
</script>

<style scoped>
.action-plan-page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--ng-bg-mobile);
}

/* Header */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
  position: sticky;
  top: 0;
  background: var(--ng-bg-mobile);
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
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-tag);
  padding: 6px 12px;
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover {
  background: var(--ng-bg-card);
}
.btn-back:active {
  transform: scale(0.98);
}
.arrow {
  font-size: var(--ng-fs-card);
}

/* Loading & Error */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px var(--ng-space-5);
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-body);
  gap: var(--ng-space-4);
}
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Main */
.main-content {
  padding: 0 var(--ng-page-margin-mobile) 40px;
}

/* Target Card */
.target-card {
  background: var(--ng-gradient-hero);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-space-6);
  margin-bottom: var(--ng-space-5);
}
.target-label {
  display: inline-block;
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
  background: var(--ng-primary-tint);
  border-radius: var(--ng-radius-tag);
  padding: 2px 10px;
  margin-bottom: 10px;
  letter-spacing: 1px;
}
.target-text {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  line-height: 1.5;
  margin: 0;
}

/* Next Step Card (PRD 5.6) */
.nextstep-card {
  background: var(--ng-bg-card);
  border: 1.5px solid var(--ng-primary);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding) var(--ng-space-5);
  margin-bottom: var(--ng-space-5);
  box-shadow: var(--ng-shadow-btn);
  animation: ng-fade-in var(--ng-dur-slow) var(--ng-ease) both;
}
.nextstep-head {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  margin-bottom: var(--ng-space-2);
}
.nextstep-icon {
  font-size: 18px;
  line-height: 1;
}
.nextstep-label {
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  letter-spacing: 0.5px;
  color: var(--ng-primary-deep);
}
.nextstep-text {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  line-height: 1.7;
  margin: 0;
}

/* Fact Record Card (PRD 5.6) */
.fact-card {
  border-left: 4px solid var(--ng-primary);
  background: var(--ng-bg-card);
}

/* Safety Banner */
.safety-banner {
  display: flex;
  gap: var(--ng-card-gap);
  align-items: flex-start;
  background: var(--ng-risk-red-soft);
  border: 1.5px solid var(--ng-risk-red);
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-card-padding);
  margin-bottom: var(--ng-space-5);
}
.safety-icon {
  font-size: 22px;
  flex-shrink: 0;
  line-height: 1;
  margin-top: 2px;
}
.safety-body strong {
  display: block;
  font-size: var(--ng-fs-body);
  color: var(--ng-risk-red);
  margin-bottom: var(--ng-space-1);
}
.safety-body p {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  margin: 0;
}

/* Section Title */
.section-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin-bottom: var(--ng-card-gap);
}

/* Steps */
.steps-section {
  margin-bottom: var(--ng-space-6);
}
.step-card {
  display: flex;
  align-items: center;
  gap: var(--ng-card-gap);
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-space-3) var(--ng-space-4);
  margin-bottom: 10px;
  box-shadow: var(--ng-shadow-card);
  border-left: 4px solid var(--ng-border-strong);
  transition: border-color var(--ng-dur-base) var(--ng-ease),
              opacity var(--ng-dur-base) var(--ng-ease);
}
.step-card.step-done {
  border-left-color: var(--ng-risk-green);
}
.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background var(--ng-dur-base) var(--ng-ease);
}
.step-number.done {
  background: var(--ng-risk-green);
}
.step-content {
  flex: 1;
  min-width: 0;
}
.step-content p {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  line-height: var(--ng-lh);
  margin: 0;
}
.step-content .text-done {
  text-decoration: line-through;
  color: var(--ng-text-hint);
}

/* Checkbox */
.step-check {
  position: relative;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  cursor: pointer;
}
.step-check input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}
.checkmark {
  display: block;
  width: 22px;
  height: 22px;
  border: 2px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-tag);
  background: var(--ng-bg-card);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.step-check input:checked + .checkmark {
  background: var(--ng-risk-green);
  border-color: var(--ng-risk-green);
}
.step-check input:checked + .checkmark::after {
  content: '';
  display: block;
  position: absolute;
  top: 3px;
  left: 7px;
  width: 5px;
  height: 10px;
  border: solid var(--ng-text-inverse);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* Don't Do */
.dont-section {
  margin-bottom: var(--ng-space-6);
}
.dont-title {
  color: var(--ng-risk-red);
}
.dont-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: var(--ng-risk-red-soft);
  border: 1px solid var(--ng-risk-red-soft);
  border-radius: var(--ng-radius-tag);
  padding: var(--ng-card-gap) var(--ng-space-3);
  margin-bottom: var(--ng-space-2);
}
.dont-icon {
  font-size: var(--ng-fs-body);
  flex-shrink: 0;
  margin-top: 2px;
}
.dont-text {
  font-size: var(--ng-fs-body);
  color: var(--ng-risk-red);
  line-height: var(--ng-lh);
}

/* Info Card */
.info-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding);
  margin-bottom: var(--ng-space-5);
  box-shadow: var(--ng-shadow-card);
  border: 1px solid var(--ng-border);
}
.info-text {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  margin: 0;
}

/* Communication Badge */
.comm-section {
  margin-bottom: var(--ng-space-6);
}
.comm-badge {
  display: inline-block;
  background: var(--ng-gradient-hero);
  color: var(--ng-primary-deep);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  border-radius: var(--ng-radius-pill);
  padding: 6px 16px;
  border: 1px solid var(--ng-primary);
}

/* Bottom Action */
.bottom-action {
  margin-top: var(--ng-space-2);
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
.btn-primary:hover {
  background: var(--ng-primary-dark);
}
.btn-primary:active {
  transform: scale(0.98);
}
</style>
