import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useSwitchStore = defineStore('switch', () => {
  const isLoading = ref(false)
  const isNewUser = ref(false)

  return {
    isLoading,
    isNewUser,
  }
})
