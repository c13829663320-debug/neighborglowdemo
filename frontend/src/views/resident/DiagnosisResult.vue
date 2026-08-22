<template>
  <div class="ng-page diagnosis-page">
    <!-- Header -->
    <header class="page-header">
      <button class="icon-btn" @click="$router.back()" aria-label="返回">←</button>
      <h1 class="ng-page-title">AI 诊断结果</h1>
      <span class="header-spacer"></span>
    </header>

    <!-- Skeleton Loading -->
    <div v-if="loading" class="loading-stack">
      <SkeletonCard text="正在分析情况…" />
      <SkeletonCard text="梳理事实与需要…" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="ng-empty">
      <div class="ng-empty-icon">📡</div>
      <div class="ng-empty-title">诊断加载失败</div>
      <div class="ng-empty-desc">{{ error }}</div>
      <button class="ng-btn ng-btn-primary" @click="loadDiagnosis">重试</button>
    </div>

    <!-- Content -->
    <div v-else-if="diagnosis" class="content-stack">
      <!-- AI Badge + confidence -->
      <div class="meta-row ng-fade-in">
        <span v-if="diagnosis.analysis_type === 'llm'" class="ai-badge">
          <span class="ai-badge-icon">✦</span> AI 智能分析
        </span>
        <span v-else class="ai-badge ai-badge--local">基础模式</span>
        <span v-if="lowConfidence" class="uncertain-tag">? 部分判断不确定</span>
      </div>

      <!-- Summary Card -->
      <section class="ng-card ng-card--hero summary-card ng-fade-in">
        <div class="summary-header">
          <h2 class="ng-section-title summary-title">诊断摘要</h2>
          <span class="ng-risk-badge" :class="riskClass">{{ riskLabel }}</span>
        </div>
        <p class="summary-text">{{ diagnosis.summary }}</p>
        <div class="confidence-section">
          <div class="confidence-label">
            <span>置信度</span>
            <span class="confidence-value">{{ Math.round(diagnosis.confidence * 100) }}%</span>
          </div>
          <div class="confidence-bar">
            <div class="confidence-fill" :style="{ width: (diagnosis.confidence * 100) + '%' }"></div>
          </div>
          <p v-if="lowConfidence" class="confidence-note">
            当前信息有限，以下判断供参考，你可以随时修正。
          </p>
        </div>
      </section>

      <!-- Four Dimensions -->
      <section class="dimensions ng-fade-in">
        <h3 class="ng-section-title">四维度分析</h3>

        <div class="ng-card dimension-card" v-for="dim in dimensions" :key="dim.key">
          <div class="dimension-header">
            <div class="dimension-title">
              <span class="dimension-icon">{{ dim.icon }}</span>
              <span>{{ dim.label }}</span>
            </div>
            <button
              class="edit-btn"
              :class="{ 'edit-btn--active': editing[dim.key] }"
              @click="toggleEdit(dim.key)"
            >
              {{ editing[dim.key] ? '完成' : '编辑' }}
            </button>
          </div>

          <!-- Display mode -->
          <template v-if="!editing[dim.key]">
            <div v-if="dim.chip" class="chip-row">
              <span class="chip" v-for="(item, i) in diagnosis[dim.key]" :key="i">{{ item }}</span>
              <span v-if="!diagnosis[dim.key]?.length" class="empty-hint">暂无</span>
            </div>
            <ul v-else class="item-list">
              <li v-for="(item, i) in diagnosis[dim.key]" :key="i">{{ item }}</li>
              <li v-if="!diagnosis[dim.key]?.length" class="empty-hint">暂无</li>
            </ul>
          </template>

          <!-- Edit mode -->
          <div v-else class="edit-mode">
            <div class="edit-row" v-for="(item, i) in diagnosis[dim.key]" :key="i">
              <input class="ng-input edit-input" v-model="diagnosis[dim.key][i]" />
              <button class="remove-btn" @click="removeItem(dim.key, i)" aria-label="删除">×</button>
            </div>
            <div class="edit-row">
              <input
                class="ng-input edit-input"
                v-model="newItems[dim.key]"
                @keyup.enter="addItem(dim.key)"
                :placeholder="'添加' + dim.label + '…'"
              />
              <button class="add-btn" @click="addItem(dim.key)">添加</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Insights -->
      <section v-if="diagnosis.insights?.length" class="ng-fade-in">
        <h3 class="ng-section-title">AI 洞察</h3>
        <div class="insight-list">
          <div class="ng-card insight-item" v-for="(ins, i) in diagnosis.insights" :key="i">
            <span class="insight-num">{{ i + 1 }}</span>
            <p>{{ ins }}</p>
          </div>
        </div>
      </section>

      <!-- Key Questions -->
      <section v-if="diagnosis.key_questions?.length" class="ng-fade-in">
        <h3 class="ng-section-title">需要进一步了解</h3>
        <div class="question-list">
          <div class="question-item" v-for="(q, i) in diagnosis.key_questions" :key="i">
            <span class="question-icon">❓</span>
            <p>{{ q }}</p>
          </div>
        </div>
      </section>

      <!-- Bottom Actions -->
      <div class="bottom-actions ng-fade-in">
        <button class="ng-btn ng-btn-primary ng-btn-block" :disabled="confirming" @click="confirmDiagnosis">
          {{ confirming ? '确认中…' : (isCritical ? '确认并进入安全响应' : '确认诊断') }}
        </button>
        <button v-if="!isCritical" class="ng-btn ng-btn-secondary ng-btn-block" @click="goToPlan">
          前往行动方案 →
        </button>
        <p class="ai-note">AI 生成，仅供参考 · 你可以随时修正以上判断</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'
