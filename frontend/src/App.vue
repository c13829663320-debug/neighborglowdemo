<template>
  <div id="app-root">
    <DegradeBanner />
    <router-view />
  </div>
</template>
<script setup>
import DegradeBanner from './components/DegradeBanner.vue'
</script>
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  background: #FFF9F0;
  min-height: 100vh;
  color: #2D2A26;
}
</style>
