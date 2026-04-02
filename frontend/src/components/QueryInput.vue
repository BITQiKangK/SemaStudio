<template>
  <div class="query-input-card">
    <div class="query-header">
      <label class="query-label">SQL Query</label>
      <button
        type="button"
        class="run-button"
        :disabled="loading"
        :aria-busy="loading"
        :aria-label="loading ? 'Run, loading' : 'Run'"
        @click="$emit('run')"
      >
        <template v-if="loading">
          <span class="run-button-wait">
            <span class="run-button-wait-ring"></span>
            Run
          </span>
        </template>
        <template v-else>
          <span class="button-icon">▶</span>
          Run
        </template>
      </button>
    </div>
    <textarea 
      v-model="model" 
      rows="8" 
      class="sql-editor" 
      placeholder="Enter your SQL query here..."
      @keydown.ctrl.enter="$emit('run')"
      @keydown.meta.enter="$emit('run')"
    ></textarea>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'run'])

const model = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v)
})
</script>

<style scoped>
.query-input-card {
  background: var(--fb-card);
  border-radius: var(--fb-radius);
  box-shadow: var(--fb-shadow-sm);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

.query-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--fb-divider);
}

.query-label {
  font-size: 1.067rem;
  font-weight: 700;
  color: var(--fb-text);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.query-label::before {
  font-size: 1rem;
}

.run-button {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  padding: 8px 20px;
  background: var(--fb-blue);
  color: #fff;
  border: none;
  border-radius: var(--fb-radius);
  font-size: 0.933rem;
  font-family: var(--fb-font);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.run-button:hover:not(:disabled) { background: var(--fb-blue-hover); }

.run-button:disabled {
  opacity: 0.92;
  justify-content: center;
}

.button-icon { font-size: 0.75rem; }

.run-button-wait {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.run-button-wait-ring {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: run-input-spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes run-input-spin {
  to { transform: rotate(360deg); }
}

.sql-editor {
  width: 100%;
  padding: 14px 16px;
  border: none;
  border-radius: 0;
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.867rem;
  line-height: 1.65;
  color: var(--fb-text);
  background: var(--fb-bg);
  resize: none;
  box-sizing: border-box;
  min-height: 130px;
  flex: 1;
  outline: none;
  transition: background 0.15s;
}


.sql-editor::placeholder {
  color: var(--fb-text-3);
}
</style>
