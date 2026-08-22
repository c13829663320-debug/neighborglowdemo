<template>
  <div class="page">
    <!-- Toast -->
    <transition name="toast-fade">
      <div v-if="toast.show" :class="['toast', `toast-${toast.type}`]">{{ toast.msg }}</div>
    </transition>

    <!-- Top Bar -->
    <header class="top-bar">
      <button class="btn-back" @click="$router.push('/staff')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        返回
      </button>
      <h1 class="page-title">物品管理</h1>
      <button class="btn-add-top" @click="showAddForm = true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      </button>
    </header>

    <!-- Add Item Form -->
    <transition name="form-slide">
      <section v-if="showAddForm" class="add-form">
        <h3 class="form-title">添加新物品</h3>
        <div class="form-group">
          <label class="form-label">物品名称</label>
          <input v-model="form.title" class="form-input" placeholder="例如：失物招领 - 黑色钱包" maxlength="60" />
        </div>
        <div class="form-group">
          <label class="form-label">描述</label>
          <textarea v-model="form.description" class="form-textarea" placeholder="描述物品详情、发现地点、时间等..." rows="3" maxlength="300"></textarea>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="closeForm">取消</button>
          <button class="btn-submit" :disabled="!form.title.trim() || submitLoading" @click="addItem">
            <div v-if="submitLoading" class="spinner-sm"></div>
            <template v-else>添加物品</template>
          </button>
        </div>
      </section>
    </transition>

    <!-- Stats -->
    <section class="stats-row">
      <div class="stat-item ng-card--hero">
        <span class="stat-num">{{ itemsList.length }}</span>
        <span class="stat-label">物品总数</span>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="loading && itemsList.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>加载物品列表...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="itemsList.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#E0D8CE" stroke-width="1.5"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
      </div>
      <p class="empty-text">暂无物品记录</p>
      <p class="empty-hint">点击上方 + 按钮添加失物招领或物品信息</p>
    </div>

    <!-- Items List -->
    <section v-else class="items-list">
      <div v-for="item in itemsList" :key="item.id" class="item-card">
        <div class="item-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E8A33D" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
        </div>
        <div class="item-body">
          <h4 class="item-title">{{ item.title }}</h4>
          <p class="item-desc" v-if="item.description">{{ item.description }}</p>
        </div>
        <button class="btn-delete" @click="confirmDelete(item)" :disabled="deleteId === item.id">
          <template v-if="deleteId === item.id">
            <div class="spinner-sm spinner-red"></div>
          </template>
          <template v-else>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
          </template>
        </button>
      </div>
    </section>

    <!-- Delete Confirm Modal -->
    <transition name="modal-fade">
      <div v-if="deleteModal.show" class="modal-overlay" @click.self="deleteModal.show = false">
        <div class="modal-box">
          <h3 class="modal-title">确认删除</h3>
          <p class="modal-desc">确定删除物品「<strong>{{ deleteModal.item?.title }}</strong>」？此操作不可撤销。</p>
          <div class="modal-actions">
            <button class="btn-modal-cancel" @click="deleteModal.show = false">取消</button>
            <button class="btn-modal-confirm" :disabled="deleteId !== null" @click="doDelete">确认删除</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { items as itemsApi } from '../../api'

const loading = ref(false)
const submitLoading = ref(false)
const deleteId = ref(null)
const showAddForm = ref(false)
const itemsList = ref([])
const form = ref({ title: '', description: '' })
const deleteModal = ref({ show: false, item: null })
const toast = ref({ show: false, msg: '', type: 'success' })
let toastTimer = null

function showToast(msg, type = 'success') {
  toast.value = { show: true, msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

async function loadItems() {
  loading.value = true
  try {
    const res = await itemsApi.list()
    itemsList.value = Array.isArray(res.data) ? res.data : []
  } catch {
    showToast('加载物品列表失败', 'error')
    itemsList.value = []
  } finally {
    loading.value = false
  }
}

function closeForm() {
  showAddForm.value = false
  form.value = { title: '', description: '' }
}

async function addItem() {
  if (!form.value.title.trim()) return
  submitLoading.value = true
  try {
    await itemsApi.create({
      title: form.value.title.trim(),
      description: form.value.description.trim() || null
    })
    showToast('物品添加成功')
    closeForm()
    await loadItems()
  } catch {
    showToast('添加失败，请重试', 'error')
  } finally {
    submitLoading.value = false
  }
}

function confirmDelete(item) {
  deleteModal.value = { show: true, item }
}

async function doDelete() {
  const item = deleteModal.value.item
  if (!item) return
  deleteModal.value.show = false
  deleteId.value = item.id
  try {
    await itemsApi.remove(item.id)
    itemsList.value = itemsList.value.filter(i => i.id !== item.id)
    showToast('已删除')
  } catch {
    showToast('删除失败，请重试', 'error')
  } finally {
    deleteId.value = null
  }
}

onMounted(() => { loadItems() })
onBeforeUnmount(() => { clearTimeout(toastTimer) })
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--ng-bg-desktop);
  color: var(--ng-text-main);
  padding: var(--ng-page-margin-desktop);
}

