<template>
  <div class="trends-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-row">
        <div class="header-left">
          <button class="btn-back" @click="goBack" aria-label="返回">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M13 4L7 10L13 16" stroke="#2D2A26" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <h1 class="page-title">社区态势</h1>
        </div>
        <div class="range-toggle">
          <button
            :class="['range-btn', { active: days === 7 }]"
            @click="switchDays(7)"
          >7天</button>
          <button
            :class="['range-btn', { active: days === 30 }]"
            @click="switchDays(30)"
          >30天</button>
        </div>
      </div>
    </header>

    <main class="page-main">
      <!-- Loading State -->
      <template v-if="loading">
        <section class="overview-grid">
          <div v-for="i in 4" :key="i" class="card skeleton-card">
            <div class="skeleton-line skeleton-short"></div>
            <div class="skeleton-line skeleton-num"></div>
          </div>
        </section>
        <section class="card skeleton-card chart-skeleton">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-bars">
            <div v-for="i in 7" :key="i" class="skeleton-bar" :style="{ height: (20 + Math.random() * 40) + 'px' }"></div>
          </div>
        </section>
        <section class="card skeleton-card">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-circle"></div>
        </section>
      </template>

      <!-- Data Loaded -->
      <template v-else>
        <!-- 1. Overview Cards (2x2) -->
        <section class="overview-grid">
          <div class="card overview-card">
            <div class="ov-label">总案例数</div>
            <div class="ov-value">{{ overview.total_cases ?? 0 }}</div>
            <div class="ov-sub">近{{ days }}天累计</div>
          </div>
          <div class="card overview-card" :class="{ 'card-alert': highRiskCount > 0 }">
            <div class="ov-label">
              高风险
              <span v-if="highRiskCount > 0" class="pulse-dot"></span>
            </div>
            <div class="ov-value" :class="{ 'text-red': highRiskCount > 0 }">{{ highRiskCount }}</div>
            <div class="ov-sub">红色 + 橙色</div>
          </div>
          <div class="card overview-card">
            <div class="ov-label">已解决</div>
            <div class="ov-value text-green">{{ resolvedCount }}</div>
            <div class="ov-sub">已调解完成</div>
          </div>
          <div class="card overview-card">
            <div class="ov-label">调解中</div>
            <div class="ov-value text-amber">{{ mediatingCount }}</div>
            <div class="ov-sub">正在处理</div>
          </div>
        </section>

        <!-- 2. Daily Trend Bar Chart -->
        <section class="card">
          <div class="card-header">
            <h2 class="card-title">每日新增趋势</h2>
          </div>
          <div v-if="dailyBars.length === 0" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <rect x="6" y="28" width="6" height="12" rx="2" fill="#E0D8CE"/>
              <rect x="15" y="22" width="6" height="18" rx="2" fill="#E0D8CE"/>
              <rect x="24" y="16" width="6" height="24" rx="2" fill="#E0D8CE"/>
              <rect x="33" y="10" width="6" height="30" rx="2" fill="#E0D8CE"/>
            </svg>
            <p>暂无趋势数据</p>
          </div>
          <div v-else class="bar-chart-container">
            <!-- Y axis labels -->
            <div class="y-axis">
              <span class="y-label">{{ maxDailyCount }}</span>
              <span class="y-label">{{ Math.ceil(maxDailyCount / 2) }}</span>
              <span class="y-label">0</span>
            </div>
            <!-- Bars area -->
            <div class="bars-area">
              <div class="grid-lines">
                <div class="grid-line" style="bottom: 100%"></div>
                <div class="grid-line" style="bottom: 50%"></div>
                <div class="grid-line" style="bottom: 0%"></div>
              </div>
              <div
                v-for="(bar, idx) in dailyBars"
                :key="idx"
                class="bar-col"
                @mouseenter="activeTooltip = idx"
                @mouseleave="activeTooltip = null"
                @click="activeTooltip = activeTooltip === idx ? null : idx"
              >
                <div class="bar-tooltip" v-if="activeTooltip === idx">
                  <span class="tooltip-date">{{ bar.displayDate }}</span>
                  <span class="tooltip-count">{{ bar.count }} 件</span>
                </div>
                <div
                  class="bar-rect"
                  :style="{
                    height: bar.heightPct + '%',
                    backgroundColor: bar.color
                  }"
                ></div>
                <span class="bar-date-label">{{ bar.displayDate }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 3. Risk Donut Chart -->
        <section class="card">
          <div class="card-header">
            <h2 class="card-title">风险分布</h2>
          </div>
          <div v-if="donutTotal === 0" class="empty-state">
            <p>暂无风险数据</p>
          </div>
          <div v-else class="donut-section">
            <div class="donut-chart-wrap">
              <svg viewBox="0 0 42 42" class="donut-svg">
                <circle cx="21" cy="21" r="15.9" fill="none" stroke="#f0ebe4" stroke-width="5"/>
                <circle
                  v-for="(seg, i) in donutSegments"
                  :key="i"
                  cx="21" cy="21" r="15.9"
                  fill="none"
                  :stroke="seg.color"
                  stroke-width="5"
                  :stroke-dasharray="seg.dashArray"
                  :stroke-dashoffset="seg.offset"
                  stroke-linecap="round"
                  class="donut-seg"
                />
                <text x="21" y="20" text-anchor="middle" class="donut-center-num">{{ donutTotal }}</text>
                <text x="21" y="24.5" text-anchor="middle" class="donut-center-label">总案例</text>
              </svg>
            </div>
            <div class="donut-legend">
              <div v-for="seg in donutSegments" :key="seg.label" class="legend-row">
                <span class="legend-dot" :style="{ backgroundColor: seg.color }"></span>
                <span class="legend-label">{{ seg.label }}</span>
                <span class="legend-count">{{ seg.count }}</span>
                <span class="legend-pct">{{ seg.pctLabel }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 4. Category Ranking -->
        <section class="card">
          <div class="card-header">
            <h2 class="card-title">分类排行</h2>
          </div>
          <div v-if="categoryList.length === 0" class="empty-state">
            <p>暂无分类数据</p>
          </div>
          <div v-else class="category-list">
            <div v-for="cat in categoryList" :key="cat.key" class="cat-row">
              <span class="cat-icon">{{ cat.icon }}</span>
              <span class="cat-name">{{ cat.label }}</span>
              <div class="cat-bar-track">
                <div
                  class="cat-bar-fill"
                  :style="{ width: cat.widthPct + '%', backgroundColor: cat.barColor }"
                ></div>
              </div>
              <span class="cat-count">{{ cat.count }}</span>
            </div>
          </div>
        </section>

        <!-- 5. Status Distribution -->
        <section class="card">
          <div class="card-header">
            <h2 class="card-title">状态分布</h2>
          </div>
          <div v-if="statusTotal === 0" class="empty-state">
            <p>暂无状态数据</p>
          </div>
          <div v-else class="status-section">
            <div class="stacked-bar">
              <div
                v-for="s in statusSegments"
                :key="s.key"
                class="stacked-seg"
                :style="{ width: s.pct + '%', backgroundColor: s.color }"
                :title="s.label + ': ' + s.count + ' (' + s.pctLabel + ')'"
              ></div>
            </div>
            <div class="status-legend">
              <div v-for="s in statusSegments" :key="s.key" class="status-legend-item">
                <span class="status-dot" :style="{ backgroundColor: s.color }"></span>
                <span class="status-name">{{ s.label }}</span>
                <span class="status-count">{{ s.count }}</span>
                <span class="status-pct">{{ s.pctLabel }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- Footer -->
      <footer class="page-footer">
        <span class="footer-time" v-if="lastUpdated">更新于 {{ lastUpdated }}</span>
        <button class="btn-refresh" @click="refreshData" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" :class="{ spinning: loading }">
            <path d="M14 8A6 6 0 1 1 8 2" stroke="#E8A33D" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M8 0L10.5 2.5L8 5" stroke="#E8A33D" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          刷新
        </button>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { community as communityApi } from '../../api'

const router = useRouter()

// --- State ---
const days = ref(7)
const loading = ref(true)
const overview = ref({})
const trendsData = ref({})
const lastUpdated = ref('')
const activeTooltip = ref(null)

// --- Constants ---
const CATEGORY_MAP = {
  noise: { label: '噪音', icon: '\uD83D\uDD0A' },
  parking: { label: '停车', icon: '\uD83D\uDE97' },
  property: { label: '物业', icon: '\uD83C\uDFE2' },
  pet: { label: '宠物', icon: '\uD83D\uDC3E' },
  boundary: { label: '边界', icon: '\uD83D\uDCCF' },
  garden: { label: '绿化', icon: '\uD83C\uDF3F' },
  safety: { label: '安全', icon: '\uD83D\uDEE1\uFE0F' },
  sanitation: { label: '卫生', icon: '\uD83E\uDDF9' },
  other: { label: '其他', icon: '\uD83D\uDCCC' },
}

const CATEGORY_COLORS = [
  '#E8A33D', '#F0B85C', '#B07A20', '#FF9800',
  '#FFC107', '#D4922E', '#4CAF50', '#F44336'
]

const RISK_COLORS = {
  green: '#4CAF50',
  yellow: '#FFC107',
  orange: '#FF9800',
  red: '#F44336',
}

const RISK_ORDER = ['green', 'yellow', 'orange', 'red']
const RISK_LABELS = { green: '绿色', yellow: '黄色', orange: '橙色', red: '红色' }

const STATUS_COLORS = {
  pending: '#FF9800',
  diagnosed: '#F0B85C',
  mediating: '#FFC107',
  escalated: '#F44336',
  resolved: '#4CAF50',
}

const STATUS_LABELS = {
  pending: '待处理',
  diagnosed: '已诊断',
  mediating: '调解中',
  escalated: '已升级',
  resolved: '已解决',
}

// --- Computed ---
const byRisk = computed(() => overview.value.by_risk_level || overview.value.by_risk || {})
const byCategory = computed(() => overview.value.by_category || {})
const byStatus = computed(() => overview.value.by_status || {})

const highRiskCount = computed(() => (byRisk.value.red || 0) + (byRisk.value.orange || 0))
const resolvedCount = computed(() => byStatus.value.resolved || 0)
const mediatingCount = computed(() => byStatus.value.mediating || 0)

// Daily bars data
const dailyBars = computed(() => {
  const dailyObj = trendsData.value.daily_counts || {}
  const entries = Object.entries(dailyObj).sort((a, b) => a[0].localeCompare(b[0]))
  if (entries.length === 0) return []

  // Determine max risk per day from category_trends or just use default color
  const catTrends = trendsData.value.category_trends || {}

  const maxVal = Math.max(1, ...entries.map(([, c]) => c))

  return entries.map(([date, count], idx) => {
    const d = new Date(date)
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const displayDate = `${mm}-${dd}`
    const heightPct = maxVal > 0 ? Math.max(count > 0 ? 8 : 2, (count / maxVal) * 100) : 2

    // Color by highest risk in that day — since we don't have per-day risk info,
    // we use a simple heuristic: if count is high, use warmer color
    let color = '#E8A33D'
    if (count >= 5) color = RISK_COLORS.red
    else if (count >= 4) color = RISK_COLORS.orange
    else if (count >= 3) color = RISK_COLORS.yellow
    else if (count >= 1) color = RISK_COLORS.green

    // Try to determine from category_trends risk association
    // Check if we have any high-risk categories trending on this day
    if (catTrends && Object.keys(catTrends).length > 0) {
      // Use the day index to check category_trends values
      let maxCatVal = 0
      Object.values(catTrends).forEach(arr => {
        if (Array.isArray(arr) && idx < arr.length) {
          maxCatVal = Math.max(maxCatVal, arr[idx])
        }
      })
      if (maxCatVal >= 3) color = RISK_COLORS.red
      else if (maxCatVal >= 2) color = RISK_COLORS.orange
      else if (count >= 2) color = RISK_COLORS.yellow
      else if (count >= 1) color = RISK_COLORS.green
    }

    return { date, displayDate, count, heightPct, color }
  })
})

const maxDailyCount = computed(() => {
  const dailyObj = trendsData.value.daily_counts || {}
  const vals = Object.values(dailyObj)
  return vals.length > 0 ? Math.max(...vals) : 0
})

// Donut segments
const donutTotal = computed(() => {
  return RISK_ORDER.reduce((sum, k) => sum + (byRisk.value[k] || 0), 0)
})

const donutSegments = computed(() => {
  const total = donutTotal.value
  if (total === 0) return []

  let accumulated = 0
  return RISK_ORDER
    .filter(k => (byRisk.value[k] || 0) > 0)
    .map(k => {
      const count = byRisk.value[k] || 0
      const pct = (count / total) * 100
      const dashArray = `${pct.toFixed(2)} ${(100 - pct).toFixed(2)}`
      // circumference offset: start at top (25 = quarter of 100)
      const offset = 25 - accumulated
      accumulated += pct
      return {
        key: k,
        label: RISK_LABELS[k],
        count,
        color: RISK_COLORS[k],
        pct,
        pctLabel: pct.toFixed(0) + '%',
        dashArray,
        offset,
      }
    })
})

// Category ranking
const categoryList = computed(() => {
  const cats = byCategory.value
  const entries = Object.entries(cats).sort((a, b) => b[1] - a[1])
  if (entries.length === 0) return []
  const maxVal = entries[0][1]

  return entries.map(([key, count], idx) => {
    const info = CATEGORY_MAP[key] || { label: key, icon: '\uD83D\uDCCC' }
    return {
      key,
      label: info.label,
      icon: info.icon,
      count,
      widthPct: maxVal > 0 ? (count / maxVal) * 100 : 0,
      barColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
    }
  })
})

// Status distribution
const statusTotal = computed(() => {
  return Object.values(byStatus.value).reduce((s, v) => s + (v || 0), 0)
})

const statusSegments = computed(() => {
  const total = statusTotal.value
  if (total === 0) return []
  const order = ['pending', 'diagnosed', 'mediating', 'escalated', 'resolved']
  return order
    .filter(k => (byStatus.value[k] || 0) > 0)
    .map(k => {
      const count = byStatus.value[k] || 0
      const pct = (count / total) * 100
      return {
        key: k,
        label: STATUS_LABELS[k] || k,
        count,
        color: STATUS_COLORS[k] || '#999',
        pct,
        pctLabel: pct.toFixed(0) + '%',
      }
    })
})

// --- Methods ---
function goBack() {
  router.push('/staff')
}

async function switchDays(d) {
  if (days.value === d) return
  days.value = d
  await fetchData()
}

async function fetchData() {
  loading.value = true
  activeTooltip.value = null
  try {
    const [ovRes, trRes] = await Promise.all([
      communityApi.overview({ days: days.value }),
      communityApi.trends({ days: days.value }),
    ])
    overview.value = ovRes.data || {}
    trendsData.value = trRes.data || {}
    const now = new Date()
    lastUpdated.value = now.toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
  } catch (err) {
    console.error('Failed to load trends data:', err)
    overview.value = {}
    trendsData.value = {}
  } finally {
    loading.value = false
  }
}

function refreshData() {
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
/* ===== Base Layout (Desktop Workbench) ===== */
.trends-page {
  min-height: 100vh;
  background: var(--ng-bg-desktop);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  color: var(--ng-text-main);
  -webkit-font-smoothing: antialiased;
}

/* ===== Header ===== */
.page-header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--ng-bg-desktop);
  border-bottom: 1px solid var(--ng-border);
  padding: 0 var(--ng-page-margin-desktop);
}
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  max-width: 600px;
  margin: 0 auto;
}
.header-left {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
}
.btn-back {
  width: 36px;
  height: 36px;
  border-radius: var(--ng-radius-btn);
  border: 1px solid var(--ng-border-strong);
  background: var(--ng-bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover {
  background: var(--ng-bg-subtle);
}
.btn-back:active { transform: scale(0.98); }
.page-title {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  margin: 0;
  color: var(--ng-text-main);
}
.range-toggle {
  display: flex;
  background: var(--ng-bg-subtle);
  border-radius: var(--ng-radius-pill);
  padding: 3px;
  gap: 2px;
}
.range-btn {
  padding: 6px 16px;
  border: none;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  background: transparent;
  color: var(--ng-text-secondary);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.range-btn.active {
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  box-shadow: var(--ng-shadow-btn);
}

/* ===== Main ===== */
.page-main {
  max-width: 600px;
  margin: 0 auto;
  padding: var(--ng-page-margin-desktop);
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-4);
}

/* ===== Cards ===== */
.card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
  padding: var(--ng-card-padding);
  transition: box-shadow var(--ng-dur-base) var(--ng-ease), transform var(--ng-dur-base) var(--ng-ease);
}
.card-header {
  margin-bottom: var(--ng-space-4);
}
.card-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  margin: 0;
  color: var(--ng-text-main);
}

/* ===== Overview Grid ===== */
.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--ng-card-gap);
}
.overview-card {
  padding: var(--ng-card-padding);
  position: relative;
  overflow: hidden;
}
.overview-card:hover {
  box-shadow: var(--ng-shadow-card-hover);
  transform: translateY(-2px);
}
.card-alert {
  border-color: var(--ng-risk-orange);
  box-shadow: 0 1px 12px color-mix(in srgb, var(--ng-risk-orange) 15%, transparent);
}
.ov-label {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
  margin-bottom: var(--ng-space-2);
  display: flex;
  align-items: center;
  gap: 6px;
}
.ov-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 6px;
  color: var(--ng-text-main);
}
.ov-sub {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
}
.text-red { color: var(--ng-risk-red); }
.text-green { color: var(--ng-risk-green); }
.text-amber { color: var(--ng-primary); }

