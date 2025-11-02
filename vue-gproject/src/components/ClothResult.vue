<script setup>
import ItemCloth from './items/ItemCloth.vue'
import { defineProps } from 'vue'
import { useUpdateDb } from '@/composables/updateDb'

const db = useUpdateDb()

const props = defineProps({
  number: {
    typeof: Number,
    default: 0,
  },
  category: {
    typeof: String,
    default: 'none',
  },
})

function onClick() {
  // db.saveToDb()
  db.addToDb('updateTest2')
}
</script>

<template>
  <div class="cloth-result">
    <h2 class="cloth-result-title">추천 스타일 {{ props.number }}: {{ props.category }}</h2>
    <section class="cloth-result-inner">
      <template v-for="item in 10" :key="item">
        <ItemCloth @click-link="onClick" />
      </template>
    </section>
  </div>
</template>

<style scoped>
.cloth-result {
  display: flex;
  flex-direction: column;
}
.cloth-result-title {
  color: var(--color-text);
  font-family: 'BMHanna';
}
.cloth-result-inner {
  overflow-x: auto;
  display: flex;
  gap: 16px;
  -ms-overflow-style: none;
}
.cloth-result-inner::-webkit-scrollbar {
  display: none;
}
</style>
