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
  font-family: var(--ng-font-family);
  background: var(--ng-bg-mobile);
  min-height: 100vh;
  color: var(--ng-text-main);
}
</style>