/* Pulse dot */
.pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ng-risk-red);
  animation: pulse-glow 1.5s ease-in-out infinite;
}
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--ng-risk-red) 50%, transparent); }
  50% { box-shadow: 0 0 0 6px color-mix(in srgb, var(--ng-risk-red) 0%, transparent); }
}

/* ===== Bar Chart ===== */
.bar-chart-container {
  display: flex;
  gap: var(--ng-space-2);
  height: 200px;
}
.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-bottom: 24px;
  width: 28px;
  flex-shrink: 0;
}
.y-label {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
  text-align: right;
  line-height: 1;
}
.bars-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: var(--ng-space-1);
  position: relative;
  padding-bottom: 24px;
}
.grid-lines {
  position: absolute;
  inset: 0;
  bottom: 24px;
  pointer-events: none;
}
.grid-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--ng-border);
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  position: relative;
  cursor: pointer;
  padding-bottom: 0;
}
.bar-rect {
  width: 100%;
  max-width: 32px;
  border-radius: var(--ng-radius-tag) var(--ng-radius-tag) 0 0;
  transition: height var(--ng-dur-slow) var(--ng-ease), opacity var(--ng-dur-fast) var(--ng-ease);
  min-height: 2px;
  position: relative;
}
.bar-col:hover .bar-rect {
  opacity: 0.85;
}
.bar-date-label {
  font-size: 9px;
  color: var(--ng-text-hint);
  margin-top: 6px;
  white-space: nowrap;
  position: absolute;
  bottom: -22px;
}
/* Tooltip */
.bar-tooltip {
  position: absolute;
  bottom: calc(100% - 16px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--ng-text-main);
  color: var(--ng-text-inverse);
  padding: 6px 10px;
  border-radius: var(--ng-radius-tag);
  font-size: var(--ng-fs-small);
  white-space: nowrap;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  box-shadow: var(--ng-shadow-float);
  pointer-events: none;
}
.bar-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: var(--ng-text-main);
}
.tooltip-date {
  font-weight: var(--ng-fw-title);
}
.tooltip-count {
  opacity: 0.85;
}

