<template>
  <div class="plan-page-container">
    <main class="main-content">
      <div class="content-scroll">
        <div class="error-banner" v-if="error">
          <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span><strong>Error:</strong> {{ error }}</span>
        </div>

        <div class="top-row-layout">
          <section class="content-section top-row-item">
            <h2 class="section-title">SQL Input</h2>
            <div class="sql-display">
              <textarea 
                v-model="sql" 
                class="sql-textarea" 
                placeholder="SELECT&#10;    ur.appp,&#10;    COUNT(*) AS review_count&#10;FROM user_reviews ur&#10;JOIN playstore p ON ur.app = p.app&#10;WHERE p.popularity > 200."
                rows="8"
              ></textarea>
            </div>
          </section>

          <ConfigOptions
            v-model:editableConfig="editableConfig"
            v-model:customConfig="customConfig"
            :loading-explain="explainLoading"
            :loading-profile="profileLoading"
            @explain="explain"
            @profile="runProfiling"
          />
        </div>

        <ExpressionCompression
          v-if="activeTab === 'profiling' && profilingData"
          :extra-info="profilingData.extra_info ?? null"
        />

        <section class="content-section prompt-info-section" v-if="promptInfo && activeTab === 'profiling'">
          <h2 class="section-title">Predicate Deduction</h2>

          <div class="pipeline-row">

            <div class="pipeline-block">
              <div class="pipeline-block-header">
                <span class="pipeline-block-title">Input NL Expressions</span>
                <span class="prompt-block-badge">{{ promptInfo.nlExpressions.length }}</span>
              </div>
              <div class="pipeline-block-body nl-scroll">
                <ul class="pipeline-expr-list">
                  <li
                    v-for="(expr, i) in promptInfo.nlExpressions"
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

            <div class="pipeline-block">
              <div class="pipeline-block-header">
                <span class="pipeline-block-title">Deduction LLM</span>
              </div>
              <div class="pipeline-block-body">
                <div class="pipeline-model-inline" :title="optimizerModel || undefined">
                  <span class="pipeline-sub-label">model:</span>
                  <span class="pipeline-model-inline-value">openai/gpt-5.4</span>
                </div>
                <div class="pipeline-sub-label">Input Prompt</div>
                <pre class="pipeline-prompt-text">{{ baseDeductionLLMPrompt }}</pre>
                <div class="pipeline-sub-label pipeline-sub-label--output">Output SQL</div>
                <ul class="pipeline-expr-list" v-if="promptInfo.deductionSql.length">
                  <li
                    v-for="(expr, i) in promptInfo.deductionSql"
                    :key="i"
                    class="pipeline-expr-item sql-expr"
                  >{{ expr }}</li>
                </ul>
                <div class="pipeline-empty" v-else>—</div>
              </div>
            </div>

            <div class="pipeline-arrow">
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>

            <div class="pipeline-block">
              <div class="pipeline-block-header">
                <span class="pipeline-block-title">Reflection LLM</span>
              </div>
              <div class="pipeline-block-body">
                <div class="pipeline-model-inline" :title="optimizerModel || undefined">
                  <span class="pipeline-sub-label">model:</span>
                  <span class="pipeline-model-inline-value">{{ optimizerModel || '—' }}</span>
                </div>
                <div class="pipeline-sub-label">Input Prompt</div>
                <pre class="pipeline-prompt-text">{{ baseReflectionLLMPrompt }}</pre>
                <div class="pipeline-sub-label pipeline-sub-label--output">Verified SQL</div>
                <div
                  v-if="promptInfo.outputSql.length"
                  class="pipeline-verified-sql-oneline pipeline-expr-item output-sql"
                  :title="promptInfo.outputSql.join('\n\n')"
                >
                  {{ promptInfo.outputSql.join('; ') }}
                </div>
                <div class="pipeline-empty" v-else>—</div>
              </div>
            </div>

            <div class="pipeline-arrow">
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </div>

            <div class="pipeline-block pipeline-block--final">
              <div class="pipeline-block-header">
                <span class="pipeline-block-title">Final Output</span>
              </div>
              <div class="pipeline-block-body">
                <div class="pipeline-sub-label">Output SQL</div>
                <div
                  v-if="promptInfo.outputSql.length"
                  class="pipeline-verified-sql-oneline pipeline-expr-item output-sql"
                  :title="promptInfo.outputSql.join('\n\n')"
                >
                  {{ promptInfo.outputSql.join('; ') }}
                </div>
                <div class="pipeline-empty" v-else>—</div>

                <div class="pipeline-stats" v-if="promptFinalHasStats">
                  <div class="pipeline-stat" v-if="promptInfo.timeMs != null">
                    <span class="pipeline-stat-label">Time</span>
                    <span class="pipeline-stat-value">{{ promptInfo.timeMs }} ms</span>
                  </div>
                  <div class="pipeline-stat" v-if="promptInfo.deductionCost != null">
                    <span class="pipeline-stat-label">Deduction Cost</span>
                    <span class="pipeline-stat-value">${{ promptInfo.deductionCost }}</span>
                  </div>
                  <div class="pipeline-stat" v-if="promptInfo.reflectCost != null">
                    <span class="pipeline-stat-label">Reflect Cost</span>
                    <span class="pipeline-stat-value">${{ promptInfo.reflectCost }}</span>
                  </div>
                  <div class="pipeline-stat pipeline-stat--highlight" v-if="promptInfo.totalCost != null">
                    <span class="pipeline-stat-label">Total Cost</span>
                    <span class="pipeline-stat-value">${{ promptInfo.totalCost }}</span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </section>

        <section class="content-section" v-if="plan && activeTab === 'explain'">
          <PlanViewer :plan="plan" />
        </section>

        <section class="content-section" v-if="profilingData && profilingTree && activeTab === 'profiling'">
          <h2 class="section-title">Profile Results</h2>
          <div class="profiling-tree-wrapper">
            <PlanTree 
              :node="profilingTree" 
              :depth="0" 
            />
          </div>
        </section>

        <section class="content-section" v-if="profilingData && activeTab === 'profiling'">
          <h2 class="section-title">Pareto Frontier</h2>
          <div class="pareto-chart-wrapper">
            <ParetoFrontierChart 
              v-if="profilingTree"
              :profiling-tree="profilingTree"
            />
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import PlanViewer from '../components/PlanViewer.vue'
import PlanTree from '../components/PlanTree.vue'
import ParetoFrontierChart from '../components/ParetoFrontierChart.vue'
import ConfigOptions from '../components/ConfigOptions.vue'
import ExpressionCompression from '../components/ExpressionCompression.vue'
import { apiRequest } from '../utils/api.js'

