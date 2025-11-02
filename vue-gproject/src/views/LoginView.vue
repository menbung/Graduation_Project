<script setup>
import { useRouter } from 'vue-router'
import { useAnonymousLogin } from '@/composables/login'
import { useGetDataDb } from '@/composables/getDataDb'
import { useSwitchStore } from '@/stores/switch.js'
import { storeToRefs } from 'pinia'

const router = useRouter()
const auth = useAnonymousLogin()
const getDataDb = useGetDataDb()
const switchStore = useSwitchStore()
const { isNewUser } = storeToRefs(switchStore)
function loginClick() {
  if (isNewUser.value) {
    getDataDb.loadFromDb()
    // router.push('/main')
    router.push('/collect-data')
  } else {
    auth.signInAnon()
    router.push('/collect-data')
  }
}
</script>

<template>
  <div class="login-popup-overlay">
    <div class="login-popup" @click.stop>
      <div class="popup-header">
        <h3>졸프에 오신걸 환영합니다</h3>
      </div>
      <div class="button-container">
        <button class="login-btn" @click="loginClick">게스트로 로그인</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.login-popup {
  background: white;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  /* animation: popupSlideIn 0.3s ease-out; */
}

.popup-header {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 24px;
}

.popup-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
  font-family: 'BMHanna';
}

.button-container {
  display: flex;
  justify-content: center;
}
.login-btn {
  padding: 12px 24px;
  background: var(--brand-color);
  border: 1px solid #717171;
  border-radius: 8px;
  cursor: pointer;
  font-size: 20px;
  font-weight: 700;
}
</style>
