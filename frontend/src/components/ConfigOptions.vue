<template>
  <section class="content-section top-row-item">
    <h2 class="section-title">Configuration Options</h2>

    <div class="config-tabs">
      <button
        class="config-tab"
        :class="{ active: activeConfigTab === 'model' }"
        @click="activeConfigTab = 'model'"
      >
        Model & API
      </button>
      <button
        class="config-tab"
        :class="{ active: activeConfigTab === 'aqe' }"
        @click="activeConfigTab = 'aqe'"
      >
        AQE Settings
      </button>
      <button
        class="config-tab"
        :class="{ active: activeConfigTab === 'batch' }"
        @click="activeConfigTab = 'batch'"
      >
        Batch
      </button>
      <button
        class="config-tab"
        :class="{ active: activeConfigTab === 'deduction' }"
        @click="activeConfigTab = 'deduction'"
      >
        Optimizer
      </button>
      <button
        class="config-tab"
        :class="{ active: activeConfigTab === 'set' }"
        @click="activeConfigTab = 'set'"
      >
        SET Commands
      </button>
    </div>

    <div class="config-tab-content">
      <div v-if="activeConfigTab === 'model'" class="config-tab-panel">
        <p class="config-tab-panel-hint">Run LLM</p>
        <div class="config-card">
          <div class="config-item">
            <span class="config-label">URL</span>
            <input
              class="config-input config-input--truncate"
              :value="editableConfig.llm_url"
              placeholder="API URL"
              :title="editableConfig.llm_url"
              @input="updateConfig('llm_url', $event.target.value)"
            />
          </div>
          <div class="config-item">
            <span class="config-label">Model</span>
            <input
              class="config-input config-input--truncate"
              :value="editableConfig.llm_model"
              placeholder="model name"
              :title="editableConfig.llm_model"
              @input="updateConfig('llm_model', $event.target.value)"
            />
          </div>
        </div>

        <template v-for="block in referenceLlmBlocks" :key="block.key">
          <p class="config-tab-panel-hint config-tab-panel-hint--stacked">{{ block.title }}</p>
          <div class="config-card">
            <div class="config-item">
              <span class="config-label">URL</span>
              <input
                class="config-input config-input--truncate"
                readonly
                tabindex="-1"
                :value="block.url"
                :title="block.url"
              />
            </div>
            <div class="config-item">
              <span class="config-label">Model</span>
              <input
                class="config-input config-input--truncate"
                readonly
                tabindex="-1"
                :value="block.model"
                :title="block.model"
              />
            </div>
          </div>
        </template>
      </div>

      <div v-if="activeConfigTab === 'aqe'" class="config-tab-panel">
        <div class="config-card">
          <div class="config-item">
            <span class="config-label">AQE</span>
            <select class="config-select" :value="editableConfig.enable_semantic_filter_multiplexer" @change="updateConfig('enable_semantic_filter_multiplexer', $event.target.value)">
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div class="config-item">
            <span class="config-label">Accuracy Threshold</span>
            <input class="config-input config-input--sm" type="number" step="0.01" min="0" max="1" :value="editableConfig.semantic_filter_accuracy_threshold" @input="updateConfig('semantic_filter_accuracy_threshold', $event.target.value)" />
          </div>
          <div class="config-item">
            <span class="config-label">Latency First</span>
            <select class="config-select" :value="editableConfig.semantic_filter_latency_first" @change="updateConfig('semantic_filter_latency_first', $event.target.value)">
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div class="config-item">
            <span class="config-label">Filter Batch</span>
            <input class="config-input config-input--sm" type="number" min="1" :value="editableConfig.semantic_filter_batch_size" @input="updateConfig('semantic_filter_batch_size', $event.target.value)" />
          </div>
        </div>
      </div>

      <div v-if="activeConfigTab === 'batch'" class="config-tab-panel">
        <div class="config-card">
          <div class="config-item">
            <span class="config-label">Batch Size</span>
            <input class="config-input config-input--sm" type="number" min="1" :value="editableConfig.semantic_batch_size" @input="updateConfig('semantic_batch_size', $event.target.value)" />
          </div>
        </div>
      </div>

      <div v-if="activeConfigTab === 'deduction'" class="config-tab-panel">
        <div class="config-card">
          <div class="config-item">
            <span class="config-label">Enable Partial Deduction</span>
            <select class="config-select" :value="editableConfig.enable_partial_deduction" @change="updateConfig('enable_partial_deduction', $event.target.value)">
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div class="config-item">
            <span class="config-label">Enable NL Expression Compression</span>
            <select class="config-select" :value="editableConfig.enable_nl_expression_compression" @change="updateConfig('enable_nl_expression_compression', $event.target.value)">
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
        </div>
      </div>

      <div v-if="activeConfigTab === 'set'" class="config-tab-panel">
        <div class="set-commands-container">
          <textarea
            :value="customConfig"
            @input="$emit('update:customConfig', $event.target.value)"
            class="set-commands-textarea"
            placeholder="SET enable_logging = true;&#10;SET semantic_batch_size = 8;&#10;SET enable_semantic_filter_multiplexer = true;"
            rows="4"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="action-buttons">
      <button
        type="button"
        class="btn btn-outline"
        :disabled="loadingExplain || loadingProfile"
        :aria-busy="loadingExplain"
        :aria-label="loadingExplain ? 'Explain, loading' : 'Explain'"
        @click="$emit('explain')"
      >
        <template v-if="loadingExplain">
          <span class="btn-wait">
            <span class="btn-wait-ring btn-wait-ring--outline"></span>
            Explain
          </span>
        </template>
        <template v-else>Explain</template>
      </button>
      <button
        type="button"
        class="btn btn-primary"
        :disabled="loadingExplain || loadingProfile"
        :aria-busy="loadingProfile"
        :aria-label="loadingProfile ? 'Profile, loading' : 'Profile'"
        @click="$emit('profile')"
      >
        <template v-if="loadingProfile">
          <span class="btn-wait">
            <span class="btn-wait-ring btn-wait-ring--primary"></span>
            Profile
          </span>
        </template>
        <template v-else>Profile</template>
      </button>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  editableConfig: {
    type: Object,
    required: true
  },
  customConfig: {
    type: String,
    default: ''
  },
  loadingExplain: { type: Boolean, default: false },
  loadingProfile: { type: Boolean, default: false }
})