const route = useRoute()

const baseDeductionLLMPrompt = `You are a database optimizer assistant. Your task is to deduce the necessary SQL preconditions (pushdown predicates) for natural language expressions (NLEs), based on the provided column statistics.

An NLE is evaluated by an LLM to determine if a row satisfies a certain condition. Because LLM evaluation is expensive, we want to filter out rows that are guaranteed to be false by executing simple SQL predicates on the CPU first.

IMPORTANT: Your goal is NOT to convert the NLE into an equivalent SQL statement. Instead, you must find the **necessary conditions** of the NLE predicate given the column statistics.

The provided statistics for each column include: whether it is nullable, the number of distinct values, and the top-5 most frequent values (sampled from a subset of rows).

Here are the steps to determine the necessary conditions of the NLE predicate:
1. Understand the semantic meaning of the NLE.
2. Examine the column statistics, especially the top frequent values.
3. Identify values that definitively violate the NLE predicate. For instance, 'nan', 'N/A', empty strings, or NULL often represent missing data. If the NLE predicate requires a valid or meaningful value, these missing values can be filtered out.
4. Formulate DuckDB SQL predicates that filter out these violating values.

If you can deduce necessary conditions, output them as a valid JSON array of strings. Each string must be a valid DuckDB SQL predicate (e.g., "col != 'nan'"). The final filter will be the logical AND of all strings in the array.
If no meaningful necessary condition can be deduced, simply output an empty array.

Example:
NLE Predicate: '{Translated_review} is a positive user review'
Column stats: [user_reviews] Translated_Review: nullable=true, distinct=10537, top5=["nan":711, "Good":13, "Negative":10, "Great":6, "Really good addictive game.":5]
Output:
["Translated_Review != 'nan'", "Translated_Review != 'Negative'", ]

Note: The output MUST be a valid JSON array of strings (or an empty array). Do not wrap the JSON in markdown code blocks. Do not output any other text or explanation.`

