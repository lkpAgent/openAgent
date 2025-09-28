<template>
  <div class="workflow-editor">
    <div class="editor-header">
      <h2>{{ currentWorkflow ? `工作流编排-${currentWorkflow.name}` : '工作流编排' }}</h2>
      <div class="header-actions">
        <el-button type="success" @click="runWorkflow" :loading="isRunning">
          <el-icon><VideoPlay /></el-icon>
          运行
        </el-button>
        <el-button type="primary" @click="saveWorkflow">
          <el-icon><DocumentAdd /></el-icon>
          保存
        </el-button>
        <!-- 激活/停用按钮 - 只在有当前工作流时显示 -->
        <template v-if="currentWorkflow">
          <el-button 
            v-if="currentWorkflow.status === 'DRAFT' || currentWorkflow.status === 'ARCHIVED'"
            type="warning" 
            @click="activateWorkflow"
            :loading="isActivating"
          >
            <el-icon><Switch /></el-icon>
            激活
          </el-button>
          <el-button 
            v-else-if="currentWorkflow.status === 'PUBLISHED'"
            type="info" 
            @click="deactivateWorkflow"
            :loading="isDeactivating"
          >
            <el-icon><SwitchButton /></el-icon>
            停用
          </el-button>
        </template>
        <el-button @click="loadWorkflow">
          <el-icon><FolderOpened /></el-icon>
          导入
        </el-button>
        <el-button @click="clearWorkflow">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
        
        <!-- WebSocket连接状态指示器 -->
        <div class="websocket-status">
          <el-tooltip :content="isWebSocketConnected ? '实时连接已建立' : '实时连接未建立'">
            <el-icon 
              :class="['connection-indicator', { 'connected': isWebSocketConnected, 'disconnected': !isWebSocketConnected }]"
            >
              <Connection />
            </el-icon>
          </el-tooltip>
        </div>
        
        <!-- 画布控制按钮 -->
        <div class="canvas-controls">
          <el-button-group>
            <el-button size="small" @click="resetCanvasView" title="重置视图">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <el-button size="small" @click="fitCanvasToContent" title="适应内容">
              <el-icon><FullScreen /></el-icon>
            </el-button>
          </el-button-group>
          <span class="zoom-info">{{ Math.round(canvasTransform.scale * 100) }}%</span>
        </div>
      </div>
    </div>

    <div class="editor-content">
      <!-- 左侧画布区域 -->
      <div class="canvas-container" :class="{ 'with-execution-panel': showExecutionPanel }">
        <div 
          ref="canvas"
          class="workflow-canvas"
          @drop="onDrop"
          @dragover="onDragOver"
          @click="onCanvasClick"
          @contextmenu.prevent="showCanvasContextMenu"
          @mousedown="startCanvasDrag"
          @wheel.prevent="onCanvasWheel"
        >
          <!-- 变换容器 -->
          <div 
            class="canvas-transform-container"
            :style="{
              transform: `translate(${canvasTransform.x}px, ${canvasTransform.y}px) scale(${canvasTransform.scale})`,
              transformOrigin: '0 0'
            }"
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
              error: errorNodes.includes(node.id),
              dragging: isDragging.value && draggedNode.value?.id === node.id
            }"
            :ref="el => setNodeRef(el, node.id)"
            @dblclick.stop="selectNode(node)"
            @contextmenu.prevent="showNodeContextMenu($event, node)"
          >
            <div class="node-header">
              <el-icon><component :is="getNodeIcon(node.type)" /></el-icon>
              <span>{{ node.name }}</span>
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
              @click.stop="(e) => showConnectionPointMenu(node, 'output', e)"
            ></div>
          </div>

          <!-- 连接线 -->
          <svg class="connections-layer">
            <path
              v-for="connection in connections"
              :key="connection.id"
              :d="getConnectionPath(connection)"
              class="connection-line"
              :class="{ selected: selectedConnection?.from === connection.from && selectedConnection?.to === connection.to }"
              @click="selectConnection(connection)"
              @contextmenu.prevent="showConnectionContextMenu($event, connection)"
            />
          </svg>

          <!-- 临时连接线 -->
          <svg v-if="tempConnection" class="connections-layer">
            <path
              :d="tempConnection.path"
              class="temp-connection-line"
            />
          </svg>
          </div> <!-- 关闭变换容器 -->
        </div>
      </div>

      <!-- 属性面板 -->
      <div class="properties-panel" v-if="selectedNode">
        <h4>{{ selectedNode.name }} - 属性配置</h4>
        
        <el-tabs v-model="activeConfigTab" type="border-card">
          <el-tab-pane label="基本配置" name="basic">
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
              <template v-if="selectedNode.type === 'llm' && selectedNode.config">
                <el-form-item label="模型">
                  <el-select v-model="selectedNode.config.model" placeholder="选择系统配置的模型">
                    <el-option 
                      v-for="config in availableLLMModels" 
                      :key="config.id"
                      :label="`${config.model_name} (${config.provider})`" 
                      :value="config.id"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="提示词">
                  <div class="prompt-input-container">
                    <el-input 
                      ref="promptInput"
                      v-model="selectedNode.config.prompt" 
                      type="textarea" 
                      :rows="4"
                      placeholder="输入提示词模板，按 / 键选择变量..."
                      @keydown="handlePromptKeydown"
                    />
                    <!-- 变量选择器 -->
                    <div v-if="showVariableSelector" class="variable-selector">
                      <div class="variable-header">
                        <span>可用变量 ({{ availableVariables.length }})</span>
                        <span class="variable-hint">/触发，↑↓选择，Enter确认，Esc取消</span>
                      </div>
                      <div class="variable-list">
                        <div
                          v-for="(variable, index) in availableVariables"
                          :key="`var-${index}-${variable.name}`"
                          @click="onVariableClick(variable)"
                          class="variable-item"
                          :class="{ 'active': selectedVariableIndex === index }"
                        >
                          <div class="variable-main">
                            <span class="variable-name">{{ variable.name }}</span>
                            <span class="variable-type">{{ variable.type }}</span>
                          </div>
                          <div class="variable-description">{{ variable.description }}</div>
                          <div class="variable-source">来源: {{ variable.source }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-form-item>
                
                <!-- 高级配置组 -->
                <el-collapse v-model="advancedConfigCollapse" style="margin-top: 16px;">
                  <el-collapse-item title="高级配置" name="advanced">
                    <el-form-item label="温度">
                      <el-slider 
                        v-model="selectedNode.config.temperature" 
                        :min="0" 
                        :max="2" 
                        :step="0.1" 
                        show-input
                        :show-input-controls="false"
                      />
                      <div class="config-hint">控制输出的随机性，值越高越随机</div>
                    </el-form-item>
                    <el-form-item label="Token数">
                      <el-input-number 
                        v-model="selectedNode.config.max_tokens" 
                        :min="1" 
                        :max="4096" 
                        :step="1"
                        placeholder="最大输出Token数"
                      />
                      <div class="config-hint">限制模型输出的最大Token数量</div>
                    </el-form-item>
                  </el-collapse-item>
                </el-collapse>
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
          </el-tab-pane>
          
          <el-tab-pane 
            v-if="selectedNode.type !== 'llm'" 
            label="参数配置" 
            name="parameters"
          >
            <NodeParameterConfig
              v-model="selectedNode.parameters"
              :node-type="selectedNode.type"
              :available-nodes="getAvailableSourceNodes(selectedNode.id)"
            />
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 运行结果展示面板 -->
      <div class="execution-panel" v-if="showExecutionPanel">
        <div class="execution-panel-header">
          <h4>运行结果</h4>
          <el-button 
            size="small" 
            text 
            @click="showExecutionPanel = false"
            :icon="Close"
          />
        </div>
        
        <div class="execution-content">
          <div class="execution-status">
            <el-tag 
              :type="executionStatus === 'running' ? 'warning' : 
                     executionStatus === 'completed' ? 'success' : 
                     executionStatus === 'failed' ? 'danger' : 'info'"
              size="large"
            >
              {{ getExecutionStatusText() }}
            </el-tag>
            <span class="execution-time" v-if="executionStartTime">
              {{ formatExecutionTime() }}
            </span>
          </div>

          <div class="node-executions" v-if="nodeExecutions.length > 0">
            <div 
              v-for="nodeExecution in nodeExecutions" 
              :key="nodeExecution.nodeId"
              class="node-execution-item"
              :class="{ 
                'running': nodeExecution.status === 'running',
                'completed': nodeExecution.status === 'completed',
                'failed': nodeExecution.status === 'failed'
              }"
            >
              <div class="node-execution-header">
                <div class="node-info">
                  <el-icon><component :is="getNodeIcon(getNodeById(nodeExecution.nodeId)?.type)" /></el-icon>
                  <span class="node-name">{{ getNodeById(nodeExecution.nodeId)?.name }}</span>
                </div>
                <el-tag 
                  size="small"
                  :type="nodeExecution.status === 'running' ? 'warning' : 
                         nodeExecution.status === 'completed' ? 'success' : 
                         nodeExecution.status === 'failed' ? 'danger' : 'info'"
                >
                  {{ getNodeStatusText(nodeExecution.status) }}
                </el-tag>
              </div>

              <!-- 输入数据 -->
              <div class="execution-section" v-if="nodeExecution.input">
                <div class="section-title">输入</div>
                <div class="section-content">
                  <pre class="data-display">{{ formatData(nodeExecution.input) }}</pre>
                </div>
              </div>

              <!-- 输出数据 -->
              <div class="execution-section" v-if="nodeExecution.output || nodeExecution.streamOutput">
                <div class="section-title">输出</div>
                <div class="section-content">
                  <!-- 流式输出 -->
                  <div v-if="nodeExecution.streamOutput && nodeExecution.status === 'running'" class="stream-output">
                    <div class="stream-content">{{ nodeExecution.streamOutput }}</div>
                    <div class="stream-cursor">|</div>
                  </div>
                  <!-- 最终输出 -->
                  <pre v-else-if="nodeExecution.output" class="data-display">{{ formatData(nodeExecution.output) }}</pre>
                </div>
              </div>

              <!-- 错误信息 -->
              <div class="execution-section error-section" v-if="nodeExecution.error">
                <div class="section-title">错误</div>
                <div class="section-content">
                  <div class="error-message">{{ nodeExecution.error }}</div>
                </div>
              </div>

              <!-- 执行时间 -->
              <div class="execution-time-info" v-if="nodeExecution.startTime">
                <span>开始时间: {{ formatTime(nodeExecution.startTime) }}</span>
                <span v-if="nodeExecution.endTime">
                  | 耗时: {{ formatDuration(nodeExecution.startTime, nodeExecution.endTime) }}
                </span>
              </div>
            </div>
          </div>

          <div v-else class="empty-execution">
            <p>暂无执行记录</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 节点右键菜单 -->
    <div 
      v-if="nodeContextMenu.visible" 
      class="context-menu"
      :style="{ left: nodeContextMenu.x + 'px', top: nodeContextMenu.y + 'px' }"
      @click.stop
    >
      <div class="context-menu-item" @click="copyNode" v-if="nodeContextMenu.node?.type !== 'start'">
        <el-icon><DocumentCopy /></el-icon>
        <span>复制</span>
      </div>
      <div class="context-menu-item" @click="deleteSelectedItem" v-if="nodeContextMenu.node?.type !== 'start'">
        <el-icon><Delete /></el-icon>
        <span>删除</span>
      </div>
    </div>

    <!-- 画布右键菜单 -->
    <div 
      v-if="canvasContextMenu.visible"
      class="context-menu"
      :style="{ left: canvasContextMenu.x + 'px', top: canvasContextMenu.y + 'px' }"
    >
      <div class="context-menu-header">添加节点</div>
      <div class="context-menu-group">
        <div class="context-menu-group-title">基础节点</div>
        <div 
          v-for="nodeType in filteredBasicNodeTypes" 
          :key="nodeType.type"
          class="context-menu-item"
          @click="addNodeFromContextMenu(nodeType)"
        >
          <el-icon><component :is="nodeType.icon" /></el-icon>
          <span>{{ nodeType.label }}</span>
        </div>
      </div>
      <div class="context-menu-group">
        <div class="context-menu-group-title">处理节点</div>
        <div 
          v-for="nodeType in processNodeTypes" 
          :key="nodeType.type"
          class="context-menu-item"
          @click="addNodeFromContextMenu(nodeType)"
        >
          <el-icon><component :is="nodeType.icon" /></el-icon>
          <span>{{ nodeType.label }}</span>
        </div>
      </div>
      <div class="context-menu-group">
        <div class="context-menu-group-title">工具节点</div>
        <div 
          v-for="nodeType in toolNodeTypes" 
          :key="nodeType.type"
          class="context-menu-item"
          @click="addNodeFromContextMenu(nodeType)"
        >
          <el-icon><component :is="nodeType.icon" /></el-icon>
          <span>{{ nodeType.label }}</span>
        </div>
      </div>
    </div>

    <!-- 连接点菜单 -->
    <div 
      v-if="connectionPointMenu.visible"
      class="context-menu"
      :style="{ left: connectionPointMenu.x + 'px', top: connectionPointMenu.y + 'px' }"
    >
      <div class="context-menu-header">添加后续节点</div>
      <div class="context-menu-group">
        <div class="context-menu-group-title">基础节点</div>
        <div 
          v-for="nodeType in filteredBasicNodeTypes" 
          :key="nodeType.type"
          class="context-menu-item"
          @click="addNodeFromConnectionPoint(nodeType)"
        >
          <el-icon><component :is="nodeType.icon" /></el-icon>
          <span>{{ nodeType.label }}</span>
        </div>
      </div>
      <div class="context-menu-group">
        <div class="context-menu-group-title">处理节点</div>
        <div 
          v-for="nodeType in processNodeTypes" 
          :key="nodeType.type"
          class="context-menu-item"
          @click="addNodeFromConnectionPoint(nodeType)"
        >
          <el-icon><component :is="nodeType.icon" /></el-icon>
          <span>{{ nodeType.label }}</span>
        </div>
      </div>
      <div class="context-menu-group">
        <div class="context-menu-group-title">工具节点</div>
        <div 
          v-for="nodeType in toolNodeTypes" 
          :key="nodeType.type"
          class="context-menu-item"
          @click="addNodeFromConnectionPoint(nodeType)"
        >
          <el-icon><component :is="nodeType.icon" /></el-icon>
          <span>{{ nodeType.label }}</span>
        </div>
      </div>
    </div>

    <!-- 连接线右键菜单 -->
    <div 
      v-if="connectionContextMenu.visible"
      class="context-menu"
      :style="{ left: connectionContextMenu.x + 'px', top: connectionContextMenu.y + 'px' }"
    >
      <div class="context-menu-item" @click="deleteConnection">
        <el-icon><Delete /></el-icon>
        <span>删除连接</span>
      </div>
    </div>

    <!-- 保存工作流对话框 -->
    <el-dialog v-model="showSaveDialog" title="保存工作流" width="500px">
      <el-form :model="saveForm" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="saveForm.name" placeholder="请输入工作流名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="saveForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入工作流描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSaveDialog = false">取消</el-button>
          <el-button type="primary" @click="saveNewWorkflow">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 加载工作流对话框 -->
    <el-dialog v-model="showLoadDialog" title="加载工作流" width="600px">
      <div class="workflow-list">
        <div 
          v-for="workflow in workflows" 
          :key="workflow.id"
          class="workflow-item"
          @click="loadSelectedWorkflow(workflow)"
        >
          <div class="workflow-info">
            <h4>{{ workflow.name }}</h4>
            <p>{{ workflow.description || '无描述' }}</p>
            <div class="workflow-meta">
              <span>状态: {{ workflow.is_active ? '激活' : '未激活' }}</span>
              <span>创建时间: {{ new Date(workflow.created_at).toLocaleString() }}</span>
            </div>
          </div>
        </div>
        <div v-if="workflows.length === 0" class="empty-state">
          <p>暂无工作流</p>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showLoadDialog = false">取消</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 参数输入对话框 -->
    <ParameterInputDialog
      v-model="showParameterDialog"
      :parameters="startNodeParameters"
      :loading="isRunning"
      @confirm="handleParameterConfirm"
      @cancel="handleParameterCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, ElDialog, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton } from 'element-plus'
