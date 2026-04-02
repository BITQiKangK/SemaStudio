<template>
  <div class="panel">
    <label>上传数据文件（CSV / Parquet，可多选）：</label>
    <input type="file" multiple @change="onChoose" />
    <button :disabled="!files.length || uploading" @click="upload">
      {{ uploading ? '上传中...' : '上传并注册为视图' }}
    </button>

    <div v-if="uploadedViews.length" class="tips">
      已注册视图：<code>{{ uploadedViews.join(', ') }}</code>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiRequest } from '../utils/api.js'

const emit = defineEmits(['uploaded'])

const files = ref([])
const uploading = ref(false)
const uploadedViews = ref([])

function onChoose(e) {
  files.value = Array.from(e.target.files || [])
}

async function upload() {
  if (!files.value.length) return
  uploading.value = true
  uploadedViews.value = []
  try {
    const fd = new FormData()
    files.value.forEach(f => fd.append('files', f))
    const res = await apiRequest('/api/upload', { method: 'POST', body: fd })
    let data
    try { data = await res.json() } catch (_) { data = {} }
    if (!res.ok || !data.ok) {
      const msg = (data && data.error) || res.statusText || '上传失败'
      throw new Error(msg)
    }
    uploadedViews.value = data.views || []
    emit('uploaded', { files: data.files, views: data.views })
  } catch (e) {
    alert(e.message)
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.panel { margin-bottom: 16px; padding: 12px; border: 1px solid #eee; border-radius: 8px; }
.tips { margin-top: 6px; color:#555; }
</style>
