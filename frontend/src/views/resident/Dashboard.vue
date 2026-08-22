<template>
  <div class="resident-dashboard ng-fade-in">
    <header class="top-bar">
      <h1>🌟 邻光</h1>
      <div class="user-info">
        <span class="user-name" @click="router.push('/resident/profile')">{{ userInfo?.display_name || userInfo?.username || '用户' }}</span>
        <div class="avatar" @click="router.push('/resident/profile')">{{ avatarLetter }}</div>
      </div>
    </header>
    <main class="main-content">
      <section class="hero ng-card--hero">
        <p class="hero-slogan">邻里之光，让善意照进千万人家！</p>
        <h2>邻里之间，有些话只是需要换一种方式说。</h2>
        <p>描述你遇到的问题，邻光会帮你理清情况、找到合适的表达，并陪你练习下一次沟通。</p>
        <button @click="$router.push('/resident/submit')" class="ng-btn ng-btn-primary ng-btn-block">开始梳理问题</button>
      </section>
      <section class="quick-scenarios">
        <h3 class="ng-section-title">快捷场景</h3>
        <div class="scenario-grid">
          <div v-for="s in scenarios" :key="s.key" class="scenario-card" @click="selectScenario(s)">
            <span class="scenario-icon">{{ s.icon }}</span>
            <span class="scenario-label">{{ s.label }}</span>
          </div>
        </div>
      </section>
      <section class="my-cases">
        <div class="section-header">
          <h3 class="ng-section-title">我的案例</h3>
          <a class="link-more" @click.prevent="router.push('/resident/my-requests')">查看全部</a>
        </div>
        <div v-if="cases.length === 0" class="empty-state ng-empty">
          <div class="empty-icon ng-empty-icon">🌱</div>
          <p class="empty-title ng-empty-title">第一次使用？</p>
          <p class="empty-text ng-empty-desc">从描述你遇到的问题开始，<br />邻光会帮你理清情况，一起想办法怎么开口。</p>
          <button class="ng-btn ng-btn-primary ng-btn-block empty-btn" @click="router.push('/resident/submit')">开始描述问题</button>
          <p class="empty-tip">也可以点击上方常见场景快速开始</p>
        </div>
        <div v-else class="case-list">
          <div v-for="c in cases.slice(0, 3)" :key="c.id" class="case-card clickable ng-card" :class="'risk-' + c.risk_level" @click="router.push('/resident/case/' + c.id)">
            <div class="case-header">
              <span class="ng-risk-badge" :class="'ng-risk-soft-' + c.risk_level"></span>
              <span class="case-title">{{ c.title }}</span>
            </div>
            <p class="case-desc">{{ c.description?.slice(0, 60) }}...</p>
            <div class="case-meta">
              <span class="case-status">{{ statusLabel(c.status) }}</span>
              <span class="case-date">{{ new Date(c.created_at).toLocaleDateString() }}</span>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Bottom Navigation -->
    <nav class="bottom-nav">
      <a class="nav-item active" @click.prevent="router.push('/resident')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>首页</span>
      </a>
      <a class="nav-item" @click.prevent="router.push('/resident/my-requests')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <span>案例</span>
      </a>
      <a class="nav-item" @click.prevent="router.push('/resident/groups')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
        <span>群组</span>
      </a>
      <a class="nav-item" @click.prevent="router.push('/resident/profile')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <span>我的</span>
      </a>
    </nav>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { cases as casesApi } from '../../api'
const router = useRouter()
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))
const cases = ref([])
const scenarios = [
  { key: 'noise', icon: '🔊', label: '深夜噪音' },
  { key: 'leak', icon: '💧', label: '漏水纠纷' },
  { key: 'public_space', icon: '🏢', label: '公共区域' },
  { key: 'pet', icon: '🐕', label: '宠物问题' },
  { key: 'garbage', icon: '🗑️', label: '异味困扰' },
  { key: 'renovation', icon: '🔨', label: '装修施工' },
]

const avatarLetter = computed(() => {
  const name = userInfo.value?.display_name || userInfo.value?.username || '?'
  return name.charAt(0).toUpperCase()
})

function statusLabel(s) {
  const map = { pending: '待处理', diagnosed: '已诊断', mediating: '调解中', escalated: '已升级', resolved: '已解决', closed: '已关闭' }
  return map[s] || s || ''
}

onMounted(async () => {
  try {
    const res = await casesApi.list()
    cases.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    console.error('Failed to load cases', e)
  }
})
function selectScenario(s) {
  router.push({ path: '/resident/submit', query: { scenario: s.key } })
}
</script>
<style scoped>
/* ---- 页面容器（移动端 480px / 奶油白底 / 左右 20px） ---- */
.resident-dashboard { max-width: 480px; margin: 0 auto; min-height: 100vh; background: var(--ng-bg-mobile); font-family: var(--ng-font-family); color: var(--ng-text-main); }