/* ===== Donut Chart ===== */
.donut-section {
  display: flex;
  align-items: center;
  gap: var(--ng-space-6);
}
.donut-chart-wrap {
  flex-shrink: 0;
  width: 140px;
  height: 140px;
}
.donut-svg {
  width: 100%;
  height: 100%;
}
.donut-svg circle {
  transform: rotate(-90deg);
  transform-origin: center;
}
.donut-seg {
  transition: stroke-dasharray var(--ng-dur-slow) var(--ng-ease);
}
.donut-center-num {
  font-size: 8px;
  font-weight: 800;
  fill: var(--ng-text-main);
}
.donut-center-label {
  font-size: 3px;
  fill: var(--ng-text-secondary);
}
.donut-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-3);
}
.legend-row {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  font-size: var(--ng-fs-aux);
}
.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-label {
  flex: 1;
  color: var(--ng-text-main);
  font-weight: var(--ng-fw-strong);
}
.legend-count {
  font-weight: 700;
  color: var(--ng-text-main);
  min-width: 20px;
  text-align: right;
}
.legend-pct {
  color: var(--ng-text-hint);
  font-size: var(--ng-fs-small);
  min-width: 36px;
  text-align: right;
}

/* ===== Category Ranking ===== */
.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-3);
}
.cat-row {
  display: flex;
  align-items: center;
  gap: var(--ng-space-3);
  padding: var(--ng-space-1) var(--ng-space-2);
  border-radius: var(--ng-radius-tag);
  transition: background var(--ng-dur-fast) var(--ng-ease);
}
.cat-row:hover {
  background: var(--ng-primary-soft2);
}
.cat-icon {
  font-size: 18px;
  width: 28px;
  text-align: center;
  flex-shrink: 0;
}
.cat-name {
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  width: 40px;
  flex-shrink: 0;
}
.cat-bar-track {
  flex: 1;
  height: 16px;
  background: var(--ng-bg-subtle);
  border-radius: var(--ng-radius-pill);
  overflow: hidden;
}
.cat-bar-fill {
  height: 100%;
  border-radius: var(--ng-radius-pill);
  transition: width var(--ng-dur-slow) var(--ng-ease);
  min-width: 4px;
}
.cat-count {
  font-size: var(--ng-fs-aux);
  font-weight: 700;
  color: var(--ng-text-main);
  min-width: 24px;
  text-align: right;
}