const emit = defineEmits(['update:editableConfig', 'update:customConfig', 'explain', 'profile'])

const activeConfigTab = ref('model')

const REFERENCE_LLM_URL = 'https://openrouter.ai/api/v1/chat/completions'
const referenceLlmBlocks = [
  { key: 'deduction', title: 'Deduction LLM', url: REFERENCE_LLM_URL, model: 'openai/gpt-5.4' },
  { key: 'reflection', title: 'Reflection LLM', url: REFERENCE_LLM_URL, model: 'qwen/qwen3-max' },
  { key: 'compression', title: 'Compression LLM', url: REFERENCE_LLM_URL, model: 'openai/gpt-5.4' },
  { key: 'verify', title: 'Verify LLM', url: REFERENCE_LLM_URL, model: 'qwen/qwen3-max' }
]

function updateConfig(key, value) {
  emit('update:editableConfig', { ...props.editableConfig, [key]: value })
}
</script>

<style scoped>
.content-section {
  background: var(--fb-card);
  border-radius: var(--fb-radius);
  padding: 16px 20px 20px;
  margin-bottom: 12px;
  box-shadow: var(--fb-shadow-sm);
}

.top-row-item {
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
}

.section-title {
  margin: 0 0 14px 0;
  font-size: 1.067rem;
  font-weight: 700;
  color: var(--fb-text);
  flex-shrink: 0;
}

.config-tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--fb-divider);
}

