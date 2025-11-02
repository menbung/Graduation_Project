<script setup>
import { useRouter, RouterView } from 'vue-router'
// import HelloWorld from './components/HelloWorld.vue'

const router = useRouter()
function goToHome() {
  router.push('/')
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <div class="logo" @click="goToHome"></div>
    </div>
  </header>

  <main class="app-main">
    <RouterView />
  </main>
</template>

<style scoped>
/* Header */
.app-header {
  background: var(--brand-color);
  position: fixed;
  top: 0;
  margin: 0;
  width: 100%;
  z-index: 100;
}
.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
}
.logo {
  margin: 0;
  width: 120px;
  height: var(--header-height);
  background-size: cover;
  background-position: center;
  background-image: url('@/assets/image/logo.png');
  cursor: pointer;
}

.app-main {
  margin: 0 auto;
  margin-top: var(--header-height);
  padding: 2rem;
}
</style>
