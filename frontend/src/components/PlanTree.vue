<template>
  <div class="plan-tree">
    <div class="tree-node-wrapper">
      <div class="tree-node" :class="{ 'has-children': hasChildren }">
        <div v-if="depth > 0 && !(isMultiplexerNode && hasPathNodes) && pathIndex === null" class="vertical-line"></div>
        <div v-if="hasChildren && !(isMultiplexerNode && hasPathNodes)" class="horizontal-line"></div>
        
        <div
          v-if="!(isMultiplexerNode && hasPathNodes)"
          class="node-content"
          :class="[nodeClass, { 'node-content--path-operator': isPathOperatorNode }]"
          :data-path-index="pathIndex"
          :data-is-best-path="isBestPath"
        >
          <div class="node-header">
            <span class="node-name">{{ nodeLabel }}</span>
            <span v-if="isBestPath" class="best-path-badge">★ Best</span>
          </div>

          <div v-if="hasAnyDetail" class="node-details-wrap">
            <div v-if="nodeDetail" class="node-detail">
              {{ nodeDetail }}
            </div>
            
            <div v-if="hasOperatorTiming || hasSemanticInfo" class="node-profiling">

              <div v-if="operatorTiming !== null" class="profiling-item">
                <span class="profiling-label">Time:</span>
                <span class="profiling-value">{{ formatTime(operatorTiming) }}</span>
              </div>
              
              <div v-if="isSemanticOperator && hasSemanticInfo && !isMultiplexerNode" class="profiling-semantic">
                <div v-if="semanticInfo.input_tokens !== undefined" class="profiling-item">
                  <span class="profiling-label">Input Tokens:</span>
                  <span class="profiling-value">{{ formatNumber(semanticInfo.input_tokens) }}</span>
                </div>
                <div v-if="semanticInfo.output_tokens !== undefined" class="profiling-item">
                  <span class="profiling-label">Output Tokens:</span>
                  <span class="profiling-value">{{ formatNumber(semanticInfo.output_tokens) }}</span>
                </div>
                <div v-if="semanticInfo.parse_success !== undefined" class="profiling-item">
                  <span class="profiling-label">Parse Success:</span>
                  <span class="profiling-value">{{ formatNumber(semanticInfo.parse_success) }}</span>
                </div>
                <div v-if="semanticInfo.parse_success_rate !== undefined" class="profiling-item">
                  <span class="profiling-label">Success Rate:</span>
                  <span class="profiling-value">{{ semanticInfo.parse_success_rate }}</span>
                </div>
              </div>
              
              <div v-if="pathIndex !== null" class="path-details">
                <div v-if="pathAccuracy !== null" class="profiling-item">
                  <span class="profiling-label">Accuracy:</span>
                  <span class="profiling-value">{{ pathAccuracy }}</span>
                </div>
                <div v-if="pathCost !== null" class="profiling-item">
                  <span class="profiling-label">Cost:</span>
                  <span class="profiling-value">{{ pathCost }}</span>
                </div>
                <div v-if="pathLatencyMs !== null" class="profiling-item">
                  <span class="profiling-label">Latency:</span>
                  <span class="profiling-value">{{ formatTime(pathLatencyMs / 1000) }}</span>
                </div>
                <div v-if="pathInputTokens !== null" class="profiling-item">
                  <span class="profiling-label">Input Tokens:</span>
                  <span class="profiling-value">{{ formatNumber(pathInputTokens) }}</span>
                </div>
                <div v-if="pathOutputTokens !== null" class="profiling-item">
                  <span class="profiling-label">Output Tokens:</span>
                  <span class="profiling-value">{{ formatNumber(pathOutputTokens) }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="hasExtraInfo" class="node-extra-info">
              <div v-for="(value, key) in filteredExtraInfo" :key="key" class="info-item" :class="{ 'info-item-expression': ['expression', 'semantic expression'].includes(key.toLowerCase()) }">
                <span class="info-key">{{ formatKey(key) }}:</span>
                <span class="info-value">{{ formatValue(value) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="hasChildren" 
           class="children-container" 
           :class="{ 
             'multiple-children': childrenNodes.length > 1,
             'join-children': isJoinNode && childrenNodes.length > 1,
             'multiplexer-children': isMultiplexerNode && hasPathNodes,
             'multiplexer-with-downstream': isMultiplexerNode && hasPathNodes && hasDownstreamNodes
           }"
           :data-children-count="childrenNodes.length">

        <template v-if="isMultiplexerNode && pathNodes.length > 0">
          <div class="path-nodes-multiplexer-layout">
            <div v-if="multiplexerInfo" class="multiplexer-info-box">
              <div class="multiplexer-info-header">
                <span class="multiplexer-info-title">AQE</span>
              </div>
              <div class="multiplexer-info-content multiplexer-info-content--expanded">
                <div v-if="multiplexerInfo.timing != null" class="multiplexer-info-item">
                  <span class="multiplexer-info-label">Total Time:</span>
                  <span class="multiplexer-info-value">{{ formatTime(multiplexerInfo.timing) }}</span>
                </div>
                <div v-if="multiplexerInfo.estimatedCardinality" class="multiplexer-info-item">
                  <span class="multiplexer-info-label">Estimated Cardinality:</span>
                  <span class="multiplexer-info-value">{{ multiplexerInfo.estimatedCardinality }}</span>
                </div>
                <div v-if="multiplexerInfo.expressionCount != null" class="multiplexer-info-item">
                  <span class="multiplexer-info-label">Expressions:</span>
                  <span class="multiplexer-info-value">{{ multiplexerInfo.expressionCount }}</span>
                </div>
                <div v-if="multiplexerInfo.individualPathCount != null" class="multiplexer-info-item">
                  <span class="multiplexer-info-label">Paths Explored:</span>
                  <span class="multiplexer-info-value">{{ multiplexerInfo.individualPathCount }}</span>
                </div>
                <div v-if="multiplexerInfo.bestPathAccuracy != null" class="multiplexer-info-item">
                  <span class="multiplexer-info-label">Best Accuracy:</span>
                  <span class="multiplexer-info-value multiplexer-info-highlight">{{ (multiplexerInfo.bestPathAccuracy * 100).toFixed(1) }}%</span>
                </div>
                <template v-if="multiplexerInfo.exploreTimeMs != null || multiplexerInfo.pathExploreTimeMs != null || multiplexerInfo.exploitTimeMs != null">
                  <div class="multiplexer-info-divider"></div>
                  <div v-if="multiplexerInfo.exploreTimeMs != null" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Expr Explore:</span>
                    <span class="multiplexer-info-value">{{ formatTime(multiplexerInfo.exploreTimeMs / 1000) }}</span>
                  </div>
                  <div v-if="multiplexerInfo.pathExploreTimeMs != null" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Path Explore:</span>
                    <span class="multiplexer-info-value">{{ formatTime(multiplexerInfo.pathExploreTimeMs / 1000) }}</span>
                  </div>
                  <div v-if="multiplexerInfo.exploitTimeMs != null" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Exploitation:</span>
                    <span class="multiplexer-info-value">{{ formatTime(multiplexerInfo.exploitTimeMs / 1000) }}</span>
                  </div>
                </template>
                <template v-if="multiplexerInfo.totalInputTokens != null">
                  <div class="multiplexer-info-divider"></div>
                  <div class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Total Input Tokens:</span>
                    <span class="multiplexer-info-value">{{ formatNumber(multiplexerInfo.totalInputTokens) }}</span>
                  </div>
                  <div v-if="multiplexerInfo.totalOutputTokens != null" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Total Output Tokens:</span>
                    <span class="multiplexer-info-value">{{ formatNumber(multiplexerInfo.totalOutputTokens) }}</span>
                  </div>
                </template>
                <template v-if="multiplexerInfo.successfulRequests != null || multiplexerInfo.errorRequests != null">
                  <div class="multiplexer-info-divider"></div>
                  <div v-if="multiplexerInfo.successfulRequests != null" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Successful Req:</span>
                    <span class="multiplexer-info-value multiplexer-info-highlight">{{ multiplexerInfo.successfulRequests }}</span>
                  </div>
                  <div v-if="multiplexerInfo.errorRequests != null" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Error Req:</span>
                    <span class="multiplexer-info-value" :style="{ color: multiplexerInfo.errorRequests > 0 ? '#ff3b30' : 'inherit' }">
                      {{ multiplexerInfo.errorRequests }}
                    </span>
                  </div>
                  <div v-if="multiplexerInfo.failureRequests != null && multiplexerInfo.failureRequests > 0" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Failure Req:</span>
                    <span class="multiplexer-info-value" style="color:#ff3b30">{{ multiplexerInfo.failureRequests }}</span>
                  </div>
                  <div v-if="multiplexerInfo.retryRequests != null && multiplexerInfo.retryRequests > 0" class="multiplexer-info-item">
                    <span class="multiplexer-info-label">Retries:</span>
                    <span class="multiplexer-info-value">{{ multiplexerInfo.retryRequests }}</span>
                  </div>
                </template>
              </div>
            </div>
            <div class="path-nodes-group-wrapper">
              <div class="path-nodes-trees-column">
              <div class="path-nodes-container path-nodes-row-hover">
                <PlanTree
                  v-for="(child, index) in pathNodes.slice(0, 4)"
                  :key="`path-${child.extra_info?.path_index || index}`"
                  :node="child"
                  :depth="depth + 1"
                  :is-last="index === Math.min(pathNodes.length, 4) - 1"
                />
              </div>
              <div v-if="pathNodes.length > 4" class="path-nodes-container path-nodes-row-hover path-nodes-row-second">
                <PlanTree
                  v-for="(child, index) in pathNodes.slice(4, 8)"
                  :key="`path-${child.extra_info?.path_index || (index + 4)}`"
                  :node="child"
                  :depth="depth + 1"
                  :is-last="index === Math.min(pathNodes.length - 4, 4) - 1"
                />
              </div>
              </div>
            </div>
          </div>
        </template>
        
        <template v-if="isMultiplexerNode && downstreamNodes.length > 0">
          <div class="downstream-nodes-container">
            <PlanTree
              v-for="(child, index) in downstreamNodes"
              :key="`downstream-${index}`"
              :node="child"
              :depth="depth + 1"
              :is-last="index === downstreamNodes.length - 1"
            />
          </div>
        </template>
        <template v-if="!isMultiplexerNode">
          <PlanTree
            v-for="(child, index) in childrenNodes"
            :key="child.id || index"
            :node="child"
            :depth="depth + 1"
            :is-last="index === childrenNodes.length - 1"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  depth: {
    type: Number,
    default: 0
  },
  isLast: {
    type: Boolean,
    default: false
  }
})

