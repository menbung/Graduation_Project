<template>
  <div class="loading-overlay">
    <div class="loading-container">
      <div class="spinner"></div>
      <p class="loading-text">
        <slot name="text"></slot>
      </p>
    </div>
  </div>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  top: var(--header-height);
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(0, 242, 255, 0.2);
  border-top: 4px solid var(--brand-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  font-family: 'BMHanna';
  font-size: 18px;
  margin: 0;
  color: var(--color-text);
  font-weight: bold;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
