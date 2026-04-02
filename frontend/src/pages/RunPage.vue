<template>
  <section class="layout">
    <aside class="left-sidebar">
      <ConnectionPanel @connected="onConnected" />
      <SchemaBrowser :refresh-key="refreshKey" />
    </aside>
    <main class="main-content">
      <div class="query-section">
        <div class="query-config-row">
          <QueryInput
            v-model="sql"
            :loading="runLoading"
            @run="runQuery"
          />
          <ConfigOptions
            v-model:editableConfig="editableConfig"
            v-model:customConfig="customConfig"
            @explain="goExplain(sql)"
            @profile="goProfiling(sql)"
          />
        </div>
      </div>

      <div class="error-card" v-if="error">
        <div class="error-icon">⚠</div>
        <div class="error-content">
          <strong>Error</strong>
          <p>{{ error }}</p>
        </div>
      </div>

      <div v-for="(item, idx) in runs" :key="idx" class="result-card">
        <template v-if="item.error">
          <div class="error-state">
            <div class="error-icon">✕</div>
            <div class="error-message">{{ item.error }}</div>
          </div>
        </template>
        <template v-else>
          <div class="result-header">
            <div class="result-stats">
              <RuntimeStats :elapsedMs="item.result.elapsed_ms" :rowCount="item.result.row_count" />
            </div>
          </div>
          <div class="result-table-container">
          <ResultTable :columns="item.result.columns" :rows="item.result.rows" />
          </div>
        </template>
      </div>
    </main>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import QueryInput from '../components/QueryInput.vue'
import ResultTable from '../components/ResultTable.vue'
import RuntimeStats from '../components/RuntimeStats.vue'
import ConnectionPanel from '../components/ConnectionPanel.vue'
import SchemaBrowser from '../components/SchemaBrowser.vue'
import ConfigOptions from '../components/ConfigOptions.vue'
import { apiRequest } from '../utils/api.js'

const router = useRouter()
const sql = ref('')
const runs = ref([])
const refreshKey = ref(0)
const error = ref('')
const runLoading = ref(false)
const customConfig = ref('')
const editableConfig = ref({
  llm_model: '',
  llm_url: '',
  enable_semantic_filter_multiplexer: 'true',
  semantic_filter_accuracy_threshold: 0.9,
  semantic_filter_latency_first: 'false',
  semantic_filter_batch_size: 4,
  semantic_batch_size: 4,
  enable_partial_deduction: 'true',
  enable_nl_expression_compression: 'true'
})

function onConnected() { refreshKey.value++ }

onMounted(async () => {
  try {
    const res = await apiRequest('/api/config')
    const data = await res.json()
    if (res.ok && data.ok) {
      editableConfig.value = {
        llm_model: data.config.llm_model ?? '',
        llm_url: data.config.llm_url ?? '',
        enable_semantic_filter_multiplexer: String(data.config.enable_semantic_filter_multiplexer ?? 'true'),
        semantic_filter_accuracy_threshold: data.config.semantic_filter_accuracy_threshold ?? 0.9,
        semantic_filter_latency_first: String(data.config.semantic_filter_latency_first ?? 'false'),
        semantic_filter_batch_size: data.config.semantic_filter_batch_size ?? 4,
        semantic_batch_size: data.config.semantic_batch_size ?? 4,
        enable_partial_deduction: String(data.config.enable_partial_deduction ?? 'true'),
        enable_nl_expression_compression: String(data.config.enable_nl_expression_compression ?? 'true')
      }
    }
  } catch (e) {
    console.error('Failed to load config:', e)
  }
})

async function runQuery() {
  error.value = ''
  runLoading.value = true
  try {
    const res = await apiRequest('/api/run', {
      method: 'POST',
      body: JSON.stringify({ query: sql.value })
    })
    let data
    try { data = await res.json() } catch (_) { data = {} }
    if (!res.ok || !data.ok) {
      const msg = (data && data.error) || res.statusText || 'Query execution failed'
      throw new Error(msg)
    }
    runs.value.unshift({ sql: sql.value, result: data, error: '' })
  } catch (e) {
    runs.value.unshift({ sql: sql.value, result: null, error: e.message || String(e) })
  } finally {
    runLoading.value = false
  }
}

function goExplain(query) {
  router.push({ path: '/plan', query: { q: query, mode: 'explain' } })
}

function goProfiling(query) {
  router.push({ path: '/plan', query: { q: query, mode: 'profiling' } })
}
</script>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  min-height: calc(100vh - var(--fb-topbar-h));
  background: var(--fb-bg);
}

.left-sidebar {
  background: var(--fb-bg);
  padding: 16px 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: var(--fb-topbar-h);
  height: calc(100vh - var(--fb-topbar-h));
}

.main-content {
  padding: 0;
  overflow-y: auto;
  background: var(--fb-bg);
  display: flex;
  flex-direction: column;
}

.query-section {
  padding: 16px 16px 0 16px;
}

.query-config-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: stretch;
}

.error-card {
  background: #FFF0F0;
  border-left: 4px solid #FA3E3E;
  border-radius: var(--fb-radius);
  padding: 12px 16px;
  margin: 12px 16px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #C62828;
  box-shadow: var(--fb-shadow-sm);
}

.error-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.error-content strong {
  display: block;
  font-size: 0.867rem;
  font-weight: 700;
  margin-bottom: 3px;
}

.error-content p {
  font-size: 0.867rem;
  color: #555;
  margin: 0;
}

.result-card {
  background: var(--fb-card);
  border-radius: var(--fb-radius);
  margin: 12px 16px;
  box-shadow: var(--fb-shadow-sm);
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--fb-divider);
}

.result-stats { flex: 1; }


.result-table-container {
  padding: 0;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: #FA3E3E;
}

.error-state .error-icon { font-size: 42px; margin-bottom: 12px; }

.error-message {
  font-size: 0.867rem;
  color: var(--fb-text-2);
  text-align: center;
}

@media (max-width: 1100px) {
  .layout { grid-template-columns: 260px 1fr; }
  .query-config-row { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .left-sidebar {
    position: static;
    height: auto;
    padding: 12px;
    flex-direction: row;
    flex-wrap: wrap;
    overflow-y: visible;
  }
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .result-actions { width: 100%; }
  .action-btn { flex: 1; justify-content: center; }
}
</style>
