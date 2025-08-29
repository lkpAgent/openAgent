<template>
  <div class="workflow-editor">
    <div class="editor-header">
      <h2>工作流编排</h2>
      <div class="header-actions">
        <el-button type="success" @click="runWorkflow" :loading="isRunning">
          <el-icon><VideoPlay /></el-icon>
          运行
        </el-button>
        <el-button type="primary" @click="saveWorkflow">
          <el-icon><DocumentAdd /></el-icon>
          保存
        </el-button>
        <el-button @click="loadWorkflow">
          <el-icon><FolderOpened /></el-icon>
          导入
        </el-button>
        <el-button @click="clearWorkflow">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <div class="editor-content">
      <div class="toolbar">
        <!-- 基础节点 -->
        <div class="tool-group">
          <h4>基础节点</h4>
          <div class="node-types">
            <div 
              v-for="nodeType in basicNodeTypes" 
              :key="nodeType.type"
              class="node-type-item"
              draggable="true"
              @dragstart="onDragStart($event, nodeType)"
            >
              <el-icon><component :is="nodeType.icon" /></el-icon>
              <span>{{ nodeType.label }}</span>
            </div>
          </div>
        </div>

        <!-- 处理节点 -->
        <div class="tool-group">
          <h4>处理节点</h4>
          <div class="node-types">
            <div 
              v-for="nodeType in processNodeTypes" 
              :key="nodeType.type"
              class="node-type-item"
              draggable="true"
              @dragstart="onDragStart($event, nodeType)"
            >
              <el-icon><component :is="nodeType.icon" /></el-icon>
              <span>{{ nodeType.label }}</span>
            </div>
          </div>
        </div>

        <!-- 工具节点 -->
        <div class="tool-group">
          <h4>工具节点</h4>
          <div class="node-types">
            <div 
              v-for="nodeType in toolNodeTypes" 
              :key="nodeType.type"
              class="node-type-item"
              draggable="true"
              @dragstart="onDragStart($event, nodeType)"
            >
              <el-icon><component :is="nodeType.icon" /></el-icon>
              <span>{{ nodeType.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="canvas-container">
        <div 
          ref="canvas"
          class="workflow-canvas"
          @drop="onDrop"
          @dragover="onDragOver"
          @click="onCanvasClick"
        >
          <!-- 工作流节点 -->
          <div
            v-for="node in nodes"
            :key="node.id"
            class="workflow-node"
            :class="{ 
              selected: selectedNode?.id === node.id,
              running: runningNodes.includes(node.id),
              completed: completedNodes.includes(node.id),
              error: errorNodes.includes(node.id)
            }"
            :style="{ left: node.x + 'px', top: node.y + 'px' }"
            @click.stop="selectNode(node)"
            @mousedown="startDrag(node, $event)"
          >
            <div class="node-header">
              <el-icon><component :is="getNodeIcon(node.type)" /></el-icon>
              <span>{{ node.name }}</span>
              <el-button 
                v-if="node.type !== 'start'"
                type="danger" 
                size="small" 
                circle 
                @click.stop="deleteNode(node.id)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div class="node-content">
              <p>{{ node.description }}</p>
              <div v-if="node.result" class="node-result">
                <el-tag size="small" :type="node.result.success ? 'success' : 'danger'">
                  {{ node.result.success ? '成功' : '失败' }}
                </el-tag>
              </div>
            </div>
            <!-- 连接点 -->
            <!-- 输入连接点 -->
            <div 
              v-if="node.type !== 'start'"
              class="connection-point input-point"
              @mousedown.stop="(e) => startConnection(node, 'input', e)"
            ></div>
            
            <!-- 输出连接点 -->
            <div 
              v-if="node.type !== 'end'"
              class="connection-point output-point"
              @mousedown.stop="(e) => startConnection(node, 'output', e)"
            ></div>
          </div>

          <!-- 连接线 -->
          <svg class="connections-layer">
            <path
              v-for="connection in connections"
              :key="connection.id"
              :d="getConnectionPath(connection)"
              class="connection-line"
              :class="{ selected: selectedConnection?.id === connection.id }"
              @click="selectConnection(connection)"
            />
          </svg>

          <!-- 临时连接线 -->
          <svg v-if="tempConnection" class="connections-layer">
            <path
              :d="tempConnection.path"
              class="temp-connection-line"
            />
          </svg>
        </div>
      </div>

      <!-- 属性面板 -->
      <div class="properties-panel" v-if="selectedNode">
        <h4>{{ selectedNode.name }} - 属性配置</h4>
        <el-form :model="selectedNode" label-width="80px" size="small">
          <el-form-item label="名称">
            <el-input v-model="selectedNode.name" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input 
              v-model="selectedNode.description" 
              type="textarea" 
              :rows="2"
            />
          </el-form-item>
          
          <!-- LLM节点配置 -->
          <template v-if="selectedNode.type === 'llm'">
            <el-form-item label="模型">
              <el-select v-model="selectedNode.config.model" placeholder="选择模型">
                <el-option label="GPT-4" value="gpt-4" />
                <el-option label="ChatGLM" value="chatglm" />
                <el-option label="ERNIE" value="ernie" />
              </el-select>
            </el-form-item>
            <el-form-item label="温度">
              <el-slider v-model="selectedNode.config.temperature" :min="0" :max="2" :step="0.1" />
            </el-form-item>
            <el-form-item label="提示词">
              <el-input 
                v-model="selectedNode.config.prompt" 
                type="textarea" 
                :rows="4"
                placeholder="输入提示词模板"
              />
            </el-form-item>
          </template>

          <!-- 条件分支配置 -->
          <template v-if="selectedNode.type === 'condition'">
            <el-form-item label="条件表达式">
              <el-input 
                v-model="selectedNode.config.condition" 
                placeholder="例: result.score > 0.8"
              />
            </el-form-item>
          </template>

          <!-- 迭代节点配置 -->
          <template v-if="selectedNode.type === 'loop'">
            <el-form-item label="迭代类型">
              <el-select v-model="selectedNode.config.loopType">
                <el-option label="固定次数" value="count" />
                <el-option label="条件循环" value="while" />
                <el-option label="遍历数组" value="foreach" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="selectedNode.config.loopType === 'count'" label="次数">
              <el-input-number v-model="selectedNode.config.count" :min="1" />
            </el-form-item>
            <el-form-item v-if="selectedNode.config.loopType === 'while'" label="条件">
              <el-input v-model="selectedNode.config.condition" />
            </el-form-item>
          </template>

          <!-- 代码执行配置 -->
          <template v-if="selectedNode.type === 'code'">
            <el-form-item label="语言">
              <el-select v-model="selectedNode.config.language">
                <el-option label="Python" value="python" />
                <el-option label="JavaScript" value="javascript" />
              </el-select>
            </el-form-item>
            <el-form-item label="代码">
              <el-input 
                v-model="selectedNode.config.code" 
                type="textarea" 
                :rows="6"
                placeholder="输入代码"
              />
            </el-form-item>
          </template>

          <!-- HTTP请求配置 -->
          <template v-if="selectedNode.type === 'http'">
            <el-form-item label="方法">
              <el-select v-model="selectedNode.config.method">
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
              </el-select>
            </el-form-item>
            <el-form-item label="URL">
              <el-input v-model="selectedNode.config.url" placeholder="https://api.example.com" />
            </el-form-item>
            <el-form-item label="请求头">
              <el-input 
                v-model="selectedNode.config.headers" 
                type="textarea" 
                :rows="3"
                placeholder="JSON格式"
              />
            </el-form-item>
            <el-form-item label="请求体">
              <el-input 
                v-model="selectedNode.config.body" 
                type="textarea" 
                :rows="3"
                placeholder="JSON格式"
              />
            </el-form-item>
          </template>

          <!-- 工具节点配置 -->
          <template v-if="isToolNode(selectedNode.type)">
            <el-form-item label="工具参数">
              <div v-for="param in getToolParameters(selectedNode.type)" :key="param.name" class="tool-param">
                <el-form-item :label="param.name">
                  <el-input 
                    v-if="param.type === 'string'"
                    v-model="selectedNode.config.parameters[param.name]" 
                    :placeholder="param.description"
                  />
                  <el-input-number 
                    v-else-if="param.type === 'number'"
                    v-model="selectedNode.config.parameters[param.name]" 
                  />
                  <el-switch 
                    v-else-if="param.type === 'boolean'"
                    v-model="selectedNode.config.parameters[param.name]" 
                  />
                </el-form-item>
              </div>
            </el-form-item>
          </template>

          <!-- 执行结果 -->
          <template v-if="selectedNode.result">
            <el-divider>执行结果</el-divider>
            <el-form-item label="状态">
              <el-tag :type="selectedNode.result.success ? 'success' : 'danger'">
                {{ selectedNode.result.success ? '成功' : '失败' }}
              </el-tag>
            </el-form-item>
            <el-form-item label="结果" v-if="selectedNode.result.data">
              <el-input 
                :value="JSON.stringify(selectedNode.result.data, null, 2)" 
                type="textarea" 
                :rows="4"
                readonly
              />
            </el-form-item>
            <el-form-item label="错误" v-if="selectedNode.result.error">
              <el-input 
                :value="selectedNode.result.error" 
                type="textarea" 
                :rows="3"
                readonly
              />
            </el-form-item>
          </template>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentAdd, FolderOpened, Close, VideoPlay, VideoPause, Cpu, Share, Refresh, Document, Link, Cloudy, DataAnalysis, Search, Picture, Operation } from '@element-plus/icons-vue'

