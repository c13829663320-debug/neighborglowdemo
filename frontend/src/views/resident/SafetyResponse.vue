<template>
  <div class="ng-page safety-page">
    <!-- Header -->
    <header class="safety-header ng-fade-in">
      <button class="back-btn" @click="$router.back()" aria-label="返回">
        <span>←</span>
      </button>
      <h1 class="ng-page-title">安全响应</h1>
      <span class="header-spacer"></span>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading-wrap">
      <div class="ng-spinner"></div>
      <p class="loading-text">正在评估安全情况…</p>
    </div>

    <template v-else>
      <!-- Risk Alert Hero -->
      <section class="risk-hero ng-safety-banner ng-fade-in">
        <div class="risk-hero-icon">🛡️</div>
        <div class="risk-hero-body">
          <span class="ng-risk-badge ng-risk-red">安全风险</span>
          <h2>你的安全是第一位的</h2>
          <p class="risk-hero-desc">
            根据你描述的情况，这件事可能涉及人身或财产安全。
            邻光暂停了普通的沟通建议，请先关注自身安全。
          </p>
        </div>
      </section>

      <!-- Emergency Actions -->
      <section class="ng-fade-in emergency-section">
        <h3 class="ng-section-title">紧急情况</h3>
        <div class="emergency-cards">
          <a class="emergency-card" href="tel:110">
            <span class="emergency-icon police">🚨</span>
            <div class="emergency-text">
              <strong>报警 110</strong>
              <span>正在发生威胁、暴力或骚扰</span>
            </div>
            <span class="emergency-arrow">→</span>
          </a>
          <a class="emergency-card" href="tel:120">
            <span class="emergency-icon medical">🚑</span>
            <div class="emergency-text">
              <strong>急救 120</strong>
              <span>有人受伤需要医疗救助</span>
            </div>
            <span class="emergency-arrow">→</span>
          </a>
        </div>
      </section>

      <!-- Safety Guidance -->
      <section class="ng-fade-in guidance-section">
        <h3 class="ng-section-title">现在可以做的事</h3>
        <div class="guidance-list">
          <div class="guidance-item" v-for="(item, idx) in guidance" :key="idx">
            <span class="guidance-num">{{ idx + 1 }}</span>
            <div class="guidance-body">
              <strong>{{ item.title }}</strong>
              <p>{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- What we paused -->
      <section class="ng-card paused-card ng-fade-in">
        <div class="paused-head">
          <span class="paused-icon">⏸</span>
          <strong>已暂停的功能</strong>
        </div>
        <p class="paused-desc">
          红色风险案例不进入沟通模拟训练，也不建议直接与对方对峙。
          这是为了保护你，而不是限制你。
        </p>
        <ul class="paused-list">
          <li>✕ 模拟对话训练（已关闭）</li>
          <li>✕ 主动上门沟通建议（已暂停）</li>
          <li>✓ 事实整理与记录（仍可使用）</li>
          <li>✓ 联系社区管理者协助（推荐）</li>
        </ul>
      </section>

      <!-- Fact recording -->
      <section class="ng-card fact-card ng-fade-in">
        <h3 class="ng-section-title">帮助整理事实</h3>
        <p class="fact-desc">
          记录发生了什么（时间、地点、经过），有助于后续向社区、警方或相关机构说明情况。
          邻光只帮助整理事实，不作法律结论。
        </p>
        <textarea
          class="ng-textarea"
          v-model="factNote"
          rows="4"
          placeholder="例如：今晚 23:30 左右，对方再次用力敲门并大声威胁…"
        ></textarea>
        <button class="ng-btn ng-btn-primary ng-btn-block" :disabled="saving" @click="saveFact">
          {{ saving ? '保存中…' : '保存事实记录' }}
        </button>
      </section>

      <!-- Bottom actions -->
      <div class="bottom-actions ng-fade-in">
        <button class="ng-btn ng-btn-primary ng-btn-block" @click="requestHelp">
          请求社区管理者协助
        </button>
        <button class="ng-btn ng-btn-ghost ng-btn-block" @click="goFollowUp">
          记录后续情况
        </button>
      </div>

      <p class="disclaimer">
        邻光提供的内容为沟通辅助参考，不构成法律意见。紧急情况请立即拨打 110 / 120。
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'
import { useToast } from '../../composables/useToast'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const loading = ref(true)
const saving = ref(false)
const factNote = ref('')
const caseId = route.params.id

const guidance = [
  { title: '离开危险环境', desc: '如果对方情绪激动或有肢体冲突风险，先到亲友家、小区公共区域或安全场所。' },
  { title: '联系可信任的人', desc: '告诉家人、朋友或邻居你现在的处境，不要独自承受。' },
  { title: '保留证据但不激化', desc: '可以记录时间、声音、照片等，但避免当面拍摄刺激对方。' },
  { title: '联系社区管理者', desc: '社区工作站可以协助核实情况、联系相关方，并在必要时陪同处理。' },
]

async function loadCase() {
  try {
    await casesApi.get(caseId)
  } catch (e) {
    // 即使案例加载失败也展示安全指引
  } finally {
    loading.value = false
  }
}

async function saveFact() {
  if (!factNote.value.trim()) {
    toast.show('请先输入要记录的内容')
    return
  }
  saving.value = true
  try {
    await casesApi.createFollowup(caseId, {
      action_type: 'safety_note',
      result: 'recorded',
      note: factNote.value.trim(),
    })
    toast.success('事实记录已保存')
    factNote.value = ''
  } catch (e) {
    // 降级：本地保留
    localStorage.setItem('ng_safety_fact_' + caseId, factNote.value)
    toast.success('已暂存到本地（服务暂不可用）')
  } finally {
    saving.value = false
  }
}

function requestHelp() {
  router.push(`/resident/case/${caseId}/followup?request_human=1`)
}

function goFollowUp() {
  router.push(`/resident/case/${caseId}/followup`)
}

onMounted(loadCase)
</script>

<style scoped>
.safety-page {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-4);
}

