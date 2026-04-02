<template>
  <div v-if="paths.length === 0" class="no-data-message">
    No path data available
  </div>
  <div v-else class="chart-wrapper">
      <svg width="100%" :height="height" class="pareto-chart" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="xMidYMid meet">
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
          </pattern>
        </defs>
        <text 
          :x="yAxisTitleX" 
          :y="height / 2" 
          text-anchor="middle" 
          font-size="13" 
          font-weight="600"
          fill="#333"
          :transform="`rotate(-90, ${yAxisTitleX}, ${height / 2})`"
        >
          Latency (ms)
        </text>

        <g class="chart-body" :transform="`translate(${chartBodyOffsetX}, 0)`">
        <rect
          :x="-chartBodyOffsetX"
          y="0"
          :width="width + chartBodyOffsetX"
          :height="height"
          fill="url(#grid)"
        />
        
        <g class="axes">
          <line 
            :x1="padding" 
            :y1="height - padding" 
            :x2="width - padding" 
            :y2="height - padding" 
            stroke="#333" 
            stroke-width="2"
          />
          <line 
            :x1="padding" 
            :y1="padding" 
            :x2="padding" 
            :y2="height - padding" 
            stroke="#333" 
            stroke-width="2"
          />
          
          <text 
            :x="width / 2" 
            :y="height - 12" 
            text-anchor="middle" 
            font-size="13" 
            font-weight="600"
            fill="#333"
          >
            Cost(10^-3 USD)
          </text>
          
          <template v-for="(tick, i) in xTicks" :key="`x-${i}`">
            <line 
              :x1="scaleX(tick)" 
              :y1="height - padding - 6" 
              :x2="scaleX(tick)" 
              :y2="height - padding" 
              stroke="#333" 
              stroke-width="1.5"
            />
            <text 
              :x="scaleX(tick)" 
              :y="height - padding + 18" 
              text-anchor="middle" 
              font-size="11" 
              fill="#666"
            >
              {{ formatNumber(tick * COST_DISPLAY_SCALE) }}
            </text>
          </template>
          
          <template v-for="(tick, i) in yTicks" :key="`y-${i}`">
            <line 
              :x1="padding" 
              :y1="scaleY(tick)" 
              :x2="padding + 6" 
              :y2="scaleY(tick)" 
              stroke="#333" 
              stroke-width="1.5"
            />
            <text 
              :x="padding - 10" 
              :y="scaleY(tick) + 4" 
              text-anchor="end" 
              font-size="11" 
              fill="#666"
            >
              {{ formatNumber(tick) }}
            </text>
          </template>
        </g>
        
        <polyline 
          v-if="paretoFrontier.length > 0"
          :points="paretoFrontierPoints"
          fill="none"
          stroke="#ff6b6b"
          stroke-width="2.5"
          stroke-dasharray="7,5"
        />
        
        <g class="data-points">
          <circle
            v-for="(path, index) in paths"
            :key="`path-${index}`"
            :cx="scaleX(path.cost)"
            :cy="scaleY(path.latency)"
            :r="path.isBest ? 7.5 : 5"
            :fill="path.isBest ? '#ffd700' : (path.isPareto ? '#ff6b6b' : '#4dabf7')"
            :stroke="path.isBest ? '#ff8c00' : '#fff'"
            :stroke-width="path.isBest ? 2.5 : 1.5"
            class="data-point"
            @mouseenter="showTooltip($event, path)"
            @mouseleave="hideTooltip"
          />
          <text
            v-for="(path, index) in paths"
            :key="`label-${index}`"
            :x="scaleX(path.cost) + 10"
            :y="scaleY(path.latency) - 9"
            font-size="11"
            fill="#333"
            font-weight="600"
          >
            P{{ path.index }}
          </text>
        </g>
        
        <g
          class="legend"
          :transform="`translate(${width - LEGEND_W - 12 - chartBodyOffsetX}, ${padding - 70})`"
        >
          <rect :width="LEGEND_W" :height="LEGEND_H" rx="4" fill="white" stroke="#ccc" stroke-width="1.25" opacity="0.95"/>
          <text x="12" y="22" font-size="12" font-weight="600" fill="#333">Legend</text>
          <circle cx="12" cy="38" r="5" fill="#ffd700" stroke="#ff8c00" stroke-width="1.25"/>
          <text x="24" y="42" font-size="11" fill="#333">Best Path</text>
          <circle cx="12" cy="54" r="5" fill="#ff6b6b"/>
          <text x="24" y="58" font-size="11" fill="#333">Pareto Frontier</text>
          <circle cx="12" cy="70" r="5" fill="#4dabf7"/>
          <text x="24" y="74" font-size="11" fill="#333">Other Paths</text>
        </g>
        </g>
      </svg>
      
      <div
        v-if="tooltip.visible && tooltip.path"
        class="tooltip"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      >
        <div class="tooltip-content">
          <div class="tooltip-title">Path {{ tooltip.path.index }}</div>
          <div class="tooltip-item">
            <span class="tooltip-label">Cost:</span>
            <span class="tooltip-value">{{ formatNumber((tooltip.path.cost ?? 0) * COST_DISPLAY_SCALE) }}</span>
          </div>
          <div class="tooltip-item">
            <span class="tooltip-label">Latency:</span>
            <span class="tooltip-value">{{ formatNumber(tooltip.path.latency ?? 0) }} ms</span>
          </div>
          <div class="tooltip-item" v-if="tooltip.path.accuracy != null">
            <span class="tooltip-label">Accuracy:</span>
            <span class="tooltip-value">{{ formatTooltipAccuracy(tooltip.path.accuracy) }}</span>
          </div>
          <div class="tooltip-item" v-if="tooltip.path.type">
            <span class="tooltip-label">Type:</span>
            <span class="tooltip-value">{{ tooltip.path.type }}</span>
          </div>
        </div>
      </div>
    </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  profilingTree: {
    type: Object,
    default: null
  }
})

