<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="logo">🌟 邻光</h1>
      <p class="subtitle">创建你的账号</p>
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
          <label>显示名称</label>
          <input v-model="form.display_name" type="text" placeholder="你的昵称" />
        </div>
        <div class="form-group">
          <label>手机号</label>
          <input v-model="form.phone" type="tel" placeholder="选填" />
        </div>
        <div class="form-group">
          <label>角色</label>
          <select v-model="form.role">
            <option value="resident">居民</option>
            <option value="staff">社区管理者</option>
          </select>
        </div>
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">注册成功！<router-link to="/login">去登录</router-link></p>
        <p class="link">已有账号？<router-link to="/login">去登录</router-link></p>
      </form>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { auth } from '../api'
const form = reactive({ username: '', password: '', display_name: '', phone: '', role: 'resident' })
const loading = ref(false)
const error = ref('')
const success = ref(false)
async function handleRegister() {
  loading.value = true
  error.value = ''
  success.value = false
  try {
    await auth.register({ ...form, real_name: form.display_name })
    success.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #FFF9F0 0%, #FDE8C8 100%); padding: 20px; }
.login-card { background: #fff; border-radius: 16px; padding: 40px 32px; width: 100%; max-width: 400px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
.logo { font-size: 28px; font-weight: 600; color: #E8A33D; text-align: center; margin-bottom: 8px; }
.subtitle { text-align: center; color: #6B6560; font-size: 14px; margin-bottom: 24px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; font-weight: 600; color: #2D2A26; margin-bottom: 6px; }
.form-group input, .form-group select { width: 100%; padding: 12px 16px; border: 1px solid #E0D8CE; border-radius: 12px; font-size: 15px; outline: none; background: #fff; }
.form-group input:focus, .form-group select:focus { border-color: #E8A33D; }
.btn-primary { width: 100%; padding: 14px; background: #E8A33D; color: #fff; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 8px; }
.btn-primary:disabled { background: #ccc; cursor: not-allowed; }
.error { color: #F44336; font-size: 13px; text-align: center; margin-top: 12px; }
.success { color: #4CAF50; font-size: 13px; text-align: center; margin-top: 12px; }
.success a { color: #E8A33D; text-decoration: none; font-weight: 600; }
.link { text-align: center; margin-top: 16px; font-size: 14px; color: #6B6560; }
.link a { color: #E8A33D; text-decoration: none; font-weight: 600; }
</style>
