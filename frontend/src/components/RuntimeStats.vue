<template>
  <div class="runtime-stats">
    <div class="stat-item">
      <span class="stat-label">⏱️ Elapsed Time</span>
      <span class="stat-value">{{ formatElapsedTime(elapsedMs) }}</span>
    </div>
    <div v-if="rowCount !== null && rowCount !== undefined" class="stat-item">
      <span class="stat-label">📊 Rows Returned</span>
      <span class="stat-value">{{ rowCount.toLocaleString() }}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">📥 Input Tokens</span>
      <span class="stat-value">{{ inputTokens }}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">📤 Output Tokens</span>
      <span class="stat-value">{{ outputTokens }}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">💲 Cost</span>
      <span class="stat-value">{{ costDisplay }}</span>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  elapsedMs: { type: Number, default: 0 },
  rowCount: { type: [Number, null], default: null },
  inputTokens: { type: String, default: '597K' },
  outputTokens: { type: String, default: '32K' },
  costDisplay: { type: String, default: '0.028 Dollar' }
})

function formatElapsedTime(ms) {
  if (ms === null || ms === undefined || ms === 0) {
    return '0ms'
  }
  
  let totalSeconds = Math.floor(ms / 1000)
  const remainingMs = ms % 1000
  
  if (totalSeconds === 0) {
    return `${ms}ms`
  }
  
  const hours = Math.floor(totalSeconds / 3600)
  totalSeconds %= 3600
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  
  const parts = []
  
  if (hours > 0) {
    parts.push(`${hours}h`)
  }
  if (minutes > 0) {
    parts.push(`${minutes}m`)
  }
  if (seconds > 0) {
    parts.push(`${seconds}s`)
  }
  
  if (remainingMs > 0 && hours === 0 && minutes === 0) {
    parts.push(`${remainingMs}ms`)
  }
  
  return parts.join(' ') || '0ms'
}
</script>

<style scoped>
.runtime-stats {
  display: flex;
  gap: 24px;
  align-items: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #86868b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #007aff;
}

@media (max-width: 600px) {
  .runtime-stats {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
