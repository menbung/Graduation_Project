import { ref, onMounted, onUnmounted } from 'vue'
import { getAuth, onAuthStateChanged, signInAnonymously, signOut } from 'firebase/auth'
import { app } from '../firebase/index.js'
import { useStatusStore } from '@/stores/status.js'
import { useSwitchStore } from '@/stores/switch.js'
import { storeToRefs } from 'pinia'

// 익명 로그인/로그아웃과 인증 상태를 제공하는 Vue Composable
// 사용 예) const { user, signInAnon, logout, isLoading, error } = useAnonymousLogin()

export function useAnonymousLogin() {
  // 현재 인증된 사용자 객체(없으면 null)
  const user = ref(null)
  // 로그인 관련 정보 저장
  const statusStore = useStatusStore()
  const switchStore = useSwitchStore()
  const { isLoading, isNewUser } = storeToRefs(switchStore)
  // 진행 중인 비동기 작업 상태 표시
  // const isLoading = ref(false)
  // 최근 오류 객체 저장
  const error = ref(null)

  // Firebase Auth 인스턴스 (앱 단일 인스턴스에 종속)
  const auth = getAuth(app)
  // onAuthStateChanged 구독 해제를 위한 핸들러
  let unsubscribe = null

  // Firebase 익명 로그인 수행
  const signInAnon = async () => {
    isLoading.value = true
    error.value = null
    try {
      const result = await signInAnonymously(auth)
      user.value = result.user
      statusStore.updateUser(result.user.uid)
    } catch (e) {
      error.value = e
    } finally {
      isLoading.value = false
    }
  }

  // 현재 로그인된 사용자 로그아웃
  const logout = async () => {
    isLoading.value = true
    error.value = null
    try {
      await signOut(auth)
      user.value = null
      statusStore.deleteUser()
    } catch (e) {
      error.value = e
    } finally {
      isLoading.value = false
    }
  }

  // 컴포넌트 마운트 시 인증 상태 변화를 구독하여 user를 동기화
  onMounted(() => {
    unsubscribe = onAuthStateChanged(auth, (u) => {
      user.value = u
      statusStore.updateUser(user.value.uid)
      isNewUser.value = true
    })
  })

  // 컴포넌트 언마운트 시 구독 정리
  onUnmounted(() => {
    if (typeof unsubscribe === 'function') unsubscribe()
  })

  // 컴포넌트에서 사용할 공개 API 반환
  return {
    user,
    isLoading,
    error,
    signInAnon,
    logout,
  }
}
