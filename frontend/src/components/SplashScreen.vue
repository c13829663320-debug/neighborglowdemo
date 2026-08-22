<template>
  <div class="ng-splash" role="status" aria-label="邻光启动中">
    <!-- 背景光晕 -->
    <div class="ng-splash__halo" aria-hidden="true"></div>
    <div class="ng-splash__glow ng-splash__glow--top" aria-hidden="true"></div>
    <div class="ng-splash__glow ng-splash__glow--bottom" aria-hidden="true"></div>

    <!-- 品牌核心 -->
    <div class="ng-splash__core">
      <div class="ng-splash__logo-wrap">
        <img :src="logoUrl" alt="邻光 NeighborGlow 标志" class="ng-splash__logo" />
      </div>
      <h1 class="ng-splash__name">邻里之光</h1>
      <p class="ng-splash__wordmark">NEIGHBORGLOW</p>
      <p class="ng-splash__slogan">
        邻里之光，<br />让善意照进千万人家！
      </p>
    </div>

    <!-- 底部加载 -->
    <div class="ng-splash__loading">
      <div class="ng-splash__dots" aria-hidden="true">
        <span class="ng-splash__dot"></span>
        <span class="ng-splash__dot"></span>
        <span class="ng-splash__dot"></span>
      </div>
      <p class="ng-splash__loading-text">正在点亮邻里善意</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import logoUrl from '../assets/logo.png'

const emit = defineEmits(['done'])

const SPLASH_DURATION = 2200

let timer = null
onMounted(() => {
  timer = setTimeout(() => emit('done'), SPLASH_DURATION)
})
onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})
</script>

<style scoped>
.ng-splash {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  background: var(--ng-bg-mobile);
  overflow: hidden;
  font-family: var(--ng-font-family);
}

/* ---------- 背景光晕 ---------- */
.ng-splash__halo {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 140vmax;
  height: 140vmax;
  transform: translate(-50%, -58%);
  background: radial-gradient(
    circle,
    rgba(232, 163, 61, 0.16) 0%,
    rgba(232, 163, 61, 0.06) 34%,
    transparent 62%
  );
  animation: ng-splash-halo-breathe 3.2s var(--ng-ease) infinite;
  pointer-events: none;
}
.ng-splash__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  pointer-events: none;
}
.ng-splash__glow--top {
  top: -18vmax;
  right: -14vmax;
  width: 46vmax;
  height: 46vmax;
  background: radial-gradient(circle, rgba(253, 232, 200, 0.9), transparent 68%);
}
.ng-splash__glow--bottom {
  bottom: -20vmax;
  left: -14vmax;
  width: 42vmax;
  height: 42vmax;
  background: radial-gradient(circle, rgba(255, 243, 224, 0.95), transparent 68%);
}
@keyframes ng-splash-halo-breathe {
  0%, 100% { opacity: 0.75; transform: translate(-50%, -58%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -58%) scale(1.05); }
}

/* ---------- 品牌核心 ---------- */
.ng-splash__core {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 var(--ng-space-6);
  margin-top: 16vh;
}
.ng-splash__logo-wrap {
  width: 118px;
  height: 118px;
  border-radius: 50%;
  background: var(--ng-bg-card);
  border: 1px solid var(--ng-border);
  box-shadow: 0 8px 24px rgba(232, 163, 61, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  animation: ng-splash-logo-in 0.7s var(--ng-ease) both;
}
.ng-splash__logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.ng-splash__name {
  margin-top: var(--ng-space-5);
  font-size: 30px;
  font-weight: var(--ng-fw-title);
  letter-spacing: 6px;
  text-indent: 6px;
  color: var(--ng-text-main);
  animation: ng-splash-rise-in 0.6s var(--ng-ease) 0.25s both;
}
.ng-splash__wordmark {
  margin-top: var(--ng-space-1);
  font-size: var(--ng-fs-small);
  font-weight: var(--ng-fw-strong);
  letter-spacing: 4px;
  text-indent: 4px;
  color: var(--ng-primary-deep);
  animation: ng-splash-rise-in 0.6s var(--ng-ease) 0.4s both;
}
.ng-splash__slogan {
  margin-top: var(--ng-space-6);
  font-size: 17px;
  line-height: 1.9;
  color: var(--ng-text-secondary);
  animation: ng-splash-rise-in 0.7s var(--ng-ease) 0.6s both;
}

/* ---------- 底部加载 ---------- */
.ng-splash__loading {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--ng-space-2);
  padding-bottom: calc(9vh + env(safe-area-inset-bottom));
  animation: ng-splash-rise-in 0.6s var(--ng-ease) 0.8s both;
}
.ng-splash__dots {
  display: flex;
  gap: var(--ng-space-2);
}
.ng-splash__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ng-primary);
  animation: ng-splash-dot-breathe 1.2s var(--ng-ease) infinite;
}
.ng-splash__dot:nth-child(2) { animation-delay: 0.2s; }
.ng-splash__dot:nth-child(3) { animation-delay: 0.4s; }
.ng-splash__loading-text {
  font-size: var(--ng-fs-aux);
  color: var(--ng-text-hint);
}

@keyframes ng-splash-logo-in {
  from { opacity: 0; transform: scale(0.82); }
  to { opacity: 1; transform: scale(1); }
}
@keyframes ng-splash-rise-in {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes ng-splash-dot-breathe {
  0%, 100% { opacity: 0.35; transform: scale(0.85); }
  50% { opacity: 1; transform: scale(1.1); }
}

/* ---------- 减弱动效偏好 ---------- */
@media (prefers-reduced-motion: reduce) {
  .ng-splash__halo,
  .ng-splash__logo-wrap,
  .ng-splash__name,
  .ng-splash__wordmark,
  .ng-splash__slogan,
  .ng-splash__loading,
  .ng-splash__dot {
    animation: none;
  }
}
</style>
