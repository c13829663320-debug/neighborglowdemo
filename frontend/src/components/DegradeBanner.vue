<template>
  <transition name="ng-slide">
    <div v-if="degraded" class="ng-degrade-banner degrade-banner-fixed">
      <span class="degrade-icon">⚠️</span>
      <span>AI 服务繁忙，已为你切换基础模式</span>
    </div>
  </transition>
</template>

<script setup>
import { useAIDegradation } from '../composables/useAIDegradation'
const { degraded } = useAIDegradation()
</script>

<style scoped>
.degrade-banner-fixed {
  position: fixed;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9000;
  width: min(440px, calc(100vw - 40px));
  box-shadow: var(--ng-shadow-float);
}
.ng-slide-enter-active,
.ng-slide-leave-active {
  transition: all var(--ng-dur-base) var(--ng-ease);
}
.ng-slide-enter-from,
.ng-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, -16px);
}
</style>
