<template>
  <div class="table-wrap">
    <table v-if="columns?.length">
      <thead>
        <tr>
          <th v-for="(c, i) in columns" :key="i">{{ c }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, ri) in rows" :key="ri">
          <td v-for="(c, ci) in columns" :key="ci">
            {{ displayCell(r[ci]) }}
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No results</div>
  </div>
</template>

<script setup>
const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] }
})

function displayCell(v) {
  if (v === null || v === undefined) return ''
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}
</script>

<style scoped>
.table-wrap {
  overflow: auto;
  max-height: 298px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background: #ffffff;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

th {
  background: #fafafa;
  color: #1d1d1f;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 0.5px;
  padding: 12px 16px;
  text-align: left;
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 2px solid #e8e8e8;
}

td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e8e8e8;
  color: #1d1d1f;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background-color: #f5f5f7;
}

tbody tr:last-child td {
  border-bottom: none;
}

.empty {
  padding: 48px 24px;
  text-align: center;
  color: #86868b;
  font-size: 14px;
}
</style>