const baseReflectionLLMPrompt = `You are a database optimizer assistant. Your task is to verify whether each candidate SQL predicate is a NECESSARY CONDITION for a set of Natural Language Expressions (NLEs).

Background:
A semantic filter evaluates NLEs (natural language conditions) on each row. Because LLM evaluation is expensive, we pre-filter rows using cheap SQL predicates. A SQL predicate P is a valid pushdown filter only if it is a NECESSARY CONDITION: whenever P is false, the overall NLE filter is guaranteed to be false.

KEY CONCEPT - Necessary vs Sufficient:
For each column, some values make NLE FALSE (set A), some make it TRUE (set B).
- **Necessary (valid)**: "column != value" for values in A. Filtering out violating values is correct.
- **Sufficient (invalid)**: "column = value" or "column IN (...)" for values in B. Whitelisting known-good values is WRONG: it would exclude valid rows whose values are not in the statistics. Output false for such predicates.

Definition of necessary condition:
  SQL predicate P is a necessary condition for NLE set S iff:
  for every possible row, NOT P => (at least one NLE in S is false)
  Equivalently: if a row passes all NLEs, it must also satisfy P.

Given the original NL Expressions and the candidate SQL Predicates, output a JSON array of booleans (same length as the SQL Predicates list):
  - true: the SQL predicate IS a valid necessary condition (typically "column != value" filtering out violating values)
  - false: the SQL predicate is NOT valid (too strict, unrelated to NLEs, or a sufficient condition like "column = value" / "column IN (...)")

Example:
NL Expressions: ["{Review} is a positive and meaningful user review"]
SQL Predicates: ["Review != 'nan'", "Review = 'Good'", "Rating > 10"]
Output: [true, false, false]
(Review != 'nan' is necessary: 'nan' violates the NLE. Review = 'Good' is NOT necessary: it is a sufficient condition that would wrongly exclude other positive reviews. Rating > 10 is unrelated to the NLE.)

Note: Output MUST be a valid JSON array of booleans only. Do not wrap in markdown code blocks. Do not output any explanation.`

const sql = ref('')
const plan = ref(null)
const error = ref('')
const explainLoading = ref(false)
const profileLoading = ref(false)
const currentConfig = ref(null)
const displayConfig = ref(null)
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
const profilingData = ref(null)
const activeTab = ref('explain')

const optimizerModel = ref('')

const customConfigLines = computed(() => {
  if (!customConfig.value) {
    return [
      "# 设置Batch",
      "semantic_batch_size = 4;",
      "",
      "# 设置AQE",
      "# Only work for Q6-Q10",
      "enable_semantic_filter_multiplexer = true; # open AQE",
      "semantic_filter_accuracy_threshold = 0.9; # acc threshold",
      "semantic_filter_latency_first = true; # false for cost first",
      "semantic_filter_batch_size = 4; # batch for AQE (not same as semantic_batch_size)"
    ]
  }
  return customConfig.value.split('\n').filter(line => line.trim() || line === '')
})