const nodeLabel = computed(() => {
  let raw = null
  if (props.node.operator_name) raw = props.node.operator_name
  else if (props.node.label) raw = props.node.label
  else if (props.node.name) raw = props.node.name
  else if (props.node.operator_type) raw = props.node.operator_type
  else return 'Unknown'
  if (String(raw).toUpperCase().includes('SEM_FILTER_MULTIPLEXER')) {
    return 'AQE'
  }
  return raw
})

const nodeDetail = computed(() => {
  return props.node.detail || ''
})

const nodeClass = computed(() => {
  const name = nodeLabel.value.toUpperCase()
  const rawOp = (props.node.operator_type || props.node.operator_name || '').toUpperCase()

  if (pathIndex.value !== null) {
    return 'node-sem-filter'
  }

  if (rawOp.includes('SEM_FILTER_MULTIPLEXER')) {
    return 'node-sem-filter'
  }
  
  if (name.includes('PROJECTION') || name.includes('PROJECT')) {
    return 'node-projection'
  } else if (name.includes('AGGREGATE') || name.includes('GROUP')) {
    return 'node-aggregate'
  } else if (name.includes('FILTER') || name.includes('SEM_FILTER')) {
    return name.includes('SEM_') ? 'node-sem-filter' : 'node-filter'
  } else if (name.includes('JOIN')) {
    return 'node-join'
  } else if (name.includes('SCAN') || name.includes('SEQ_SCAN')) {
    return 'node-scan'
  }
  return 'node-default'
})