// 节点类型定义
interface NodeType {
  type: string
  label: string
  icon: string
  description: string
}

// 工作流节点
interface WorkflowNode {
  id: string
  type: string
  name: string
  description: string
  x: number
  y: number
  config?: string
}

// 连接线
interface Connection {
  id: string
  from: string
  to: string
  fromPoint: string
  toPoint: string
}

// 响应式数据
const canvas = ref<HTMLElement>()
const nodes = ref<WorkflowNode[]>([])
const connections = ref<Connection[]>([])
const selectedNode = ref<WorkflowNode | null>(null)
const selectedConnection = ref<Connection | null>(null)
const draggedNode = ref<WorkflowNode | null>(null)
const isDragging = ref(false)
const dragOffset = reactive({ x: 0, y: 0 })
const isRunning = ref(false)
const runningNodes = ref<string[]>([])
const completedNodes = ref<string[]>([])
const errorNodes = ref<string[]>([])
const tempConnection = ref<any>(null)
const isConnecting = ref(false)
const connectingFrom = ref<{ nodeId: string; type: string } | null>(null)

// 节点类型定义
const basicNodeTypes: NodeType[] = [
  {
    type: 'start',
    label: '开始',
    icon: 'VideoPlay',
    description: '工作流开始节点'
  },
  {
    type: 'end',
    label: '结束',
    icon: 'VideoPause',
    description: '工作流结束节点'
  }
]

