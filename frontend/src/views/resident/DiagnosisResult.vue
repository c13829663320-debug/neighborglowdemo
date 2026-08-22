<template>
  <div class="diagnosis-result-page">
    <!-- Header -->
    <div class="header">
      <button class="back-btn" @click="$router.back()">
        <span>←</span>
      </button>
      <h1>AI 诊断结果</h1>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在生成诊断结果...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadDiagnosis" class="retry-btn">重试</button>
    </div>

    <!-- Content -->
    <div v-else-if="diagnosis" class="content">
      <!-- AI Badge -->
      <div v-if="diagnosis.analysis_type === 'llm'" class="ai-badge">
        <span class="ai-badge-icon">✦</span>
        <span>AI 智能分析</span>
      </div>

      <!-- Summary Card -->
      <div class="summary-card">
        <div class="summary-header">
          <h2>诊断摘要</h2>
          <div class="risk-badge" :class="riskClass">
            {{ riskLabel }}
          </div>
        </div>
        <p class="summary-text" :class="{ 'summary-text--large': diagnosis.analysis_type === 'llm' && diagnosis.summary }">{{ diagnosis.summary }}</p>
        
        <div class="confidence-section">
          <div class="confidence-label">
            <span>置信度</span>
            <span class="confidence-value">{{ Math.round(diagnosis.confidence * 100) }}%</span>
          </div>
          <div class="confidence-bar">
            <div 
              class="confidence-fill" 
              :style="{ width: (diagnosis.confidence * 100) + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Four Dimensions -->
      <div class="dimensions-section">
        <h3>四维度分析</h3>
        
        <!-- Facts -->
        <div class="dimension-card">
          <div class="dimension-header">
            <div class="dimension-title">
              <span class="icon">📋</span>
              <span>事实</span>
            </div>
            <button 
              v-if="!editing.facts" 
              @click="startEdit('facts')" 
              class="edit-btn"
            >
              编辑
            </button>
            <button 
              v-else 
              @click="finishEdit('facts')" 
              class="edit-btn finish"
            >
              完成编辑
            </button>
          </div>
          
          <div class="dimension-content">
            <ul v-if="!editing.facts" class="item-list">
              <li v-for="(item, index) in diagnosis.facts" :key="index">
                {{ item }}
              </li>
            </ul>
            
            <div v-else class="edit-mode">
              <div class="editable-list">
                <div 
                  v-for="(item, index) in diagnosis.facts" 
                  :key="index" 
                  class="editable-item"
                >
                  <input 
                    v-model="diagnosis.facts[index]" 
                    type="text" 
                    class="edit-input"
                  />
                  <button @click="removeItem('facts', index)" class="remove-btn">
                    ×
                  </button>
                </div>
              </div>
              <div class="add-item">
                <input 
                  v-model="newItems.facts" 
                  @keyup.enter="addItem('facts')"
                  type="text" 
                  placeholder="添加新事实..." 
                  class="add-input"
                />
                <button @click="addItem('facts')" class="add-btn">添加</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Assumptions -->
        <div class="dimension-card">
          <div class="dimension-header">
            <div class="dimension-title">
              <span class="icon">💭</span>
              <span>推测</span>
            </div>
            <button 
              v-if="!editing.assumptions" 
              @click="startEdit('assumptions')" 
              class="edit-btn"
            >
              编辑
            </button>
            <button 
              v-else 
              @click="finishEdit('assumptions')" 
              class="edit-btn finish"
            >
              完成编辑
            </button>
          </div>
          
          <div class="dimension-content">
            <ul v-if="!editing.assumptions" class="item-list">
              <li v-for="(item, index) in diagnosis.assumptions" :key="index">
                {{ item }}
              </li>
            </ul>
            
            <div v-else class="edit-mode">
              <div class="editable-list">
                <div 
                  v-for="(item, index) in diagnosis.assumptions" 
                  :key="index" 
                  class="editable-item"
                >
                  <input 
                    v-model="diagnosis.assumptions[index]" 
                    type="text" 
                    class="edit-input"
                  />
                  <button @click="removeItem('assumptions', index)" class="remove-btn">
                    ×
                  </button>
                </div>
              </div>
              <div class="add-item">
                <input 
                  v-model="newItems.assumptions" 
                  @keyup.enter="addItem('assumptions')"
                  type="text" 
                  placeholder="添加新推测..." 
                  class="add-input"
                />
                <button @click="addItem('assumptions')" class="add-btn">添加</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Emotions -->
        <div class="dimension-card">
          <div class="dimension-header">
            <div class="dimension-title">
              <span class="icon">💖</span>
              <span>情绪</span>
            </div>
            <button 
              v-if="!editing.emotions" 
              @click="startEdit('emotions')" 
              class="edit-btn"
            >
              编辑
            </button>
            <button 
              v-else 
              @click="finishEdit('emotions')" 
              class="edit-btn finish"
            >
              完成编辑
            </button>
          </div>
          
          <div class="dimension-content">
            <div v-if="!editing.emotions" class="tag-chips">
              <span 
                v-for="(item, index) in diagnosis.emotions" 
                :key="index" 
                class="chip"
              >
                {{ item }}
              </span>
            </div>
            
            <div v-else class="edit-mode">
              <div class="editable-chips">
                <div 
                  v-for="(item, index) in diagnosis.emotions" 
                  :key="index" 
                  class="editable-chip"
                >
                  <input 
                    v-model="diagnosis.emotions[index]" 
                    type="text" 
                    class="chip-input"
                  />
                  <button @click="removeItem('emotions', index)" class="chip-remove">
                    ×
                  </button>
                </div>
              </div>
              <div class="add-item">
                <input 
                  v-model="newItems.emotions" 
                  @keyup.enter="addItem('emotions')"
                  type="text" 
                  placeholder="添加情绪标签..." 
                  class="add-input"
                />
                <button @click="addItem('emotions')" class="add-btn">添加</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Needs -->
        <div class="dimension-card">
          <div class="dimension-header">
            <div class="dimension-title">
              <span class="icon">🎯</span>
              <span>需求</span>
            </div>
            <button 
              v-if="!editing.needs" 
              @click="startEdit('needs')" 
              class="edit-btn"
            >
              编辑
            </button>
            <button 
              v-else 
              @click="finishEdit('needs')" 
              class="edit-btn finish"
            >
              完成编辑
            </button>
          </div>
          
          <div class="dimension-content">
            <ul v-if="!editing.needs" class="item-list">
              <li v-for="(item, index) in diagnosis.needs" :key="index">
                {{ item }}
              </li>
            </ul>
            
            <div v-else class="edit-mode">
              <div class="editable-list">
                <div 
                  v-for="(item, index) in diagnosis.needs" 
                  :key="index" 
                  class="editable-item"
                >
                  <input 
                    v-model="diagnosis.needs[index]" 
                    type="text" 
                    class="edit-input"
                  />
                  <button @click="removeItem('needs', index)" class="remove-btn">
                    ×
                  </button>
                </div>
              </div>
              <div class="add-item">
                <input 
                  v-model="newItems.needs" 
                  @keyup.enter="addItem('needs')"
                  type="text" 
                  placeholder="添加新需求..." 
                  class="add-input"
                />
                <button @click="addItem('needs')" class="add-btn">添加</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Insights -->
      <div v-if="diagnosis.insights && diagnosis.insights.length > 0" class="insights-section">
        <h3>AI 洞察</h3>
        <div class="insights-list">
          <div 
            v-for="(insight, index) in diagnosis.insights" 
            :key="index" 
            class="insight-item"
          >
            <span class="insight-number">{{ index + 1 }}</span>
            <p class="insight-text">{{ insight }}</p>
          </div>
        </div>
      </div>

      <!-- Key Questions -->
      <div v-if="diagnosis.key_questions && diagnosis.key_questions.length > 0" class="questions-section">
        <h3>需要进一步了解</h3>
        <div class="questions-list">
          <div 
            v-for="(question, index) in diagnosis.key_questions" 
            :key="index" 
            class="question-item"
          >
            <span class="question-icon">❓</span>
            <p class="question-text">{{ question }}</p>
          </div>
        </div>
      </div>

      <!-- Bottom Actions -->
      <div class="bottom-actions">
        <button 
          @click="confirmDiagnosis" 
          :disabled="confirming"
          class="confirm-btn"
        >
          {{ confirming ? '确认中...' : '确认诊断' }}
        </button>
        <button 
          @click="goToPlan" 
          class="plan-btn"
        >
          前往行动方案 →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const confirming = ref(false)
