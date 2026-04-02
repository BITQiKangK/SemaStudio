<template>
  <div class="panel">
    <label>Connect to .duckdb file</label>

    <button class="btn-connect" @click="showModal = true">
      Connect
    </button>


    <!-- Upload Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
        <div class="modal">
          <div class="modal-header">
            <span class="modal-title">Upload .duckdb File</span>
            <button class="modal-close" @click="showModal = false">✕</button>
          </div>

          <div
            class="drop-zone"
            :class="{ 'drag-over': isDragging, 'has-file': selectedFile, 'uploading': uploading }"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDrop"
          >
            <template v-if="!uploading">
              <div class="drop-icon">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="24" cy="24" r="24" fill="rgba(24,119,242,0.1)"/>
                <line x1="24" y1="13" x2="24" y2="35" stroke="#1877f2" stroke-width="3" stroke-linecap="round"/>
                <line x1="13" y1="24" x2="35" y2="24" stroke="#1877f2" stroke-width="3" stroke-linecap="round"/>
              </svg>
            </div>
              <div class="drop-text" v-if="!selectedFile">
                <span class="drop-main">Dragging file here to connect</span>
                <span class="drop-sub">or</span>
              </div>
              <div class="drop-text" v-else>
                <span class="drop-main file-name">{{ selectedFile.name }}</span>
                <span class="drop-sub">{{ formatSize(selectedFile.size) }}</span>
              </div>
              <button class="btn-browse" @click="fileInput.click()">
                Browse Files
              </button>
              <input
                ref="fileInput"
                type="file"
                accept=".duckdb"
                style="display:none"
                @change="onFileChange"
              />
            </template>
            <template v-else>
              <div class="uploading-spinner"></div>
              <div class="uploading-text">Connecting...</div>
            </template>
          </div>

          <div class="modal-error" v-if="error">{{ error }}</div>

          <div class="modal-actions">
            <button class="btn-cancel" @click="showModal = false">Cancel</button>
            <button class="btn-upload" @click="upload" :disabled="!selectedFile || uploading">
              {{ uploading ? 'Connecting...' : 'Connect' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiRequest } from '../utils/api.js'

const emit = defineEmits(['connected'])
const current = ref('')
const showModal = ref(false)
const isDragging = ref(false)
const selectedFile = ref(null)
const uploading = ref(false)
const error = ref('')
const fileInput = ref(null)

async function refresh() {
  try {
    const res = await apiRequest('/api/connection')
    const data = await res.json()
    if (data?.ok) current.value = data.db_path || ''
  } catch (e) {
    console.error('Failed to refresh connection info:', e)
  }
}

function onDrop(e) {
  isDragging.value = false
  error.value = ''
  const file = e.dataTransfer.files[0]
  if (!file) return
  if (!file.name.endsWith('.duckdb')) {
    error.value = 'Only .duckdb files are supported'
    return
  }
  selectedFile.value = file
}

function onFileChange(e) {
  error.value = ''
  const file = e.target.files[0]
  if (!file) return
  selectedFile.value = file
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  error.value = ''
  try {
    const form = new FormData()
    form.append('file', selectedFile.value)
    const res = await apiRequest('/api/upload_db', { method: 'POST', body: form })
    const data = await res.json()
    if (!res.ok || !data.ok) throw new Error(data.error || 'Upload failed')
    current.value = data.db_path
    emit('connected', data.db_path)
    showModal.value = false
    selectedFile.value = null
  } catch (e) {
    error.value = e.message
  } finally {
    uploading.value = false
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

onMounted(refresh)
</script>

<style scoped>
.panel {
  background: var(--fb-card);
  border-radius: var(--fb-radius);
  box-shadow: var(--fb-shadow-sm);
  padding: 16px;
}

label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--fb-text);
  margin-bottom: 12px;
}

label::before {
  content: '🔗';
  font-size: 0.95rem;
}

.btn-connect {
  width: 100%;
  padding: 10px 16px;
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

.btn-connect:hover { background: var(--fb-blue-hover); }

.tips {
  margin-top: 10px;
  font-size: 0.8rem;
  color: var(--fb-text-2);
  line-height: 1.5;
  word-break: break-all;
}

.tips code {
  display: inline-block;
  max-width: 100%;
  background: var(--fb-bg);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.78rem;
  word-break: break-all;
  color: var(--fb-text);
  margin-top: 3px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(2px);
}

.modal {
  background: #fff;
  border-radius: 14px;
  padding: 24px;
  width: 460px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.modal-title {
  font-size: 1.067rem;
  font-weight: 700;
  color: #1d1d1f;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1rem;
  color: #86868b;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  line-height: 1;
  transition: background 0.15s;
}

.modal-close:hover { background: #f0f0f0; }

/* Drop zone */
.drop-zone {
  border: 2px dashed #90c0f8;
  border-radius: 12px;
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  transition: border-color 0.2s, background 0.2s;
  cursor: default;
  min-height: 180px;
  justify-content: center;
  background: rgba(24, 119, 242, 0.04);
}

.drop-zone.drag-over {
  border-color: var(--fb-blue, #1877f2);
  background: rgba(24, 119, 242, 0.04);
}

.drop-zone.has-file {
  border-color: #34c759;
  background: rgba(52, 199, 89, 0.04);
}

.drop-icon {
  line-height: 1;
}

.drop-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.drop-main {
  font-size: 0.933rem;
  font-weight: 600;
  color: #1d1d1f;
}

.drop-main.file-name {
  color: #34c759;
  word-break: break-all;
  text-align: center;
}

.drop-sub {
  font-size: 0.8rem;
  color: #86868b;
}

.btn-browse {
  margin-top: 4px;
  padding: 8px 20px;
  background: var(--fb-blue, #1877f2);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.867rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-browse:hover { background: var(--fb-blue-hover, #166fe5); }

.uploading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e0e0e0;
  border-top-color: var(--fb-blue, #1877f2);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.uploading-text {
  font-size: 0.933rem;
  color: #86868b;
  margin-top: 6px;
}

.modal-error {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fff0f0;
  border: 1px solid #ffdddd;
  border-radius: 8px;
  color: #c62828;
  font-size: 0.867rem;
  word-break: break-word;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-cancel {
  padding: 9px 20px;
  background: var(--fb-bg, #f0f2f5);
  color: var(--fb-text, #1d1d1f);
  border: none;
  border-radius: 8px;
  font-size: 0.867rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-cancel:hover { background: #e4e6ea; }

.btn-upload {
  padding: 9px 24px;
  background: var(--fb-blue, #1877f2);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.867rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-upload:hover:not(:disabled) { background: var(--fb-blue-hover, #166fe5); }

.btn-upload:disabled {
  background: #d1d1d6;
  cursor: not-allowed;
}
</style>
