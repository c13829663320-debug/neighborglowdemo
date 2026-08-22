<template>
  <div class="page ng-fade-in">
    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="'toast-' + toast.type">{{ toast.msg }}</div>
    </Transition>

    <!-- Loading overlay -->
    <div v-if="pageLoading" class="loading-overlay">
      <span class="spinner"></span>
      <span>加载中...</span>
    </div>

    <template v-if="!pageLoading && user">
      <!-- 1. 顶部头像区 -->
      <section class="profile-card">
        <div class="avatar-large" :style="{ background: avatarBg }">
          {{ avatarInitial }}
        </div>
        <div class="user-meta">
          <h2 class="user-name">{{ user.display_name || user.username }}</h2>
          <span class="role-badge" :class="'role-' + user.role">
            {{ user.role === 'staff' ? '管理者' : '居民' }}
          </span>
        </div>
        <p v-if="user.username && user.display_name" class="user-username">@{{ user.username }}</p>
        <p class="join-date">加入于 {{ relativeTime(user.created_at) }}</p>
      </section>

      <!-- 2. 数据统计行 -->
      <section class="stats-row">
        <div class="stat-card">
          <span class="stat-num">{{ stats.total }}</span>
          <span class="stat-label">我的案例</span>
        </div>
        <div class="stat-card">
          <span class="stat-num stat-green">{{ stats.resolved }}</span>
          <span class="stat-label">已解决</span>
        </div>
        <div class="stat-card">
          <span class="stat-num stat-amber">{{ stats.inProgress }}</span>
          <span class="stat-label">进行中</span>
        </div>
      </section>

      <!-- 3. 个人信息编辑区 -->
      <section class="section-card">
        <h3 class="section-title">个人信息</h3>
        <form @submit.prevent="saveProfile" class="form">
          <div class="form-group">
            <label class="form-label">显示名</label>
            <input
              v-model="form.display_name"
              type="text"
              class="form-input"
              placeholder="设置你的显示名称"
            />
          </div>
          <div class="form-group">
            <label class="form-label">真实姓名</label>
            <input
              v-model="form.real_name"
              type="text"
              class="form-input"
              placeholder="输入真实姓名"
            />
          </div>
          <div class="form-group">
            <label class="form-label">手机号</label>
            <input
              v-model="form.phone"
              type="tel"
              class="form-input"
              placeholder="输入手机号"
              maxlength="11"
            />
            <span v-if="phoneError" class="form-error">{{ phoneError }}</span>
          </div>
          <div class="form-group">
            <label class="form-label">所属社区</label>
            <select v-model="form.community_id" class="form-select">
              <option :value="null" disabled>请选择社区</option>
              <option v-for="c in communities" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="form-group form-group-row">
            <label class="form-label" style="margin-bottom:0">隐私授权</label>
            <label class="toggle-switch">
              <input type="checkbox" v-model="form.privacy_consent" />
              <span class="toggle-slider"></span>
              <span class="toggle-text">{{ form.privacy_consent ? '已授权' : '未授权' }}</span>
            </label>
          </div>
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </form>
      </section>

      <!-- 4. 我的案例统计 -->
      <section class="section-card">
        <h3 class="section-title">案例统计</h3>
        <!-- 风险分布条 -->
        <div class="risk-section">
          <p class="risk-title">风险分布</p>
          <div class="risk-bar" v-if="stats.total > 0">
            <div
              v-for="seg in riskSegments"
              :key="seg.level"
              class="risk-segment"
              :style="{ width: seg.pct + '%', background: seg.color }"
            ></div>
          </div>
          <div class="risk-bar" v-else style="background: var(--ng-bg-subtle)">
            <div class="risk-empty-text">暂无案例数据</div>
          </div>
          <div class="risk-legend">
            <span v-for="seg in riskSegments" :key="seg.level" class="legend-item">
              <span class="legend-dot" :style="{ background: seg.color }"></span>
              {{ seg.label }} {{ seg.count }}
            </span>
          </div>
        </div>
        <!-- 最近案例 -->
        <div class="recent-section">
          <p class="risk-title">最近案例</p>
          <div v-if="recentCases.length === 0" class="recent-empty">暂无案例</div>
          <div
            v-for="c in recentCases"
            :key="c.id"
            class="recent-item"
            @click="$router.push('/resident/case/' + c.id)"
          >
            <div class="recent-item-left">
              <span class="risk-dot" :class="'dot-' + c.risk_level"></span>
              <div>
                <p class="recent-item-title">{{ c.title }}</p>
                <p class="recent-item-date">{{ formatDate(c.created_at) }}</p>
              </div>
            </div>
            <span class="status-tag" :class="'status-' + c.status">{{ statusLabel(c.status) }}</span>
          </div>
        </div>
      </section>

      <!-- 5. 快捷操作 -->
      <section class="section-card">
        <h3 class="section-title">快捷操作</h3>
        <div class="action-list">
          <div class="action-item" @click="$router.push('/resident/my-requests')">
            <div class="action-icon action-icon-case">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </div>
            <span class="action-text">我的案例</span>
            <span class="action-arrow">&#8250;</span>
          </div>
          <div class="action-item" @click="$router.push('/resident/groups')">
            <div class="action-icon action-icon-group">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <span class="action-text">社区群组</span>
            <span class="action-arrow">&#8250;</span>
          </div>
          <div class="action-item" @click="showPwdModal = true">
            <div class="action-icon action-icon-lock">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <span class="action-text">修改密码</span>
            <span class="action-arrow">&#8250;</span>
          </div>
          <div class="action-item action-item-danger" @click="logout">
            <div class="action-icon action-icon-logout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </div>
            <span class="action-text">退出登录</span>
            <span class="action-arrow">&#8250;</span>
          </div>
        </div>
      </section>

      <!-- 6. 底部安全提示 -->
      <section class="security-footer">
        <div class="security-row">
          <svg class="shield-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span>你的数据受到加密保护</span>
        </div>
        <a class="privacy-link" href="javascript:void(0)" @click="$router.push('/resident/profile')">隐私政策</a>
        <p class="slogan-text">邻里之光，让善意照进千万人家！</p>
        <p class="version-text">NeighborGlow v1.0.0</p>
      </section>
    </template>

    <!-- 修改密码模态框 -->
    <Transition name="modal">
      <div v-if="showPwdModal" class="modal-overlay" @click.self="closePwdModal">
        <div class="modal-box">
          <div class="modal-header">
            <h3>修改密码</h3>
            <button class="modal-close" @click="closePwdModal">&times;</button>
          </div>
          <form @submit.prevent="changePassword" class="form">
            <div class="form-group">
              <label class="form-label">旧密码</label>
              <input
                v-model="pwdForm.oldPassword"
                type="password"
                class="form-input"
                placeholder="输入当前密码"
              />
              <span v-if="pwdErrors.oldPassword" class="form-error">{{ pwdErrors.oldPassword }}</span>
            </div>
            <div class="form-group">
              <label class="form-label">新密码</label>
              <input
                v-model="pwdForm.password"
                type="password"
                class="form-input"
                placeholder="至少6位字符"
              />
              <span v-if="pwdErrors.password" class="form-error">{{ pwdErrors.password }}</span>
            </div>
            <div class="form-group">
              <label class="form-label">确认密码</label>
              <input
                v-model="pwdForm.confirmPassword"
                type="password"
                class="form-input"
                placeholder="再次输入新密码"
              />
              <span v-if="pwdErrors.confirmPassword" class="form-error">{{ pwdErrors.confirmPassword }}</span>
            </div>
            <button type="submit" class="btn-primary" :disabled="changingPwd">
              {{ changingPwd ? '修改中...' : '确认修改' }}
            </button>
          </form>
        </div>
      </div>
    </Transition>

    <!-- 底部导航栏 -->
    <nav class="bottom-nav">
      <router-link to="/resident" class="nav-item">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>首页</span>
      </router-link>
      <router-link to="/resident/my-requests" class="nav-item">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
        <span>案例</span>
      </router-link>
      <router-link to="/resident/groups" class="nav-item">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        <span>群组</span>
      </router-link>
      <router-link to="/resident/profile" class="nav-item active">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        <span>我的</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api, { auth, cases as casesApi } from '../../api'

