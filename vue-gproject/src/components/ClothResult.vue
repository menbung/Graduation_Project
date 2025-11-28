<script setup>
import ItemCloth from './items/ItemCloth.vue'
import { computed, defineProps } from 'vue'
import { useUpdateDb } from '@/composables/updateDb'
import { useDataStore } from '@/stores/data'
import { storeToRefs } from 'pinia'

const props = defineProps({
  number: {
    type: Number,
    default: 0,
  },
  category: {
    type: String,
    default: 'none',
  },
})

const db = useUpdateDb()
const { clothData } = storeToRefs(useDataStore())
const clothList = computed(() => {
  const list = clothData.value?.[props.number]
  return Array.isArray(list) ? list : []
})

function onClick(id) {
  const clothText = `${props.category}/${id}`
  db.addToDb(clothText)
}
</script>

<template>
  <div class="cloth-result">
    <h2 class="cloth-result-title">추천 스타일 {{ props.number + 1 }}: {{ props.category }}</h2>
    <section class="cloth-result-inner">
      <template v-for="(cloth, index) in clothList" :key="index">
        <ItemCloth
          :id="cloth.img_id"
          :img="cloth.img_url"
          :link="cloth.web_url"
          @click-link="onClick"
        />
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