import { useToast } from '../../composables/useToast'
import SkeletonCard from '../../components/SkeletonCard.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const loading = ref(false)
const confirming = ref(false)
const error = ref('')
const diagnosis = ref(null)

const dimensions = [
  { key: 'facts', label: '事实', icon: '📋', chip: false },
  { key: 'assumptions', label: '推测', icon: '💭', chip: false },
  { key: 'emotions', label: '情绪', icon: '💖', chip: true },
  { key: 'needs', label: '需求', icon: '🎯', chip: false },
]

const editing = reactive({ facts: false, assumptions: false, emotions: false, needs: false })
const newItems = reactive({ facts: '', assumptions: '', emotions: '', needs: '' })

const lowConfidence = computed(() => (diagnosis.value?.confidence ?? 1) < 0.6)
const isCritical = computed(() => diagnosis.value?.risk_level === 'red')

const riskClass = computed(() => {
  const map = { green: 'ng-risk-green', yellow: 'ng-risk-yellow', orange: 'ng-risk-orange', red: 'ng-risk-red' }
  return map[diagnosis.value?.risk_level] || ''
})

const riskLabel = computed(() => {
  const labels = { green: '低风险', yellow: '中风险', orange: '高风险', red: '安全风险' }
  return labels[diagnosis.value?.risk_level] || diagnosis.value?.risk_level || ''
})

async function loadDiagnosis() {
  loading.value = true
  error.value = ''
  try {
    const caseId = route.params.id
    const caseRes = await casesApi.get(caseId)
    const caseData = caseRes.data
    if (caseData.diagnosis && caseData.diagnosis.summary) {
      diagnosis.value = caseData.diagnosis
    } else {
      try {
        const res = await casesApi.diagnoseLLM(caseId)
        diagnosis.value = res.data
      } catch (llmErr) {
        const status = llmErr.response?.status
        if (status === 400 || status === 500 || status === 503) {
          const res = await casesApi.diagnose(caseId)
          diagnosis.value = res.data
        } else {
          throw llmErr
        }
      }
    }
    // 确保字段存在
    for (const d of dimensions) {
      if (!Array.isArray(diagnosis.value[d.key])) diagnosis.value[d.key] = []
    }
  } catch (err) {
    error.value = err.message || '未知错误'
  } finally {
    loading.value = false
  }
}

function toggleEdit(key) {
  editing[key] = !editing[key]
  newItems[key] = ''
}

function addItem(key) {
  const value = newItems[key].trim()
  if (value) {
    diagnosis.value[key].push(value)
    newItems[key] = ''
  }
}

function removeItem(key, index) {
  diagnosis.value[key].splice(index, 1)
}

async function confirmDiagnosis() {
  confirming.value = true
  try {
    const caseId = route.params.id
    await casesApi.confirmDiagnosis(caseId, {
      facts: diagnosis.value.facts,
      assumptions: diagnosis.value.assumptions,
      emotions: diagnosis.value.emotions,
      needs: diagnosis.value.needs,
      risk_level: diagnosis.value.risk_level,
    })
    toast.success('诊断已确认')
    // 红色风险 → 安全响应页（PRD：不进入普通沟通建议）
    if (isCritical.value) {
      setTimeout(() => router.replace(`/resident/case/${caseId}/safety`), 600)
    }
  } catch (err) {
    toast.error('确认失败: ' + (err.message || '未知错误'))
  } finally {
    confirming.value = false
  }
}