const router = useRouter()

// --- Warm avatar palette ---
const warmColors = [
  '#E8A33D', '#D4842A', '#C97B3A', '#E0924A',
  '#D97B5A', '#CF8855', '#B8864E', '#D4922E',
]

// --- State ---
const pageLoading = ref(true)
const saving = ref(false)
const changingPwd = ref(false)
const showPwdModal = ref(false)
const user = ref(null)
const communities = ref([])
const casesList = ref([])
const avatarBg = ref(warmColors[Math.floor(Math.random() * warmColors.length)])

const form = reactive({
  display_name: '',
  real_name: '',
  phone: '',
  community_id: null,
  privacy_consent: false,
})

const pwdForm = reactive({
  oldPassword: '',
  password: '',
  confirmPassword: '',
})

const toast = reactive({
  show: false,
  msg: '',
  type: 'success',
})

// --- Computed ---
const avatarInitial = computed(() => {
  if (!user.value) return '?'
  const name = user.value.display_name || user.value.real_name || user.value.username || ''
  return name.charAt(0).toUpperCase()
})

const stats = computed(() => {
  const list = casesList.value
  return {
    total: list.length,
    resolved: list.filter(c => c.status === 'resolved').length,
    inProgress: list.filter(c => ['in_progress', 'diagnosed'].includes(c.status)).length,
  }
})