.config-tab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--fb-text-2);
  font-size: 0.867rem;
  font-family: var(--fb-font);
  font-weight: 600;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: color 0.15s, border-color 0.15s;
  outline: none;
  position: relative;
  top: 1px;
}

.config-tab:hover { color: var(--fb-text); }

.config-tab.active {
  color: var(--fb-blue);
  border-bottom-color: var(--fb-blue);
}

.config-tab-content {
  height: 180px;
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.config-tab-panel {
  animation: fadeIn 0.15s ease;
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.config-tab-panel::-webkit-scrollbar {
  display: none;
}

.config-tab-panel-hint {
  margin: 0 0 8px 0;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--fb-text-3);
}

.config-tab-panel-hint--stacked {
  margin-top: 14px;
}


.config-input--truncate {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-input[readonly] {
  cursor: default;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(3px); }
  to   { opacity: 1; transform: translateY(0); }
}

.config-card {
  background: var(--fb-bg);
  border: 1px solid var(--fb-divider);
  border-radius: var(--fb-radius);
  padding: 14px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid var(--fb-divider);
}

.config-item:last-child { border-bottom: none; }

.config-label {
  font-size: 0.867rem;
  color: var(--fb-text-2);
}

.config-input {
  font-size: 0.867rem;
  font-weight: 600;
  color: var(--fb-blue);
  max-width: 260px;
  width: 100%;
  border: none;
  border-bottom: 1.5px solid transparent;
  background: transparent;
  outline: none;
  padding: 2px 4px;
  border-radius: 4px;
  transition: border-color 0.2s, background 0.2s;
  text-align: right;
}

.config-input:hover,
.config-input:focus {
  background: transparent;
  border-bottom-color: transparent;
}

.config-input--sm {
  max-width: 90px;
}

.config-select {
  font-size: 0.867rem;
  font-weight: 600;
  color: var(--fb-blue);
  border: none;
  border-bottom: 1.5px solid transparent;
  background: transparent;
  outline: none;
  padding: 2px 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  text-align: right;
}

.config-select:hover,
.config-select:focus {
  background: transparent;
  border-bottom-color: transparent;
}

.set-commands-container { display: flex; flex-direction: column; }

.set-commands-textarea {
  width: 100%;
  min-height: 110px;
  max-height: 110px;
  font-size: 0.867rem;
  line-height: 1.6;
  color: var(--fb-text);
  background: var(--fb-bg);
  border: 1.5px solid var(--fb-border);
  border-radius: var(--fb-radius);
  padding: 10px 14px;
  resize: none;
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow-y: auto;
  font-family: var(--fb-font);
}

.set-commands-textarea:focus {
  background: #fff;
  border-color: var(--fb-blue);
  box-shadow: 0 0 0 2px rgba(24, 119, 242, 0.2);
}

.set-commands-textarea::placeholder { color: var(--fb-text-3); }

.action-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-start;
  margin-top: auto;
  padding-top: 14px;
}

.action-buttons .btn {
  box-sizing: border-box;
  min-width: 132px;
  min-height: 38px;
  justify-content: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  padding: 9px 22px;
  border-radius: var(--fb-radius);
  font-size: 0.933rem;
  font-family: var(--fb-font);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  border: none;
  white-space: nowrap;
}

.btn-outline {
  background: var(--fb-blue-light);
  color: var(--fb-blue);
}

.btn-primary { background: var(--fb-blue); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--fb-blue-hover); }

.btn-outline:disabled,
.btn-primary:disabled {
  opacity: 0.92;
}

.btn-outline:hover:not(:disabled) { background: #d0e8ff; }

.btn-wait {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-wait-ring {
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-radius: 50%;
  animation: config-btn-spin 0.7s linear infinite;
  flex-shrink: 0;
}

.btn-wait-ring--outline {
  border-color: rgba(24, 119, 242, 0.35);
  border-top-color: var(--fb-blue);
}

.btn-wait-ring--primary {
  border-color: rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
}

@keyframes config-btn-spin {
  to { transform: rotate(360deg); }
}
</style>
