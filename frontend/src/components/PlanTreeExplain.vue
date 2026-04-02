
<template>
  <div class="plan-tree plan-tree--explain">
    <div class="tree-node-wrapper">
      <div class="tree-node" :class="{ 'has-children': hasChildren }">
        <div v-if="depth > 0" class="vertical-line"></div>
        <div v-if="hasChildren" class="horizontal-line"></div>

        <div class="node-content" :class="nodeClass">
          <div class="node-header">
            <span class="node-name">{{ nodeLabel }}</span>
          </div>

          <div v-if="hasAnyDetail" class="node-details-wrap">
            <div v-if="nodeDetail && !hasExtraInfo" class="node-detail">
              {{ nodeDetail }}
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

      <div
        v-if="hasChildren"
        class="children-container"
        :class="{
          'multiple-children': childrenNodes.length > 1,
          'join-children': isJoinNode && childrenNodes.length > 1
        }"
        :data-children-count="childrenNodes.length"
      >
        <PlanTreeExplain
          v-for="(child, index) in childrenNodes"
          :key="child.id || index"
          :node="child"
          :depth="depth + 1"
        />
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

const extraInfo = computed(() => {
  return props.node.extra_info || {}
})

const filteredExtraInfo = computed(() => {
  const info = extraInfo.value
  if (!info || typeof info !== 'object') return {}

  const filtered = {}
  for (const [key, value] of Object.entries(info)) {
    if (typeof value === 'string' && /={8,}/.test(value)) continue
    filtered[key] = value
  }
  return filtered
})

const hasExtraInfo = computed(() => {
  const info = filteredExtraInfo.value
  return info && Object.keys(info).length > 0
})


const hasAnyDetail = computed(() => {
  return !!(nodeDetail.value || hasExtraInfo.value)
})

const hasChildren = computed(() => {
  return props.node.children && Array.isArray(props.node.children) && props.node.children.length > 0
})

const childrenNodes = computed(() => {
  if (props.node.children && Array.isArray(props.node.children)) {
    const validChildren = props.node.children.filter(child => {
      return child !== null && child !== undefined && typeof child === 'object'
    })
    
    if (validChildren.length > 1) {
      console.log(`[PlanTreeExplain] Node "${nodeLabel.value}" has ${validChildren.length} children:`, 
                  validChildren.map(c => c.label || c.name || c.operator_name || 'Unknown'))
    }
    return validChildren
  }
  return []
})

function formatKey(key) {
  return key.replace(/_/g, ' ').toUpperCase()
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
  padding: 10px 14px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  min-width: 120px;
  max-width: 240px;
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
  min-width: 120px;
  max-width: 180px;
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
  letter-spacing: 0.2px;
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

.node-detail {
  margin-top: 8px;
  font-size: 11px;
  color: #4a7c6e;
  line-height: 1.6;
  word-break: break-word;
  overflow-wrap: break-word;
  text-align: center;
}

.node-extra-info {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  font-size: 11px;
  text-align: center;
}

.info-item {
  margin: 5px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
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
  font-weight: 500;
}

.info-item-expression .info-value {
  line-height: 1.5;
}
</style>