function goToPlan() {
  router.push(`/resident/case/${route.params.id}/plan`)
}

onMounted(loadDiagnosis)
</script>

<style scoped>
.diagnosis-page {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-4);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--ng-space-2);
}
.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  font-size: 20px;
  color: var(--ng-text-main);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--ng-dur-fast) var(--ng-ease);
}
.icon-btn:hover { background: var(--ng-bg-subtle); }
.icon-btn:active { background: var(--ng-primary-soft2); transform: scale(0.98); }
.header-spacer { width: 40px; }

.loading-stack {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}

.meta-row {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  flex-wrap: wrap;
}
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  padding: 5px 14px;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
}
.ai-badge--local {
  background: var(--ng-bg-subtle);
  color: var(--ng-text-secondary);
}
.uncertain-tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux);
  background: var(--ng-risk-yellow-soft);
  color: var(--ng-primary-deep);
}

.content-stack {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-4);
}

.summary-card { padding: var(--ng-space-5); }
.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--ng-space-2);
}
.summary-title { margin-bottom: 0; }
.summary-text {
  font-size: var(--ng-fs-body);
  line-height: 1.7;
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-3) 0;
}

.confidence-label {
  display: flex;
  justify-content: space-between;
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  margin-bottom: 6px;
}
.confidence-value { font-weight: var(--ng-fw-title); color: var(--ng-primary-deep); }
.confidence-bar {
  height: 6px;
  background: var(--ng-primary-soft);
  border-radius: var(--ng-radius-pill);
  overflow: hidden;
}
.confidence-fill {
  height: 100%;
  background: var(--ng-gradient-btn);
  border-radius: var(--ng-radius-pill);
  transition: width var(--ng-dur-slow) var(--ng-ease);
}
.confidence-note {
  margin-top: var(--ng-space-2);
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}

.dimensions { display: flex; flex-direction: column; gap: var(--ng-card-gap); }
.dimensions .ng-section-title { margin-bottom: 0; }
.dimension-card { padding: var(--ng-card-padding); }
.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--ng-space-3);
}
.dimension-title {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
}
.dimension-icon { font-size: 18px; }

.edit-btn {
  padding: 5px 14px;
  background: transparent;
  border: 1px solid var(--ng-primary);
  color: var(--ng-primary);
  border-radius: var(--ng-radius-tag);
  font-size: var(--ng-fs-aux);
  cursor: pointer;
  transition: all var(--ng-dur-fast);
}
.edit-btn--active,
.edit-btn:active {
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
}

.item-list { margin: 0; padding-left: 20px; }
.item-list li {
  font-size: var(--ng-fs-body);
  line-height: 1.8;
  color: var(--ng-text-main);
}
.empty-hint { color: var(--ng-text-hint); font-size: var(--ng-fs-aux); list-style: none; }

.chip-row { display: flex; flex-wrap: wrap; gap: var(--ng-space-2); }
.chip {
  background: var(--ng-primary-soft);
  color: var(--ng-primary-deep);
  padding: 5px 14px;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux);
}

.edit-mode { display: flex; flex-direction: column; gap: var(--ng-space-2); }
.edit-row { display: flex; gap: var(--ng-space-2); align-items: center; }
.edit-input { padding: 8px 12px; font-size: var(--ng-fs-aux); }
.remove-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
  border: none;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.remove-btn:hover { background: var(--ng-risk-red); color: var(--ng-text-inverse); }
.remove-btn:active { transform: scale(0.98); }
.add-btn {
  padding: 8px 14px;
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-input);
  font-size: var(--ng-fs-aux);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.add-btn:hover { background: var(--ng-primary-dark); }
.add-btn:active { transform: scale(0.98); }

.insight-list,
.question-list {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}
.insight-item {
  display: flex;
  gap: var(--ng-space-3);
  align-items: flex-start;
  padding: 14px var(--ng-card-padding);
}
.insight-item p {
  margin: 0;
  font-size: var(--ng-fs-body);
  line-height: var(--ng-lh);
  color: var(--ng-text-main);
}
.insight-num {
  width: 24px;
  height: 24px;
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  flex-shrink: 0;
}
.question-item {
  display: flex;
  gap: var(--ng-space-3);
  align-items: flex-start;
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  padding: 14px var(--ng-card-padding);
}
.question-item p {
  margin: 0;
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  line-height: var(--ng-lh);
}
.question-icon { flex-shrink: 0; }

.bottom-actions {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-3);
  padding-bottom: var(--ng-space-5);
}
.ai-note {
  text-align: center;
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
}
</style>