const isJoinNode = computed(() => {
  const name = nodeLabel.value.toUpperCase()
  return name.includes('JOIN') || name.includes('COMPARISON_JOIN') || name.includes('HASH_JOIN')
})

const isMultiplexerNode = computed(() => {
  const name = nodeLabel.value.toUpperCase()
  const operatorType = props.node.operator_type || props.node.operator_name || ''
  return name.includes('MULTIPLEXER') || operatorType.toUpperCase().includes('MULTIPLEXER')
})

const extraInfo = computed(() => {
  return props.node.extra_info || {}
})

const operatorTiming = computed(() => {
  if (props.node.operator_timing !== undefined && props.node.operator_timing !== null) {
    return props.node.operator_timing
  }
  return null
})

const hasOperatorTiming = computed(() => {
  return operatorTiming.value !== null
})

const isSemanticOperator = computed(() => {
  const name = nodeLabel.value.toUpperCase()
  const operatorType = props.node.operator_type || props.node.operator_name || ''
  return name.includes('SEM_FILTER') || 
         name.includes('SEMANTIC') || 
         operatorType.toUpperCase().includes('SEM_FILTER')
})

const pathIndex = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.path_index !== undefined ? extraInfo.path_index : null
})

const isPathOperatorNode = computed(() => {
  const ei = props.node.extra_info || {}
  return ei.path_index !== undefined || ei.is_path_node === true
})