const error = ref('')
const diagnosis = ref(null)

const editing = reactive({
  facts: false,
  assumptions: false,
  emotions: false,
  needs: false
})

const newItems = reactive({
  facts: '',
  assumptions: '',
  emotions: '',
  needs: ''
})

const riskClass = computed(() => {
  if (!diagnosis.value) return ''
  const level = diagnosis.value.risk_level
  if (level === 'low') return 'risk-green'
  if (level === 'medium') return 'risk-yellow'
  if (level === 'high') return 'risk-orange'
  if (level === 'critical') return 'risk-red'
  return ''
})

const riskLabel = computed(() => {
  if (!diagnosis.value) return ''
  const level = diagnosis.value.risk_level
  const labels = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
    critical: '严重风险'
  }
  return labels[level] || level
})

async function loadDiagnosis() {
  loading.value = true
  error.value = ''
  
  try {
    const caseId = route.params.id
    // Check if case already has diagnosis
    const caseData = await casesApi.get(caseId)
    
    if (caseData.diagnosis && caseData.diagnosis.summary) {
      // Use existing diagnosis
      diagnosis.value = caseData.diagnosis
    } else {
      // Try LLM diagnosis first, fallback to standard diagnosis
      try {
        diagnosis.value = await casesApi.diagnoseLLM(caseId)
      } catch (llmErr) {
        const status = llmErr.response?.status
        if (status === 400 || status === 500) {
          // LLM unavailable, fallback to standard diagnosis
          diagnosis.value = await casesApi.diagnose(caseId)
        } else {
          throw llmErr
        }
      }
    }
  } catch (err) {
    error.value = '加载诊断结果失败: ' + (err.message || '未知错误')
  } finally {
    loading.value = false
  }
}

