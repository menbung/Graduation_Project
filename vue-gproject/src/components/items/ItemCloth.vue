<script setup>
const emit = defineEmits('click-link')

function onClick() {
  emit('click-link')
}
</script>

<template>
  <article class="item-cloth">
    <div class="result-img" aria-hidden="true"></div>
    <h3 class="card-title">Product1</h3>
    <button class="link-btn" type="button" @click="onClick">
      <span class="btn-label">바로가기</span>
      <span class="material-symbols-outlined">arrow_outward</span>
    </button>
  </article>
</template>

<style scoped>
.item-cloth {
  flex: none;
  width: 120px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.result-img {
  width: 100%;
  aspect-ratio: 3 / 5;
  background: #e8e8e8;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background-size: cover;
  background-position: center;
}
.card-title {
  font-family: 'BMHanna';
  font-size: 16px;
  font-weight: 600;
}
.link-btn {
  padding: 8px 16px;
  background: var(--brand-color);
  border: 1px solid #717171;
  border-radius: 16px;
  cursor: pointer;
  display: flex;
  gap: 2px;
  align-items: center;
  justify-content: center;
}
.btn-label {
  font-family: 'BMHanna';
  font-weight: 700;
}
.material-symbols-outlined {
  font-size: 16px;
  font-variation-settings: 'FILL' 0 'wght' 400 'GRAD' 0 'opsz' 24;
}
</style>