const isBestPath = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.is_best === true || extraInfo.is_best === "true"
})

const pathExpression = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.expression || null
})

const pathAccuracy = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.accuracy !== undefined ? extraInfo.accuracy : null
})

const pathCost = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.cost !== undefined ? extraInfo.cost : null
})

const pathLatencyMs = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.latency_ms !== undefined ? extraInfo.latency_ms : null
})

const pathInputTokens = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.input_tokens !== undefined ? extraInfo.input_tokens : null
})

const pathOutputTokens = computed(() => {
  const extraInfo = props.node.extra_info || {}
  return extraInfo.output_tokens !== undefined ? extraInfo.output_tokens : null
})

const pathNodes = computed(() => {
  if (!isMultiplexerNode.value || !childrenNodes.value) return []
  return childrenNodes.value.filter(child => {
    const childExtraInfo = child.extra_info || {}
    return childExtraInfo.path_index !== undefined || childExtraInfo.is_path_node === true
  })
})

const downstreamNodes = computed(() => {
  if (!isMultiplexerNode.value || !childrenNodes.value) return []
  return childrenNodes.value.filter(child => {
    const childExtraInfo = child.extra_info || {}
    return childExtraInfo.path_index === undefined && childExtraInfo.is_path_node !== true
  })
})

const hasPathNodes = computed(() => pathNodes.value.length > 0)
const hasDownstreamNodes = computed(() => downstreamNodes.value.length > 0)

const multiplexerInfo = computed(() => {
  if (!isMultiplexerNode.value) return null

  const ei = props.node.extra_info || {}
  return {
    timing:               props.node.operator_timing,
    estimatedCardinality: ei['Estimated Cardinality'] || ei['estimated_cardinality'],
    individualPathCount:  parseInt(
      ei['total_paths'] || ei['individual_path_count'] || ei['paths_count'] || pathNodes.value.length
    ),
    expressionCount:  ei['expression_count']           ? parseInt(ei['expression_count'])           : null,
    bestPathAccuracy: ei['best_path_accuracy']         ? parseFloat(ei['best_path_accuracy'])       : null,
    exploreTimeMs:    ei['expression_exploration_time_ms'] ? parseFloat(ei['expression_exploration_time_ms']) : null,
    pathExploreTimeMs:ei['path_exploration_time_ms']       ? parseFloat(ei['path_exploration_time_ms'])       : null,
    exploitTimeMs:    ei['exploitation_time_ms']           ? parseFloat(ei['exploitation_time_ms'])           : null,
    totalInputTokens: ei['total_input_tokens']             ? parseInt(ei['total_input_tokens'])               : null,
    totalOutputTokens:ei['total_output_tokens']            ? parseInt(ei['total_output_tokens'])              : null,
    successfulRequests: ei['successful_requests'] != null ? parseInt(ei['successful_requests']) : null,
    errorRequests:      ei['error_requests']       != null ? parseInt(ei['error_requests'])      : null,
    failureRequests:    ei['failure_requests']     != null ? parseInt(ei['failure_requests'])    : null,
    retryRequests:      ei['retry_requests']       != null ? parseInt(ei['retry_requests'])      : null,
  }
})