function startEdit(dimension) {
  editing[dimension] = true
  newItems[dimension] = ''
}

function finishEdit(dimension) {
  editing[dimension] = false
  newItems[dimension] = ''
}

function addItem(dimension) {
  const value = newItems[dimension].trim()
  if (value) {
    diagnosis.value[dimension].push(value)
    newItems[dimension] = ''
  }
}

function removeItem(dimension, index) {
  diagnosis.value[dimension].splice(index, 1)
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
      risk_level: diagnosis.value.risk_level
    })
    
    alert('诊断已确认')
  } catch (err) {
    alert('确认失败: ' + (err.message || '未知错误'))
  } finally {
    confirming.value = false
  }
}

function goToPlan() {
  const caseId = route.params.id
  router.push(`/resident/cases/${caseId}/plan`)
}

onMounted(() => {
  loadDiagnosis()
})
</script>

<style scoped>
.diagnosis-result-page {
  max-width: 480px;
  margin: 0 auto;
  padding: 16px;
  min-height: 100vh;
  background: #FFF9F0;
}

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.back-btn {
  background: #fff;
  border: 1px solid #E0D8CE;
  border-radius: 8px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  color: #2D2A26;
}

.back-btn:active {
  background: #F5F0E8;
}

.header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #E0D8CE;
  border-top-color: #E8A33D;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.error-state p {
  color: #6B6560;
  font-size: 14px;
  margin: 8px 0;
}

.retry-btn {
  margin-top: 12px;
  padding: 8px 20px;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #E8A33D;
  color: #fff;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
  align-self: flex-start;
}

.ai-badge-icon {
  font-size: 14px;
  line-height: 1;
}

.summary-text--large {
  font-size: 17px;
  font-weight: 500;
  line-height: 1.7;
}

.summary-card {
  background: linear-gradient(135deg, #FDE8C8 0%, #FFF3E0 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.summary-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0;
}

.risk-badge {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
}

.risk-green {
  background: #4CAF50;
}

.risk-yellow {
  background: #FFC107;
  color: #2D2A26;
}

.risk-orange {
  background: #FF9800;
}

.risk-red {
  background: #F44336;
}

.summary-text {
  font-size: 14px;
  line-height: 1.6;
  color: #2D2A26;
  margin: 0 0 16px 0;
}

.confidence-section {
  margin-top: 16px;
}

.confidence-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #6B6560;
  margin-bottom: 6px;
}

.confidence-value {
  font-weight: 600;
  color: #E8A33D;
}

.confidence-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 3px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: #E8A33D;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.dimensions-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 12px 0;
}

.dimension-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  border: 1px solid #E0D8CE;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dimension-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #2D2A26;
}

.icon {
  font-size: 18px;
}

.edit-btn {
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #E8A33D;
  color: #E8A33D;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn:active {
  background: #E8A33D;
  color: #fff;
}

.edit-btn.finish {
  background: #E8A33D;
  color: #fff;
}

.dimension-content {
  color: #2D2A26;
}

.item-list {
  margin: 0;
  padding-left: 20px;
}

.item-list li {
  font-size: 14px;
  line-height: 1.8;
  color: #2D2A26;
}

.tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  background: #FDE8C8;
  color: #2D2A26;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
}

.edit-mode {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editable-list,
.editable-chips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.editable-item,
.editable-chip {
  display: flex;
  gap: 8px;
  align-items: center;
}

.edit-input,
.chip-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #E0D8CE;
  border-radius: 6px;
  font-size: 14px;
  color: #2D2A26;
  background: #FFF9F0;
}

.edit-input:focus,
.chip-input:focus {
  outline: none;
  border-color: #E8A33D;
}

.remove-btn,
.chip-remove {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #F44336;
  color: #fff;
  border: none;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-item {
  display: flex;
  gap: 8px;
}

.add-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #E0D8CE;
  border-radius: 6px;
  font-size: 14px;
  color: #2D2A26;
  background: #fff;
}

.add-input:focus {
  outline: none;
  border-color: #E8A33D;
}

.add-btn {
  padding: 8px 16px;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.insights-section h3,
.questions-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #2D2A26;
  margin: 0 0 12px 0;
}

.insights-list,
.questions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insight-item,
.question-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: #fff;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid #E0D8CE;
}

.insight-number {
  width: 24px;
  height: 24px;
  background: #E8A33D;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.question-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.insight-text,
.question-text {
  font-size: 14px;
  line-height: 1.6;
  color: #2D2A26;
  margin: 0;
}

.bottom-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
  padding-bottom: 20px;
}

.confirm-btn,
.plan-btn {
  padding: 14px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.confirm-btn {
  background: #E8A33D;
  color: #fff;
}

.confirm-btn:disabled {
  background: #E0D8CE;
  cursor: not-allowed;
}

.confirm-btn:not(:disabled):active {
  background: #D6922E;
}

.plan-btn {
  background: #fff;
  color: #E8A33D;
  border: 2px solid #E8A33D;
}

.plan-btn:active {
  background: #FFF3E0;
}
</style>
