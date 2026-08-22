<template>
  <div class="ng-skeleton-card">
    <div class="ng-skeleton" style="width: 40%; height: 18px"></div>
    <div class="ng-skeleton" style="width: 100%; height: 64px; border-radius: 12px"></div>
    <div class="ng-skeleton" style="width: 90%; height: 12px"></div>
    <div class="ng-skeleton" style="width: 70%; height: 12px"></div>
    <p class="skeleton-hint">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '正在分析情况…' },
})
</script>

<style scoped>
.skeleton-hint {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-hint);
  text-align: center;
  margin-top: var(--ng-space-1);
}
</style>
