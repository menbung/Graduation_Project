import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useStatusStore = defineStore('status', () => {
  //유저가 선택한 음악 번호 리스트
  const musicId = ref([])
  //유저 성별
  const gender = ref('none')

  const getMusicId = computed(() => musicId.value)
  const getGender = computed(() => gender.value)

  function addMusic(id) {
    musicId.value.push(id)
  }
  function removeMusic(id) {
    musicId.value = musicId.value.filter((item) => item !== id)
  }

  return {
    musicId,
    gender,
    getMusicId,
    getGender,
    addMusic,
    removeMusic,
  }
})
