<template>
  <template v-if="plan?.format === 'json'">
    <template v-if="plan.unoptimized || plan.optimized || plan.physical">
      <div class="panel explain-results-panel">
        <h3>Explain Results</h3>
        
        <div class="explain-tree-section">
          <div class="explain-tree-container">
            <div class="plans-container">
        <div class="plan-column" v-if="plan.unoptimized">
          <div class="plan-header">
            <h3>Unoptimized Logical Plan</h3>
          </div>
          <div class="plan-tree-container">
            <PlanTreeExplain 
              :node="plan.unoptimized" 
              :depth="0" 
            />
          </div>
        </div>
        
        <div class="plan-column" v-if="plan.optimized">
          <div class="plan-header">
            <h3>Optimized Logical Plan</h3>
          </div>
          <div class="plan-tree-container">
            <PlanTreeExplain 
              :node="plan.optimized" 
              :depth="0" 
            />
          </div>
        </div>
        
        <div class="plan-column" v-if="plan.physical">
          <div class="plan-header">
            <h3>Physical Plan</h3>
          </div>
          <div class="plan-tree-container">
            <PlanTreeExplain 
              :node="plan.physical" 
              :depth="0" 
            />
          </div>
        </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    
    <template v-else-if="plan.plans && Array.isArray(plan.plans) && plan.plans.length > 0">
      <div class="plan-section" v-for="(planData, index) in plan.plans" :key="index">
        <div class="plan-header">
          <h3>{{ getPlanTitle(planData, index) }}</h3>
        </div>
        <div class="plan-tree-container">
          <PlanTreeExplain 
            v-if="Array.isArray(planData) && planData.length > 0 && planData[0] && planData[0].name"
            :node="planData[0]" 
            :depth="0" 
          />
          <PlanTreeExplain 
            v-else-if="planData && typeof planData === 'object' && planData.name"
            :node="planData" 
            :depth="0" 
          />
          <div v-else class="error-info">
            <p>无法解析计划数据 (索引 {{ index }})</p>
            <p>类型: {{ typeof planData }}</p>
            <p v-if="Array.isArray(planData)">是数组，长度: {{ planData.length }}</p>
            <p v-if="planData && typeof planData === 'object'">对象键: {{ Object.keys(planData).join(', ') }}</p>
            <details>
              <summary>查看原始数据</summary>
              <pre>{{ pretty(planData) }}</pre>
            </details>
          </div>
        </div>
      </div>
    </template>
    
    <template v-else-if="plan.raw && Array.isArray(plan.raw) && plan.raw.length > 0">
      <div class="plan-section" v-for="(planData, index) in plan.raw" :key="index">
        <div class="plan-header">
          <h3>{{ getPlanTitle(planData, index) }}</h3>
        </div>
        <div class="plan-tree-container">
          <PlanTreeExplain 
            v-if="Array.isArray(planData) && planData.length > 0 && planData[0] && planData[0].name"
            :node="planData[0]" 
            :depth="0" 
          />
          <PlanTreeExplain 
            v-else-if="planData && typeof planData === 'object' && planData.name"
            :node="planData" 
            :depth="0" 
          />
        </div>
      </div>
    </template>
    
    <template v-else-if="isArrayFormat && planArray.length > 0">
      <div class="plan-section" v-for="(planData, index) in planArray" :key="index">
        <div class="plan-header">
          <h3>{{ getPlanTitle(planData, index) }}</h3>
        </div>
        <div class="plan-tree-container">
          <PlanTreeExplain :node="planData" :depth="0" />
        </div>
      </div>
    </template>
    
    <template v-else>
      <div class="plan-section" v-if="plan.logical_plan || plan.unoptimized_logical_plan">
        <div class="plan-header">
          <h3>Unoptimized Logical Plan</h3>
        </div>
        <div class="plan-tree-container">
          <PlanTreeExplain 
            :node="plan.logical_plan || plan.unoptimized_logical_plan" 
            :depth="0" 
          />
        </div>
      </div>
      
      <div class="plan-section" v-if="plan.optimized_logical_plan">
        <div class="plan-header">
          <h3>Optimized Logical Plan</h3>
        </div>
        <div class="plan-tree-container">
          <PlanTreeExplain :node="plan.optimized_logical_plan" :depth="0" />
        </div>
      </div>
      
      <div class="plan-section" v-if="plan.physical_plan">
        <div class="plan-header">
          <h3>Physical Plan</h3>
        </div>
        <div class="plan-tree-container">
          <PlanTreeExplain :node="plan.physical_plan" :depth="0" />
        </div>
      </div>
      
      <div class="plan-section" v-if="plan.raw && typeof plan.raw === 'object' && plan.raw.name && !Array.isArray(plan.raw)">
        <div class="plan-header">
          <h3>Execution Plan</h3>
        </div>
        <div class="plan-tree-container">
          <PlanTreeExplain :node="plan.raw" :depth="0" />
        </div>
      </div>
      
      <div class="plan-section" v-if="!hasTreeData && (!plan.raw || (typeof plan.raw !== 'object' || !plan.raw.name))">
        <h3>Raw Plan Data (Debug Mode)</h3>
        <details>
          <summary>点击查看原始数据</summary>
          <pre>{{ pretty(plan.raw || plan) }}</pre>
        </details>
      </div>
    </template>
  </template>

  <template v-else>
    <div class="plan-section" v-if="plan?.format === 'json' && plan?.text">
      <h3>Execution Plan (Raw JSON)</h3>
      <details>
        <summary>点击展开查看原始 JSON 数据</summary>
        <pre class="text">{{ plan.text }}</pre>
      </details>
      <div v-if="plan.parse_error || plan.process_error" class="error-info">
        <strong>注意：</strong> {{ plan.parse_error || plan.process_error }}
      </div>
    </div>
    <div class="plan-section" v-else>
      <h3>EXPLAIN (Text)</h3>
      <pre class="text">{{ plan?.text }}</pre>
    </div>
  </template>
