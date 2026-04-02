<template>
  <section
    v-if="necInfo"
    class="content-section prompt-info-section"
  >
    <h2 class="section-title">Expression Compression</h2>

    <div class="pipeline-row">
      <!-- Block 1 -->
      <div class="pipeline-block">
        <div class="pipeline-block-header">
          <span class="pipeline-block-title">NEC Input Expressions</span>
          <span class="prompt-block-badge">{{ necInfo.inputs.length }}</span>
        </div>
        <div class="pipeline-block-body nl-scroll">
          <ul class="pipeline-expr-list">
            <li
              v-for="(expr, i) in necInfo.inputs"
              :key="i"
              class="pipeline-expr-item nl-expr"
              :title="expr"
            >{{ expr }}</li>
          </ul>
        </div>
      </div>

      <div class="pipeline-arrow">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </div>

      <!-- Block 2: Compression LLM -->
      <div class="pipeline-block">
        <div class="pipeline-block-header">
          <span class="pipeline-block-title">Compression LLM</span>
        </div>
        <div class="pipeline-block-body">
          <div class="pipeline-model-inline" :title="MODEL_ID">
            <span class="pipeline-sub-label">model:</span>
            <span class="pipeline-model-inline-value">openai/gpt-5.4</span>
          </div>
          <div class="pipeline-sub-label">Input Prompt</div>
          <pre class="pipeline-prompt-text">{{ NLEC_COMPRESS_SYSTEM_PROMPT }}</pre>
          <div class="pipeline-sub-label pipeline-sub-label--output">Output</div>
          <ul class="pipeline-expr-list" v-if="necInfo.compressed.length">
            <li
              v-for="(expr, i) in necInfo.compressed"
              :key="i"
              class="pipeline-expr-item nl-expr"
              :title="expr"
            >{{ expr }}</li>
          </ul>
          <div class="pipeline-empty" v-else>—</div>
        </div>
      </div>

      <div class="pipeline-arrow">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </div>

      <!-- Block 3: Verify LLM -->
      <div class="pipeline-block">
        <div class="pipeline-block-header">
          <span class="pipeline-block-title">Verify LLM</span>
        </div>
        <div class="pipeline-block-body">
          <div class="pipeline-model-inline" :title="MODEL_ID">
            <span class="pipeline-sub-label">model:</span>
            <span class="pipeline-model-inline-value">{{ MODEL_ID }}</span>
          </div>
          <div class="pipeline-sub-label">Input Prompt</div>
          <pre class="pipeline-prompt-text">{{ NLEC_VERIFY_SYSTEM_PROMPT }}</pre>
          <div class="pipeline-sub-label pipeline-sub-label--output">Output</div>
          <ul class="pipeline-expr-list" v-if="necInfo.verify.length">
            <li
              v-for="(v, i) in necInfo.verify"
              :key="i"
              class="pipeline-expr-item verify-result-item"
            >{{ formatVerifyBool(v) }}</li>
          </ul>
          <div class="pipeline-empty" v-else>—</div>
        </div>
      </div>

      <div class="pipeline-arrow">
        <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </div>

      <!-- Block 4: Final Output -->
      <div class="pipeline-block pipeline-block--final">
        <div class="pipeline-block-header">
          <span class="pipeline-block-title">Final Output</span>
        </div>
        <div class="pipeline-block-body">
          <div class="pipeline-sub-label">Compressed Output</div>
          <ul class="pipeline-expr-list" v-if="necInfo.compressed.length">
            <li
              v-for="(expr, i) in necInfo.compressed"
              :key="i"
              class="pipeline-expr-item nl-expr"
              :title="expr"
            >{{ expr }}</li>
          </ul>
          <div class="pipeline-empty" v-else>—</div>

          <div class="pipeline-stats" v-if="necFinalHasStats">
            <div class="pipeline-stat" v-if="necInfo.timeMs != null">
              <span class="pipeline-stat-label">Time</span>
              <span class="pipeline-stat-value">{{ necInfo.timeMs }} ms</span>
            </div>
            <div class="pipeline-stat" v-if="necInfo.compressionCost != null">
              <span class="pipeline-stat-label">Compression Cost</span>
              <span class="pipeline-stat-value">${{ necInfo.compressionCost }}</span>
            </div>
            <div class="pipeline-stat" v-if="necInfo.verifyCost != null">
              <span class="pipeline-stat-label">Verify Cost</span>
              <span class="pipeline-stat-value">${{ necInfo.verifyCost }}</span>
            </div>
            <div class="pipeline-stat pipeline-stat--highlight" v-if="necInfo.totalCost != null">
              <span class="pipeline-stat-label">Total Cost</span>
              <span class="pipeline-stat-value">${{ necInfo.totalCost }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const MODEL_ID = 'qwen/qwen3-max'

const NLEC_COMPRESS_SYSTEM_PROMPT =
  'You are a natural-language query optimizer. The user sends a JSON array of instructions (same order matters). ' +
  'For EACH instruction, produce a shorter rewrite that preserves its exact semantic meaning.\n\n' +
  'Each instruction may contain column-value placeholders {__VAR_0__}, {__VAR_1__}, etc. These MUST appear unchanged in the corresponding output string.\n\n' +
  'Compression guidelines:\n' +
  '1. Remove stop words and filler that do not affect meaning.\n' +
  '2. Simplify complex or nested sentences into direct statements.\n' +
  '3. Do NOT change logical meaning, scope, or conditions.\n' +
  '4. Do NOT add or remove conditions.\n' +
  '5. Keep all {__VAR_N__} placeholders in the correct positions for that item.\n\n' +
  'Output MUST be a JSON array of strings with the SAME length and order as the input array. ' +
  'Each element i is the compressed form of input element i. No markdown, no explanation.\n'

const NLEC_VERIFY_SYSTEM_PROMPT =
  'You are a semantic equivalence checker for natural-language query instructions.\n\n' +
  'The user sends two JSON arrays of equal length: "originals" and "compressed". ' +
  'For each index i, determine whether compressed[i] is semantically equivalent to originals[i] ' +
  '(same true/false outcome for any inputs; same placeholders preserved).\n\n' +
  'Output MUST be a JSON array of booleans with the SAME length: true only when pair i is equivalent, false otherwise. ' +
  'No markdown, no explanation.\n'

const props = defineProps({
  extraInfo: {
    type: Object,
    default: null
  }
})

function safeParseJsonArray(val) {
  if (val == null || val === '') return []
  if (Array.isArray(val)) return val
  try {
    const parsed = JSON.parse(val)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function formatVerifyBool(v) {
  if (v === true) return 'true'
  if (v === false) return 'false'
  return String(v)
}

const necInfo = computed(() => {
  const extra = props.extraInfo
  if (!extra || typeof extra !== 'object') return null
  const inputs = safeParseJsonArray(extra.nec_compression_inputs)
  const compressed = safeParseJsonArray(extra.nec_compression_outputs)
  const verify = safeParseJsonArray(extra.nec_verify_results)
  if (!inputs.length && !compressed.length && !verify.length) return null
  return {
    inputs,
    compressed,
    verify,
    timeMs: extra.nec_total_time_ms ?? null,
    compressionCost: extra.nec_compression_llm_cost ?? null,
    verifyCost: extra.nec_verify_llm_cost ?? null,
    totalCost: extra.nec_total_llm_cost ?? null
  }
})

const necFinalHasStats = computed(() => {
  const n = necInfo.value
  if (!n) return false
  return (
    n.timeMs != null ||
    n.compressionCost != null ||
    n.verifyCost != null ||
    n.totalCost != null
  )
})
</script>

<style scoped>
.content-section {
  background: var(--fb-card);
  border-radius: var(--fb-radius);
  padding: 16px 20px 20px;
  margin-bottom: 12px;
  box-shadow: var(--fb-shadow-sm);
}

.section-title {
  margin: 0 0 14px 0;
  font-size: 1.067rem;
  font-weight: 700;
  color: var(--fb-text);
}

.prompt-info-section {
  border-left: 4px solid var(--fb-blue);
}

.prompt-block-badge {
  background: var(--fb-blue);
  color: #fff;
  font-size: 0.733rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}

.pipeline-row {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 10px;
  overflow-x: auto;
}

.pipeline-block {
  flex: 1;
  min-width: 180px;
  display: flex;
  flex-direction: column;
  background: var(--fb-bg);
  border: 1px solid var(--fb-divider);
  border-radius: var(--fb-radius);
  overflow: hidden;
}

.pipeline-block--final {
  border-color: var(--fb-blue);
}

.pipeline-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--fb-divider);
  background: var(--fb-card);
  flex-shrink: 0;
}

.pipeline-block--final .pipeline-block-header {
  background: var(--fb-blue-light);
  border-bottom-color: #b3d4ff;
}

.pipeline-block-title {
  font-size: 0.867rem;
  font-weight: 700;
  color: var(--fb-text);
}

.pipeline-block-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.nl-scroll {
  max-height: 300px;
}

.pipeline-model-inline {
  display: flex;
  align-items: baseline;
  gap: 0.35em;
  min-width: 0;
  flex-shrink: 0;
}

.pipeline-model-inline > .pipeline-sub-label {
  margin: 0;
  flex-shrink: 0;
}

.pipeline-model-inline-value {
  font-family: var(--fb-font);
  font-size: 0.733rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--fb-text-2);
  text-transform: none;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pipeline-sub-label {
  font-size: 0.733rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--fb-text-2);
  flex-shrink: 0;
}