const processNodeTypes: NodeType[] = [
  {
    type: 'llm',
    label: 'LLM',
    icon: 'Cpu',
    description: '大语言模型处理'
  },
  {
    type: 'condition',
    label: '条件分支',
    icon: 'Share',
    description: '条件判断节点'
  },
  {
    type: 'loop',
    label: '迭代',
    icon: 'Refresh',
    description: '循环迭代节点'
  },
  {
    type: 'code',
    label: '代码执行',
    icon: 'Document',
    description: '执行代码片段'
  },
  {
    type: 'http',
    label: 'HTTP请求',
    icon: 'Link',
    description: 'HTTP API调用'
  }
]

const toolNodeTypes: NodeType[] = [
  {
    type: 'weather',
    label: '天气查询',
    icon: 'Cloudy',
    description: '查询天气信息'
  },
  {
    type: 'calculator',
    label: '计算器',
    icon: 'DataAnalysis',
    description: '数学计算工具'
  },
  {
    type: 'search',
    label: '搜索',
    icon: 'Search',
    description: '网络搜索工具'
  },
  {
    type: 'image_gen',
    label: '图像生成',
    icon: 'Picture',
    description: 'AI图像生成'
  }
]

// 方法
const onDragStart = (event: DragEvent, nodeType: NodeType) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/json', JSON.stringify(nodeType))
  }
}

const onDragOver = (event: DragEvent) => {
  event.preventDefault()
}

const onDrop = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    const nodeTypeData = event.dataTransfer.getData('application/json')
    if (nodeTypeData) {
      const nodeType = JSON.parse(nodeTypeData) as NodeType
      const rect = canvas.value?.getBoundingClientRect()
      if (rect) {
        const x = event.clientX - rect.left
        const y = event.clientY - rect.top
        addNode(nodeType, x, y)
      }
    }
  }
}

const addNode = (nodeType: NodeType, x: number, y: number) => {
  const newNode: WorkflowNode = {
    id: `node_${Date.now()}`,
    type: nodeType.type,
    name: nodeType.label,
    description: nodeType.description,
    x,
    y,
    config: getDefaultConfig(nodeType.type)
  }
  nodes.value.push(newNode)
}