const riskDistribution = computed(() => {
  const dist = { green: 0, yellow: 0, orange: 0, red: 0 }
  casesList.value.forEach(c => {
    if (c.risk_level && dist[c.risk_level] !== undefined) {
      dist[c.risk_level]++
    }
  })
  return dist
})

const riskSegments = computed(() => {
  const total = stats.value.total || 1
  const d = riskDistribution.value
  return [
    { level: 'green', label: '低风险', count: d.green, color: '#34C759', pct: (d.green / total) * 100 },
    { level: 'yellow', label: '中风险', count: d.yellow, color: '#FF9500', pct: (d.yellow / total) * 100 },
    { level: 'orange', label: '高风险', count: d.orange, color: '#FF6B35', pct: (d.orange / total) * 100 },
    { level: 'red', label: '安全风险', count: d.red, color: '#FF3B30', pct: (d.red / total) * 100 },
  ].filter(s => s.count > 0)
})

const recentCases = computed(() => {
  const sorted = [...casesList.value].sort((a, b) => {
    return new Date(b.created_at) - new Date(a.created_at)
  })
  return sorted.slice(0, 3)
})

const phoneError = computed(() => {
  if (!form.phone) return ''
  if (!/^1[3-9]\d{9}$/.test(form.phone)) return '请输入正确的11位手机号'
  return ''
})

const pwdErrors = computed(() => {
  const errs = {}
  if (pwdForm.password && pwdForm.password.length < 6) {
    errs.password = '密码至少需要6位字符'
  }
  if (pwdForm.confirmPassword && pwdForm.password !== pwdForm.confirmPassword) {
    errs.confirmPassword = '两次输入的密码不一致'
  }
  return errs
})

// --- Methods ---
function showToast(msg, type = 'success') {
  toast.msg = msg
  toast.type = type
  toast.show = true
  setTimeout(() => { toast.show = false }, 2500)
}

function relativeTime(dateStr) {
  if (!dateStr) return '未知'
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)
  if (years > 0) return `${years} 年前`
  if (months > 0) return `${months} 个月前`
  if (days > 0) return `${days} 天前`
  if (hours > 0) return `${hours} 小时前`
  if (minutes > 0) return `${minutes} 分钟前`
  return '刚刚'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function statusLabel(s) {
  return { draft: '待诊断', diagnosed: '已诊断', in_progress: '进行中', resolved: '已解决', escalated: '已升级' }[s] || s
}

function fillForm(u) {
  form.display_name = u.display_name || ''
  form.real_name = u.real_name || ''
  form.phone = u.phone || ''
  form.community_id = u.community_id || null
  form.privacy_consent = !!u.privacy_consent
}

function closePwdModal() {
  showPwdModal.value = false
  pwdForm.oldPassword = ''
  pwdForm.password = ''
  pwdForm.confirmPassword = ''
}

