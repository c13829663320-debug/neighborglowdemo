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
        <p class="hero-brand">
          <span class="hero-brand-name">邻光</span>
          <span class="hero-brand-sep">｜</span>
          <span>邻里之光，让善意照进千万人家</span>
        </p>
        <h2>说说你的烦心事，<br />我来帮你理理头绪</h2>
        <p class="hero-sub">智能分析 · 专业引导 · 隐私保护</p>
        <button @click="router.push('/resident/submit')" class="hero-cta">
          <span class="hero-cta-icon">✨</span>
          <span>开始梳理问题</span>
        </button>
      </section>
      <section class="entry-cards">
        <div class="entry-card ng-card" @click="router.push('/resident/groups')">
          <span class="entry-icon entry-icon--chat">💬</span>
          <div class="entry-text">
            <p class="entry-title">社区支持群聊</p>
            <p class="entry-desc">和邻居们一起聊聊</p>
          </div>
          <svg class="entry-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        <div class="entry-card ng-card" @click="router.push('/resident/my-requests')">
          <span class="entry-icon entry-icon--case">📋</span>
          <div class="entry-text">
            <p class="entry-title">待跟进的案例</p>
            <p class="entry-desc">查看案例进展与反馈</p>
          </div>
          <span v-if="pendingCount > 0" class="entry-badge">{{ pendingCount }}</span>
          <svg class="entry-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
      </section>
      <section class="quick-scenarios">
        <h3 class="ng-section-title">常见情况</h3>
        <div class="scenario-grid">
          <div v-for="s in scenarios" :key="s.key" class="scenario-card" @click="selectScenario(s)">
            <span class="scenario-icon">{{ s.icon }}</span>
            <span class="scenario-label">{{ s.label }}</span>
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

const pendingCount = computed(() =>
  cases.value.filter((c) => ['pending', 'diagnosed', 'mediating', 'escalated'].includes(c.status)).length
)

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

/* ---- 主视觉卡：品牌行 + 大标题 + 副标题 + 渐变主按钮 ---- */
.hero { border-radius: var(--ng-radius-card); padding: var(--ng-space-6); margin: var(--ng-space-4) 0 var(--ng-space-5); text-align: center; }
.hero-brand { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: var(--ng-space-1); font-size: var(--ng-fs-small); letter-spacing: 0.06em; color: var(--ng-primary-deep); opacity: 0.9; margin-bottom: var(--ng-space-4); }
.hero-brand-name { font-weight: var(--ng-fw-title); font-size: var(--ng-fs-aux); }
.hero-brand-sep { opacity: 0.5; }
.hero h2 { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); color: var(--ng-primary-deep); margin-bottom: var(--ng-space-2); line-height: 1.4; }
.hero-sub { font-size: var(--ng-fs-aux); color: var(--ng-primary-deep); opacity: 0.75; letter-spacing: 0.08em; margin-bottom: var(--ng-space-5); }
.hero-cta { display: inline-flex; align-items: center; justify-content: center; gap: var(--ng-space-2); width: 100%; padding: var(--ng-space-3) var(--ng-space-5); min-height: 48px; border: none; border-radius: var(--ng-radius-btn); background: var(--ng-gradient-btn); color: var(--ng-text-inverse); font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); font-family: inherit; letter-spacing: 0.1em; cursor: pointer; box-shadow: var(--ng-shadow-btn); transition: transform var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease), filter var(--ng-dur-fast) var(--ng-ease); }
.hero-cta:hover { transform: translateY(-2px); filter: brightness(1.05); }
.hero-cta:active { transform: translateY(0); }
.hero-cta-icon { font-size: var(--ng-fs-card); line-height: 1; }

/* ---- 次级入口卡：群聊 / 待跟进案例 ---- */
.entry-cards { display: flex; flex-direction: column; gap: var(--ng-card-gap); margin-bottom: var(--ng-space-6); }
.entry-card { display: flex; align-items: center; gap: var(--ng-space-3); padding: var(--ng-space-4); cursor: pointer; transition: transform var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease), border-color var(--ng-dur-fast) var(--ng-ease); }
.entry-card:hover { transform: translateY(-2px); box-shadow: var(--ng-shadow-card-hover); border-color: var(--ng-primary); }
.entry-icon { width: 44px; height: 44px; flex: none; border-radius: var(--ng-radius-btn); display: flex; align-items: center; justify-content: center; font-size: 22px; }
.entry-icon--chat { background: var(--ng-primary-soft); }
.entry-icon--case { background: var(--ng-primary-soft); }
.entry-text { flex: 1; min-width: 0; }
.entry-title { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-strong); color: var(--ng-text-main); margin: 0 0 2px; }
.entry-desc { font-size: var(--ng-fs-aux); color: var(--ng-text-hint); margin: 0; }
.entry-badge { flex: none; min-width: 22px; height: 22px; padding: 0 6px; border-radius: var(--ng-radius-pill); background: var(--ng-gradient-btn); color: var(--ng-text-inverse); font-size: var(--ng-fs-small); font-weight: var(--ng-fw-title); display: inline-flex; align-items: center; justify-content: center; }
.entry-arrow { flex: none; color: var(--ng-text-hint); }

/* ---- 快捷场景 ---- */
.quick-scenarios { margin-bottom: var(--ng-space-6); }
.scenario-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--ng-card-gap); }
.scenario-card { background: var(--ng-bg-card); border-radius: var(--ng-radius-card); padding: var(--ng-space-4) var(--ng-space-2); text-align: center; cursor: pointer; box-shadow: var(--ng-shadow-card); border: 1px solid var(--ng-border); transition: all var(--ng-dur-fast) var(--ng-ease); }
.scenario-card:hover { transform: translateY(-2px); border-color: var(--ng-primary); box-shadow: var(--ng-shadow-card-hover); }
.scenario-icon { font-size: 24px; display: block; margin-bottom: var(--ng-space-1); }
.scenario-label { font-size: var(--ng-fs-aux); color: var(--ng-text-main); }

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