const promptInfo = computed(() => {
  if (!profilingData.value) return null
  const extra = profilingData.value.extra_info
  if (!extra || typeof extra !== 'object') return null

  const safeParseJson = (val) => {
    if (!val) return []
    if (Array.isArray(val)) return val
    try { return JSON.parse(val) } catch { return [val] }
  }

  const nlExpressions = safeParseJson(extra.pde_input_nl_expressions)
  const deductionSql  = safeParseJson(extra.pde_deduction_output_sql_expressions)
  const outputSql     = safeParseJson(extra.pde_output_sql_expressions)

  if (!nlExpressions.length && !deductionSql.length && !outputSql.length) return null

  return {
    nlExpressions,
    deductionSql,
    outputSql,
    timeMs:        extra.pde_time_ms        ?? null,
    totalCost:     extra.pde_total_llm_cost ?? null,
    deductionCost: extra.pde_deduction_llm_cost ?? null,
    reflectCost:   extra.pde_reflect_llm_cost   ?? null,
  }
})

const promptFinalHasStats = computed(() => {
  const p = promptInfo.value
  if (!p) return false
  return p.timeMs != null || p.deductionCost != null || p.reflectCost != null || p.totalCost != null
})

const deductionLLMFullPrompt = computed(() => {
  const info = promptInfo.value
  if (!info || !info.nlExpressions?.length) {
    return baseDeductionLLMPrompt
  }
  const nlSection = [
    '',
    'Current NL Expressions:',
    ...info.nlExpressions.map((expr, idx) => `${idx + 1}. ${expr}`)
  ].join('\n')
  return `${baseDeductionLLMPrompt}\n${nlSection}`
})

const reflectionLLMFullPrompt = computed(() => {
  const info = promptInfo.value
  if (!info || !info.deductionSql?.length) {
    return baseReflectionLLMPrompt
  }
  const sqlSection = [
    '',
    'Candidate SQL Predicates (from deduction):',
    ...info.deductionSql.map((expr, idx) => `${idx + 1}. ${expr}`)
  ].join('\n')
  return `${baseReflectionLLMPrompt}\n${sqlSection}`
})

function expandMultiplexerPaths(node) {
  if (!node) return node

  const name = (node.operator_name || node.operator_type || '').toUpperCase()
  const isMultiplexer = name.includes('MULTIPLEXER')

  if (isMultiplexer && node.extra_info) {
    const ei = node.extra_info

    const totalPaths = parseInt(ei.total_paths || ei.individual_path_count || ei.paths_count || '0')
    const hasPaths   = totalPaths > 0 && ei['path_0_accuracy'] !== undefined

    if (hasPaths) {
      const bestIdx = parseInt(ei.best_path_index ?? '-1')
      const pathNodes = []
      for (let i = 0; i < totalPaths; i++) {
        const latencyMs = parseFloat(ei[`path_${i}_exploration_time_ms`] || ei[`path_${i}_latency`] || '0')
        pathNodes.push({
          operator_name: `Path ${i}`,
          operator_type: 'PATH_NODE',
          extra_info: {
            path_index:    i,
            is_path_node:  true,
            is_best:       i === bestIdx,
            accuracy:      parseFloat(ei[`path_${i}_accuracy`]      || '0'),
            cost:          parseFloat(ei[`path_${i}_cost`]          || '0'),
            latency_ms:    latencyMs,
            input_tokens:  parseInt(ei[`path_${i}_input_tokens`]   || '0'),
            output_tokens: parseInt(ei[`path_${i}_output_tokens`]  || '0'),
            expression:    ei[`path_${i}_expression`] || '',
            skipped:       ei[`path_${i}_skipped`] === 'true'
          },
          children: []
        })
      }
      return {
        ...node,
        children: [
          ...pathNodes,
          ...(node.children || []).map(expandMultiplexerPaths)
        ]
      }
    }

    return {
      ...node,
      children: (node.children || []).map(expandMultiplexerPaths)
    }
  }

  return {
    ...node,
    children: (node.children || []).map(expandMultiplexerPaths)
  }
}

const profilingTree = computed(() => {
  if (!profilingData.value) return null

  if (profilingData.value.children &&
      Array.isArray(profilingData.value.children) &&
      profilingData.value.children.length > 0) {

    const explainAnalyzeNode = profilingData.value.children[0]

    let root
    if (explainAnalyzeNode.operator_name === 'EXPLAIN_ANALYZE' &&
        explainAnalyzeNode.children &&
        Array.isArray(explainAnalyzeNode.children) &&
        explainAnalyzeNode.children.length > 0) {
      root = explainAnalyzeNode.children[0]
    } else {
      root = explainAnalyzeNode
    }

    return expandMultiplexerPaths(root)
  }

  return null
})