import { DocumentAdd, FolderOpened, Close, VideoPlay, VideoPause, Cpu, Share, Refresh, Document, Link, Cloudy, DataAnalysis, Search, Picture, Operation, DocumentCopy, Delete, Plus, ArrowRight, ChatDotRound, Switch, FullScreen, Connection, SwitchButton } from '@element-plus/icons-vue'
import { workflowApi, type Workflow, type WorkflowDefinition, type WorkflowNode as ApiWorkflowNode, type WorkflowConnection as ApiWorkflowConnection } from '@/api/workflow'
import { llmConfigApi, type LLMConfig } from '@/api/llmConfig'
import { workflowSSEService, type WorkflowExecutionCallbacks } from '@/services/sse'
import { useUserStore } from '@/stores/user'
import NodeParameterConfig from './NodeParameterConfig.vue'
import ParameterInputDialog from './ParameterInputDialog.vue'
import type { NodeInputOutput } from '@/types'

// 路由参数
const route = useRoute()
const workflowId = computed(() => {
  const id = route.params.id
  return id && id !== 'new' ? parseInt(id as string) : null
})

// 用户store
const userStore = useUserStore()

// WebSocket相关状态
const isWebSocketConnected = ref(false)
const webSocketConnectionId = ref<string | null>(null)

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
  parameters?: NodeInputOutput
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
const nodeRefs = ref<Map<string, HTMLElement>>(new Map())

// 工作流管理相关状态
const currentWorkflow = ref<Workflow | null>(null)
const workflows = ref<Workflow[]>([])
const showSaveDialog = ref(false)
const showLoadDialog = ref(false)
const saveForm = reactive({
  name: '',
  description: ''
})
const executionId = ref<number | null>(null)

// 激活/停用相关状态
const isActivating = ref(false)
const isDeactivating = ref(false)

// LLM配置相关状态
const llmConfigs = ref<LLMConfig[]>([])
const availableLLMModels = computed(() => 
  llmConfigs.value.filter(config => config.is_active && !config.is_embedding)
)
const advancedConfigCollapse = ref<string[]>([])

// 过滤后的节点类型（排除开始节点）
const filteredBasicNodeTypes = computed(() => 
  basicNodeTypes.filter(nodeType => nodeType.type !== 'start')
)

// 获取可用变量
const availableVariables = computed(() => {
  if (!selectedNode.value) return []
  
  const variables: Array<{ name: string; type: string; description: string; source: string }> = []
  
  // 获取开始节点的输入参数
  const startNode = nodes.value.find(node => node.type === 'start')
  
  if (startNode && startNode.parameters?.inputs) {
    startNode.parameters.inputs.forEach(input => {
      variables.push({
        name: input.name,
        type: input.type,
        description: input.description || '',
        source: '开始节点'
      })
    })
  }
  
  console.log('最终可用变量列表:', variables)
  
  // 获取当前节点之前的所有节点的输出参数
  const currentNodeIndex = nodes.value.findIndex(n => n.id === selectedNode.value?.id)
  if (currentNodeIndex > 0) {
    for (let i = 0; i < currentNodeIndex; i++) {
      const node = nodes.value[i]
      if (node.type !== 'start' && node.parameters?.outputs) {
        node.parameters.outputs.forEach(output => {
          variables.push({
            name: `${node.name}.${output.name}`,
            type: output.type,
            description: output.description || '',
            source: node.name
          })
        })
      }
    }
  }
  
  return variables
})

// 配置选项卡状态
const activeConfigTab = ref('basic')

// 运行结果面板相关状态
const showExecutionPanel = ref(false)

