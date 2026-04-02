<template>
  <div class="panel">
    <div class="head">
      <span>Schemas & tables</span>
      <button @click="load" :disabled="loading">{{ loading ? '...' : 'Refresh' }}</button>
    </div>
    <div v-if="error" class="err">{{ error }}</div>
    <ul class="schemas">
      <li v-for="sch in schemas" :key="sch.name">
        <div class="schema">{{ sch.name }}</div>
        <ul class="tables">
          <li v-for="t in sch.tables" :key="sch.name + '.' + t.name" class="table-item">
            <div class="table-header" @click="toggleTable(sch.name, t.name)">
              <span class="tbl">{{ t.name }}</span>
              <span class="type">{{ t.type }}</span>
              <span class="toggle-icon" :class="{ 'expanded': isExpanded(sch.name, t.name) }">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M2.5 3.5L5 6L7.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </div>
            <div v-if="isExpanded(sch.name, t.name)" class="table-columns">
              <div v-if="getColumnsLoading(sch.name, t.name)" class="loading">加载中...</div>
              <div v-else-if="getColumnsError(sch.name, t.name)" class="column-error">{{ getColumnsError(sch.name, t.name) }}</div>
              <ul v-else-if="getColumns(sch.name, t.name).length > 0" class="columns-list">
                <li v-for="col in getColumns(sch.name, t.name)" :key="col.name" class="column-item">
                  <span class="column-name">{{ col.name }}</span>
                  <span class="column-type">{{ col.type }}</span>
                </li>
              </ul>
              <div v-else class="no-columns">无列信息</div>
            </div>
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { apiRequest } from '../utils/api.js'

const props = defineProps({ refreshKey: { type: Number, default: 0 } })

const schemas = ref([])
const loading = ref(false)
const error = ref('')

const expandedTables = ref(new Set())
const tableColumns = ref(new Map())

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await apiRequest('/api/catalog')
    const data = await res.json()
    if (!res.ok || !data.ok) throw new Error(data.error || 'Load failed')
    schemas.value = data.schemas || []
    expandedTables.value.clear()
    tableColumns.value.clear()
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function getTableKey(schema, table) {
  return `${schema}.${table}`
}

function isExpanded(schema, table) {
  return expandedTables.value.has(getTableKey(schema, table))
}

function getColumns(schema, table) {
  const key = getTableKey(schema, table)
  const data = tableColumns.value.get(key)
  return data?.columns || []
}

function getColumnsLoading(schema, table) {
  const key = getTableKey(schema, table)
  const data = tableColumns.value.get(key)
  return data?.loading || false
}

function getColumnsError(schema, table) {
  const key = getTableKey(schema, table)
  const data = tableColumns.value.get(key)
  return data?.error || null
}

async function toggleTable(schema, table) {
  const key = getTableKey(schema, table)
  
  if (expandedTables.value.has(key)) {
    expandedTables.value.delete(key)
  } else {
    expandedTables.value.add(key)
    
    if (!tableColumns.value.has(key)) {
      await loadTableColumns(schema, table)
    }
  }
}

async function loadTableColumns(schema, table) {
  const key = getTableKey(schema, table)
  
  tableColumns.value.set(key, {
    columns: [],
    loading: true,
    error: null
  })
  
  try {
    const res = await apiRequest(`/api/table/columns?schema=${encodeURIComponent(schema)}&table=${encodeURIComponent(table)}`)
    const data = await res.json()
    
    if (!res.ok || !data.ok) {
      throw new Error(data.error || '加载列信息失败')
    }
    
    tableColumns.value.set(key, {
      columns: data.columns || [],
      loading: false,
      error: null
    })
  } catch (e) {
    tableColumns.value.set(key, {
      columns: [],
      loading: false,
      error: e.message || String(e)
    })
  }
}

onMounted(load)
watch(() => props.refreshKey, () => load())
</script>

<style scoped>
.panel {
  background: var(--fb-card);
  border-radius: var(--fb-radius);
  box-shadow: var(--fb-shadow-sm);
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.head span {
  font-size: 1rem;
  font-weight: 700;
  color: var(--fb-text);
}

button {
  padding: 6px 14px;
  background: var(--fb-hover);
  color: var(--fb-text);
  border: none;
  border-radius: var(--fb-radius);
  font-size: 0.8rem;
  font-family: var(--fb-font);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

button:hover:not(:disabled) { background: var(--fb-divider); }

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.schemas {
  list-style: none;
  padding: 0;
  margin: 0;
}

.schema {
  font-weight: 700;
  font-size: 0.8rem;
  color: var(--fb-text-2);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-top: 14px;
  margin-bottom: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--fb-divider);
}

.schema:first-child { margin-top: 0; }

.tables {
  list-style: none;
  padding-left: 0;
  margin: 4px 0 0 0;
}

.table-item { margin: 1px 0; }

.table-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 7px 10px;
  border-radius: var(--fb-radius);
  transition: background 0.15s;
}

.table-header:hover { background: var(--fb-hover); }
.table-header:active { background: var(--fb-divider); }

.tbl {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.867rem;
  color: var(--fb-text);
  font-weight: 500;
  flex: 1;
}

.type {
  color: var(--fb-text-3);
  margin-left: 8px;
  font-size: 0.733rem;
  background: var(--fb-bg);
  padding: 1px 6px;
  border-radius: 10px;
}

.toggle-icon {
  color: var(--fb-text-3);
  transition: transform 0.2s;
  margin-left: 6px;
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.toggle-icon svg { width: 100%; height: 100%; }
.toggle-icon.expanded { transform: rotate(180deg); }

.table-columns {
  margin: 3px 0 3px 20px;
  padding-left: 12px;
  border-left: 2px solid var(--fb-blue-light);
  animation: slideDown 0.15s ease;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.columns-list {
  list-style: none;
  padding: 0;
  margin: 4px 0;
}

.column-item {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  font-size: 0.8rem;
  border-radius: 4px;
  transition: background 0.12s;
}

.column-item:hover { background: var(--fb-bg); }

.column-name {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  color: var(--fb-text);
  min-width: 100px;
  font-weight: 500;
}

.column-type {
  color: var(--fb-text-3);
  margin-left: 10px;
  font-size: 0.733rem;
}

.loading {
  color: var(--fb-text-3);
  font-size: 0.8rem;
  padding: 8px;
  font-style: italic;
}

.column-error {
  color: #FA3E3E;
  font-size: 0.8rem;
  padding: 8px;
}

.no-columns {
  color: var(--fb-text-3);
  font-size: 0.8rem;
  padding: 8px;
  font-style: italic;
  padding-left: 8px;
}

.err {
  color: #C62828;
  background: #FFF0F0;
  padding: 10px 12px;
  border-radius: var(--fb-radius);
  font-size: 0.8rem;
  margin-bottom: 10px;
  border-left: 3px solid #FA3E3E;
}
</style>