/* Toast */
.toast {
  position: fixed; top: var(--ng-space-4); left: 50%; transform: translateX(-50%);
  z-index: 1000; padding: 10px 24px; border-radius: var(--ng-radius-pill);
  font-size: var(--ng-fs-aux); font-weight: var(--ng-fw-strong);
  box-shadow: var(--ng-shadow-float); white-space: nowrap;
}
.toast-success { background: var(--ng-text-main); color: var(--ng-text-inverse); }
.toast-error { background: var(--ng-risk-red); color: var(--ng-text-inverse); }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* Top Bar */
.top-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: var(--ng-space-4); margin-bottom: var(--ng-space-5);
  border-bottom: 1px solid var(--ng-border);
}
.btn-back {
  display: flex; align-items: center; gap: var(--ng-space-1);
  background: none; border: none; color: var(--ng-primary);
  font-size: var(--ng-fs-body); font-weight: var(--ng-fw-strong);
  cursor: pointer; padding: 6px 10px; border-radius: var(--ng-radius-btn);
  transition: background var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { background: var(--ng-primary-soft2); }
.page-title { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); margin: 0; }
.btn-add-top {
  width: 36px; height: 36px; border-radius: var(--ng-radius-btn); border: none;
  background: var(--ng-gradient-btn); color: var(--ng-text-inverse);
  display: flex; align-items: center; justify-content: center; cursor: pointer;
  box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-add-top:hover { filter: brightness(0.94); }
.btn-add-top:active { transform: scale(0.98); }

/* Add Form */
.add-form {
  margin-bottom: var(--ng-space-5); padding: var(--ng-card-padding);
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border); border-radius: var(--ng-radius-card);
  box-shadow: var(--ng-shadow-card);
}
.form-title { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0 0 14px; }
.form-group { margin-bottom: var(--ng-card-gap); }
.form-label {
  display: block; font-size: var(--ng-fs-small); font-weight: var(--ng-fw-title);
  color: var(--ng-text-secondary); margin-bottom: 6px;
}
.form-input {
  width: 100%; padding: 10px var(--ng-space-3);
  border: 1px solid var(--ng-border-strong); border-radius: var(--ng-radius-input);
  font-size: var(--ng-fs-body); color: var(--ng-text-main); background: var(--ng-bg-card);
  outline: none; transition: all var(--ng-dur-fast) var(--ng-ease); box-sizing: border-box;
}
.form-input:focus { border-color: var(--ng-primary); box-shadow: 0 0 0 3px var(--ng-primary-tint); }
.form-input::placeholder { color: var(--ng-text-hint); }
.form-textarea {
  width: 100%; padding: 10px var(--ng-space-3);
  border: 1px solid var(--ng-border-strong); border-radius: var(--ng-radius-input);
  font-size: var(--ng-fs-body); color: var(--ng-text-main); background: var(--ng-bg-card);
  outline: none; resize: vertical; min-height: 70px;
  transition: all var(--ng-dur-fast) var(--ng-ease);
  box-sizing: border-box; font-family: inherit;
}
.form-textarea:focus { border-color: var(--ng-primary); box-shadow: 0 0 0 3px var(--ng-primary-tint); }
.form-textarea::placeholder { color: var(--ng-text-hint); }
.form-actions { display: flex; gap: 10px; margin-top: 14px; }
.btn-cancel {
  flex: 1; padding: 10px; border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card); font-size: var(--ng-fs-body); color: var(--ng-text-secondary);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-cancel:hover { background: var(--ng-bg-subtle); }
.btn-submit {
  flex: 1; padding: 10px; border: none; border-radius: var(--ng-radius-btn);
  background: var(--ng-gradient-btn); color: var(--ng-text-inverse);
  font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  gap: 6px; box-shadow: var(--ng-shadow-btn);
  transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-submit:hover:not(:disabled) { filter: brightness(0.94); }
.btn-submit:active:not(:disabled) { transform: scale(0.98); }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.form-slide-enter-active, .form-slide-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.form-slide-enter-from, .form-slide-leave-to { opacity: 0; transform: translateY(-10px); }

/* Stats */
.stats-row { margin-bottom: var(--ng-space-5); }
.stat-item {
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding); display: flex; align-items: center; gap: 10px;
  box-shadow: var(--ng-shadow-card);
  transition: all var(--ng-dur-base) var(--ng-ease);
}
.stat-item:hover { box-shadow: var(--ng-shadow-card-hover); transform: translateY(-2px); }
.stat-num { font-size: var(--ng-fs-page); font-weight: var(--ng-fw-title); }
.stat-label { font-size: var(--ng-fs-aux); }
.stat-item.ng-card--hero .stat-num,
.stat-item.ng-card--hero .stat-label { color: var(--ng-primary-deep); }