// 参数输入对话框相关状态
const showParameterDialog = ref(false)
const startNodeParameters = ref<any[]>([])
const userInputParameters = ref<Record<string, any>>({})
const executionStatus = ref<'idle' | 'running' | 'completed' | 'failed'>('idle')
const executionStartTime = ref<Date | null>(null)
const nodeExecutions = ref<NodeExecution[]>([])

// 节点执行状态接口
interface NodeExecution {
  nodeId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  input?: any
  output?: any
  streamOutput?: string
  streamingStarted?: boolean
  error?: string
  startTime?: Date
  endTime?: Date
}

// 节点引用管理
const setNodeRef = (el: HTMLElement | null, nodeId: string) => {
  if (el) {
    nodeRefs.value.set(nodeId, el)
    // 设置初始位置
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      el.style.left = node.x + 'px'
      el.style.top = node.y + 'px'
    }
    
    // 添加原生拖拽事件监听器
    el.addEventListener('mousedown', (event: MouseEvent) => {
      // 重新查找节点，确保获取最新的节点数据
      const currentNode = nodes.value.find(n => n.id === nodeId)
      if (currentNode) {
        startDragNative(currentNode, event)
      }
    })
  } else {
    nodeRefs.value.delete(nodeId)
  }
}

// 画布右键菜单状态
const canvasContextMenu = reactive({
  visible: false,
  x: 0,
  y: 0
})

// 连接点菜单状态
const connectionPointMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  sourceNode: null as WorkflowNode | null,
  sourcePoint: '' // 'output' 或具体的输出点名称
})

// 画布拖动和缩放状态
const canvasTransform = reactive({
  x: 0,
  y: 0,
  scale: 1
})

const isCanvasDragging = ref(false)
const canvasDragStart = reactive({ x: 0, y: 0 })
const canvasDragOffset = reactive({ x: 0, y: 0 })
const hasDraggedCanvas = ref(false) // 跟踪是否实际发生了拖动

// 节点右键菜单状态
const nodeContextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  node: null as WorkflowNode | null
})

// 连接线右键菜单状态
const connectionContextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  connection: null as WorkflowConnection | null
})

// 子菜单状态
const showSubmenu = ref(false)

// 变量选择器状态
const showVariableSelector = ref(false)
const selectedVariableIndex = ref(0)
const promptInput = ref<any>(null)

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
  // {
  //   type: 'condition',
  //   label: '条件分支',
  //   icon: 'Share',
  //   description: '条件判断节点'
  // },
  // {
  //   type: 'loop',
  //   label: '迭代',
  //   icon: 'Refresh',
  //   description: '循环迭代节点'
  // },
  {
    type: 'code',
    label: '代码执行',
    icon: 'Document',
    description: '执行代码片段'
  },
  // {
  //   type: 'http',
  //   label: 'HTTP请求',
  //   icon: 'Link',
  //   description: 'HTTP API调用'
  // }
]

const toolNodeTypes: NodeType[] = [
  // {
  //   type: 'weather',
  //   label: '天气查询',
  //   icon: 'Cloudy',
  //   description: '查询天气信息'
  // },
  // {
  //   type: 'calculator',
  //   label: '计算器',
  //   icon: 'DataAnalysis',
  //   description: '数学计算工具'
  // },
  // {
  //   type: 'search',
  //   label: '搜索',
  //   icon: 'Search',
  //   description: '网络搜索工具'
  // },
  // {
  //   type: 'image_gen',
  //   label: '图像生成',
  //   icon: 'Picture',
  //   description: 'AI图像生成'
  // }
]

// 方法
// 处理提示词输入框的键盘事件
const handlePromptKeydown = (event: KeyboardEvent) => {
  if (event.key === '/' && !showVariableSelector.value) {
    event.preventDefault()
    showVariableSelector.value = true
    selectedVariableIndex.value = 0
    
    // 计算变量选择器的位置
    nextTick(() => {
      const target = event.target as HTMLElement
      const rect = target.getBoundingClientRect()
      const selector = document.querySelector('.variable-selector') as HTMLElement
      if (selector) {
        selector.style.top = `${rect.bottom + 5}px`
        selector.style.left = `${rect.left}px`
      }
    })
  } else if (showVariableSelector.value) {
    if (event.key === 'ArrowUp') {
      event.preventDefault()
      selectedVariableIndex.value = Math.max(0, selectedVariableIndex.value - 1)
    } else if (event.key === 'ArrowDown') {
      event.preventDefault()
      selectedVariableIndex.value = Math.min(availableVariables.value.length - 1, selectedVariableIndex.value + 1)
    } else if (event.key === 'Enter') {
      event.preventDefault()
      selectVariable(availableVariables.value[selectedVariableIndex.value])
    } else if (event.key === 'Escape') {
      event.preventDefault()
      showVariableSelector.value = false
    }
  }
}

// 选择变量
const selectVariable = (variable: { name: string; type: string; description: string; source: string }) => {
  if (selectedNode.value && selectedNode.value.type === 'llm') {
    const currentPrompt = selectedNode.value.config.prompt || ''
    const variableRef = `{${variable.name}}`
    selectedNode.value.config.prompt = currentPrompt + variableRef
  }
  showVariableSelector.value = false
}

// 点击变量选择
const onVariableClick = (variable: { name: string; type: string; description: string; source: string }) => {
  selectVariable(variable)
}

// 处理全局点击事件，用于关闭变量选择器
const handleGlobalClick = (event: MouseEvent) => {
  if (!showVariableSelector.value) return
  
  const target = event.target as HTMLElement
  const variableSelector = document.querySelector('.variable-selector')
  const promptInputContainer = document.querySelector('.prompt-input-container')
  
  // 如果点击的不是变量选择器或提示词输入容器，则关闭选择器
  if (variableSelector && !variableSelector.contains(target) && 
      promptInputContainer && !promptInputContainer.contains(target)) {
    showVariableSelector.value = false
    selectedVariableIndex.value = -1
  }
}

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
    config: getDefaultConfig(nodeType.type),
    parameters: getDefaultNodeParameters(nodeType.type)
  }
  nodes.value.push(newNode)
  return newNode
}

// 获取节点默认参数配置
const getDefaultNodeParameters = (nodeType: string): NodeInputOutput => {
  const defaultParameters: Record<string, NodeInputOutput> = {
    start: {
      inputs: [],
      outputs: [
        { name: 'workflow_input', type: 'object', description: '工作流输入数据', required: true, default_value: null }
      ]
    },
    end: {
      inputs: [
        { name: 'result', type: 'object', description: '最终结果', required: true, default_value: null, source: 'node' }
      ],
      outputs: []
    },
    llm: {
      inputs: [
        { name: 'prompt_variables', type: 'object', description: '提示词变量', required: false, default_value: {}, source: 'node' }
      ],
      outputs: [
        { name: 'response', type: 'string', description: 'LLM响应内容', required: true, default_value: null },
        { name: 'tokens_used', type: 'number', description: '使用的Token数量', required: false, default_value: 0 }
      ]
    },
    code: {
      inputs: [
        { name: 'input_data', type: 'object', description: '代码输入数据', required: false, default_value: {}, source: 'node' }
      ],
      outputs: [
        { name: 'result', type: 'object', description: '代码执行结果', required: true, default_value: null },
        { name: 'output', type: 'string', description: '标准输出', required: false, default_value: '' }
      ]
    },
    http: {
      inputs: [
        { name: 'url_params', type: 'object', description: 'URL参数', required: false, default_value: {}, source: 'node' },
        { name: 'request_data', type: 'object', description: '请求数据', required: false, default_value: {}, source: 'node' }
      ],
      outputs: [
        { name: 'response_data', type: 'object', description: '响应数据', required: true, default_value: null },
        { name: 'status_code', type: 'number', description: 'HTTP状态码', required: true, default_value: 200 }
      ]
    },
    condition: {
      inputs: [
        { name: 'condition_data', type: 'object', description: '条件判断数据', required: true, default_value: {}, source: 'node' }
      ],
      outputs: [
        { name: 'result', type: 'boolean', description: '条件判断结果', required: true, default_value: false }
      ]
    }
  }
  
  // 工具节点的默认参数
  const toolDefaults: NodeInputOutput = {
    inputs: [
      { name: 'tool_input', type: 'object', description: '工具输入参数', required: false, default_value: {}, source: 'node' }
    ],
    outputs: [
      { name: 'tool_output', type: 'object', description: '工具输出结果', required: true, default_value: null }
    ]
  }
  
  return defaultParameters[nodeType] || toolDefaults
}

