<script setup>
import { ref } from 'vue'

const isOnClick = ref(false)
const emit = defineEmits(['add-count', 'sub-count'])
const props = defineProps({
  count: {
    typeof: Number,
    default: 0,
  },
  id: {
    typeof: Number,
    default: 0,
  },
})

function onClick() {
  if (isOnClick.value) {
    isOnClick.value = false
    emit('sub-count', props.id)
  } else if (props.count < 3) {
    isOnClick.value = true
    emit('add-count', props.id)
  }
}
</script>

<template>
  <article class="item-music" :class="{ check: isOnClick }" @click="onClick">
    <div class="music-img" aria-hidden="true"></div>
    <div class="music-singer">Singer 1</div>
    <div class="music-title">Music 1</div>
  </article>
</template>

<style scoped>
.item-music {
  flex: none;
  width: 100px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.check {
  background-color: var(--brand-color);
  color: #000000;
}
.music-img {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #e8e8e8;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background-size: cover;
  background-position: center;
}
.music-singer,
.music-title {
  font-family: 'BMHanna';
  font-size: 16px;
  font-weight: 600;
}
</style>
