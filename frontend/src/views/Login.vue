<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="logo">🌟 邻光</h1>
      <p class="subtitle">邻里之间，有些话只是需要换一种方式说</p>
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
  background: linear-gradient(135deg, #FFF9F0 0%, #FDE8C8 100%);
  padding: 20px;
}
.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 32px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}
.logo {
  font-size: 28px;
  font-weight: 600;
  color: #E8A33D;
  text-align: center;
  margin-bottom: 8px;
}
.subtitle {
  text-align: center;
  color: #6B6560;
  font-size: 14px;
  margin-bottom: 32px;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #2D2A26;
  margin-bottom: 6px;
}
.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E0D8CE;
  border-radius: 12px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus {
  border-color: #E8A33D;
}
.btn-primary {
  width: 100%;
  padding: 14px;
  background: #E8A33D;
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
  transition: background 0.2s;
}
.btn-primary:hover {
  background: #D4922E;
}
.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.error-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #FFF0F0;
  border: 1px solid #FFD4D4;
  border-radius: 10px;
  padding: 12px 16px;
  margin-top: 14px;
  color: #D32F2F;
  font-size: 13px;
  font-weight: 500;
}
.error-box svg {
  flex-shrink: 0;
  color: #F44336;
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
  transition: opacity 0.3s ease;
}
.shake-leave-to {
  opacity: 0;
}
.link {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #6B6560;
}
.link a {
  color: #E8A33D;
  text-decoration: none;
  font-weight: 600;
}
</style>
