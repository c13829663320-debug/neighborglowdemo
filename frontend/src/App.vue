<template>
  <div id="app-root">
    <Transition name="ng-splash-fade">
      <SplashScreen v-if="showSplash" @done="showSplash = false" />
    </Transition>
    <DegradeBanner />
    <router-view />
  </div>
</template>
<script setup>
import { ref } from 'vue'
import DegradeBanner from './components/DegradeBanner.vue'
import SplashScreen from './components/SplashScreen.vue'

const showSplash = ref(true)
</script>
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: var(--ng-font-family);
  background: var(--ng-bg-mobile);
  min-height: 100vh;
  color: var(--ng-text-main);
}
/* 闪屏淡出过渡 */
.ng-splash-fade-leave-active {
  transition: opacity 0.45s var(--ng-ease);
}
.ng-splash-fade-leave-to {
  opacity: 0;
}
</style>
