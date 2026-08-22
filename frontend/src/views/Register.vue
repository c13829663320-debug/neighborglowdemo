<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="logo">🌟 邻光</h1>
      <p class="subtitle">创建你的账号，加入社区</p>
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
  background: linear-gradient(135deg, #FFF9F0 0%, #FDE8C8 100%);
  padding: 20px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 32px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
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

.optional {
  font-weight: 400;
  font-size: 12px;
  color: #6B6560;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #E0D8CE;
  border-radius: 12px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  border-color: #E8A33D;
}

.form-group input.input-error {
  border-color: #F44336;
}

.field-error {
  display: block;
  color: #F44336;
  font-size: 12px;
  margin-top: 4px;
  padding-left: 4px;
}

/* Role selection cards */
.role-cards {
  display: flex;
  gap: 12px;
}

.role-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 8px;
  border: 1.5px solid #E0D8CE;
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
  background: #fff;
  user-select: none;
}

.role-card:hover {
  border-color: #E8A33D;
  background: #FFFBF4;
}

.role-card.active {
  border-color: #E8A33D;
  background: #FFF7EC;
  box-shadow: 0 0 0 1px #E8A33D;
}

.role-icon {
  font-size: 24px;
  line-height: 1;
}

.role-title {
  font-size: 14px;
  font-weight: 600;
  color: #2D2A26;
}

.role-desc {
  font-size: 11px;
  color: #6B6560;
}

/* Button */
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

/* Messages */
.error {
  color: #F44336;
  font-size: 13px;
  text-align: center;
  margin-top: 12px;
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
