<template>
  <div class="agent-workflow">
    <div class="workflow-header">
      <h3>智能体工作流</h3>
      <div class="header-actions">
        <el-button size="small" @click="clearWorkflow">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
        <el-button size="small" @click="toggleAutoScroll">
          <el-icon><Position /></el-icon>
          {{ autoScroll ? '停止滚动' : '自动滚动' }}
        </el-button>
      </div>
    </div>
    
    <div class="workflow-content">
      <!-- 当前状态 -->
      <div class="current-status">
        <div class="status-item">
          <span class="status-label">当前智能体:</span>
          <span class="status-value">{{ currentAgent || '未选择' }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">执行状态:</span>
          <el-tag :type="getStatusType(executionStatus)" size="small">
            {{ getStatusText(executionStatus) }}
          </el-tag>
        </div>
        <div class="status-item">
          <span class="status-label">执行时间:</span>
          <span class="status-value">{{ formatDuration(executionTime) }}</span>
        </div>
      </div>
      
      <!-- 工作流步骤 -->
      <div class="workflow-steps" ref="stepsContainer">
        <div 
          v-for="(step, index) in workflowSteps" 
          :key="step.id"
          :class="['workflow-step', step.status, { active: step.status === 'running' }]"
        >
          <div class="step-header">
            <div class="step-icon">
              <el-icon v-if="step.status === 'pending'" class="pending-icon"><Clock /></el-icon>
              <el-icon v-else-if="step.status === 'running'" class="running-icon"><Loading /></el-icon>
              <el-icon v-else-if="step.status === 'completed'" class="completed-icon"><Check /></el-icon>
              <el-icon v-else-if="step.status === 'failed'" class="failed-icon"><Close /></el-icon>
            </div>
            <div class="step-info">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-time">{{ formatTime(step.timestamp) }}</div>
            </div>
            <div class="step-duration" v-if="step.duration">
              {{ formatDuration(step.duration) }}
            </div>
          </div>
          
          <div class="step-content" v-if="step.description || step.details">
            <p v-if="step.description" class="step-description">{{ step.description }}</p>
            
            <!-- 详细信息 -->
            <div v-if="step.details" class="step-details">
              <!-- API调用详情 -->
              <div v-if="step.type === 'api_call'" class="api-details">
                <div class="detail-item">
                  <span class="detail-label">接口:</span>
                  <span class="detail-value">{{ step.details.endpoint }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">方法:</span>
                  <span class="detail-value">{{ step.details.method }}</span>
                </div>
                <div v-if="step.details.response_time" class="detail-item">
                  <span class="detail-label">响应时间:</span>
                  <span class="detail-value">{{ step.details.response_time }}ms</span>
                </div>
              </div>
              
              <!-- 数据处理详情 -->
              <div v-else-if="step.type === 'data_process'" class="process-details">
                <div class="detail-item">
                  <span class="detail-label">处理类型:</span>
                  <span class="detail-value">{{ step.details.process_type }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">输入数据:</span>
                  <span class="detail-value">{{ step.details.input_size }} 条</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">输出数据:</span>
                  <span class="detail-value">{{ step.details.output_size }} 条</span>
                </div>
              </div>
              
              <!-- 知识库查询详情 -->
              <div v-else-if="step.type === 'knowledge_query'" class="knowledge-details">
                <div class="detail-item">
                  <span class="detail-label">查询关键词:</span>
                  <span class="detail-value">{{ step.details.keywords }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">匹配结果:</span>
                  <span class="detail-value">{{ step.details.match_count }} 条</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">相似度:</span>
                  <span class="detail-value">{{ step.details.similarity }}%</span>
                </div>
              </div>
              
              <!-- 模型推理详情 -->
              <div v-else-if="step.type === 'model_inference'" class="inference-details">
                <div class="detail-item">
                  <span class="detail-label">模型:</span>
                  <span class="detail-value">{{ step.details.model_name }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">输入Token:</span>
                  <span class="detail-value">{{ step.details.input_tokens }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">输出Token:</span>
                  <span class="detail-value">{{ step.details.output_tokens }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">温度:</span>
                  <span class="detail-value">{{ step.details.temperature }}</span>
                </div>
              </div>
            </div>
            
            <!-- 错误信息 -->
            <div v-if="step.error" class="step-error">
              <el-alert
                :title="step.error.message"
                type="error"
                :description="step.error.details"
                show-icon
                :closable="false"
              />
            </div>
            
            <!-- 输出结果 -->
            <div v-if="step.output" class="step-output">
              <div class="output-header">
                <span class="output-label">输出结果:</span>
                <el-button size="small" text @click="copyOutput(step.output)">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
              </div>
              <div class="output-content">
                <pre>{{ step.output }}</pre>
              </div>
            </div>
          </div>
          
          <!-- 连接线 -->
          <div v-if="index < workflowSteps.length - 1" class="step-connector"></div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="workflowSteps.length === 0" class="empty-workflow">
          <div class="empty-content">
            <el-icon class="empty-icon"><Connection /></el-icon>
            <h4>暂无工作流执行记录</h4>
            <p>开始对话后，智能体的工作流程将在这里显示</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Delete,
  Position,
  Clock,
  Loading,
  Check,
  Close,
  CopyDocument,
  Connection
} from '@element-plus/icons-vue'

// 类型定义
interface WorkflowStepDetails {
  // API调用详情
  endpoint?: string
  method?: string
  response_time?: number
  
  // 数据处理详情
  process_type?: string
  input_size?: number
  output_size?: number
  
  // 知识库查询详情
  keywords?: string
  match_count?: number
  similarity?: number
  
  // 模型推理详情
  model_name?: string
  input_tokens?: number
  output_tokens?: number
  temperature?: number
}

interface WorkflowStepError {
  message: string
  details?: string
  code?: string
}

interface WorkflowStep {
  id: string
  title: string
  description?: string
  type: 'api_call' | 'data_process' | 'knowledge_query' | 'model_inference' | 'condition_check' | 'user_input'
  status: 'pending' | 'running' | 'completed' | 'failed'
  timestamp: string
  duration?: number
  details?: WorkflowStepDetails
  output?: string
  error?: WorkflowStepError
}

// Props
interface Props {
  agentName?: string
  isActive?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  agentName: '',
  isActive: false
})

// 响应式数据
const currentAgent = ref(props.agentName)
const executionStatus = ref<'idle' | 'running' | 'completed' | 'failed'>('idle')
const executionTime = ref(0)
const autoScroll = ref(true)
const stepsContainer = ref<HTMLElement>()
const workflowSteps = ref<WorkflowStep[]>([])

// 模拟数据 - 在实际应用中这些数据会从父组件传入或通过API获取
const sampleSteps: WorkflowStep[] = [
  {
    id: '1',
    title: '接收用户输入',
    description: '用户发送了一条消息："请帮我查询产品信息"',
    type: 'user_input',
    status: 'completed',
    timestamp: new Date(Date.now() - 5000).toISOString(),
    duration: 100,
    output: '用户消息：请帮我查询产品信息'
  },
  {
    id: '2',
    title: '意图识别',
    description: '分析用户消息的意图和实体',
    type: 'model_inference',
    status: 'completed',
    timestamp: new Date(Date.now() - 4500).toISOString(),
    duration: 800,
    details: {
      model_name: 'intent-classifier-v1',
      input_tokens: 15,
      output_tokens: 8,
      temperature: 0.3
    },
    output: '意图：产品查询\n实体：产品信息'
  },
  {
    id: '3',
    title: '知识库查询',
    description: '在产品知识库中搜索相关信息',
    type: 'knowledge_query',
    status: 'completed',
    timestamp: new Date(Date.now() - 3500).toISOString(),
    duration: 1200,
    details: {
      keywords: '产品信息',
      match_count: 5,
      similarity: 85
    },
    output: '找到5条相关产品信息'
  },
  {
    id: '4',
    title: '生成回复',
    description: '基于查询结果生成用户回复',
    type: 'model_inference',
    status: 'running',
    timestamp: new Date(Date.now() - 2000).toISOString(),
    details: {
      model_name: 'gpt-3.5-turbo',
      input_tokens: 256,
      output_tokens: 0,
      temperature: 0.7
    }
  }
]

// 计算属性
const getStatusType = (status: string) => {
  const typeMap = {
    idle: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    idle: '空闲',
    running: '执行中',
    completed: '已完成',
    failed: '执行失败'
  }
  return textMap[status] || status
}

// 方法
const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

const formatDuration = (duration: number) => {
  if (duration < 1000) {
    return `${duration}ms`
  } else if (duration < 60000) {
    return `${(duration / 1000).toFixed(1)}s`
  } else {
    const minutes = Math.floor(duration / 60000)
    const seconds = Math.floor((duration % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }
}

const copyOutput = async (output: string) => {
  try {
    await navigator.clipboard.writeText(output)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const clearWorkflow = () => {
  workflowSteps.value = []
  executionStatus.value = 'idle'
  executionTime.value = 0
}

const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
}

const scrollToBottom = () => {
  if (autoScroll.value && stepsContainer.value) {
    nextTick(() => {
      stepsContainer.value!.scrollTop = stepsContainer.value!.scrollHeight
    })
  }
}

// 添加新步骤
const addStep = (step: WorkflowStep) => {
  workflowSteps.value.push(step)
  scrollToBottom()
}

// 更新步骤状态
const updateStep = (stepId: string, updates: Partial<WorkflowStep>) => {
  const index = workflowSteps.value.findIndex(step => step.id === stepId)
  if (index > -1) {
    workflowSteps.value[index] = { ...workflowSteps.value[index], ...updates }
  }
}

// 模拟工作流执行
const simulateWorkflow = () => {
  if (workflowSteps.value.length > 0) return
  
  executionStatus.value = 'running'
  let stepIndex = 0
  
  const executeNextStep = () => {
    if (stepIndex < sampleSteps.length) {
      const step = { ...sampleSteps[stepIndex] }
      
      if (stepIndex === sampleSteps.length - 1) {
        // 最后一步，保持运行状态
        step.status = 'running'
        delete step.duration
      }
      
      addStep(step)
      stepIndex++
      
      if (stepIndex < sampleSteps.length) {
        setTimeout(executeNextStep, 1000 + Math.random() * 2000)
      } else {
        // 模拟最后一步完成
        setTimeout(() => {
          updateStep(step.id, {
            status: 'completed',
            duration: 1500,
            output: '根据您的查询，我为您找到了以下产品信息：\n\n1. 产品A - 高性能处理器\n2. 产品B - 大容量存储\n3. 产品C - 高清显示屏\n\n您需要了解哪个产品的详细信息呢？'
          })
          executionStatus.value = 'completed'
        }, 2000)
      }
    }
  }
  
  executeNextStep()
}

// 监听props变化
watch(() => props.agentName, (newName) => {
  currentAgent.value = newName
})

watch(() => props.isActive, (isActive) => {
  if (isActive && workflowSteps.value.length === 0) {
    // 当激活时，模拟开始工作流
    setTimeout(() => {
      simulateWorkflow()
    }, 1000)
  }
})

// 监听步骤变化，自动滚动
watch(workflowSteps, () => {
  scrollToBottom()
}, { deep: true })

// 定时器更新执行时间
let executionTimer: number | null = null

const startExecutionTimer = () => {
  if (executionTimer) {
    clearInterval(executionTimer)
  }
  
  const startTime = Date.now()
  executionTimer = setInterval(() => {
    if (executionStatus.value === 'running') {
      executionTime.value = Date.now() - startTime
    } else {
      if (executionTimer) {
        clearInterval(executionTimer)
        executionTimer = null
      }
    }
  }, 100)
}

watch(executionStatus, (newStatus) => {
  if (newStatus === 'running') {
    startExecutionTimer()
  }
})

// 暴露方法给父组件
defineExpose({
  addStep,
  updateStep,
  clearWorkflow,
  simulateWorkflow
})

onMounted(() => {
  // 组件挂载后的初始化
})

onUnmounted(() => {
  if (executionTimer) {
    clearInterval(executionTimer)
  }
})
</script>

<style scoped>
.agent-workflow {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.workflow-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafbfc;
}

.workflow-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.workflow-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 当前状态 */
.current-status {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #f8f9fa;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.status-value {
  font-size: 12px;
  color: #303133;
  font-weight: 600;
}

/* 工作流步骤 */
.workflow-steps {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  position: relative;
}

.workflow-step {
  position: relative;
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: white;
  transition: all 0.3s ease;
}

.workflow-step.pending {
  border-color: #e4e7ed;
  background: #fafbfc;
}

.workflow-step.running {
  border-color: #e6a23c;
  background: #fdf6ec;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.2);
}

.workflow-step.completed {
  border-color: #67c23a;
  background: #f0f9ff;
}

.workflow-step.failed {
  border-color: #f56c6c;
  background: #fef0f0;
}

.workflow-step.active {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.2);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(230, 162, 60, 0.1);
  }
  100% {
    box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.2);
  }
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.step-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.pending-icon {
  color: #909399;
  background: #f4f4f5;
}

.running-icon {
  color: #e6a23c;
  background: #fdf6ec;
  animation: spin 1s linear infinite;
}

.completed-icon {
  color: #67c23a;
  background: #f0f9ff;
}

.failed-icon {
  color: #f56c6c;
  background: #fef0f0;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.step-info {
  flex: 1;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.step-time {
  font-size: 11px;
  color: #909399;
}

.step-duration {
  font-size: 11px;
  color: #606266;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 10px;
}

.step-content {
  margin-top: 12px;
}

.step-description {
  font-size: 13px;
  color: #606266;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

/* 详细信息 */
.step-details {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.detail-value {
  font-size: 12px;
  color: #303133;
  font-weight: 600;
}

/* 错误信息 */
.step-error {
  margin-bottom: 12px;
}

/* 输出结果 */
.step-output {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}

.output-header {
  padding: 8px 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.output-label {
  font-size: 12px;
  color: #606266;
  font-weight: 600;
}

.output-content {
  padding: 12px;
  background: white;
  max-height: 200px;
  overflow-y: auto;
}

.output-content pre {
  margin: 0;
  font-size: 12px;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

/* 连接线 */
.step-connector {
  position: absolute;
  left: 50%;
  bottom: -24px;
  width: 2px;
  height: 24px;
  background: #e4e7ed;
  transform: translateX(-50%);
}

.workflow-step.running .step-connector {
  background: #e6a23c;
}

.workflow-step.completed .step-connector {
  background: #67c23a;
}

.workflow-step.failed .step-connector {
  background: #f56c6c;
}

/* 空状态 */
.empty-workflow {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.empty-content {
  text-align: center;
  color: #606266;
}

.empty-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.empty-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.empty-content p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

/* 滚动条样式 */
.workflow-steps::-webkit-scrollbar {
  width: 6px;
}

.workflow-steps::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.workflow-steps::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.workflow-steps::-webkit-scrollbar-thumb:hover {
  background: #a8abb2;
}
</style>