async function saveProfile() {
  if (phoneError.value) {
    showToast(phoneError.value, 'error')
    return
  }
  saving.value = true
  try {
    const payload = {
      display_name: form.display_name,
      real_name: form.real_name,
      phone: form.phone,
      community_id: form.community_id,
      privacy_consent: form.privacy_consent,
    }
    const res = await auth.updateMe(payload)
    user.value = { ...user.value, ...res.data }
    const stored = JSON.parse(localStorage.getItem('userInfo') || '{}')
    Object.assign(stored, res.data)
    localStorage.setItem('userInfo', JSON.stringify(stored))
    showToast('个人信息已保存')
  } catch (e) {
    const msg = e.response?.data?.detail || '保存失败，请稍后再试'
    showToast(msg, 'error')
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (!pwdForm.oldPassword) {
    showToast('请输入旧密码', 'error')
    return
  }
  if (!pwdForm.password) {
    showToast('请输入新密码', 'error')
    return
  }
  if (pwdErrors.value.password) {
    showToast(pwdErrors.value.password, 'error')
    return
  }
  if (pwdErrors.value.confirmPassword) {
    showToast(pwdErrors.value.confirmPassword, 'error')
    return
  }
  if (!pwdForm.confirmPassword) {
    showToast('请确认新密码', 'error')
    return
  }
  changingPwd.value = true
  try {
    await auth.updateMe({ password: pwdForm.password })
    closePwdModal()
    showToast('密码修改成功')
  } catch (e) {
    const msg = e.response?.data?.detail || '密码修改失败，请稍后再试'
    showToast(msg, 'error')
  } finally {
    changingPwd.value = false
  }
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  router.push('/login')
}

// --- Init ---
onMounted(async () => {
  try {
    const [meRes, communitiesRes, casesRes] = await Promise.all([
      auth.me(),
      api.get('/communities'),
      casesApi.list(),
    ])
    user.value = meRes.data
    communities.value = communitiesRes.data || []
    casesList.value = casesRes.data || []
    fillForm(meRes.data)
  } catch (e) {
    console.error('Failed to load profile data', e)
    showToast('加载失败，请刷新重试', 'error')
  } finally {
    pageLoading.value = false
  }
})
</script>

<style scoped>
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--ng-bg-mobile);
  padding-bottom: 80px;
  position: relative;
}

/* Toast */
.toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  padding: 10px 24px;
  border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  box-shadow: var(--ng-shadow-float);
  pointer-events: none;
}
.toast-success {
  background: var(--ng-bg-card);
  color: var(--ng-text-main);
  border: 1px solid var(--ng-border);
}
.toast-success::before {
  content: '\2713 ';
  color: var(--ng-risk-green);
  font-weight: 700;
}
.toast-error {
  background: var(--ng-bg-card);
  color: var(--ng-text-main);
  border: 1px solid var(--ng-border);
}
.toast-error::before {
  content: '\2717 ';
  color: var(--ng-risk-red);
  font-weight: 700;
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity var(--ng-dur-base) var(--ng-ease), transform var(--ng-dur-base) var(--ng-ease);
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-12px);
}

/* Loading */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 0;
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-body);
  gap: var(--ng-space-3);
}
.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Profile Card */
.profile-card {
  background: var(--ng-gradient-hero);
  margin: var(--ng-space-4);
  border-radius: var(--ng-radius-card);
  box-shadow: var(--ng-shadow-card);
  padding: 28px var(--ng-space-5) 22px;
  text-align: center;
}
.avatar-large {
  width: 76px;
  height: 76px;
  border-radius: 50%;
  background: var(--ng-primary);
  color: var(--ng-text-inverse);
  font-size: 32px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--ng-space-3);
  letter-spacing: 1px;
  box-shadow: var(--ng-shadow-btn), 0 0 0 3px var(--ng-bg-card);
}
.user-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--ng-space-2);
  margin-bottom: var(--ng-space-1);
}
.user-name {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
  margin: 0;
}
.user-username {
  font-size: var(--ng-fs-aux);
  color: var(--ng-primary-deep);
  opacity: 0.75;
  margin: 0 0 2px;
}
.role-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--ng-radius-tag);
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
}
.role-resident {
  background: var(--ng-bg-card);
  color: var(--ng-primary-deep);
}
.role-staff {
  background: var(--ng-bg-card);
  color: var(--ng-text-secondary);
  border: 1px solid var(--ng-border-strong);
}
.join-date {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
  margin: 0;
}

/* Stats Row */
.stats-row {
  display: flex;
  gap: 10px;
  margin: 0 var(--ng-space-4) var(--ng-space-4);
}
.stat-card {
  flex: 1;
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
  padding: var(--ng-space-4) var(--ng-space-2);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: var(--ng-space-1);
}
.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--ng-primary);
  line-height: 1.1;
}
.stat-green {
  color: var(--ng-risk-green);
}
.stat-amber {
  color: var(--ng-risk-orange);
}
.stat-label {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}