</template>

<script setup>
import { computed } from 'vue'
import PlanTreeExplain from './PlanTreeExplain.vue'

const props = defineProps({
  plan: { type: Object, required: true }
})

const isArrayFormat = computed(() => {
  if (!props.plan) return false
  if (Array.isArray(props.plan.raw)) {
    return props.plan.raw.length > 0 && props.plan.raw[0] && typeof props.plan.raw[0] === 'object' && 'name' in props.plan.raw[0]
  }
  if (Array.isArray(props.plan.logical_plan)) {
    return props.plan.logical_plan.length > 0 && props.plan.logical_plan[0] && typeof props.plan.logical_plan[0] === 'object' && 'name' in props.plan.logical_plan[0]
  }
  if (Array.isArray(props.plan.physical_plan)) {
    return props.plan.physical_plan.length > 0 && props.plan.physical_plan[0] && typeof props.plan.physical_plan[0] === 'object' && 'name' in props.plan.physical_plan[0]
  }
  if (props.plan.raw && typeof props.plan.raw === 'object' && 'name' in props.plan.raw) {
    return true
  }
  if (props.plan.logical_plan && typeof props.plan.logical_plan === 'object' && 'name' in props.plan.logical_plan) {
    return true
  }
  if (props.plan.physical_plan && typeof props.plan.physical_plan === 'object' && 'name' in props.plan.physical_plan) {
    return true
  }
  return false
})

const planArray = computed(() => {
  if (Array.isArray(props.plan.raw)) {
    return props.plan.raw
  }
  if (Array.isArray(props.plan.logical_plan)) {
    return props.plan.logical_plan
  }
  if (props.plan.raw && typeof props.plan.raw === 'object' && 'name' in props.plan.raw) {
    return [props.plan.raw]
  }
  if (props.plan.logical_plan && typeof props.plan.logical_plan === 'object' && 'name' in props.plan.logical_plan) {
    return [props.plan.logical_plan]
  }
  if (props.plan.physical_plan && typeof props.plan.physical_plan === 'object' && 'name' in props.plan.physical_plan) {
    return [props.plan.physical_plan]
  }
  return []
})

const hasTreeData = computed(() => {
  if (props.plan.unoptimized || props.plan.optimized || props.plan.physical) {
    return true
  }
  if (props.plan.plans && Array.isArray(props.plan.plans) && props.plan.plans.length > 0) {
    return true
  }
  if (props.plan.raw && Array.isArray(props.plan.raw) && props.plan.raw.length > 0) {
    const first = props.plan.raw[0]
    if (Array.isArray(first) && first.length > 0 && first[0] && first[0].name) {
      return true
    }
    if (first && typeof first === 'object' && first.name) {
      return true
    }
  }
  return props.plan.logical_plan || props.plan.unoptimized_logical_plan || 
         props.plan.optimized_logical_plan || props.plan.physical_plan || isArrayFormat.value
})

function getPlanTitle(planData, index) {
  if (planData.plan_type) {
    return planData.plan_type
  }
  if (index === 0) return 'Unoptimized Logical Plan'
  if (index === 1) return 'Optimized Logical Plan'
  if (index === 2) return 'Physical Plan'
  return `Plan ${index + 1}`
}

function pretty(obj) {
  try { return JSON.stringify(obj, null, 2) } catch (e) { return String(obj) }
}
</script>

<style scoped>
.plans-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
  padding: 0;
  margin-top: 0;
}

@media (min-width: 1200px) {
  .plans-container {
    grid-template-columns: repeat(3, 1fr);
  }
}

.plan-column {
  display: flex;
  flex-direction: column;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px;
  background: #f8f9fa;
  min-height: 450px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.plan-column:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}

.plan-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  text-align: center;
  position: relative;
}

.plan-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  height: 3px;
  background: #007aff;
  border-radius: 3px;
  opacity: 0.8;
}

.plan-header h3 { 
  margin: 0; 
  font-size: 16px; 
  font-weight: 700; 
  color: #1d1d1f;
  letter-spacing: -0.2px;
}

.plan-subtitle {
  font-size: 13px;
  color: #86868b;
  font-weight: 500;
}

.plan-tree-container {
  flex: 1;
  padding: 0;
  background: transparent;
  overflow-y: auto;
  overflow-x: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  min-width: 0;
}

.plan-section { 
  margin-top: 16px; 
  padding: 24px; 
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 16px; 
  background: #f8f9fa;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

h3 { 
  margin: 0 0 16px 0; 
  font-size: 16px; 
  font-weight: 600; 
  color: #1d1d1f; 
}

pre { 
  white-space: pre-wrap; 
  word-break: break-word; 
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; 
  font-size: 13px; 
  margin: 0; 
  line-height: 1.6;
}

.text { 
  background: #fafafa; 
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.error-info {
  margin-top: 12px;
  padding: 12px 16px;
  background: #fff3f3;
  border: 1px solid #ffdddd;
  border-radius: 8px;
  color: #d32f2f;
  font-size: 13px;
}

details {
  margin-top: 12px;
}

details summary {
  cursor: pointer;
  color: #007aff;
  font-weight: 600;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f0f0f0;
  border-radius: 6px;
  transition: background 0.2s ease;
}

details summary:hover {
  background: #e8e8e8;
}

@media (max-width: 768px) {
  .plans-container {
    grid-template-columns: 1fr;
  }
  
  .plan-column {
    min-height: 300px;
  }
}
</style>
