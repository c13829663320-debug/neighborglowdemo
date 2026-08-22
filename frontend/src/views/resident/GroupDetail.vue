<template>
  <div class="page">
    <header class="top-bar">
      <button @click="$router.back()" class="btn-back">← 返回</button>
      <h1>群组详情</h1>
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
.page { max-width: 480px; margin: 0 auto; min-height: 100vh; background: #FFF9F0; }
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.btn-back { background: none; border: none; font-size: 14px; color: #E8A33D; cursor: pointer; }
.top-bar h1 { font-size: 17px; font-weight: 600; }
.main-content { padding: 20px; }
</style>