/* ---- 顶栏 ---- */
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: var(--ng-space-4) var(--ng-page-margin-mobile); background: var(--ng-bg-card); border-bottom: 1px solid var(--ng-border-strong); position: sticky; top: 0; z-index: 10; }
.top-bar h1 { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); color: var(--ng-primary); margin: 0; }
.user-info { display: flex; align-items: center; gap: var(--ng-space-3); }
.user-name { font-size: var(--ng-fs-body); color: var(--ng-text-main); font-weight: var(--ng-fw-strong); cursor: pointer; transition: color var(--ng-dur-fast) var(--ng-ease); }
.user-name:hover { color: var(--ng-primary-deep); }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--ng-gradient-btn); color: var(--ng-text-inverse); display: flex; align-items: center; justify-content: center; font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title); cursor: pointer; box-shadow: var(--ng-shadow-btn); transition: transform var(--ng-dur-fast) var(--ng-ease); }
.avatar:hover { transform: scale(1.1); }

.main-content { padding: 0 var(--ng-page-margin-mobile) 100px; }

/* ---- 主视觉卡：琥珀渐变 + 深琥珀文字 ---- */
.hero { border-radius: var(--ng-radius-card); padding: var(--ng-space-6); margin: var(--ng-space-4) 0 var(--ng-space-6); }
.hero-slogan { font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-title); letter-spacing: 0.08em; color: var(--ng-primary-deep); opacity: 0.85; margin-bottom: var(--ng-space-2); }
.hero h2 { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); color: var(--ng-primary-deep); margin-bottom: var(--ng-space-3); line-height: 1.4; }
.hero p { font-size: var(--ng-fs-body); color: var(--ng-primary-deep); margin-bottom: var(--ng-space-5); line-height: 1.6; }

/* ---- 快捷场景 ---- */
.quick-scenarios { margin-bottom: var(--ng-space-6); }
.scenario-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--ng-card-gap); }
.scenario-card { background: var(--ng-bg-card); border-radius: var(--ng-radius-card); padding: var(--ng-space-4) var(--ng-space-2); text-align: center; cursor: pointer; box-shadow: var(--ng-shadow-card); border: 1px solid var(--ng-border); transition: all var(--ng-dur-fast) var(--ng-ease); }
.scenario-card:hover { transform: translateY(-2px); border-color: var(--ng-primary); box-shadow: var(--ng-shadow-card-hover); }
.scenario-icon { font-size: 24px; display: block; margin-bottom: var(--ng-space-1); }
.scenario-label { font-size: var(--ng-fs-aux); color: var(--ng-text-main); }

/* ---- 我的案例 ---- */
.my-cases { margin-bottom: var(--ng-space-6); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--ng-space-3); }
.section-header h3 { margin: 0; }
.link-more { font-size: var(--ng-fs-aux); color: var(--ng-primary-deep); font-weight: var(--ng-fw-strong); cursor: pointer; text-decoration: none; transition: color var(--ng-dur-fast) var(--ng-ease); }
.link-more:hover { color: var(--ng-primary); text-decoration: underline; }

/* ---- 空状态（套用 .ng-empty 系列） ---- */
.empty-state { background: var(--ng-bg-card); border-radius: var(--ng-radius-card); border: 1px dashed var(--ng-border-strong); }
.empty-btn { max-width: 260px; margin: 0 auto; }
.empty-tip { font-size: var(--ng-fs-small); color: var(--ng-text-hint); margin: var(--ng-space-2) 0 0; }

/* ---- 案例卡片列表 ---- */
.case-list { display: flex; flex-direction: column; gap: var(--ng-card-gap); }
.case-card { cursor: pointer; border-left: 4px solid var(--ng-risk-green); transition: transform var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease), border-color var(--ng-dur-fast) var(--ng-ease); }
.case-card:hover { transform: translateY(-2px); box-shadow: var(--ng-shadow-card-hover); }
.case-card.risk-yellow { border-left-color: var(--ng-risk-yellow); }
.case-card.risk-orange { border-left-color: var(--ng-risk-orange); }
.case-card.risk-red { border-left-color: var(--ng-risk-red); }
.case-header { display: flex; align-items: center; gap: var(--ng-space-2); margin-bottom: var(--ng-space-2); }
.case-title { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); color: var(--ng-text-main); }
.case-desc { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); margin-bottom: var(--ng-space-2); line-height: 1.5; }
.case-meta { display: flex; justify-content: space-between; font-size: var(--ng-fs-small); color: var(--ng-text-hint); }
.case-status { font-weight: var(--ng-fw-strong); color: var(--ng-text-secondary); }

/* ---- 底部导航 ---- */
.bottom-nav {
  position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
  width: 100%; max-width: 480px; background: var(--ng-bg-card); border-top: 1px solid var(--ng-border-strong);
  display: flex; justify-content: space-around; align-items: center;
  padding: var(--ng-space-2) 0 env(safe-area-inset-bottom, 8px); z-index: 50;
  box-shadow: var(--ng-shadow-card);
}
.nav-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: var(--ng-space-1) var(--ng-space-3); cursor: pointer; color: var(--ng-text-hint); text-decoration: none;
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.nav-item:hover { color: var(--ng-primary); }
.nav-item.active { color: var(--ng-primary); }
.nav-item span { font-size: var(--ng-fs-small); font-weight: var(--ng-fw-strong); }
</style>