/* ===== Status Distribution ===== */
.status-section {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-4);
}
.stacked-bar {
  display: flex;
  height: 24px;
  border-radius: var(--ng-radius-btn);
  overflow: hidden;
  background: var(--ng-bg-subtle);
}
.stacked-seg {
  transition: width var(--ng-dur-slow) var(--ng-ease);
  min-width: 2px;
}
.status-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ng-space-3) var(--ng-space-5);
}
.status-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--ng-fs-small);
}
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-name {
  color: var(--ng-text-main);
  font-weight: var(--ng-fw-strong);
}
.status-count {
  font-weight: 700;
  color: var(--ng-text-main);
}
.status-pct {
  color: var(--ng-text-hint);
}

/* ===== Empty State ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--ng-space-8) 0;
  color: var(--ng-text-hint);
  gap: var(--ng-space-3);
}
.empty-state p {
  margin: 0;
  font-size: var(--ng-fs-aux);
}

/* ===== Footer ===== */
.page-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ng-space-2) 0 var(--ng-space-6);
}
.footer-time {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
}
.btn-refresh {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card);
  font-size: var(--ng-fs-aux);
  color: var(--ng-primary);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-refresh:hover:not(:disabled) {
  background: var(--ng-primary-soft2);
}
.btn-refresh:active:not(:disabled) { transform: scale(0.98); }
.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== Skeleton Loading ===== */
.skeleton-card {
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-3);
}
.skeleton-line {
  background: linear-gradient(90deg, var(--ng-bg-subtle) 25%, var(--ng-bg-card) 50%, var(--ng-bg-subtle) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--ng-radius-tag);
}
.skeleton-short {
  width: 60px;
  height: 12px;
}
.skeleton-num {
  width: 48px;
  height: 32px;
  border-radius: var(--ng-radius-tag);
}
.skeleton-title {
  width: 100px;
  height: 14px;
  margin-bottom: var(--ng-space-2);
}
.skeleton-bars {
  display: flex;
  align-items: flex-end;
  gap: var(--ng-space-2);
  height: 80px;
}
.skeleton-bar {
  flex: 1;
  background: linear-gradient(90deg, var(--ng-bg-subtle) 25%, var(--ng-bg-card) 50%, var(--ng-bg-subtle) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--ng-radius-tag) var(--ng-radius-tag) 0 0;
}
.skeleton-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(90deg, var(--ng-bg-subtle) 25%, var(--ng-bg-card) 50%, var(--ng-bg-subtle) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  margin: var(--ng-space-2) auto;
}
.chart-skeleton {
  min-height: 140px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ===== Responsive: Desktop ===== */
@media (min-width: 768px) {
  .header-row {
    max-width: 800px;
  }
  .page-main {
    max-width: 800px;
  }
  .overview-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: var(--ng-card-gap);
  }
  .donut-section {
    gap: var(--ng-space-8);
  }
  .donut-chart-wrap {
    width: 180px;
    height: 180px;
  }
  .bar-chart-container {
    height: 240px;
  }
  .card {
    padding: var(--ng-space-6);
  }
  .ov-value {
    font-size: 36px;
  }
}

/* ===== Responsive: Small mobile ===== */
@media (max-width: 380px) {
  .overview-grid {
    gap: var(--ng-space-2);
  }
  .overview-card {
    padding: var(--ng-space-3);
  }
  .ov-value {
    font-size: 26px;
  }
  .donut-section {
    flex-direction: column;
    align-items: center;
  }
  .donut-chart-wrap {
    width: 120px;
    height: 120px;
  }
  .bar-date-label {
    font-size: 8px;
  }
  .page-main {
    padding: var(--ng-space-3);
  }
}
</style>