.pipeline-sub-label--output {
  color: var(--fb-blue);
  margin-top: 4px;
}

.pipeline-prompt-text {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.767rem;
  line-height: 1.55;
  color: var(--fb-text-2);
  background: var(--fb-card);
  border: 1px solid var(--fb-divider);
  border-radius: 4px;
  padding: 8px 10px;
  margin: 0;
  box-sizing: border-box;
  width: 100%;
  height: 100px;
  min-height: 100px;
  max-height: 100px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  flex-shrink: 0;
}

.pipeline-expr-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

.pipeline-expr-item {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  padding: 5px 9px;
  border-radius: 4px;
  word-break: break-all;
}

.nl-expr {
  background: var(--fb-blue-light);
  color: var(--fb-blue);
  border: 1px solid #b3d4ff;
}

.verify-result-item {
  background: #fff;
  color: var(--fb-text);
  border: 1px solid var(--fb-divider);
}

.pipeline-empty {
  font-size: 0.8rem;
  color: var(--fb-text-3);
  padding: 4px 0;
}

.pipeline-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--fb-blue);
  opacity: 0.6;
  width: 24px;
}

.pipeline-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
  flex-shrink: 0;
}

.pipeline-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #fff;
  border: 1px solid var(--fb-divider);
  border-radius: 4px;
}

.pipeline-stat--highlight {
  background: var(--fb-blue-light);
  border-color: #b3d4ff;
}

.pipeline-stat-label {
  font-size: 0.733rem;
  color: var(--fb-text-2);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.pipeline-stat-value {
  font-size: 0.867rem;
  font-weight: 700;
  color: var(--fb-text);
}

.pipeline-stat--highlight .pipeline-stat-value {
  color: var(--fb-blue);
}

@media (max-width: 1100px) {
  .pipeline-row {
    overflow-x: auto;
  }
}
</style>