function formatPathExpression(expr) {
  if (!expr) return ""
  const matches = expr.match(/s'([^']+)'/g)
  if (matches && matches.length > 0) {
    return matches.map(m => m.replace(/s'|'/g, '')).join(' AND ')
  }
  if (expr.includes("Predicates A") || expr.includes("Predicates B")) {
    return expr.replace(/s'|'/g, '').substring(0, 100) + (expr.length > 100 ? '...' : '')
  }
  return expr.substring(0, 150) + (expr.length > 150 ? '...' : '')
}
const filteredExtraInfo = computed(() => {
  const info = extraInfo.value
  if (!info) return {}

  if (isMultiplexerNode.value) {
    const filtered = {}
    const hiddenPrefixes = [
      'path_', 'expr_', 'similarity_', 'expression_exploration_',
      'path_exploration_', 'exploitation_', 'best_path_', 'total_',
      'expression_count', 'multiplexer_type',
      'input_tokens', 'output_tokens', 'parse_success', 'parse_failure',
      'parse_success_rate',
    ]
    const hiddenExact = new Set([
      'execution_status_summary', 'exploitation_phase',
      'expression_exploration_phase', 'path_exploration_phase',
      'expression exploration phase', 'path exploration phase',
      'exploitation phase', 'execution status summary',
    ])

    for (const [key, value] of Object.entries(info)) {
      const k = key.toLowerCase()
      if (hiddenExact.has(k)) continue
      if (hiddenPrefixes.some(p => k.startsWith(p.toLowerCase()))) continue
      if (typeof value === 'string' && /={8,}/.test(value)) continue
      filtered[key] = value
    }
    return filtered
  }

  if (pathIndex.value !== null) {
    const filtered = {}
    const excludeKeys = [
      'accuracy',
      'cost',
      'latency_ms', 
      'input_tokens', 
      'output_tokens', 
      'is_best',
      'is_path_node',
      'multiplexer_estimated_cardinality',
      'multiplexer_individual_path_count',
      'multiplexer_timing',
      'path_index',
      'path_type'
    ]
    
    for (const [key, value] of Object.entries(info)) {
      if (!excludeKeys.includes(key.toLowerCase())) {
        filtered[key] = value
      }
    }
    return filtered
  }

  if (hasOperatorTiming.value && isSemanticOperator.value) {
    const filtered = {}
    const excludeKeys = [
      'input_tokens', 
      'output_tokens', 
      'parse_success', 
      'parse_failure',
      'parse_success_rate'
    ]
    
    for (const [key, value] of Object.entries(info)) {
      if (!excludeKeys.includes(key.toLowerCase())) {
        filtered[key] = value
      }
    }
    return filtered
  }
  
  return info
})

const hasExtraInfo = computed(() => {
  const info = filteredExtraInfo.value
  return info && Object.keys(info).length > 0
})


const semanticInfo = computed(() => {
  const extraInfo = props.node.extra_info || {}
  const info = {}
  
  if (extraInfo.input_tokens !== undefined) {
    info.input_tokens = extraInfo.input_tokens
  }
  if (extraInfo.output_tokens !== undefined) {
    info.output_tokens = extraInfo.output_tokens
  }
  if (extraInfo.parse_success !== undefined) {
    info.parse_success = extraInfo.parse_success
  }
  if (extraInfo.parse_success_rate !== undefined) {
    info.parse_success_rate = extraInfo.parse_success_rate
  }
  
  return info
})

const hasSemanticInfo = computed(() => {
  return Object.keys(semanticInfo.value).length > 0
})