/* Section Card */
.section-card {
  background: var(--ng-bg-card);
  margin: 0 var(--ng-space-4) var(--ng-space-4);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  box-shadow: var(--ng-shadow-card);
  padding: var(--ng-space-5);
}
.section-title {
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-4);
  padding-bottom: var(--ng-space-3);
  border-bottom: 1px solid var(--ng-border);
}

/* Form */
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group-row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}
.form-label {
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-secondary);
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-input);
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  background: var(--ng-bg-card);
  outline: none;
  transition: border-color var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease);
  box-sizing: border-box;
}
.form-input:focus {
  border-color: var(--ng-primary);
  box-shadow: 0 0 0 3px var(--ng-primary-tint);
}
.form-input::placeholder {
  color: var(--ng-text-hint);
}
.form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-input);
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  background: var(--ng-bg-card);
  outline: none;
  transition: border-color var(--ng-dur-fast) var(--ng-ease), box-shadow var(--ng-dur-fast) var(--ng-ease);
  box-sizing: border-box;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' fill='none' stroke='%239E9893' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 36px;
}
.form-select:focus {
  border-color: var(--ng-primary);
  box-shadow: 0 0 0 3px var(--ng-primary-tint);
}
.form-error {
  font-size: var(--ng-fs-small);
  color: var(--ng-risk-red);
}

/* Toggle Switch */
.toggle-switch {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  cursor: pointer;
  user-select: none;
}
.toggle-switch input {
  display: none;
}
.toggle-slider {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--ng-border-strong);
  border-radius: var(--ng-radius-pill);
  transition: background var(--ng-dur-base) var(--ng-ease);
  flex-shrink: 0;
}
.toggle-slider::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  background: var(--ng-bg-card);
  border-radius: 50%;
  transition: transform var(--ng-dur-base) var(--ng-ease);
  box-shadow: var(--ng-shadow-card);
}
.toggle-switch input:checked + .toggle-slider {
  background: var(--ng-primary);
}
.toggle-switch input:checked + .toggle-slider::after {
  transform: translateX(20px);
}
.toggle-text {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
}

/* Buttons */
.btn-primary {
  width: 100%;
  padding: 12px;
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  font-size: 15px;
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
  margin-top: var(--ng-space-1);
}
.btn-primary:hover {
  filter: brightness(0.96);
}
.btn-primary:active {
  transform: scale(0.98);
}
.btn-primary:disabled {
  background: var(--ng-border-strong);
  box-shadow: none;
  cursor: not-allowed;
}

/* Risk Section */
.risk-section {
  margin-bottom: 18px;
}
.risk-title {
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0 0 10px;
}
.risk-bar {
  display: flex;
  height: 10px;
  border-radius: var(--ng-radius-pill);
  overflow: hidden;
  background: var(--ng-bg-subtle);
  margin-bottom: var(--ng-space-2);
}
.risk-segment {
  min-width: 2px;
  transition: width var(--ng-dur-slow) var(--ng-ease);
}
.risk-empty-text {
  width: 100%;
  text-align: center;
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
  line-height: 10px;
}
.risk-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ng-space-3);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--ng-space-1);
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Recent Cases */
.recent-section {
  border-top: 1px solid var(--ng-border);
  padding-top: var(--ng-space-4);
}
.recent-empty {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-hint);
  text-align: center;
  padding: var(--ng-space-4) 0;
}
.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ng-space-3) 0;
  border-bottom: 1px solid var(--ng-border);
  cursor: pointer;
  transition: background var(--ng-dur-fast) var(--ng-ease);
  margin: 0 -4px;
  padding-left: 4px;
  padding-right: 4px;
  border-radius: var(--ng-radius-tag);
}
.recent-item:last-child {
  border-bottom: none;
}
.recent-item:hover {
  background: var(--ng-bg-mobile);
}
.recent-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.risk-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-green { background: var(--ng-risk-green); }
.dot-yellow { background: var(--ng-risk-yellow); }
.dot-orange { background: var(--ng-risk-orange); }
.dot-red { background: var(--ng-risk-red); }
.recent-item-title {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-main);
  font-weight: var(--ng-fw-strong);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