const width = 800
const height = 500
const padding = 78
const chartBodyOffsetX = 36
const yAxisTitleX = 22

const LEGEND_W = 158
const LEGEND_H = 88

const COST_DISPLAY_SCALE = 1e-3

const paths = ref([])
const paretoFrontier = ref([])
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  path: null
})

function extractPathsFromMultiplexerEI(ei) {
  const total = parseInt(ei.total_paths || ei.individual_path_count || ei.paths_count || '0')
  if (total > 0 && ei['path_0_cost'] !== undefined) {
    const bestIdx = parseInt(ei.best_path_index ?? '-1')
    const paths = []
    for (let i = 0; i < total; i++) {
      const cost    = parseFloat(ei[`path_${i}_cost`]     || '0')
      const latency = parseFloat(ei[`path_${i}_exploration_time_ms`] || ei[`path_${i}_latency`] || '0')
      if (cost > 0 || latency > 0) {
        paths.push({
          index:    i,
          cost:     cost,
          latency:  latency,
          accuracy: parseFloat(ei[`path_${i}_accuracy`] || '0'),
          type:     null,
          isBest:   i === bestIdx,
          isPareto: false
        })
      }
    }
    return paths
  }
  return []
}

function extractPaths(node) {
  const result = []
  
  if (!node || typeof node !== 'object') {
    return result
  }
  
  const extraInfo = node.extra_info || {}
  const nodeName  = (node.operator_name || node.operator_type || '').toUpperCase()
  const isMultiplexer = nodeName.includes('MULTIPLEXER')

  if (extraInfo.path_index !== undefined || extraInfo.is_path_node === true) {
    const cost    = parseFloat(extraInfo.cost)      || 0
    const latency = parseFloat(extraInfo.latency_ms) || 0
    if (cost > 0 || latency > 0) {
      result.push({
        index:    extraInfo.path_index !== undefined ? extraInfo.path_index : '?',
        cost:     cost,
        latency:  latency,
        accuracy: extraInfo.accuracy,
        type:     extraInfo.path_type,
        isBest:   extraInfo.is_best === true || extraInfo.is_best === 'true',
        isPareto: false
      })
    }
    return result
  }

  if (isMultiplexer) {
    const children = node.children || []
    const hasPathNodeChildren = children.some(
      c => c.extra_info && (c.extra_info.is_path_node === true || c.extra_info.path_index !== undefined)
    )

    if (hasPathNodeChildren) {
      for (const child of children) {
        result.push(...extractPaths(child))
      }
    } else { 
      const fromEI = extractPathsFromMultiplexerEI(extraInfo)
      result.push(...fromEI)
      for (const child of children) {
        result.push(...extractPaths(child))
      }
    }
    return result
  }

  const children = node.children || []
  for (const child of children) {
    result.push(...extractPaths(child))
  }
  
  return result
}

function calculateParetoFrontier(paths) {
  if (paths.length === 0) return []
  
  const paretoPoints = []
  
  for (const point of paths) {
    let isPareto = true
    
    for (const other of paths) {
      if (other !== point) {
        if (other.cost <= point.cost && other.latency <= point.latency &&
            (other.cost < point.cost || other.latency < point.latency)) {
          isPareto = false
          break
        }
      }
    }
    
    if (isPareto) {
      paretoPoints.push(point)
      point.isPareto = true
    }
  }
  
  return paretoPoints.sort((a, b) => a.cost - b.cost)
}