const getDefaultConfig = (nodeType: string) => {
  const configs: Record<string, any> = {
    llm: {
      model: 'gpt-4',
      temperature: 0.7,
      prompt: ''
    },
    condition: {
      condition: ''
    },
    loop: {
      loopType: 'count',
      count: 1,
      condition: ''
    },
    code: {
      language: 'python',
      code: ''
    },
    http: {
      method: 'GET',
      url: '',
      headers: '{}',
      body: '{}'
    },
    weather: {
      parameters: { location: '' }
    },
    calculator: {
      parameters: { expression: '' }
    },
    search: {
      parameters: { query: '', limit: 10 }
    },
    image_gen: {
      parameters: { prompt: '', size: '512x512' }
    }
  }
  return configs[nodeType] || {}
}

const selectNode = (node: WorkflowNode) => {
  selectedNode.value = node
  selectedConnection.value = null
}

const selectConnection = (connection: Connection) => {
  selectedConnection.value = connection
  selectedNode.value = null
}

const deleteNode = (nodeId: string) => {
  const index = nodes.value.findIndex(n => n.id === nodeId)
  if (index > -1) {
    nodes.value.splice(index, 1)
    // 删除相关连接
    connections.value = connections.value.filter(
      c => c.from !== nodeId && c.to !== nodeId
    )
    if (selectedNode.value?.id === nodeId) {
      selectedNode.value = null
    }
  }
}

