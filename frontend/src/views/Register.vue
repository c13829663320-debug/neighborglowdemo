<template>
  <div class="login-page">
    <div class="login-card ng-fade-in">
      <h1 class="logo">🌟 邻光</h1>
      <p class="subtitle">邻里之光，让善意照进千万人家！</p>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="form.username" type="text" placeholder="请输入用户名" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="form.password" type="password" placeholder="请输入密码" required />
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
            :class="{ 'input-error': passwordMismatch }"
          />
          <span v-if="passwordMismatch" class="field-error">两次输入的密码不一致</span>
        </div>
        <div class="form-group">
          <label>角色选择</label>
          <div class="role-cards">
            <div
              class="role-card"
              :class="{ active: form.role === 'resident' }"
              @click="form.role = 'resident'"
            >
              <span class="role-icon">🏠</span>
              <span class="role-title">居民</span>
              <span class="role-desc">我是社区居民</span>
            </div>
            <div
              class="role-card"
              :class="{ active: form.role === 'staff' }"
              @click="form.role = 'staff'"
            >
              <span class="role-icon">🏢</span>
              <span class="role-title">社区管理者</span>
              <span class="role-desc">我是社区管理人员</span>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label>显示名称 <span class="optional">（选填）</span></label>
          <input v-model="form.display_name" type="text" placeholder="你的昵称" />
        </div>
        <button type="submit" class="btn-primary" :disabled="loading || passwordMismatch">
          {{ loading ? '注册中...' : '注册' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
        <p class="link">已有账号？<router-link to="/login">立即登录</router-link></p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../api'

const router = useRouter()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'resident',
  display_name: ''
})

const loading = ref(false)
const error = ref('')

const passwordMismatch = computed(() => {
  return form.confirmPassword.length > 0 && form.password !== form.confirmPassword
})

async function handleRegister() {
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const payload = {
      username: form.username,
      password: form.password,
      role: form.role,
      display_name: form.display_name || undefined
    }
    const res = await auth.register(payload)
    const data = res.data
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userInfo', JSON.stringify({
      role: data.role,
      user_id: data.user_id,
      username: data.username
    }))
    router.push(data.role === 'resident' ? '/resident' : '/staff')
  } catch (e) {
    error.value = e.response?.data?.detail || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--ng-bg-mobile) 0%, var(--ng-primary-soft) 100%);
  padding: var(--ng-page-margin-mobile);
}

.login-card {
  background: var(--ng-bg-card);
  border-radius: var(--ng-radius-card);
  border: 1px solid var(--ng-border);
  padding: 40px var(--ng-space-8);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--ng-shadow-float);
}

.logo {
  display: flex;
  align-items: center;
  width: max-content;
  margin: 0 auto var(--ng-space-4);
  padding: var(--ng-space-3) var(--ng-space-6);
  background: var(--ng-gradient-hero);
  border-radius: var(--ng-radius-pill);
  font-size: 24px;
  font-weight: var(--ng-fw-title);
  color: var(--ng-primary-deep);
}

.subtitle {
  text-align: center;
  color: var(--ng-text-secondary);
  font-size: var(--ng-fs-body);
  margin-bottom: var(--ng-space-8);
}

.form-group {
  margin-bottom: var(--ng-space-4);
}

.form-group label {
  display: block;
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-strong);
  color: var(--ng-text-main);
  margin-bottom: var(--ng-space-2);
}

.optional {
  font-weight: var(--ng-fw-body);
  font-size: var(--ng-fs-small);
  color: var(--ng-text-hint);
}

.form-group input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-input);
  font-size: var(--ng-fs-body);
  font-family: inherit;
  color: var(--ng-text-main);
  background: var(--ng-bg-card);
  outline: none;
  box-sizing: border-box;
  transition: border-color var(--ng-dur-fast) var(--ng-ease),
              box-shadow var(--ng-dur-fast) var(--ng-ease);
}

.form-group input:focus {
  border-color: var(--ng-primary);
  box-shadow: 0 0 0 3px var(--ng-primary-tint);
}

.form-group input.input-error {
  border-color: var(--ng-risk-red);
}

.form-group input.input-error:focus {
  border-color: var(--ng-risk-red);
  box-shadow: 0 0 0 3px var(--ng-risk-red-soft);
}

.field-error {
  display: block;
  color: var(--ng-risk-red);
  font-size: var(--ng-fs-small);
  margin-top: var(--ng-space-1);
  padding-left: var(--ng-space-1);
}

/* Role selection cards */
.role-cards {
  display: flex;
  gap: var(--ng-space-3);
}

.role-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-1);
  padding: 14px var(--ng-space-2);
  border: 1.5px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  cursor: pointer;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  background: var(--ng-bg-card);
  user-select: none;
}

.role-card:hover {
  border-color: var(--ng-primary);
  background: var(--ng-bg-mobile);
}

.role-card.active {
  border-color: var(--ng-primary);
  background: var(--ng-primary-soft2);
  box-shadow: 0 0 0 1px var(--ng-primary);
}

.role-icon {
  font-size: 24px;
  line-height: 1;
}

.role-title {
  font-size: var(--ng-fs-body);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
}

.role-desc {
  font-size: var(--ng-fs-small);
  color: var(--ng-text-secondary);
}

/* Button */
.btn-primary {
  width: 100%;
  padding: 14px;
  background: var(--ng-gradient-btn);
  color: var(--ng-text-inverse);
  border: none;
  border-radius: var(--ng-radius-btn);
  font-size: var(--ng-fs-card);
  font-weight: var(--ng-fw-title);
  cursor: pointer;
  margin-top: var(--ng-space-2);
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}

.btn-primary:hover {
  background: var(--ng-primary-dark);
}

.btn-primary:active {
  transform: scale(0.98);
}

.btn-primary:disabled {
  background: var(--ng-border-strong);
  box-shadow: none;
  cursor: not-allowed;
}

/* Messages */
.error {
  color: var(--ng-risk-red);
  font-size: var(--ng-fs-aux);
  text-align: center;
  margin-top: var(--ng-space-3);
}

.link {
  text-align: center;
  margin-top: var(--ng-space-4);
  font-size: var(--ng-fs-body);
  color: var(--ng-text-secondary);
}

.link a {
  color: var(--ng-primary-deep);
  text-decoration: none;
  font-weight: var(--ng-fw-strong);
  transition: color var(--ng-dur-fast) var(--ng-ease);
}

.link a:hover {
  color: var(--ng-primary-dark);
}
</style>
