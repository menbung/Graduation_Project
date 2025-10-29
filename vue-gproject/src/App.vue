<script setup>
import { useRouter, RouterView } from 'vue-router'
// import HelloWorld from './components/HelloWorld.vue'

const router = useRouter()
function goToHome() {
  router.push('/about')
}
</script>

<template>
  <!-- <header>
    <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="125" height="125" />

    <div class="wrapper">
      <HelloWorld msg="You did it!" />

      <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
      </nav>
    </div>
  </header> -->
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
/* header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
} */

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

@media (min-width: 1024px) {
  /* header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  } */
}
</style>