watch([plan, profilingData], ([newPlan, newProfiling]) => {
  if (newPlan && !newProfiling) {
    activeTab.value = 'explain'
  } else if (newProfiling && !newPlan) {
    activeTab.value = 'profiling'
  }
})

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(async () => {
  await loadConfig()
  
  const q = route.query.q
  const mode = route.query.mode
  
  if (typeof q === 'string' && q.trim()) {
    sql.value = q
    
    if (mode === 'profiling') {
      runProfiling()
    } else {
      explain()
    }
  }
})

async function loadConfig() {
  try {
    const res = await apiRequest('/api/config')
    const data = await res.json()
    if (res.ok && data.ok) {
      currentConfig.value = data.config
      displayConfig.value = {
        llm_model: data.config.llm_model,
        llm_url: data.config.llm_url,
        llm_api_key: data.config.llm_api_key,
        semantic_batch_size: data.config.semantic_batch_size,
        enable_semantic_filter_multiplexer: data.config.enable_semantic_filter_multiplexer,
        semantic_filter_accuracy_threshold: data.config.semantic_filter_accuracy_threshold,
        semantic_filter_latency_first: data.config.semantic_filter_latency_first,
        semantic_filter_batch_size: data.config.semantic_filter_batch_size,
        enable_partial_deduction: data.config.enable_partial_deduction,
        enable_nl_expression_compression: data.config.enable_nl_expression_compression
      }
      optimizerModel.value = data.config.optimizer_model ?? ''
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
}

function buildSetCommands() {
  const cfg = editableConfig.value
  const lines = []
  const boolKeys = ['enable_semantic_filter_multiplexer', 'semantic_filter_latency_first', 'enable_partial_deduction', 'enable_nl_expression_compression']
  const allKeys = [
    'llm_model', 'llm_url',
    'enable_semantic_filter_multiplexer',
    'semantic_filter_accuracy_threshold',
    'semantic_filter_latency_first',
    'semantic_filter_batch_size',
    'semantic_batch_size',
    'enable_partial_deduction',
    'enable_nl_expression_compression'
  ]
  for (const key of allKeys) {
    const val = cfg[key]
    if (val === '' || val === null || val === undefined) continue
    if (boolKeys.includes(key)) {
      lines.push(`SET ${key} = "${val}";`)
    } else {
      lines.push(`SET ${key} = "${val}";`)
    }
  }
  return lines.join('\n')
}

async function explain() {
  error.value = ''
  plan.value = null
  explainLoading.value = true
  try {
    const generatedCmds = buildSetCommands()
    const mergedConfig = [generatedCmds, customConfig.value].filter(Boolean).join('\n')
    const res = await apiRequest('/api/explain', {
      method: 'POST',
      body: JSON.stringify({ 
        query: sql.value,
        config: mergedConfig
      })
    })
    let data
    try { data = await res.json() } catch (_) { data = {} }
    if (!res.ok || !data.ok) {
      const msg = (data && data.error) || res.statusText || 'Explain failed'
      throw new Error(msg)
    }
    const { ok, ...planData } = data
    plan.value = planData
    activeTab.value = 'explain'
  } catch (e) {
    error.value = e.message
  } finally {
    explainLoading.value = false
  }
}

async function runProfiling() {
  error.value = ''
  profilingData.value = null
  plan.value = null
  profileLoading.value = true
  try {
    const generatedCmds = buildSetCommands()
    const mergedConfig = [generatedCmds, customConfig.value].filter(Boolean).join('\n')
    const res = await apiRequest('/api/profile', {
      method: 'POST',
      body: JSON.stringify({ 
        query: sql.value,
        config: mergedConfig
      })
    })
    let data
    try { data = await res.json() } catch (_) { data = {} }
    
    if (!res.ok || !data.ok) {
      const msg = (data && data.error) || res.statusText || 'Profiling failed'
      throw new Error(msg)
    }
    
    profilingData.value = data.profiling
    activeTab.value = 'profiling'
  } catch (e) {
    error.value = e.message
  } finally {
    profileLoading.value = false
  }
}
</script>

<style scoped>
.plan-page-container {
  display: flex;
  width: 100%;
  min-height: calc(100vh - var(--fb-topbar-h));
  background: var(--fb-bg);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.error-banner {
  background: #FFF0F0;
  border-left: 4px solid #FA3E3E;
  border-radius: var(--fb-radius);
  padding: 12px 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #C62828;
  box-shadow: var(--fb-shadow-sm);
}

.error-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.content-section {
  background: var(--fb-card);
  border-radius: var(--fb-radius);
  padding: 16px 20px 20px;
  margin-bottom: 12px;
  box-shadow: var(--fb-shadow-sm);
}

.top-row-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.top-row-item {
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
}

.top-row-item .section-title { flex-shrink: 0; }

.top-row-item .sql-display,
.top-row-item .config-grid,
.top-row-item .custom-config,
.top-row-item .action-buttons {
  flex: 1;
  min-height: 0;
}

.section-title {
  margin: 0 0 14px 0;
  font-size: 1.067rem;
  font-weight: 700;
  color: var(--fb-text);
}

.sql-display {
  background: var(--fb-bg);
  border: 1.5px solid var(--fb-border);
  border-radius: var(--fb-radius);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.sql-textarea {
  width: 100%;
  height: 100%;
  min-height: 180px;
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.867rem;
  line-height: 1.65;
  color: var(--fb-text);
  background: transparent;
  border: none;
  outline: none;
  padding: 14px 16px;
  resize: none;
  box-sizing: border-box;
  flex: 1;
  overflow-y: auto;
}

.sql-textarea:focus { background: #fff; }
.sql-textarea::placeholder { color: var(--fb-text-3); }


.profiling-tree-wrapper {
  background: var(--fb-bg);
  border: 1px solid var(--fb-divider);
  border-radius: var(--fb-radius);
  padding: 16px;
  overflow-x: auto;
  min-height: 300px;
}

.pareto-chart-wrapper { min-height: 400px; }

.prompt-info-section { border-left: 4px solid var(--fb-blue); }

.prompt-block-full {
  margin-bottom: 14px;
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

.pipeline-verified-sql-oneline {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  max-width: 100%;
  word-break: normal;
}

.pipeline-block .pipeline-expr-item.sql-expr {
  background: #fff;
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

.llm-prompt-grid {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-bottom: 14px;
}

.simplified-llm-block {
  background: var(--fb-bg);
  border: 1px solid var(--fb-divider);
  border-radius: var(--fb-radius);
  padding: 16px 20px;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.llm-prompt-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.llm-prompt-icon {
  font-size: 1.2rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.llm-prompt-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--fb-text);
}

.llm-prompt-summary {
  font-size: 0.8rem;
  color: #6c757d;
  font-style: italic;
  margin-top: 4px;
}

.sequence-arrow {
  display: flex;
  justify-content: center;
  align-items: center;
  color: var(--fb-blue);
  opacity: 0.6;
}

.sequence-arrow-right {
  margin: 0 10px;
}

.input-nl-block {
  background: var(--fb-bg);
  border-color: var(--fb-divider);
  align-items: stretch;
  text-align: left;
}

.input-nl-block .llm-prompt-header {
  justify-content: flex-start;
}

.input-nl-block .llm-prompt-title {
  flex: 1;
}

.prompt-expr-list-truncated {
  max-width: 100%;
  overflow: hidden;
  width: 100%;
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  display: block;
  word-break: normal;
}

.prompt-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.prompt-block {
  background: var(--fb-bg);
  border: 1px solid var(--fb-divider);
  border-radius: var(--fb-radius);
  padding: 12px 14px;
  margin-bottom: 10px;
}

.prompt-block:last-child { margin-bottom: 0; }

.prompt-right-col { display: flex; flex-direction: column; }

.prompt-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.prompt-block-icon { font-size: 0.933rem; line-height: 1; }

.prompt-block-title {
  font-size: 0.867rem;
  font-weight: 600;
  color: var(--fb-text);
  flex: 1;
}

.prompt-block-badge {
  background: var(--fb-blue);
  color: #fff;
  font-size: 0.733rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}

.prompt-expr-list {
  list-style: none;
  margin: 0; padding: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.prompt-expr-item {
  font-family: ui-monospace, 'SF Mono', Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  padding: 6px 10px;
  border-radius: var(--fb-radius);
  word-break: break-all;
}

.text-truncate {
  word-break: normal;
}

.nl-expr   { background: var(--fb-blue-light); color: var(--fb-blue);    border: 1px solid #b3d4ff; }
.sql-expr  { background: var(--fb-bg);          color: var(--fb-text);    border: 1px solid var(--fb-divider); }
.output-sql{ background: #F0FFF4;               color: #1A7A3A;           border: 1px solid #B7E4C7; }

.prompt-stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: auto;
  padding-top: 10px;
}

.prompt-bottom-row {
  display: flex;
  align-items: stretch;
  gap: 14px;
  margin-top: 4px;
}

.prompt-bottom-row .prompt-final-card {
  flex: 1 1 0;
  min-width: 0;
  margin-top: 0;
}

.prompt-stats-col {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 8px;
  align-items: stretch;
  align-self: stretch;
  flex-shrink: 0;
}

.prompt-stats-col .prompt-stat {
  margin: 0;
  flex: 0 0 auto;
  min-width: 100px;
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.prompt-stats-col .prompt-stat-label {
  font-size: 0.75rem;
  white-space: nowrap;
}

.prompt-stats-col .prompt-stat-value {
  font-size: 1rem;
  white-space: nowrap;
}

.prompt-final-card {
  margin-top: 4px;
  background: var(--fb-bg);
  border: 1px solid var(--fb-divider);
  border-radius: var(--fb-radius);
  overflow: hidden;
}

.prompt-final-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--fb-divider);
}

.prompt-stats-row--inline {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  margin: 0;
  padding: 0;
}

.prompt-final-title {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.prompt-stat-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.stat-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  background: white;
  border: 1px solid var(--fb-divider);
  border-radius: 20px;
  white-space: nowrap;
}

.stat-badge--highlight {
  background: var(--fb-blue-light);
  border-color: #b3d4ff;
}

.stat-badge-label {
  font-size: 0.733rem;
  color: var(--fb-text-2);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-badge-value {
  font-size: 0.867rem;
  font-weight: 700;
  color: var(--fb-text);
}

.stat-badge--highlight .stat-badge-value {
  color: var(--fb-blue);
}

.prompt-final-expr-list {
  padding: 10px 14px;
  margin: 0;
}

.prompt-stat {
  flex: 1;
  min-width: 90px;
  background: var(--fb-bg);
  border: 1px solid var(--fb-divider);
  border-radius: var(--fb-radius);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.prompt-stat.highlight {
  background: var(--fb-blue-light);
  border-color: #b3d4ff;
}

.prompt-stat-label {
  font-size: 0.733rem;
  color: var(--fb-text-2);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.prompt-stat-value {
  font-size: 0.933rem;
  font-weight: 700;
  color: var(--fb-text);
}

.prompt-stat.highlight .prompt-stat-value { color: var(--fb-blue); }

@media (max-width: 1100px) {
  .top-row-layout { grid-template-columns: 1fr; }
  .top-row-item { margin-bottom: 12px; }
  .config-grid { grid-template-columns: 1fr; }
  .prompt-info-grid { grid-template-columns: 1fr; }
  .llm-prompt-grid { flex-direction: column; }
  .pipeline-row { overflow-x: auto; }
  .sequence-arrow-right { transform: rotate(90deg); margin: 10px 0; }
}
</style>