/* Loading & Empty */
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px var(--ng-space-5); color: var(--ng-text-secondary); gap: var(--ng-card-gap);
}
.loading-state p { font-size: var(--ng-fs-body); margin: 0; }
.spinner {
  width: 32px; height: 32px; border: 3px solid var(--ng-border-strong);
  border-top-color: var(--ng-primary); border-radius: 50%; animation: spin 0.8s linear infinite;
}
.spinner-sm {
  width: 16px; height: 16px; border: 2px solid var(--ng-primary-tint);
  border-top-color: var(--ng-text-inverse); border-radius: 50%;
  animation: spin 0.8s linear infinite; flex-shrink: 0;
}
.spinner-red { border-top-color: var(--ng-risk-red); }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 64px var(--ng-space-6); text-align: center;
}
.empty-icon { margin-bottom: var(--ng-space-4); opacity: 0.6; }
.empty-text { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-strong); color: var(--ng-text-main); margin: 0 0 6px; }
.empty-hint { font-size: var(--ng-fs-aux); color: var(--ng-text-secondary); margin: 0; }

/* Items List */
.items-list { display: flex; flex-direction: column; gap: var(--ng-card-gap); }
.item-card {
  display: flex; align-items: flex-start; gap: var(--ng-card-gap);
  background: var(--ng-bg-card); border: 1px solid var(--ng-border);
  border-radius: var(--ng-radius-card);
  padding: var(--ng-card-padding); box-shadow: var(--ng-shadow-card);
  transition: all var(--ng-dur-base) var(--ng-ease);
}
.item-card:hover { box-shadow: var(--ng-shadow-card-hover); transform: translateY(-2px); }
.item-icon {
  width: 40px; height: 40px; border-radius: var(--ng-radius-btn);
  background: var(--ng-primary-soft2);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.item-body { flex: 1; min-width: 0; }
.item-title {
  font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title); color: var(--ng-text-main);
  margin: 0 0 var(--ng-space-1);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.item-desc {
  font-size: var(--ng-fs-small); color: var(--ng-text-secondary); line-height: 1.5; margin: 0;
  overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}
.btn-delete {
  flex-shrink: 0; width: 36px; height: 36px; border-radius: var(--ng-radius-btn);
  border: 1px solid var(--ng-border-strong); background: var(--ng-bg-card);
  color: var(--ng-text-hint);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-delete:hover:not(:disabled) {
  border-color: var(--ng-risk-red); color: var(--ng-risk-red); background: var(--ng-risk-red-soft);
}
.btn-delete:active:not(:disabled) { transform: scale(0.98); }
.btn-delete:disabled { opacity: 0.5; cursor: not-allowed; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: var(--ng-primary-tint);
  backdrop-filter: blur(2px); z-index: 200;
  display: flex; align-items: center; justify-content: center; padding: var(--ng-space-6);
}
.modal-box {
  background: var(--ng-bg-card); border-radius: var(--ng-radius-card);
  padding: var(--ng-space-6);
  width: 100%; max-width: 360px; box-shadow: var(--ng-shadow-float);
}
.modal-title { font-size: var(--ng-fs-card); font-weight: var(--ng-fw-title); margin: 0 0 var(--ng-card-gap); }
.modal-desc { font-size: var(--ng-fs-body); color: var(--ng-text-secondary); line-height: 1.6; margin: 0 0 var(--ng-space-5); }
.modal-actions { display: flex; gap: 10px; }
.btn-modal-cancel {
  flex: 1; padding: 10px; border: 1px solid var(--ng-border-strong);
  border-radius: var(--ng-radius-btn);
  background: var(--ng-bg-card); font-size: var(--ng-fs-body); color: var(--ng-text-secondary);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-modal-cancel:hover { background: var(--ng-bg-subtle); }
.btn-modal-confirm {
  flex: 1; padding: 10px; border: none; border-radius: var(--ng-radius-btn);
  background: var(--ng-risk-red); color: var(--ng-text-inverse);
  font-size: var(--ng-fs-body); font-weight: var(--ng-fw-title);
  cursor: pointer; transition: all var(--ng-dur-fast) var(--ng-ease);
}
.btn-modal-confirm:hover:not(:disabled) { filter: brightness(0.92); }
.btn-modal-confirm:active:not(:disabled) { transform: scale(0.98); }
.btn-modal-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: all var(--ng-dur-base) var(--ng-ease); }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