const xRange = computed(() => {
  if (paths.value.length === 0) return { min: 0, max: 100 }
  const costs = paths.value.map(p => p.cost)
  const min = Math.min(...costs)
  const max = Math.max(...costs)
  const span    = max - min
  const padding = span > 0 ? span * 0.2 : Math.max(max * 0.1, 0.001)
  return { min: Math.max(0, min - padding), max: max + padding }
})

const yRange = computed(() => {
  if (paths.value.length === 0) return { min: 0, max: 1000 }
  const latencies = paths.value.map(p => p.latency)
  const min = Math.min(...latencies)
  const max = Math.max(...latencies)
  const span    = max - min
  const padding = span > 0 ? span * 0.2 : Math.max(max * 0.05, 1)
  return { min: Math.max(0, min - padding), max: max + padding }
})

function scaleX(value) {
  const range = xRange.value
  return padding + ((value - range.min) / (range.max - range.min)) * (width - 2 * padding)
}

function scaleY(value) {
  const range = yRange.value
  return height - padding - ((value - range.min) / (range.max - range.min)) * (height - 2 * padding)
}

const xTicks = computed(() => {
  const range = xRange.value
  const step = (range.max - range.min) / 5
  const ticks = []
  for (let i = 0; i <= 5; i++) {
    ticks.push(range.min + step * i)
  }
  return ticks
})

const yTicks = computed(() => {
  const range = yRange.value
  const step = (range.max - range.min) / 5
  const ticks = []
  for (let i = 0; i <= 5; i++) {
    ticks.push(range.min + step * i)
  }
  return ticks
})

const paretoFrontierPoints = computed(() => {
  if (paretoFrontier.value.length === 0) return ''
  return paretoFrontier.value.map(p => `${scaleX(p.cost)},${scaleY(p.latency)}`).join(' ')
})

function showTooltip(event, path) {
  tooltip.value = {
    visible: true,
    x: event.clientX - event.currentTarget.closest('.chart-wrapper').getBoundingClientRect().left + 20,
    y: event.clientY - event.currentTarget.closest('.chart-wrapper').getBoundingClientRect().top - 20,
    path: path
  }
}

function hideTooltip() {
  tooltip.value.visible = false
}


function formatNumber(value) {
  if (value === null || value === undefined) return '0'
  if (typeof value === 'string') {
    const num = parseFloat(value)
    if (isNaN(num)) return value
    value = num
  }
  if (typeof value !== 'number' || Number.isNaN(value)) return '—'
  if (value >= 1000) {
    return value.toFixed(0)
  } else if (value >= 1) {
    return value.toFixed(2)
  } else {
    return value.toFixed(4)
  }
}

function formatTooltipAccuracy(acc) {
  if (acc == null || acc === '') return '—'
  const n = typeof acc === 'number' ? acc : parseFloat(acc)
  if (Number.isNaN(n)) return String(acc)
  if (n > 0 && n <= 1) return `${(n * 100).toFixed(1)}%`
  return String(acc)
}

watch(() => props.profilingTree, (newTree) => {
  if (newTree) {
    paths.value = extractPaths(newTree)
    paretoFrontier.value = calculateParetoFrontier(paths.value)
  } else {
    paths.value = []
    paretoFrontier.value = []
  }
}, { immediate: true })
</script>

<style scoped>
.no-data-message {
  text-align: center;
  color: #86868b;
  padding: 40px 16px;
  font-style: italic;
  font-size: 13px;
  background: #fafafa;
  border-radius: 8px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-wrapper {
  position: relative;
  width: 100%;
  overflow: hidden;
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.pareto-chart {
  display: block;
  margin: 0 auto;
  max-width: 60%;
  height: auto;
}

.data-point {
  cursor: pointer;
  transition: all 0.2s ease;
}

.data-point:hover {
  r: 9;
  filter: drop-shadow(0 0 6px rgba(0, 122, 255, 0.5));
}

.tooltip {
  position: absolute;
  background: #fff;
  color: #1d1d1f;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 12px;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(0, 0, 0, 0.08);
  max-width: 300px;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-title {
  font-weight: 600;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  padding-bottom: 6px;
  font-size: 13px;
  color: #1d1d1f;
}

.tooltip-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
}

.tooltip-label {
  color: #636366;
  font-size: 11px;
  flex-shrink: 0;
}

.tooltip-value {
  font-weight: 600;
  color: #1d1d1f;
  font-size: 11px;
  text-align: right;
  min-width: 0;
}

.legend {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #1d1d1f;
}

.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentColor;
}

@media (max-width: 768px) {
  .chart-wrapper {
    padding: 12px;
  }
}
</style>