.recent-item-date {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
  margin: 2px 0 0;
}
.status-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--ng-radius-tag);
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  flex-shrink: 0;
}
.status-draft {
  background: var(--ng-bg-subtle);
  color: var(--ng-text-secondary);
}
.status-diagnosed {
  background: var(--ng-primary-soft);
  color: var(--ng-primary-deep);
}
.status-in_progress {
  background: var(--ng-risk-orange-soft);
  color: var(--ng-risk-orange);
}
.status-resolved {
  background: var(--ng-risk-green-soft);
  color: var(--ng-risk-green);
}
.status-escalated {
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
}

/* Action List */
.action-list {
  display: flex;
  flex-direction: column;
}
.action-item {
  display: flex;
  align-items: center;
  gap: var(--ng-space-3);
  padding: 14px 4px;
  border-bottom: 1px solid var(--ng-border);
  cursor: pointer;
  transition: background var(--ng-dur-fast) var(--ng-ease);
  border-radius: var(--ng-radius-tag);
  margin: 0 -4px;
  padding-left: 4px;
  padding-right: 4px;
}
.action-item:last-child {
  border-bottom: none;
}
.action-item:hover {
  background: var(--ng-bg-mobile);
}
.action-item-danger:hover {
  background: var(--ng-risk-red-soft);
}
.action-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--ng-radius-btn);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.action-icon svg {
  width: 18px;
  height: 18px;
}
.action-icon-case {
  background: var(--ng-primary-soft2);
  color: var(--ng-primary-deep);
}
.action-icon-group {
  background: var(--ng-risk-green-soft);
  color: var(--ng-risk-green);
}
.action-icon-lock {
  background: var(--ng-risk-yellow-soft);
  color: var(--ng-risk-orange);
}
.action-icon-logout {
  background: var(--ng-risk-red-soft);
  color: var(--ng-risk-red);
}
.action-text {
  flex: 1;
  font-size: 15px;
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
}
.action-item-danger .action-text {
  color: var(--ng-risk-red);
}
.action-arrow {
  color: var(--ng-text-hint);
  font-size: 20px;
  font-weight: 300;
}

/* Security Footer */
.security-footer {
  text-align: center;
  padding: var(--ng-space-5) var(--ng-space-4) var(--ng-space-8);
}
.security-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-secondary);
}
.shield-icon {
  width: 16px;
  height: 16px;
  color: var(--ng-risk-green);
  flex-shrink: 0;
}
.privacy-link {
  display: inline-block;
  margin-top: 6px;
  font-size: var(--ng-fs-small);
  color: var(--ng-primary-deep);
  text-decoration: none;
}
.privacy-link:hover {
  text-decoration: underline;
}
.slogan-text {
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-title);
  letter-spacing: 0.04em;
  color: var(--ng-primary-deep);
  opacity: 0.8;
  margin-top: var(--ng-space-3);
}
.version-text {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
  margin-top: var(--ng-space-2);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--ng-text-main);
  background: color-mix(in srgb, var(--ng-text-main) 45%, transparent);
  z-index: 5000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--ng-space-6);
}
.modal-box {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  width: 100%;
  max-width: 400px;
  padding: var(--ng-space-6) var(--ng-space-5);
  box-shadow: var(--ng-shadow-float);
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--ng-space-5);
}
.modal-header h3 {
  font-size: 17px;
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}
.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--ng-text-hint);
  cursor: pointer;
  padding: 0 var(--ng-space-1);
  line-height: 1;
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.modal-close:hover {
  color: var(--ng-text-main);
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--ng-dur-base) var(--ng-ease);
}
.modal-enter-active .modal-box,
.modal-leave-active .modal-box {
  transition: transform var(--ng-dur-base) var(--ng-ease);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-box {
  transform: scale(0.95) translateY(10px);
}
.modal-leave-to .modal-box {
  transform: scale(0.95) translateY(10px);
}

/* Bottom Navigation */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  background: var(--ng-bg-card);
  border-top: 1px solid var(--ng-border-strong);
  display: flex;
  align-items: stretch;
  justify-content: space-around;
  padding: 6px 0 env(safe-area-inset-bottom, 0);
  z-index: 1000;
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 6px 0;
  flex: 1;
  text-decoration: none;
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-small);
  transition: color var(--ng-dur-fast) var(--ng-ease);
}
.nav-item.active {
  color: var(--ng-primary);
}
.nav-icon {
  width: 22px;
  height: 22px;
}
</style>
