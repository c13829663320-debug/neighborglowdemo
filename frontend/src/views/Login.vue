<template>
  <div class="login-page">
    <div class="login-card ng-fade-in">
      <h1 class="logo">🌟 邻光</h1>
      <p class="subtitle">邻里之光，让善意照进千万人家！</p>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码" required />
        </div>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <transition name="shake">
          <div v-if="error" class="error-box">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span>{{ error }}</span>
          </div>
        </transition>
        <p class="link">还没有账号？<router-link to="/register">立即注册</router-link></p>
      </form>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../api'
const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const res = await auth.login(username.value, password.value)
    const data = res.data
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userInfo', JSON.stringify({ role: data.role, user_id: data.user_id, username: data.username }))
    router.push(data.role === 'resident' ? '/resident' : '/staff')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败，请重试'
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
.error-box {
  display: flex;
  align-items: center;
  gap: var(--ng-space-2);
  background: var(--ng-risk-red-soft);
  border: 1px solid var(--ng-risk-red);
  border-radius: var(--ng-radius-btn);
  padding: var(--ng-space-3) var(--ng-space-4);
  margin-top: var(--ng-space-3);
  color: var(--ng-risk-red);
  font-size: var(--ng-fs-aux);
  font-weight: var(--ng-fw-strong);
}
.error-box svg {
  flex-shrink: 0;
  color: var(--ng-risk-red);
}

/* Shake animation */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}
.shake-enter-active {
  animation: shake 0.5s ease-in-out;
}
.shake-leave-active {
  transition: opacity var(--ng-dur-base) var(--ng-ease);
}
.shake-leave-to {
  opacity: 0;
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
