<template>
  <div class="page ng-fade-in">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">← 返回</button>
      <h1>我的群组</h1>
      <span></span>
    </header>
    <main class="main-content">
      <p>页面开发中...</p>
    </main>
  </div>
</template>
<script setup>
</script>
<style scoped>
.page {
  max-width: 480px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--ng-bg-mobile);
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--ng-space-4) var(--ng-page-margin-mobile);
}
.btn-back {
  background: none;
  border: none;
  font-size: var(--ng-fs-body);
  color: var(--ng-primary-deep);
  cursor: pointer;
  transition: opacity var(--ng-dur-fast) var(--ng-ease);
}
.btn-back:hover { opacity: 0.75; }
.top-bar h1 {
  font-size: var(--ng-fs-page);
  font-weight: var(--ng-fw-title);
  color: var(--ng-text-main);
  margin: 0;
}
.main-content { padding: var(--ng-page-margin-mobile); }
.main-content p {
  font-size: var(--ng-fs-body);
  color: var(--ng-text-hint);
  text-align: center;
}
</style>