const startDrag = (node: WorkflowNode, event: MouseEvent) => {
  draggedNode.value = node
  isDragging.value = true
  dragOffset.x = event.offsetX
  dragOffset.y = event.offsetY
  
  const onMouseMove = (e: MouseEvent) => {
    if (isDragging.value && draggedNode.value) {
      const rect = canvas.value?.getBoundingClientRect()
      if (rect) {
        draggedNode.value.x = e.clientX - rect.left - dragOffset.x
        draggedNode.value.y = e.clientY - rect.top - dragOffset.y
      }
    }
  }
  
  const onMouseUp = () => {
    isDragging.value = false
    draggedNode.value = null
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const startConnection = (node: WorkflowNode, pointType: string, event: MouseEvent) => {
  if (pointType === 'input') {
    // 输入点不能作为连接起点
    return
  }
  
  isConnecting.value = true
  connectingFrom.value = { nodeId: node.id, type: pointType }
  
  const onMouseMove = (e: MouseEvent) => {
    if (isConnecting.value && connectingFrom.value && canvas.value) {
      const rect = canvas.value.getBoundingClientRect()
      const fromNode = nodes.value.find(n => n.id === connectingFrom.value!.nodeId)
      if (fromNode) {
        const startX = fromNode.x + 180 + 6    // 输出点中心 (节点宽度180px + 连接点偏移6px)
        const startY = fromNode.y + 45      // 调整到连接点中心位置
        const endX = e.clientX - rect.left
        const endY = e.clientY - rect.top
        
        tempConnection.value = {
          path: `M ${startX} ${startY} Q ${(startX + endX) / 2} ${startY} ${endX} ${endY}`
        }
      }
    }
  }
  
  const onMouseUp = (e: MouseEvent) => {
    if (isConnecting.value && canvas.value) {
      // 检查是否在输入点上结束
      const rect = canvas.value.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      
      // 查找目标节点
      const targetNode = nodes.value.find(node => {
        if (node.type === 'start' || node.id === connectingFrom.value!.nodeId) return false
        const nodeRect = {
          left: node.x,
          top: node.y,
          right: node.x + 160,
          bottom: node.y + 80
        }
        return x >= nodeRect.left - 10 && x <= nodeRect.left + 10 && 
               y >= nodeRect.top + 30 && y <= nodeRect.top + 50
      })
      
      if (targetNode && connectingFrom.value) {
        // 创建连接
        const existingConnection = connections.value.find(
          c => c.from === connectingFrom.value!.nodeId && c.to === targetNode.id
        )
        
        if (!existingConnection) {
          const newConnection: Connection = {
            id: `conn-${Date.now()}`,
            from: connectingFrom.value.nodeId,
            to: targetNode.id
          }
          connections.value.push(newConnection)
        }
      }
    }
    
    // 清理状态
    isConnecting.value = false
    connectingFrom.value = null
    tempConnection.value = null
    
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const getNodeIcon = (nodeType: string) => {
  const allTypes = [...basicNodeTypes, ...processNodeTypes, ...toolNodeTypes]
  const type = allTypes.find(t => t.type === nodeType)
  return type?.icon || 'Operation'
}

const isToolNode = (nodeType: string) => {
  return toolNodeTypes.some(t => t.type === nodeType)
}

const getToolParameters = (nodeType: string) => {
  const toolParams: Record<string, any[]> = {
    weather: [
      { name: 'location', type: 'string', description: '城市名称' }
    ],
    calculator: [
      { name: 'expression', type: 'string', description: '数学表达式' }
    ],
    search: [
      { name: 'query', type: 'string', description: '搜索关键词' },
      { name: 'limit', type: 'number', description: '结果数量' }
    ],
    image_gen: [
      { name: 'prompt', type: 'string', description: '图像描述' },
      { name: 'size', type: 'string', description: '图像尺寸' }
    ]
  }
  return toolParams[nodeType] || []
}

const runWorkflow = async () => {
  if (isRunning.value) {
    ElMessage.warning('工作流正在执行中')
    return
  }
  
  isRunning.value = true
  runningNodes.value = []
  completedNodes.value = []
  errorNodes.value = []
  
  try {
    // 重置所有节点状态
    nodes.value.forEach(node => {
      if (node.result) {
        delete node.result
      }
    })
    
    // 找到开始节点
    const startNode = nodes.value.find(n => n.type === 'start')
    if (!startNode) {
      ElMessage.error('未找到开始节点')
      return
    }
    
    // 执行工作流
    await executeNode(startNode)
    
    ElMessage.success('工作流执行完成')
  } catch (error) {
    console.error('工作流执行失败:', error)
    ElMessage.error('工作流执行失败: ' + error.message)
  } finally {
    isRunning.value = false
  }
}

const executeNode = async (node: WorkflowNode) => {
  runningNodes.value.push(node.id)
  
  try {
    // 模拟节点执行
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 根据节点类型执行不同逻辑
    switch (node.type) {
      case 'start':
        node.result = { success: true, data: '工作流开始' }
        break
      case 'llm':
        node.result = { success: true, data: 'LLM处理完成' }
        break
      case 'condition':
        node.result = { success: true, data: '条件判断完成' }
        break
      case 'code':
        node.result = { success: true, data: '代码执行完成' }
        break
      case 'http':
        node.result = { success: true, data: 'HTTP请求完成' }
        break
      default:
        if (isToolNode(node.type)) {
          node.result = { success: true, data: `${node.name}工具执行完成` }
        } else {
          node.result = { success: true, data: '节点执行完成' }
        }
    }
    
    runningNodes.value = runningNodes.value.filter(id => id !== node.id)
    completedNodes.value.push(node.id)
    
    // 执行下一个节点
    const nextConnections = connections.value.filter(c => c.from === node.id)
    for (const connection of nextConnections) {
      const nextNode = nodes.value.find(n => n.id === connection.to)
      if (nextNode && !runningNodes.value.includes(nextNode.id) && !completedNodes.value.includes(nextNode.id)) {
        await executeNode(nextNode)
      }
    }
    
  } catch (error) {
    runningNodes.value = runningNodes.value.filter(id => id !== node.id)
    errorNodes.value.push(node.id)
    node.result = { success: false, error: error.message }
    throw error
  }
}

const clearWorkflow = () => {
  ElMessageBox.confirm('确定要清空当前工作流吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    nodes.value = [
      {
        id: 'start-1',
        type: 'start',
        name: '开始',
        description: '工作流开始节点',
        x: 100,
        y: 100,
        config: {}
      }
    ]
    connections.value = []
    selectedNode.value = null
    selectedConnection.value = null
    runningNodes.value = []
    completedNodes.value = []
    errorNodes.value = []
    ElMessage.success('工作流已清空')
  }).catch(() => {
    // 用户取消
  })
}

const getConnectionPath = (connection: Connection) => {
  const fromNode = nodes.value.find(n => n.id === connection.from)
  const toNode = nodes.value.find(n => n.id === connection.to)
  
  if (!fromNode || !toNode) {
    return 'M 0 0 L 0 0'
  }
  
  // 计算起点和终点坐标，精确到连接点中心
  // 输出连接点：right: -6px，12px宽，中心在节点右边缘外6px
  const startX = fromNode.x + 180 + 6  // 输出点中心 (节点宽度180px + 连接点偏移6px)
  const startY = fromNode.y + 45       // 调整到连接点中心位置
  // 输入连接点：left: -6px，12px宽，中心在节点左边缘外6px
  const endX = toNode.x - 6            // 输入点中心 (节点左边缘 - 连接点偏移6px)
  const endY = toNode.y + 45           // 调整到连接点中心位置
  
  // 计算控制点，创建贝塞尔曲线
  const controlX1 = startX + (endX - startX) * 0.5
  const controlY1 = startY
  const controlX2 = startX + (endX - startX) * 0.5
  const controlY2 = endY
  
  // 返回SVG路径字符串
  return `M ${startX} ${startY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${endX} ${endY}`
}

const onCanvasClick = () => {
  selectedNode.value = null
  selectedConnection.value = null
}

const saveWorkflow = () => {
  const workflow = {
    nodes: nodes.value,
    connections: connections.value,
    timestamp: new Date().toISOString()
  }
  
  // 保存到本地存储
  localStorage.setItem('workflow', JSON.stringify(workflow))
  
  // 创建下载链接
  const blob = new Blob([JSON.stringify(workflow, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('工作流已保存')
}

const loadWorkflow = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = (event: Event) => {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const result = e.target?.result as string
          const workflow = JSON.parse(result)
          nodes.value = workflow.nodes || []
          connections.value = workflow.connections || []
          selectedNode.value = null
          selectedConnection.value = null
          ElMessage.success('工作流导入成功')
        } catch (error) {
          ElMessage.error('工作流文件格式错误')
        }
      }
      reader.readAsText(file)
    }
  }
  input.click()
}

onMounted(() => {
  // 初始化
})
</script>

<style scoped>
.workflow-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.editor-header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.toolbar {
  width: 280px;
  background: white;
  border-right: 1px solid #e4e7ed;
  padding: 16px;
  overflow-y: auto;
}

.tool-group {
  margin-bottom: 24px;
}

.tool-group h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.node-types {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-type-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
  user-select: none;
}

.node-type-item:hover {
  background: #ecf5ff;
  border-color: #409eff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.node-type-item:active {
  cursor: grabbing;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.workflow-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  background: 
    radial-gradient(circle, #ddd 1px, transparent 1px);
  background-size: 20px 20px;
  overflow: auto;
}

.workflow-node {
  position: absolute;
  width: 180px;
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: move;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  user-select: none;
}

.workflow-node:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.workflow-node.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.workflow-node.running {
  border-color: #E6A23C;
  animation: pulse 1.5s infinite;
}

.workflow-node.completed {
  border-color: #67C23A;
}

.workflow-node.error {
  border-color: #F56C6C;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(230, 162, 60, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(230, 162, 60, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(230, 162, 60, 0);
  }
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  border-radius: 6px 6px 0 0;
}

.node-header span {
  flex: 1;
  font-weight: 500;
  color: #303133;
}

.node-content {
  padding: 12px;
}

.node-content p {
  margin: 0;
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
}

.node-result {
  margin-top: 8px;
}

.connection-point {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid #409EFF;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
  top: 50%;
  transform: translateY(-50%);
}

.connection-point:hover {
  background: #409EFF;
  transform: translateY(-50%) scale(1.3);
}

.input-point {
  left: -6px;
}

.output-point {
  right: -6px;
}

.connections-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.connection-line {
  stroke: #409eff;
  stroke-width: 2;
  fill: none;
  pointer-events: stroke;
  cursor: pointer;
}

.connection-line:hover {
  stroke: #66b1ff;
  stroke-width: 3;
}

.connection-line.selected {
  stroke: #E6A23C;
  stroke-width: 3;
}

.temp-connection-line {
  stroke: #E6A23C;
  stroke-width: 2;
  fill: none;
  stroke-dasharray: 5,5;
  animation: dash 1s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}

.properties-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #e4e7ed;
  padding: 16px;
  overflow-y: auto;
}

.properties-panel h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-weight: 600;
}

.tool-param {
  margin-bottom: 8px;
}

/* 滚动条样式 */
.toolbar::-webkit-scrollbar,
.properties-panel::-webkit-scrollbar {
  width: 6px;
}

.toolbar::-webkit-scrollbar-track,
.properties-panel::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.toolbar::-webkit-scrollbar-thumb,
.properties-panel::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.toolbar::-webkit-scrollbar-thumb:hover,
.properties-panel::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>