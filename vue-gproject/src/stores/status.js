import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useStatusStore = defineStore('status', () => {
  // 유저 정보
  const user = ref(null)
  //유저가 선택한 음악 번호 리스트
  const musicId = ref([])
  //유저의 스타일 태그 리스트
  const styleTag = ref([])
  //유저 성별
  const gender = ref('none')

  const getMusicId = computed(() => musicId.value)
  const getGender = computed(() => gender.value)
  const getStyleTag = computed(() => styleTag.value)

  function updateUser(id) {
    user.value = id
  }
  function deleteUser() {
    user.value = null
    musicId.value = []
    styleTag.value = []
    gender.value = 'none'
  }
  function addMusic(id) {
    musicId.value.push(id)
  }
  function removeMusic(id) {
    musicId.value = musicId.value.filter((item) => item !== id)
  }
  function addStyleTag(tag) {
    styleTag.value.push(tag)
  }
  function inputGender(gend) {
    gender.value = gend
  }

  return {
    user,
    musicId,
    styleTag,
    gender,
    getMusicId,
    getGender,
    getStyleTag,
    updateUser,
    deleteUser,
    addMusic,
    removeMusic,
    inputGender,
    addStyleTag,
  }
})