const hasAnyDetail = computed(() => {
  return !!(nodeDetail.value || hasOperatorTiming.value || hasSemanticInfo.value || hasExtraInfo.value)
})

const hasChildren = computed(() => {
  return props.node.children && Array.isArray(props.node.children) && props.node.children.length > 0
})

const childrenNodes = computed(() => {
  if (props.node.children && Array.isArray(props.node.children)) {
    const validChildren = props.node.children.filter(child => {
      return child !== null && child !== undefined && typeof child === 'object'
    })
    
    if (validChildren.length > 1 && !isMultiplexerNode.value) {
      console.log(`[PlanTree:profiling] Node "${nodeLabel.value}" has ${validChildren.length} children:`, 
                  validChildren.map(c => c.label || c.name || c.operator_name || 'Unknown'))
    }
    return validChildren
  }
  return []
})

function formatKey(key) {

  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatValue(value) {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

function formatTime(seconds) {
  if (seconds === null || seconds === undefined) return 'N/A'
  if (seconds === 0) return '< 0.001s'
  if (seconds < 0.001) return `${(seconds * 1000000).toFixed(2)}μs`
  if (seconds < 1) return `${(seconds * 1000).toFixed(2)}ms`
  return `${seconds.toFixed(3)}s`
}

function formatNumber(num) {
  if (num === null || num === undefined) return 'N/A'
  return num.toLocaleString()
}
</script>

<style scoped>
.plan-tree {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  font-size: 13px;
}

.tree-node-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: fit-content;
  max-width: 100%;
  margin-left: auto;
  margin-right: auto;
}

.tree-node {
  position: relative;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: fit-content;
  min-width: 180px;
}

.tree-node.has-children::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.vertical-line {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.horizontal-line {
  display: none;
}

.children-container {
  position: relative;
  display: flex;
  flex-direction: row !important; 
  justify-content: center;
  align-items: flex-start;
  width: fit-content; 
  max-width: 100%; 
  margin-top: 0;
  padding-top: 20px;
  gap: 20px;
  flex-wrap: wrap;
  margin-left: auto;
  margin-right: auto;
}


.children-container:not(.multiple-children):not(.join-children)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.children-container.multiple-children {
  flex-direction: row !important;  
  flex-wrap: nowrap;  
  justify-content: center;
  align-items: flex-start;
  gap: 15px;
  max-width: 100%;
}

.children-container.multiple-children::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.children-container.multiple-children::after {
  display: none;
}

.children-container.multiple-children > .plan-tree {
  position: relative;
}

.children-container.multiple-children > .plan-tree::before {
  content: '';
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.children-container.multiple-children > .plan-tree:first-child::after {
  content: '';
  position: absolute;
  top: -20px;
  left: 50%;
  right: -8px;
  height: 2px;
  background: #999;
  z-index: 0;
}

.children-container.multiple-children > .plan-tree:last-child::after {
  content: '';
  position: absolute;
  top: -20px;
  left: -8px;
  right: 50%;
  height: 2px;
  background: #999;
  z-index: 0;
}

.children-container.multiple-children > .plan-tree:not(:first-child):not(:last-child)::after {
  content: '';
  position: absolute;
  top: -20px;
  left: -8px;
  right: -8px;
  height: 2px;
  background: #999;
  z-index: 0;
}

.children-container.join-children {
  flex-direction: row !important;  
  flex-wrap: nowrap; 
  justify-content: center;
  align-items: flex-start;
  gap: 15px;
  max-width: 100%;
  padding-top: 40px; 
}

.children-container.join-children::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px; 
  background: #999;
  z-index: 0;
}

.children-container.join-children::after {
  content: '';
  position: absolute;
  top: 20px; 
  left: 100px;
  right: 91px;
  height: 2px;
  background: #999;
  z-index: 0;
}

.children-container.join-children > .plan-tree {
  position: relative;
}

.children-container.join-children > .plan-tree::before {
  content: '';
  position: absolute;
  top: -20px;  
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.children-container.join-children > .plan-tree {
  flex: 0 0 auto;
}

.children-container.multiple-children > .plan-tree {
  flex: 0 0 auto;
}

.node-content {
  border: 2px solid #e8e8e8;
  border-radius: 10px;
  padding: 10px 12px;  
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-width: 80px;
  max-width: 200px;
  width: fit-content;
  text-align: center;
  min-height: auto;
  position: relative;
  z-index: 1;
  transition: box-shadow 0.15s ease;
}

.node-content:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.node-projection {
  border-color: #FFB020;
  background: linear-gradient(135deg, #FFFBF0 0%, #FFF8E1 100%);
}

.node-aggregate {
  border-color: #FF6F00;
  background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
}

.node-filter {
  border-color: #E91E63;
  background: linear-gradient(135deg, #FCE4EC 0%, #F8BBD0 100%);
}

.node-sem-filter {
  border-color: #2196F3;
  background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
}

.node-join {
  border-color: #9C27B0;
  background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%);
}

.node-scan {
  border-color: #4CAF50;
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
  min-width: 80px;
  min-height: auto;
}

.node-default {
  border-color: #BDBDBD;
  background: linear-gradient(135deg, #FAFAFA 0%, #F5F5F5 100%);
}

.node-header {
  font-weight: 600;
  margin-bottom: 0;
  color: #1d1d1f;
}

.node-name {
  font-size: 14px; 
  color: #007aff;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.node-hover-hint {
  display: block;
  font-size: 9px;
  font-weight: 400;
  color: #aaa;
  letter-spacing: 0.3px;
  margin-top: 4px;
  text-align: center;
  transition: opacity 0.15s ease, max-height 0.15s ease;
  overflow: hidden;
  max-height: 20px;
}

.node-content:hover .node-hover-hint {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  pointer-events: none;
}

.node-details-wrap {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  transition: max-height 0.25s ease, opacity 0.2s ease;
}

.node-content:hover .node-details-wrap {
  max-height: 1000px;
  opacity: 1;
}

.node-content:hover .node-header {
  margin-bottom: 6px;
}

.node-content--path-operator .node-details-wrap {
  max-height: 1000px;
  opacity: 1;
}

.node-content--path-operator .node-header {
  margin-bottom: 6px;
}


.node-detail {
  margin-top: 8px;
  padding: 6px 8px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
  font-size: 11px;  
  color: #86868b;
  line-height: 1.4; 
  word-break: break-word;
  overflow-wrap: break-word;
}

.node-extra-info {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 11px;
}

.info-item {
  margin: 5px 0;
  line-height: 1.5;
}

.info-key {
  font-weight: 600;
  color: #86868b;
  margin-right: 6px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  color: #1d1d1f;
  word-break: break-word;
  font-weight: 500;
}

.info-item-expression .info-value {
  display: block;
  max-height: 3em;
  overflow-y: auto;
  overflow-x: hidden;
  line-height: 1.5;
  padding-right: 4px;
}

.info-item-expression .info-value::-webkit-scrollbar {
  width: 6px;
}

.info-item-expression .info-value::-webkit-scrollbar-thumb {
  background: #d1d1d6;
  border-radius: 3px;
}

.node-profiling {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 11px;
}

.profiling-item {
  margin: 6px 0;
  line-height: 1.5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profiling-label {
  font-weight: 600;
  color: #007aff;
  margin-right: 8px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.profiling-value {
  color: #1d1d1f;
  font-weight: 600;
}

.profiling-semantic {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
}

.path-label {
  display: inline-block;
  margin-left: 8px;
  padding: 3px 8px;
  background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
  color: #1976D2;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.best-path-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 3px 8px;
  background: linear-gradient(135deg, #FFD700 0%, #FFC107 100%);
  color: #1d1d1f;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(255, 193, 7, 0.3);
}

.path-expression {
  margin-top: 10px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  font-size: 11px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.path-expression-label {
  font-weight: 700;
  color: #86868b;
  margin-bottom: 6px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.path-expression-content {
  color: #1d1d1f;
  line-height: 1.5;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
}

.path-details {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  font-size: 11px;
}

.node-profiling > .path-details:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.node-content[data-path-index] {
  border-width: 2px;
  min-width: 210px;
  max-width: 210px;
}


.node-content[data-is-best-path="true"] {
  border-color: #FFD700;
  border-width: 3px;
  background: linear-gradient(135deg, #FFFEF0 0%, #FFF9E6 100%);
  box-shadow: 0 0 16px rgba(255, 215, 0, 0.4), 0 4px 12px rgba(0, 0, 0, 0.1);
}

.children-container.multiplexer-children {
  flex-direction: column !important;
  align-items: stretch;
  gap: 0;
  padding-top: 20px;
}

.path-nodes-multiplexer-layout {
  display: flex;
  flex-direction: row;  
  align-items: flex-start;
  gap: 16px;
  width: 100%;
  max-width: 100%;
  align-self: stretch;
}

.path-nodes-group-wrapper {
  position: relative;
  flex: 1;
  align-self: flex-start;
  min-width: 0;
  border: 2px dashed #BDBDBD;
  border-radius: 12px;
  padding: 16px 16px 20px 16px;
  margin: 0;
  background: linear-gradient(135deg, #FAFAFA 0%, #F5F5F5 100%);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  z-index: 1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: visible;
}

.multiplexer-info-box {
  flex: 0 0 auto;
  align-self: flex-start;
  width: min(240px, 32vw);
  min-width: 200px;
  background: white;
  padding: 10px 14px 14px;
  border: 2px solid #007aff;
  border-radius: 10px;
  font-size: 11px;
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.12);
}

.multiplexer-info-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #007aff;
  margin-bottom: 8px;
}

.multiplexer-info-title {
  display: block;
  font-weight: 700;
  font-size: 15px;
  line-height: 1.2;
  letter-spacing: 0.04em;
}

.multiplexer-info-content--expanded {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: visible;
  opacity: 1;
}

.path-nodes-trees-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.multiplexer-info-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.multiplexer-info-item {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  line-height: 1.5;
}

.multiplexer-info-label {
  font-weight: 600;
  color: #86868b;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.multiplexer-info-value {
  color: #1d1d1f;
  font-weight: 600;
}

.multiplexer-info-highlight {
  color: #34c759;
}

.multiplexer-info-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
  margin: 6px 0;
}

.path-nodes-container {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: flex-start;
  gap: 20px;
  position: relative;
  width: 100%;
  padding-top: 8px;
  padding-bottom: 20px;
}

.path-nodes-row-second {
  padding-top: 0;
  padding-bottom: 20px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
  margin-top: 0;
}

.path-nodes-container > * {
  position: relative;
}

.path-nodes-group-wrapper .vertical-line {
  display: none !important;
}

.path-nodes-group-wrapper .path-nodes-container > .plan-tree::before,
.path-nodes-group-wrapper .path-nodes-container > .plan-tree::after {
  content: none !important;
  display: none !important;
}

.path-nodes-group-wrapper .children-container.multiple-children::before,
.path-nodes-group-wrapper .children-container.multiple-children > .plan-tree::before,
.path-nodes-group-wrapper .children-container.multiple-children > .plan-tree::after {
  content: none !important;
  display: none !important;
}

.path-nodes-group-wrapper .children-container:not(.multiple-children):not(.join-children)::before {
  content: none !important;
}

.path-nodes-group-wrapper .children-container.join-children::before,
.path-nodes-group-wrapper .children-container.join-children::after,
.path-nodes-group-wrapper .children-container.join-children > .plan-tree::before {
  content: none !important;
  display: none !important;
}

.path-nodes-group-wrapper::before {
  content: none;
}


.downstream-nodes-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  width: 100%;
  padding-top: 20px;
  margin-top: 0;
}

.downstream-nodes-container {
  position: relative;
}

.downstream-nodes-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.downstream-nodes-container > .plan-tree {
  position: relative;
}

.downstream-nodes-container > .plan-tree::before {
  content: '';
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}

.children-container.multiplexer-with-downstream {
  position: relative;
}

.children-container.multiplexer-with-downstream::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 20px;
  background: #999;
  z-index: 0;
}
</style>

