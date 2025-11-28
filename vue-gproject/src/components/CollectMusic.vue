<script setup>
import ItemMusic from './items/ItemMusic.vue'
import { ref } from 'vue'
import { useStatusStore } from '@/stores/status'
import { useDataStore } from '@/stores/data'
import { storeToRefs } from 'pinia'

const status = useStatusStore()
const { musicData } = storeToRefs(useDataStore())
const emit = defineEmits(['call-api'])

const musicCount = ref(0)

// const openPopup = () => {
//   emit('open-popup')
// }

const callApi = () => {
  emit('call-api')
}

function addCount(id) {
  musicCount.value++
  status.addMusic(id)
}
function subCount(id) {
  musicCount.value--
  status.removeMusic(id)
}
</script>

<template>
  <div class="title">선호하는 음악을 선택해 주세요!<br />선택된 음악 ({{ musicCount }}/3)</div>
  <div class="music-bundle">
    <template v-for="(music, index) in musicData" :key="index">
      <ItemMusic
        :count="musicCount"
        :id="music.number"
        :imageUrl="music.url || 'none'"
        @add-count="addCount"
        @sub-count="subCount"
      >
        <template #singer>{{ music.singer }}</template>
        <template #title>{{ music.title }}</template>
      </ItemMusic>
    </template>
  </div>
  <div class="button-container">
    <button class="confirm-btn" @click="callApi" :disabled="musicCount !== 3">선택 완료</button>
  </div>
</template>

<style scoped>
.title {
  text-align: center;
  font-family: 'Ohsquare';
  font-size: 30px;
  padding-bottom: 10px;
}
.music-bundle {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}
.button-container {
  display: flex;
  justify-content: center;
  padding-top: 10px;
}
.confirm-btn {
  padding: 12px 24px;
  background: var(--brand-color);
  border: 1px solid #717171;
  border-radius: 8px;
  cursor: pointer;
  font-family: 'BMHanna';
  font-size: 20px;
  font-weight: 700;
}
.confirm-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}
</style>