.safety-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--ng-space-2);
}
.back-btn {
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
.back-btn:active { background: var(--ng-bg-subtle); }
.header-spacer { width: 40px; }

.loading-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-3);
  padding: 80px 0;
}
.loading-text { color: var(--ng-text-secondary); }

/* Risk Hero */
.risk-hero {
  border-radius: var(--ng-radius-card);
  padding: var(--ng-space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--ng-space-3);
  box-shadow: var(--ng-shadow-card);
}
.risk-hero-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--ng-bg-card);
  box-shadow: var(--ng-shadow-card);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
}
.risk-hero-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-2);
}
.risk-hero-body h2 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-risk-red);
}
.risk-hero-desc {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  max-width: 320px;
}

/* Emergency */
.emergency-cards {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}
.emergency-card {
  display: flex;
  align-items: center;
  gap: var(--ng-space-3);
  background: var(--ng-bg-card);
  border: 1.5px solid var(--ng-risk-red);
  border-radius: var(--ng-radius-card);
  padding: 14px var(--ng-card-padding);
  text-decoration: none;
  box-shadow: var(--ng-shadow-card);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.emergency-card:active { transform: scale(0.985); box-shadow: var(--ng-shadow-card-hover); }
.emergency-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--ng-radius-btn);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.emergency-icon.police { background: var(--ng-risk-red-soft); }
.emergency-icon.medical { background: var(--ng-risk-orange-soft); }
.emergency-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.emergency-text strong { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); color: var(--ng-risk-red); }
.emergency-text span { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); }
.emergency-arrow { color: var(--ng-risk-red); font-size: 18px; }

/* Guidance */
.guidance-list {
  display: flex;
  flex-direction: column;
  gap: var(--ng-card-gap);
}
.guidance-item {
  display: flex;
  gap: var(--ng-space-3);
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding);
  box-shadow: var(--ng-shadow-card);
}
.guidance-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.guidance-body strong {
  font-size: var(--ng-fs-card);
  color: var(--ng-text-main);
  display: block;
  margin-bottom: 2px;
}
.guidance-body p {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
  line-height: var(--ng-lh);
  margin: 0;
}

/* Paused card */
.paused-head {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  margin-bottom: var(--ng-space-2);
  font-size: var(--ng-fs-card);
  color: var(--ng-text-main);
}
.paused-icon { font-size: 18px; }
.paused-desc {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  margin-bottom: var(--ng-space-3);
}
.paused-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-2);
  font-size: var(--ng-fs-body);
}
.paused-list li:nth-child(-n+2) { color: var(--ng-text-hint); }
.paused-list li:nth-child(n+3) { color: var(--ng-risk-green); }

/* Fact card */
.fact-desc {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  margin-bottom: var(--ng-space-3);
}
.fact-card .ng-btn { margin-top: var(--ng-space-3); }

/* Bottom */
.bottom-actions {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-3);
}

.disclaimer {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
  text-align: center;
  padding-bottom: var(--ng-space-4);
}
</style>
