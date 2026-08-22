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
  background: #FFF9F0;
}

/* Header */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  position: sticky;
  top: 0;
  background: #FFF9F0;
  z-index: 10;
}
.top-bar h1 {
  font-size: 18px;
  font-weight: 600;
  color: #2D2A26;
}
.btn-back {
  background: none;
  border: 1px solid #E0D8CE;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 14px;
  color: #6B6560;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.btn-back:hover {
  background: #fff;
}
.arrow {
  font-size: 16px;
}

/* Loading & Error */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6B6560;
  font-size: 15px;
  gap: 16px;
}
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #E0D8CE;
  border-top-color: #E8A33D;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Main */
.main-content {
  padding: 0 20px 40px;
}

/* Target Card */
.target-card {
  background: linear-gradient(135deg, #FDE8C8, #FFF3E0);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
}
.target-label {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: #E8A33D;
  background: rgba(232, 163, 61, 0.15);
  border-radius: 6px;
  padding: 2px 10px;
  margin-bottom: 10px;
  letter-spacing: 1px;
}
.target-text {
  font-size: 20px;
  font-weight: 600;
  color: #2D2A26;
  line-height: 1.5;
}

/* Safety Banner */
.safety-banner {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: linear-gradient(135deg, #FFF0EE, #FFE0DB);
  border: 1px solid #F44336;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}
.safety-icon {
  font-size: 22px;
  flex-shrink: 0;
  line-height: 1;
  margin-top: 2px;
}
.safety-body strong {
  display: block;
  font-size: 14px;
  color: #D32F2F;
  margin-bottom: 4px;
}
.safety-body p {
  font-size: 13px;
  color: #5D4037;
  line-height: 1.6;
  margin: 0;
}

/* Section Title */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin-bottom: 12px;
}

/* Steps */
.steps-section {
  margin-bottom: 24px;
}
.step-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border-left: 4px solid #E0D8CE;
  transition: border-color 0.25s, opacity 0.25s;
}
.step-card.step-done {
  border-left-color: #4CAF50;
}
.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #E8A33D;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.25s;
}
.step-number.done {
  background: #4CAF50;
}
.step-content {
  flex: 1;
  min-width: 0;
}
.step-content p {
  font-size: 14px;
  color: #2D2A26;
  line-height: 1.6;
  margin: 0;
}
.step-content .text-done {
  text-decoration: line-through;
  color: #9E9893;
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
  border: 2px solid #E0D8CE;
  border-radius: 6px;
  background: #fff;
  transition: all 0.2s;
}
.step-check input:checked + .checkmark {
  background: #4CAF50;
  border-color: #4CAF50;
}
.step-check input:checked + .checkmark::after {
  content: '';
  display: block;
  position: absolute;
  top: 3px;
  left: 7px;
  width: 5px;
  height: 10px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

/* Don't Do */
.dont-section {
  margin-bottom: 24px;
}
.dont-title {
  color: #D32F2F;
}
.dont-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #FFF5F5;
  border: 1px solid #FFCDD2;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 8px;
}
.dont-icon {
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}
.dont-text {
  font-size: 14px;
  color: #C62828;
  line-height: 1.6;
}

/* Info Card */
.info-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #E0D8CE;
}
.info-text {
  font-size: 14px;
  color: #6B6560;
  line-height: 1.6;
  margin: 0;
}

/* Communication Badge */
.comm-section {
  margin-bottom: 24px;
}
.comm-badge {
  display: inline-block;
  background: linear-gradient(135deg, #FDE8C8, #FFF3E0);
  color: #B07A20;
  font-size: 14px;
  font-weight: 600;
  border-radius: 20px;
  padding: 6px 16px;
  border: 1px solid #E8A33D;
}

/* Bottom Action */
.bottom-action {
  margin-top: 8px;
}
.btn-primary {
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 14px 32px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}
.btn-primary:hover {
  background: #D4922E;
}
</style>