const getDefaultConfig = (nodeType: string) => {
  const configs: Record<string, any> = {
    llm: {
      model: '',
      temperature: 0.7,
      prompt: '',
      max_tokens: 1000
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
  // 防护性检查：确保节点对象存在且有效
  if (!node || !node.id) {
    console.warn('selectNode: Invalid node object', node)
    return
  }
  
  // 确保节点配置对象完整
  if (node.type === 'llm' && node.config) {
    // 确保LLM节点有所有必需的配置字段
    if (node.config.max_tokens === undefined) {
      node.config.max_tokens = 1000
    }
    if (node.config.temperature === undefined) {
      node.config.temperature = 0.7
    }
    if (node.config.model === undefined) {
      node.config.model = ''
    }
    if (node.config.prompt === undefined) {
      node.config.prompt = ''
    }
  }
  
  // 确保parameters属性存在，但不覆盖已有的参数
  console.log(`selectNode - 节点 ${node.id} 的原始参数:`, node.parameters)
  console.log(`selectNode - 参数是否为空:`, !node.parameters)
  if (!node.parameters) {
    console.log(`selectNode - 使用默认参数`)
    node.parameters = getDefaultNodeParameters(node.type)
  } else {
    console.log(`selectNode - 保持原有参数`)
  }
  console.log(`selectNode - 节点 ${node.id} 的最终参数:`, node.parameters)
  
  selectedNode.value = node
  selectedConnection.value = null
}

const selectConnection = (connection: Connection) => {
  selectedConnection.value = connection
  selectedNode.value = null
}

// 获取可用的源节点（用于参数配置）
const getAvailableSourceNodes = (currentNodeId: string) => {
  return nodes.value.filter(node => {
    // 排除当前节点和结束节点
    if (node.id === currentNodeId || node.type === 'end') {
      return false
    }
    
    // 检查是否存在从源节点到当前节点的路径
    const hasPath = findPath(node.id, currentNodeId)
    return hasPath
  })
}

// 查找两个节点之间是否存在路径
const findPath = (fromNodeId: string, toNodeId: string): boolean => {
  const visited = new Set<string>()
  const queue = [fromNodeId]
  
  while (queue.length > 0) {
    const currentId = queue.shift()!
    if (currentId === toNodeId) {
      return true
    }
    
    if (visited.has(currentId)) {
      continue
    }
    visited.add(currentId)
    
    // 找到所有从当前节点出发的连接
    const outgoingConnections = connections.value.filter(conn => conn.from === currentId)
    for (const conn of outgoingConnections) {
      if (!visited.has(conn.to)) {
        queue.push(conn.to)
      }
    }
  }
  
  return false
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
  
  // 获取节点DOM元素
  const nodeElement = nodeRefs.value.get(node.id)
  if (!nodeElement) return
  
  const onMouseMove = (e: MouseEvent) => {
    const rect = canvas.value?.getBoundingClientRect()
    if (rect && draggedNode.value && nodeElement) {
      const newX = e.clientX - rect.left - dragOffset.x
      const newY = e.clientY - rect.top - dragOffset.y
      
      // 直接更新DOM位置，获得最佳性能
      nodeElement.style.left = newX + 'px'
      nodeElement.style.top = newY + 'px'
      
      // 同时更新数据，用于连接线计算
      draggedNode.value.x = newX
      draggedNode.value.y = newY
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

// 原生拖拽实现（完全绕过Vue）
const startDragNative = (node: WorkflowNode, event: MouseEvent) => {
  event.preventDefault()
  event.stopPropagation()
  
  const nodeElement = nodeRefs.value.get(node.id)
  if (!nodeElement) return
  
  const rect = nodeElement.getBoundingClientRect()
  const canvasRect = canvas.value?.getBoundingClientRect()
  if (!canvasRect) return
  
  // 计算鼠标在节点内的偏移量（考虑画布变换）
  const offsetX = event.clientX - rect.left
  const offsetY = event.clientY - rect.top
  
  // 添加拖拽样式
  nodeElement.classList.add('dragging')
  
  const onMouseMove = (e: MouseEvent) => {
    // 计算鼠标在画布中的位置（相对于画布容器）
    const canvasMouseX = e.clientX - canvasRect.left
    const canvasMouseY = e.clientY - canvasRect.top
    
    // 转换为变换容器中的坐标（考虑画布的平移和缩放）
    const transformedMouseX = (canvasMouseX - canvasTransform.x) / canvasTransform.scale
    const transformedMouseY = (canvasMouseY - canvasTransform.y) / canvasTransform.scale
    
    // 计算节点在变换容器中的新位置
    const newX = transformedMouseX - (offsetX / canvasTransform.scale)
    const newY = transformedMouseY - (offsetY / canvasTransform.scale)
    
    // 直接更新DOM位置
    nodeElement.style.left = newX + 'px'
    nodeElement.style.top = newY + 'px'
    
    // 更新Vue数据（用于连接线）
    node.x = newX
    node.y = newY
  }
  
  const onMouseUp = () => {
    nodeElement.classList.remove('dragging')
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

// WebSocket初始化和回调处理
const initializeSSE = async () => {
  try {
    const userStore = useUserStore()
    const token = localStorage.getItem('access_token')
    
    if (!token || !userStore.user) {
      console.warn('用户未登录或无有效token，无法初始化SSE连接')
      return
    }

    // 设置SSE回调
    const callbacks: WorkflowExecutionCallbacks = {
      onWorkflowStarted: (data) => {
        console.log('工作流开始执行:', data)
        executionStatus.value = 'running'
        executionStartTime.value = new Date()
        runningNodes.value = []
        completedNodes.value = []
        errorNodes.value = []
        nodeExecutions.value = []
        isWebSocketConnected.value = true // 重用这个状态表示SSE连接
      },
      
      onWorkflowCompleted: (data) => {
        console.log('工作流执行完成:', data)
        executionStatus.value = 'completed'
        runningNodes.value = []
        isWebSocketConnected.value = false
        ElMessage.success('工作流执行完成')
      },
      
      onWorkflowFailed: (data) => {
        console.log('工作流执行失败:', data)
        executionStatus.value = 'failed'
        runningNodes.value = []
        isWebSocketConnected.value = false
        ElMessage.error(`工作流执行失败: ${data.error_message || data.error}`)
      },
      
      onNodeStarted: (nodeId: string, data: any) => {
        console.log('节点开始执行:', nodeId, data)
        const nodeName = data.node_name || nodeId
        // 添加到运行中的节点
        if (!runningNodes.value.includes(nodeName)) {
          runningNodes.value.push(nodeName)
        }
        // 从其他状态中移除
        completedNodes.value = completedNodes.value.filter(n => n !== nodeName)
        errorNodes.value = errorNodes.value.filter(n => n !== nodeName)
        
        // 添加节点执行记录
        nodeExecutions.value.push({
          nodeId: nodeId,
          status: 'running',
          input: {},  // started状态没有input数据，将在completed时更新
          output: null,
          error: null,
          startTime: data.started_at ? new Date(data.started_at) : new Date(),
          endTime: null
        })
      },
      
      onNodeCompleted: (nodeId: string, data: any) => {
        console.log('节点执行完成:', nodeId, data)
        const nodeName = data.node_name || nodeId
        // 从运行中移除，添加到完成
        runningNodes.value = runningNodes.value.filter(n => n !== nodeName)
        if (!completedNodes.value.includes(nodeName)) {
          completedNodes.value.push(nodeName)
        }
        
        // 更新节点执行记录
        const execution = nodeExecutions.value.find(e => e.nodeId === nodeId && e.status === 'running')
        if (execution) {
          execution.status = 'completed'
          execution.output = data.output || {}  // 使用正确的output字段
          // 如果output中包含输入数据（如start节点），也更新input
          if (data.output && data.output.user_input) {
            execution.input = data.output.user_input || {}
          }
          execution.endTime = data.completed_at ? new Date(data.completed_at) : new Date()
        }
      },
      
      onNodeFailed: (nodeId, data) => {
        console.log('节点执行失败:', nodeId, data)
        const nodeName = data.node_name || nodeId
        // 从运行中移除，添加到错误
        runningNodes.value = runningNodes.value.filter(n => n !== nodeName)
        if (!errorNodes.value.includes(nodeName)) {
          errorNodes.value.push(nodeName)
        }
        
        // 更新节点执行记录，修正错误数据路径
        const execution = nodeExecutions.value.find(e => e.nodeId === nodeId && e.status === 'running')
        if (execution) {
          execution.status = 'failed'
          execution.error = data.error_message || data.error  // 直接从data中获取error_message
          execution.endTime = data.completed_at ? new Date(data.completed_at) : new Date()
        }
      },
      
      onWorkflowResult: (data) => {
        console.log('工作流结果:', data)
        // 处理最终结果
      },
      
      onError: (error) => {
        console.error('SSE错误:', error)
        isWebSocketConnected.value = false
        ElMessage.error(`实时连接错误: ${error}`)
      }
    }

    // 设置SSE回调
    workflowSSEService.setCallbacks(callbacks)
    
  } catch (error) {
    console.error('初始化SSE失败:', error)
    ElMessage.error('初始化实时连接失败')
  }
}

const runWorkflow = async () => {
  if (isRunning.value) {
    ElMessage.warning('工作流正在执行中')
    return
  }
  
  if (!currentWorkflow.value) {
    ElMessage.error('请先保存工作流')
    return
  }
  
  // 添加调试日志
  console.log('currentWorkflow.value:', currentWorkflow.value)
  console.log('currentWorkflow.value.id:', currentWorkflow.value.id)
  console.log('currentWorkflow.value.id type:', typeof currentWorkflow.value.id)
  console.log('currentWorkflow.value.id === undefined:', currentWorkflow.value.id === undefined)
  console.log('currentWorkflow.value.id == null:', currentWorkflow.value.id == null)
  console.log('!currentWorkflow.value.id:', !currentWorkflow.value.id)
  
  if (!currentWorkflow.value.id || currentWorkflow.value.id === undefined || currentWorkflow.value.id === null) {
    ElMessage.error('工作流ID无效，请重新保存工作流')
    return
  }
  
  // 检查开始节点是否有输入参数
  const startNode = nodes.value.find(node => node.type === 'start')
  console.log('开始节点:', startNode)
  console.log('开始节点参数:', startNode?.parameters)
  console.log('开始节点输入参数:', startNode?.parameters?.inputs)
  
  if (startNode && startNode.parameters && startNode.parameters.inputs && startNode.parameters.inputs.length > 0) {
    // 准备参数列表
    startNodeParameters.value = startNode.parameters.inputs.map(input => ({
      name: input.name,
      type: input.type,
      value: input.default_value || ''
    }))
    
    // 显示参数输入对话框
    showParameterDialog.value = true
    return // 等待用户输入参数
  }
  
  // 如果没有参数或已经有参数值，直接执行工作流
  await executeWorkflowWithParameters()
}

// 执行工作流的实际逻辑
const executeWorkflowWithParameters = async () => {
  isRunning.value = true
  runningNodes.value = []
  completedNodes.value = []
  errorNodes.value = []
  
  // 初始化运行结果面板
  showExecutionPanel.value = true
  executionStatus.value = 'running'
  executionStartTime.value = new Date()
  nodeExecutions.value = []
  
  // 不再预先创建节点执行记录，等待SSE回调时动态创建
  
  try {
    // 重置所有节点状态
    nodes.value.forEach(node => {
      if (node.result) {
        delete node.result
      }
    })
    
    // 使用SSE执行工作流，传递用户输入的参数
    await workflowSSEService.startWorkflowExecution(currentWorkflow.value.id, {
      user_input: userInputParameters.value
    })
    
    ElMessage.success('工作流开始执行')
    
  } catch (error) {
    console.error('工作流执行失败:', error)
    ElMessage.error('工作流执行失败: ' + (error as Error).message)
  } finally {
    isRunning.value = false
  }
}

// 处理参数输入确认
const handleParameterConfirm = async (parameters: Record<string, any>) => {
  userInputParameters.value = parameters
  showParameterDialog.value = false
  
  // 执行工作流
  await executeWorkflowWithParameters()
}

// 处理参数输入取消
const handleParameterCancel = () => {
  showParameterDialog.value = false
  userInputParameters.value = {}
}

// 轮询执行状态
const pollExecutionStatus = async (executionId: number) => {
  const maxAttempts = 30 // 最多轮询30次
  let attempts = 0
  
  const poll = async () => {
    try {
      const response = await workflowApi.getExecution(executionId)
      
      // 添加调试日志
      console.log('轮询响应:', response)
      console.log('response.data:', response.data)
      
      // 处理响应数据结构
      const execution = response.data.data || response.data
      console.log('解析后的 execution:', execution)
      console.log('execution.status:', execution.status)
      
      // 更新运行结果面板的整体状态
      executionStatus.value = execution.status
      
      // 更新节点执行状态
      if (execution.node_executions) {
        execution.node_executions.forEach(nodeExec => {
          const node = nodes.value.find(n => n.id === nodeExec.node_id)
          if (node) {
            // 更新画布上的节点状态
            node.result = {
              success: nodeExec.status === 'completed',
              data: nodeExec.output_data || nodeExec.error_message
            }
            
            // 更新运行结果面板中的节点执行状态
            updateNodeExecution(nodeExec.node_id, {
              status: nodeExec.status,
              input: nodeExec.input_data,
              output: nodeExec.output_data,
              error: nodeExec.error_message,
              startTime: nodeExec.start_time ? new Date(nodeExec.start_time) : undefined,
              endTime: nodeExec.end_time ? new Date(nodeExec.end_time) : undefined
            })
            
            // 如果是LLM节点且正在运行，模拟流式输出
            if (node.type === 'llm' && nodeExec.status === 'running') {
              simulateStreamingOutput(nodeExec.node_id)
            }
            
            // 更新画布节点状态数组
            const nodeId = node.id
            if (nodeExec.status === 'running') {
              if (!runningNodes.value.includes(nodeId)) {
                runningNodes.value.push(nodeId)
              }
              completedNodes.value = completedNodes.value.filter(id => id !== nodeId)
              errorNodes.value = errorNodes.value.filter(id => id !== nodeId)
            } else if (nodeExec.status === 'completed') {
              if (!completedNodes.value.includes(nodeId)) {
                completedNodes.value.push(nodeId)
              }
              runningNodes.value = runningNodes.value.filter(id => id !== nodeId)
              errorNodes.value = errorNodes.value.filter(id => id !== nodeId)
            } else if (nodeExec.status === 'failed') {
              if (!errorNodes.value.includes(nodeId)) {
                errorNodes.value.push(nodeId)
              }
              runningNodes.value = runningNodes.value.filter(id => id !== nodeId)
              completedNodes.value = completedNodes.value.filter(id => id !== nodeId)
            }
          }
        })
      }
      
      if (execution.status === 'completed') {
        ElMessage.success('工作流执行完成')
        executionStatus.value = 'completed'
        return
      } else if (execution.status === 'failed') {
        ElMessage.error('工作流执行失败: ' + execution.error_message)
        executionStatus.value = 'failed'
        return
      } else if ((execution.status === 'running' || execution.status === 'pending') && attempts < maxAttempts) {
        attempts++
        console.log(`轮询第 ${attempts} 次，状态: ${execution.status}`)
        setTimeout(poll, 1000) // 1秒后再次轮询
      } else if (attempts >= maxAttempts) {
        console.log(`轮询超时，已尝试 ${attempts} 次，最终状态: ${execution.status}`)
        ElMessage.warning('工作流执行超时')
      } else {
        console.log(`未知状态: ${execution.status}`)
        ElMessage.warning(`工作流状态异常: ${execution.status}`)
      }
    } catch (error) {
      console.error('轮询执行状态失败:', error)
      ElMessage.error('获取执行状态失败')
    }
  }
  
  await poll()
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

// 运行结果面板辅助方法
const getExecutionStatusText = () => {
  switch (executionStatus.value) {
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '执行失败'
    default: return '待执行'
  }
}

const getNodeStatusText = (status: string) => {
  switch (status) {
    case 'running': return '运行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'pending': return '等待中'
    default: return '未知'
  }
}

const getNodeById = (nodeId: string) => {
  return nodes.value.find(node => node.id === nodeId)
}

const formatData = (data: any) => {
  if (data === null || data === undefined) {
    return '无数据'
  }
  
  if (typeof data === 'string') {
    // 如果是JSON字符串，尝试格式化
    try {
      const parsed = JSON.parse(data)
      return JSON.stringify(parsed, null, 2)
    } catch {
      return data
    }
  }
  
  if (typeof data === 'number' || typeof data === 'boolean') {
    return String(data)
  }
  
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return '空数组'
    }
    return JSON.stringify(data, null, 2)
  }
  
  if (typeof data === 'object') {
    if (Object.keys(data).length === 0) {
      return '空对象'
    }
    return JSON.stringify(data, null, 2)
  }
  
  return String(data)
}

const formatTime = (time: Date) => {
  return time.toLocaleTimeString()
}

const formatDuration = (startTime: Date, endTime: Date) => {
  const duration = endTime.getTime() - startTime.getTime()
  if (duration < 1000) {
    return `${duration}ms`
  } else if (duration < 60000) {
    return `${(duration / 1000).toFixed(1)}s`
  } else {
    return `${(duration / 60000).toFixed(1)}m`
  }
}

const formatExecutionTime = () => {
  if (!executionStartTime.value) return ''
  const now = new Date()
  const duration = now.getTime() - executionStartTime.value.getTime()
  if (duration < 1000) {
    return `${duration}ms`
  } else if (duration < 60000) {
    return `${(duration / 1000).toFixed(1)}s`
  } else {
    return `${(duration / 60000).toFixed(1)}m`
  }
}

// 更新节点执行状态
const updateNodeExecution = (nodeId: string, updates: Partial<NodeExecution>) => {
  const index = nodeExecutions.value.findIndex(exec => exec.nodeId === nodeId)
  if (index !== -1) {
    nodeExecutions.value[index] = { ...nodeExecutions.value[index], ...updates }
  }
}

// 添加流式输出
const appendStreamOutput = (nodeId: string, content: string) => {
  const execution = nodeExecutions.value.find(exec => exec.nodeId === nodeId)
  if (execution) {
    execution.streamOutput = (execution.streamOutput || '') + content
  }
}

// 模拟流式输出（用于演示）
const simulateStreamingOutput = (nodeId: string) => {
  const execution = nodeExecutions.value.find(exec => exec.nodeId === nodeId)
  if (!execution || execution.streamingStarted) return
  
  execution.streamingStarted = true
  execution.streamOutput = ''
  
  // 模拟的响应文本
  const mockResponse = "这是一个模拟的大模型响应。我正在逐字输出这段文本，以演示流式输出的效果。您可以看到文字是如何一个一个地出现的，就像真正的AI模型在思考和生成回答一样。这种流式输出可以让用户更好地感受到AI的工作过程，提升用户体验。"
  
  let index = 0
  const streamInterval = setInterval(() => {
    if (index < mockResponse.length) {
      appendStreamOutput(nodeId, mockResponse[index])
      index++
    } else {
      clearInterval(streamInterval)
      // 流式输出完成后，设置最终输出
      updateNodeExecution(nodeId, {
        output: execution.streamOutput
      })
    }
  }, 50) // 每50ms输出一个字符
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

const onCanvasClick = (event: MouseEvent) => {
  // 如果正在拖动画布或刚刚完成拖动，不处理点击事件
  if (isCanvasDragging.value || hasDraggedCanvas.value) {
    return
  }
  
  selectedNode.value = null
  selectedConnection.value = null
  // 隐藏所有菜单
  hideAllMenus()
}

// 显示画布右键菜单
const showCanvasContextMenu = (event: MouseEvent) => {
  // 检查是否点击在节点上，如果是则不显示画布菜单
  const target = event.target as HTMLElement
  const isClickOnNode = target.closest('.workflow-node')
  
  if (isClickOnNode) {
    return // 如果点击在节点上，不显示画布菜单
  }
  
  hideAllMenus()
  canvasContextMenu.x = event.clientX
  canvasContextMenu.y = event.clientY
  canvasContextMenu.visible = true
}

// 隐藏所有菜单
const hideAllMenus = () => {
  canvasContextMenu.visible = false
  connectionPointMenu.visible = false
  nodeContextMenu.visible = false
  connectionContextMenu.visible = false
}

// 处理文档点击事件 - 只在左键点击时隐藏菜单
const handleDocumentClick = (event: MouseEvent) => {
  // 只在左键点击时隐藏菜单，避免右键点击时立即隐藏右键菜单
  if (event.button === 0) {
    hideAllMenus()
  }
}

// 画布拖动相关方法
const startCanvasDrag = (event: MouseEvent) => {
  // 检查是否点击在节点或连接点上
  const target = event.target as HTMLElement
  const isClickOnNode = target.closest('.workflow-node') || target.closest('.connection-point')
  
  // 如果点击在节点上，不启动画布拖动
  if (isClickOnNode) {
    return
  }
  
  // 在空白处点击鼠标左键或中键时允许拖动画布
  if (event.button === 0 || event.button === 1) {
    event.preventDefault()
    event.stopPropagation()
    isCanvasDragging.value = true
    hasDraggedCanvas.value = false // 重置拖动标志
    canvasDragStart.x = event.clientX - canvasTransform.x
    canvasDragStart.y = event.clientY - canvasTransform.y
    
    // 添加拖拽状态的CSS类
    if (canvas.value) {
      canvas.value.classList.add('dragging')
    }
  }
}

const onCanvasMouseMove = (event: MouseEvent) => {
  if (isCanvasDragging.value) {
    event.preventDefault()
    hasDraggedCanvas.value = true // 标记实际发生了拖动
    canvasTransform.x = event.clientX - canvasDragStart.x
    canvasTransform.y = event.clientY - canvasDragStart.y
  }
}

const onCanvasMouseUp = () => {
  if (isCanvasDragging.value) {
    isCanvasDragging.value = false
    
    // 移除拖拽状态的CSS类
    if (canvas.value) {
      canvas.value.classList.remove('dragging')
    }
    
    // 延迟重置拖动标志，防止点击事件立即触发
    setTimeout(() => {
      hasDraggedCanvas.value = false
    }, 10)
  }
}

// 画布缩放方法
const onCanvasWheel = (event: WheelEvent) => {
  if (event.ctrlKey) {
    // 阻止浏览器默认的缩放行为
    event.preventDefault()
    event.stopPropagation()
    
    const rect = canvas.value?.getBoundingClientRect()
    if (!rect) return
    
    const mouseX = event.clientX - rect.left
    const mouseY = event.clientY - rect.top
    
    // 计算缩放前的鼠标在画布中的位置
    const beforeZoomX = (mouseX - canvasTransform.x) / canvasTransform.scale
    const beforeZoomY = (mouseY - canvasTransform.y) / canvasTransform.scale
    
    // 计算新的缩放比例
    const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1
    const newScale = Math.max(0.1, Math.min(3, canvasTransform.scale * zoomFactor))
    
    // 计算缩放后的鼠标在画布中的位置
    const afterZoomX = beforeZoomX * newScale
    const afterZoomY = beforeZoomY * newScale
    
    // 调整画布位置以保持鼠标位置不变
    canvasTransform.x = mouseX - afterZoomX
    canvasTransform.y = mouseY - afterZoomY
    canvasTransform.scale = newScale
  }
}

// 重置画布视图
const resetCanvasView = () => {
  canvasTransform.x = 0
  canvasTransform.y = 0
  canvasTransform.scale = 1
}

// 适应画布内容
const fitCanvasToContent = () => {
  if (nodes.value.length === 0) {
    resetCanvasView()
    return
  }
  
  // 计算所有节点的边界
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  
  nodes.value.forEach(node => {
    minX = Math.min(minX, node.x)
    minY = Math.min(minY, node.y)
    maxX = Math.max(maxX, node.x + 180) // 节点宽度
    maxY = Math.max(maxY, node.y + 100) // 节点高度估计
  })
  
  const rect = canvas.value?.getBoundingClientRect()
  if (!rect) return
  
  const contentWidth = maxX - minX
  const contentHeight = maxY - minY
  const padding = 50
  
  // 计算合适的缩放比例
  const scaleX = (rect.width - padding * 2) / contentWidth
  const scaleY = (rect.height - padding * 2) / contentHeight
  const scale = Math.min(scaleX, scaleY, 1) // 不超过100%
  
  // 计算居中位置
  const centerX = (minX + maxX) / 2
  const centerY = (minY + maxY) / 2
  
  canvasTransform.scale = scale
  canvasTransform.x = rect.width / 2 - centerX * scale
  canvasTransform.y = rect.height / 2 - centerY * scale
}

// 显示连接线右键菜单
const showConnectionContextMenu = (event: MouseEvent, connection: WorkflowConnection) => {
  event.stopPropagation()
  hideAllMenus()
  connectionContextMenu.visible = true
  connectionContextMenu.x = event.clientX
  connectionContextMenu.y = event.clientY
  connectionContextMenu.connection = connection
}

// 从画布右键菜单添加节点
const addNodeFromContextMenu = (nodeType: NodeType) => {
  const rect = canvas.value?.getBoundingClientRect()
  if (rect) {
    const x = canvasContextMenu.x - rect.left
    const y = canvasContextMenu.y - rect.top
    addNode(nodeType, x, y)
  }
  hideAllMenus()
}

// 显示连接点菜单
const showConnectionPointMenu = (node: WorkflowNode, pointType: string, event: MouseEvent) => {
  hideAllMenus()
  connectionPointMenu.x = event.clientX
  connectionPointMenu.y = event.clientY
  connectionPointMenu.sourceNode = node
  connectionPointMenu.sourcePoint = pointType
  connectionPointMenu.visible = true
}

// 从连接点菜单添加节点
const addNodeFromConnectionPoint = (nodeType: NodeType) => {
  if (connectionPointMenu.sourceNode) {
    const sourceNode = connectionPointMenu.sourceNode
    const newX = sourceNode.x + 250 // 在源节点右侧250px处添加新节点
    const newY = sourceNode.y
    
    const newNode = addNode(nodeType, newX, newY)
    
    // 自动创建连接
    if (newNode) {
      connections.value.push({
        id: `${sourceNode.id}-${newNode.id}`,
        from: sourceNode.id,
        to: newNode.id,
        fromPoint: connectionPointMenu.sourcePoint,
        toPoint: 'input'
      })
    }
  }
  hideAllMenus()
}

const saveWorkflow = () => {
  if (nodes.value.length === 0) {
    ElMessage.warning('工作流为空，无法保存')
    return
  }
  
  // 如果已有工作流，直接更新
  if (currentWorkflow.value) {
    updateCurrentWorkflow()
  } else {
    // 显示保存对话框
    showSaveDialog.value = true
  }
}

// 保存新工作流
const saveNewWorkflow = async () => {
  if (!saveForm.name.trim()) {
    ElMessage.warning('请输入工作流名称')
    return
  }
  
  try {
    const workflowDefinition: WorkflowDefinition = {
      nodes: nodes.value.map(node => ({
        id: node.id,
        type: node.type,
        name: node.name,
        description: node.description,
        config: node.config || {},
        position: { x: node.x, y: node.y },
        parameters: node.parameters
      })),
      connections: connections.value.map((conn, index) => ({
        id: conn.id || `conn_${index}`,
        from: conn.from,
        to: conn.to
      }))
    }
    
    const response = await workflowApi.createWorkflow({
      name: saveForm.name,
      description: saveForm.description,
      definition: workflowDefinition
    })
    
    // 修复：使用response.data而不是response
    const workflow = response.data
    
    // 添加调试日志
    console.log('API响应 response:', response)
    console.log('工作流数据 workflow:', workflow)
    console.log('workflow.id:', workflow.id)
    console.log('workflow.id type:', typeof workflow.id)
    
    currentWorkflow.value = workflow
    
    // 验证赋值后的状态
    console.log('赋值后 currentWorkflow.value:', currentWorkflow.value)
    console.log('赋值后 currentWorkflow.value.id:', currentWorkflow.value.id)
    
    showSaveDialog.value = false
    saveForm.name = ''
    saveForm.description = ''
    
    ElMessage.success('工作流保存成功')
  } catch (error) {
    console.error('保存工作流失败:', error)
    ElMessage.error('保存工作流失败: ' + (error as Error).message)
  }
}

// 更新当前工作流
const updateCurrentWorkflow = async () => {
  if (!currentWorkflow.value) return
  
  try {
    const workflowDefinition: WorkflowDefinition = {
      nodes: nodes.value.map(node => ({
        id: node.id,
        type: node.type,
        name: node.name,
        description: node.description,
        config: node.config || {},
        position: { x: node.x, y: node.y },
        parameters: node.parameters
      })),
      connections: connections.value.map((conn, index) => ({
        id: conn.id || `conn_${index}`,
        from: conn.from,
        to: conn.to
      }))
    }
    
    await workflowApi.updateWorkflow(currentWorkflow.value.id, {
      definition: workflowDefinition
    })
    
    ElMessage.success('工作流更新成功')
  } catch (error) {
    console.error('更新工作流失败:', error)
    ElMessage.error('更新工作流失败: ' + (error as Error).message)
  }
}

const loadWorkflow = async () => {
  try {
    const response = await workflowApi.getWorkflows()
    workflows.value = response.workflows
    showLoadDialog.value = true
  } catch (error) {
    console.error('获取工作流列表失败:', error)
    ElMessage.error('获取工作流列表失败: ' + (error as Error).message)
  }
}

// 加载选中的工作流
const loadSelectedWorkflow = async (workflow: Workflow) => {
  try {
    const fullWorkflow = await workflowApi.getWorkflow(workflow.id)
    
    console.log('加载的工作流数据:', fullWorkflow)
    console.log('节点数据:', fullWorkflow.definition.nodes)
    
    // 转换节点数据
    nodes.value = fullWorkflow.definition.nodes.map(node => {
      console.log(`节点 ${node.id} 的参数:`, node.parameters)
      // 确保参数存在，如果不存在则使用默认参数
      const parameters = node.parameters || getDefaultNodeParameters(node.type)
      console.log(`节点 ${node.id} 最终参数:`, parameters)
      return {
        id: node.id,
        type: node.type,
        name: node.name,
        description: node.description,
        x: node.position?.x || 100,
        y: node.position?.y || 100,
        config: node.config,
        parameters: parameters
      }
    })
    
    // 转换连接数据
    connections.value = fullWorkflow.definition.connections.map(conn => ({
      id: `conn-${conn.from_node}-${conn.to_node}`,
      from: conn.from_node,
      to: conn.to_node,
      fromPoint: 'output',
      toPoint: 'input'
    }))
    
    currentWorkflow.value = fullWorkflow
    showLoadDialog.value = false
    selectedNode.value = null
    selectedConnection.value = null
    
    ElMessage.success('工作流加载成功')
  } catch (error) {
    console.error('加载工作流失败:', error)
    ElMessage.error('加载工作流失败: ' + (error as Error).message)
  }
}

// 激活工作流
const activateWorkflow = async () => {
  if (!currentWorkflow.value) {
    ElMessage.error('没有可激活的工作流')
    return
  }
  
  isActivating.value = true
  try {
    await workflowApi.activateWorkflow(currentWorkflow.value.id)
    currentWorkflow.value.status = 'PUBLISHED'
    ElMessage.success('工作流激活成功')
  } catch (error) {
    console.error('激活工作流失败:', error)
    ElMessage.error('激活工作流失败: ' + (error as Error).message)
  } finally {
    isActivating.value = false
  }
}

// 停用工作流
const deactivateWorkflow = async () => {
  if (!currentWorkflow.value) {
    ElMessage.error('没有可停用的工作流')
    return
  }
  
  isDeactivating.value = true
  try {
    await workflowApi.deactivateWorkflow(currentWorkflow.value.id)
    currentWorkflow.value.status = 'ARCHIVED'
    ElMessage.success('工作流停用成功')
  } catch (error) {
    console.error('停用工作流失败:', error)
    ElMessage.error('停用工作流失败: ' + (error as Error).message)
  } finally {
    isDeactivating.value = false
  }
}

// 右键菜单相关方法
const showNodeContextMenu = (event: MouseEvent, node: WorkflowNode) => {
  event.preventDefault()
  event.stopPropagation() // 阻止事件冒泡到画布
  
  // 如果是开始节点，不显示右键菜单
  if (node.type === 'start') {
    return
  }
  
  hideAllMenus()
  nodeContextMenu.visible = true
  nodeContextMenu.x = event.clientX
  nodeContextMenu.y = event.clientY
  nodeContextMenu.node = node
}





const copyNode = () => {
  if (nodeContextMenu.node) {
    const newNode: WorkflowNode = {
      ...nodeContextMenu.node,
      id: `node_${Date.now()}`,
      x: nodeContextMenu.node.x + 50,
      y: nodeContextMenu.node.y + 50,
      name: nodeContextMenu.node.name + ' (副本)'
    }
    nodes.value.push(newNode)
    ElMessage.success('节点已复制')
  }
  hideAllMenus()
}

const deleteSelectedItem = () => {
  if (nodeContextMenu.node) {
    deleteNode(nodeContextMenu.node.id)
  }
  hideAllMenus()
}

// 删除连接线
const deleteConnection = () => {
  if (connectionContextMenu.connection) {
    const connection = connectionContextMenu.connection
    const index = connections.value.findIndex(c => 
      c.from === connection.from && c.to === connection.to
    )
    if (index > -1) {
      connections.value.splice(index, 1)
      ElMessage.success('连接已删除')
    }
  }
  hideAllMenus()
}



// 键盘事件处理
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Delete' && selectedConnection.value) {
    const connection = selectedConnection.value
    const index = connections.value.findIndex(c => 
      c.from === connection.from && c.to === connection.to
    )
    if (index > -1) {
      connections.value.splice(index, 1)
      ElMessage.success('连接已删除')
    }
    selectedConnection.value = null
  }
}



onMounted(async () => {
  // 初始化 - 只在左键点击时隐藏菜单
  document.addEventListener('click', handleDocumentClick)
  document.addEventListener('keydown', handleKeyDown)
  document.addEventListener('mousemove', onCanvasMouseMove)
  document.addEventListener('mouseup', onCanvasMouseUp)
  // 添加全局点击事件监听器，用于关闭变量选择器
  document.addEventListener('click', handleGlobalClick)
  
  // 初始化SSE连接
  await initializeSSE()
  
  // 加载工作流列表
  try {
    const response = await workflowApi.getWorkflows()
    workflows.value = response.workflows
  } catch (error) {
    console.error('加载工作流列表失败:', error)
  }
  
  // 加载LLM配置列表
  try {
    const response = await llmConfigApi.getLLMConfigs({ is_active: true })
    llmConfigs.value = response.data || []
  } catch (error) {
    console.error('加载LLM配置失败:', error)
  }
  
  // 根据路由参数加载工作流或创建新工作流
  console.log('当前路由参数:', route.params)
  console.log('解析的workflowId:', workflowId.value)
  
  if (workflowId.value) {
    // 加载现有工作流
    try {
      console.log('开始加载工作流，ID:', workflowId.value)
      const response = await workflowApi.getWorkflow(workflowId.value)
      console.log('API返回的响应数据:', response)
      console.log('提取的工作流数据:', response.data)
      await loadWorkflowData(response.data)
    } catch (error) {
      console.error('加载工作流失败:', error)
      ElMessage.error('加载工作流失败: ' + (error as Error).message)
      // 如果加载失败，创建默认工作流
      initializeDefaultWorkflow()
    }
  } else {
    // 创建新工作流，初始化默认节点
    console.log('没有workflowId，初始化默认工作流')
    initializeDefaultWorkflow()
  }
})

// 初始化默认工作流
const initializeDefaultWorkflow = () => {
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
  currentWorkflow.value = null
}

// 加载工作流数据
const loadWorkflowData = async (workflow: Workflow) => {
  try {
    console.log('loadWorkflowData 接收到的工作流数据:', workflow)
    console.log('工作流名称:', workflow?.name)
    console.log('工作流定义:', workflow?.definition)
    
    // 安全检查：确保definition存在且包含必要的字段
    if (!workflow.definition) {
      console.warn('工作流定义为空，初始化默认工作流')
      initializeDefaultWorkflow()
      currentWorkflow.value = workflow
      ElMessage.warning(`工作流 "${workflow.name}" 定义为空，已初始化默认节点`)
      return
    }

    // 安全检查：确保nodes数组存在
    const workflowNodes = workflow.definition.nodes || []
    const workflowConnections = workflow.definition.connections || []

    // 转换节点数据
    nodes.value = workflowNodes.map(node => {
      console.log(`loadWorkflowData - 节点 ${node.id} 的参数:`, node.parameters)
      // 确保参数存在，如果不存在则使用默认参数
      const parameters = node.parameters || getDefaultNodeParameters(node.type)
      console.log(`loadWorkflowData - 节点 ${node.id} 最终参数:`, parameters)
      return {
        id: node.id,
        type: node.type,
        name: node.name,
        description: node.description || '',
        x: node.position?.x || 100,
        y: node.position?.y || 100,
        config: node.config || {},
        parameters: parameters
      }
    })
    
    // 转换连接数据
    connections.value = workflowConnections.map(conn => ({
      id: conn.id,
      from: conn.from,
      to: conn.to,
      fromPoint: 'output',
      toPoint: 'input'
    }))

    // 如果没有节点，添加默认的开始节点
    if (nodes.value.length === 0) {
      console.warn('工作流没有节点，添加默认开始节点')
      nodes.value.push({
        id: 'start-' + Date.now(),
        type: 'start',
        name: '开始',
        description: '工作流开始节点',
        x: 300,
        y: 200,
        config: {}
      })
    }
    
    currentWorkflow.value = workflow
    ElMessage.success(`工作流 "${workflow.name}" 加载成功`)
  } catch (error) {
    console.error('解析工作流数据失败:', error)
    ElMessage.error('解析工作流数据失败')
    // 发生错误时，初始化默认工作流以确保界面可用
    initializeDefaultWorkflow()
    throw error
  }
}

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
  document.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('mousemove', onCanvasMouseMove)
  document.removeEventListener('mouseup', onCanvasMouseUp)
  // 移除全局点击事件监听器
  document.removeEventListener('click', handleGlobalClick)
  
  // 清理SSE连接
  if (isWebSocketConnected.value) {
    workflowSSEService.disconnect()
  }
})
</script>

<style scoped>
.workflow-editor {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e293b;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #334155;
  border-bottom: 1px solid #475569;
}

.editor-header h2 {
  margin: 0;
  color: #e2e8f0;
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
  background: #334155;
  border-right: 1px solid #475569;
  padding: 16px;
  overflow-y: auto;
}

.tool-group {
  margin-bottom: 24px;
}

.tool-group h4 {
  margin: 0 0 12px 0;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #475569;
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
  background: #475569;
  border: 1px solid #64748b;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
  user-select: none;
  color: #e2e8f0;
}

.node-type-item:hover {
  background: #5b6b7a;
  border-color: #8b5cf6;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.2);
}

.node-type-item:active {
  cursor: grabbing;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.canvas-container.with-execution-panel {
  flex: 0 0 60%;
}

.workflow-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  background: 
    radial-gradient(circle, #64748b 1px, transparent 1px);
  background-size: 20px 20px;
  background-color: #1e293b;
  overflow: hidden;
}

.workflow-node {
  position: absolute;
  width: 180px;
  background: #334155;
  border: 2px solid #64748b;
  border-radius: 8px;
  cursor: move;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  user-select: none;
}

.workflow-node.dragging {
  transition: none;
}

.workflow-node:hover {
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.workflow-node.selected {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3);
}

.workflow-node.running {
  border-color: #f59e0b;
  animation: pulse 1.5s infinite;
}

.workflow-node.completed {
  border-color: #10b981;
}

.workflow-node.error {
  border-color: #ef4444;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(245, 158, 11, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
  }
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #475569;
  border-bottom: 1px solid #64748b;
  border-radius: 6px 6px 0 0;
}

.node-header span {
  flex: 1;
  font-weight: 500;
  color: #e2e8f0;
}

.node-content {
  padding: 12px;
}

.node-content p {
  margin: 0;
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.4;
}

.node-result {
  margin-top: 8px;
}

.connection-point {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid #8b5cf6;
  border-radius: 50%;
  background: #334155;
  cursor: pointer;
  transition: all 0.2s;
  z-index: 10;
  top: 50%;
  transform: translateY(-50%);
}

.connection-point:hover {
  background: #8b5cf6;
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
  stroke: #8b5cf6;
  stroke-width: 2;
  fill: none;
  pointer-events: all;
  cursor: pointer;
  stroke-linecap: round;
}

.connection-line:hover {
  stroke: #a78bfa;
  stroke-width: 3;
}

.connection-line.selected {
  stroke: #f59e0b;
  stroke-width: 3;
}

.temp-connection-line {
  stroke: #f59e0b;
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

/* 工作流对话框样式 */
.workflow-list {
  max-height: 400px;
  overflow-y: auto;
}

.workflow-item {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.workflow-item:hover {
  border-color: #8b5cf6;
  background-color: #f8fafc;
}

.workflow-info h4 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.workflow-info p {
  margin: 0 0 12px 0;
  color: #6b7280;
  font-size: 14px;
}

.workflow-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #9ca3af;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

.empty-state p {
  margin: 0;
  font-size: 16px;
}

/* 变量选择器样式 */
.prompt-input-container {
  position: relative;
}

.variable-selector {
  position: fixed;
  background: #374151;
  border: 1px solid #64748b;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  max-height: 300px;
  overflow-y: auto;
  min-width: 300px;
}

.variable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #4b5563;
  border-bottom: 1px solid #64748b;
  font-size: 12px;
  color: #e2e8f0;
}

.variable-hint {
  color: #94a3b8;
  font-size: 11px;
}

.variable-list {
  padding: 4px 0;
}

.variable-item {
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #4b5563;
}

.variable-item:last-child {
  border-bottom: none;
}

.variable-item:hover,
.variable-item.active {
  background: #4b5563;
}

.variable-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.variable-name {
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 500;
}

.variable-type {
  color: #94a3b8;
  font-size: 11px;
  background: #64748b;
  padding: 2px 6px;
  border-radius: 4px;
}

.variable-description {
  color: #94a3b8;
  font-size: 12px;
  margin-bottom: 2px;
}

.variable-source {
  color: #6b7280;
  font-size: 11px;
}
</style>

<style scoped>
.properties-panel {
  width: 450px;
  background: #334155;
  border-left: 1px solid #475569;
  padding: 16px;
  overflow-y: auto;
}

.properties-panel h4 {
  margin: 0 0 16px 0;
  color: #e2e8f0;
  font-weight: 600;
}

.tool-param {
  margin-bottom: 8px;
}

/* 运行结果面板样式 */
.execution-panel {
  width: 40%;
  background: #334155;
  border-left: 1px solid #475569;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.execution-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #475569;
  background: #3e4c5a;
}

.execution-panel-header h4 {
  margin: 0;
  color: #e2e8f0;
  font-weight: 600;
}

.execution-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.execution-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background: #3e4c5a;
  border-radius: 8px;
}

.execution-time {
  color: #94a3b8;
  font-size: 12px;
}

.node-executions {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.node-execution-item {
  background: #3e4c5a;
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid #64748b;
  transition: all 0.3s ease;
}

.node-execution-item.running {
  border-left-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.node-execution-item.completed {
  border-left-color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.node-execution-item.failed {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.node-execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-name {
  color: #e2e8f0;
  font-weight: 500;
}

.execution-section {
  margin-bottom: 12px;
}

.section-title {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-content {
  background: #1e293b;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #475569;
}

.data-display {
  margin: 0;
  color: #e2e8f0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-all;
}

.stream-output {
  display: flex;
  align-items: flex-end;
  gap: 4px;
}

.stream-content {
  color: #e2e8f0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-all;
  flex: 1;
}

.stream-cursor {
  color: #8b5cf6;
  font-weight: bold;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.error-section .section-content {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
}

.error-message {
  color: #fca5a5;
  font-size: 12px;
  line-height: 1.4;
}

.execution-time-info {
  display: flex;
  gap: 8px;
  color: #94a3b8;
  font-size: 11px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #475569;
}

.empty-execution {
  text-align: center;
  color: #94a3b8;
  padding: 40px 20px;
}

.empty-execution p {
  margin: 0;
  font-size: 14px;
}

/* Element Plus 组件深色主题适配 */
.workflow-editor :deep(.el-button) {
  background: #475569;
  border-color: #64748b;
  color: #e2e8f0;
}

.workflow-editor :deep(.el-button:hover) {
  background: #5b6b7a;
  border-color: #8b5cf6;
  color: #e2e8f0;
}

.workflow-editor :deep(.el-button--primary) {
  background: #8b5cf6;
  border-color: #8b5cf6;
  color: #ffffff;
}

.workflow-editor :deep(.el-button--primary:hover) {
  background: #a78bfa;
  border-color: #a78bfa;
}

.workflow-editor :deep(.el-button--success) {
  background: #10b981;
  border-color: #10b981;
  color: #ffffff;
}

.workflow-editor :deep(.el-button--success:hover) {
  background: #34d399;
  border-color: #34d399;
}

.workflow-editor :deep(.el-input__wrapper) {
  background: #475569;
  border: 1px solid #64748b;
  box-shadow: none;
}

.workflow-editor :deep(.el-input__inner) {
  color: #e2e8f0;
  background: transparent;
}

.workflow-editor :deep(.el-input__wrapper:hover) {
  border-color: #8b5cf6;
}

.workflow-editor :deep(.el-input__wrapper.is-focus) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.2);
}

.workflow-editor :deep(.el-select) {
  --el-select-input-color: #e2e8f0;
  --el-select-input-focus-border-color: #8b5cf6;
}

.workflow-editor :deep(.el-select .el-input__wrapper) {
  background: #475569;
  border-color: #64748b;
}

.workflow-editor :deep(.el-textarea__inner) {
  background: #475569;
  border-color: #64748b;
  color: #e2e8f0;
}

.workflow-editor :deep(.el-textarea__inner:hover) {
  border-color: #8b5cf6;
}

.workflow-editor :deep(.el-textarea__inner:focus) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.2);
}

/* 表单标签深色主题样式 */
.workflow-editor :deep(.el-form-item__label) {
  color: #e2e8f0 !important;
  font-weight: 500;
}

.workflow-editor :deep(.el-form-item__content) {
  color: #e2e8f0;
}

/* Tab组件深色主题样式 */
.workflow-editor :deep(.el-tabs) {
  background: transparent;
}

.workflow-editor :deep(.el-tabs__header) {
  background: transparent;
  border-bottom: 1px solid #475569;
  margin: 0 0 16px 0;
}

.workflow-editor :deep(.el-tabs__nav-wrap) {
  background: transparent;
}

.workflow-editor :deep(.el-tabs__nav) {
  background: transparent;
}

.workflow-editor :deep(.el-tabs__item) {
  color: #94a3b8;
  background: transparent;
  border: none;
  padding: 0 16px;
  height: 40px;
  line-height: 40px;
}

.workflow-editor :deep(.el-tabs__item:hover) {
  color: #e2e8f0;
}

.workflow-editor :deep(.el-tabs__item.is-active) {
  color: #8b5cf6;
  background: transparent;
}

.workflow-editor :deep(.el-tabs__active-bar) {
  background-color: #8b5cf6;
}

.workflow-editor :deep(.el-tabs__content) {
  background: transparent;
  color: #e2e8f0;
}

.workflow-editor :deep(.el-tab-pane) {
  background: transparent;
}

/* 滚动条样式 */
.toolbar::-webkit-scrollbar,
.properties-panel::-webkit-scrollbar {
  width: 6px;
}

.toolbar::-webkit-scrollbar-track,
.properties-panel::-webkit-scrollbar-track {
  background: #475569;
  border-radius: 3px;
}

.toolbar::-webkit-scrollbar-thumb,
.properties-panel::-webkit-scrollbar-thumb {
  background: #64748b;
  border-radius: 3px;
}

.toolbar::-webkit-scrollbar-thumb:hover,
.properties-panel::-webkit-scrollbar-thumb:hover {
  background: #8b5cf6;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  background: #334155;
  border: 1px solid #475569;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  min-width: 200px;
  max-height: 400px;
  overflow-y: auto;
  padding: 8px 0;
}

.context-menu-header {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  border-bottom: 1px solid #475569;
  margin-bottom: 4px;
}

.context-menu-group {
  margin-bottom: 4px;
}

.context-menu-group:last-child {
  margin-bottom: 0;
}

.context-menu-group-title {
  padding: 4px 16px;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #e2e8f0;
  transition: all 0.2s;
}

.context-menu-item:hover {
  background-color: #475569;
  color: #8b5cf6;
}

.context-menu-item .el-icon {
  font-size: 16px;
  width: 16px;
  height: 16px;
}

.config-hint {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
  line-height: 1.4;
}

.context-menu-item span {
  flex: 1;
}

/* 折叠面板深色主题样式 */
.workflow-editor :deep(.el-collapse) {
  border: none;
  background: transparent;
}

.workflow-editor :deep(.el-collapse-item) {
  border: none;
  background: transparent;
}

.workflow-editor :deep(.el-collapse-item__header) {
  background: #475569;
  border: 1px solid #64748b;
  border-radius: 8px;
  color: #e2e8f0;
  font-weight: 500;
  padding: 12px 16px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.workflow-editor :deep(.el-collapse-item__header:hover) {
  background: #5a6b7d;
  border-color: #8b5cf6;
}

.workflow-editor :deep(.el-collapse-item__header.is-active) {
  background: #5a6b7d;
  border-color: #8b5cf6;
  margin-bottom: 0;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.workflow-editor :deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

.workflow-editor :deep(.el-collapse-item__content) {
  background: #3e4c5a;
  border: 1px solid #8b5cf6;
  border-top: none;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
  padding: 16px;
  color: #e2e8f0;
}

.workflow-editor :deep(.el-collapse-item__arrow) {
  color: #e2e8f0;
  font-weight: bold;
}

/* WebSocket状态指示器样式 */
.websocket-status {
  display: flex;
  align-items: center;
  margin-left: 16px;
}

.connection-indicator {
  font-size: 18px;
  transition: color 0.3s ease;
}

.connection-indicator.connected {
  color: #10b981;
}

.connection-indicator.disconnected {
  color: #ef4444;
}

/* 画布控制样式 */
.canvas-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.zoom-info {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  min-width: 40px;
  text-align: center;
}

/* 变换容器样式 */
.canvas-transform-container {
  width: 100%;
  height: 100%;
  position: relative;
}

/* 画布拖拽状态 */
.workflow-canvas.dragging {
  cursor: grabbing !important;
}

.workflow-canvas:not(.dragging) {
  cursor: grab;
}
</style>