<template>
  <div class="node-parameter-config">
    <!-- 开始节点：只显示输入参数 -->
    <div v-if="nodeType === 'start'" class="parameter-section">
      <h4 class="section-title">
        <i class="fas fa-sign-in-alt"></i>
        输入参数
      </h4>
      <div class="parameter-list">
        <div
          v-for="(param, index) in parameters.inputs"
          :key="`input-${index}`"
          class="parameter-item"
        >
          <div class="parameter-header">
            <input
              v-model="param.name"
              placeholder="参数名称"
              class="param-name"
            />
            <select v-model="param.type" class="param-type">
              <option value="string">字符串</option>
              <option value="number">数字</option>
              <option value="boolean">布尔值</option>
              <option value="object">对象</option>
              <option value="array">数组</option>
            </select>
          </div>
          <button
            @click="removeParameter('inputs', index)"
            class="remove-btn-icon"
            title="删除参数"
          >
            <i class="fas fa-times"></i>
          </button>
          <div class="parameter-details">
            <input
              v-model="param.description"
              placeholder="参数描述"
              class="param-description"
            />
            <div class="param-options">
              <label class="checkbox-label">
                <input
                  v-model="param.required"
                  type="checkbox"
                />
                必填
              </label>
              <input
                v-model="param.default_value"
                placeholder="默认值"
                class="param-default"
              />
            </div>
            <div class="param-value" v-if="nodeType === 'start'">
              <input
                v-model="param.default_value"
                placeholder="默认值（可选）"
                class="param-default-input"
              />
            </div>
            <div class="param-variable" v-else>
              <label class="variable-label">选择变量:</label>
              <select
                v-model="param.variable_name"
                class="variable-select"
              >
                <option value="">选择变量</option>
                <option
                  v-for="variable in availableVariables"
                  :key="variable.key"
                  :value="variable.key"
                >
                  {{ variable.label }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <button @click="addParameter('inputs')" class="add-btn">
          <i class="fas fa-plus"></i>
          添加输入参数
        </button>
      </div>
    </div>

    <!-- 结束节点：只显示输出参数，值从前面节点变量中选择 -->
    <div v-else-if="nodeType === 'end'" class="parameter-section">
      <h4 class="section-title">
        <i class="fas fa-sign-out-alt"></i>
        输出参数
      </h4>
      <div class="parameter-list">
        <div
          v-for="(param, index) in parameters.outputs"
          :key="`output-${index}`"
          class="parameter-item"
        >
          <div class="parameter-header">
            <input
              v-model="param.name"
              placeholder="输出参数名称"
              class="param-name"
            />
            <select v-model="param.type" class="param-type">
              <option value="string">字符串</option>
              <option value="number">数字</option>
              <option value="boolean">布尔值</option>
              <option value="object">对象</option>
              <option value="array">数组</option>
            </select>
          </div>
          <button
            @click="removeParameter('outputs', index)"
            class="remove-btn-icon"
            title="删除参数"
          >
            <i class="fas fa-times"></i>
          </button>
          <div class="parameter-details">
            <input
              v-model="param.description"
              placeholder="参数描述"
              class="param-description"
            />
            <div class="param-variable">
              <label class="variable-label">选择变量:</label>
              <select
                v-model="param.variable_name"
                class="variable-select"
              >
                <option value="">选择变量</option>
                <option
                  v-for="variable in availableVariables"
                  :key="variable.key"
                  :value="variable.key"
                >
                  {{ variable.label }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <button @click="addParameter('outputs')" class="add-btn">
          <i class="fas fa-plus"></i>
          添加输出参数
        </button>
      </div>
    </div>

    <!-- 大模型节点：显示prompt输入框和输出参数 -->
    <div v-else-if="nodeType === 'llm'" class="llm-node-config">
      <!-- Prompt输入区域 -->
      <div class="parameter-section">
        <h4 class="section-title">
          <i class="fas fa-edit"></i>
          提示词配置
        </h4>
        <div class="prompt-input-container">
          <textarea
            v-model="promptText"
            @keydown="handlePromptKeydown"
            placeholder="输入提示词，按 / 键选择变量..."
            class="prompt-textarea"
            rows="6"
          ></textarea>
          <!-- 变量选择器 -->
          <div v-if="showVariableSelector" class="variable-selector">
            <div class="variable-list">
              <div
                v-for="variable in availableVariables"
                :key="variable.key"
                @click="insertVariable(variable)"
                class="variable-item"
              >
                <span class="variable-name">{{ variable.label }}</span>
                <span class="variable-type">{{ variable.type }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输出参数配置 -->
      <div class="parameter-section">
        <h4 class="section-title">
          <i class="fas fa-sign-out-alt"></i>
          输出参数
        </h4>
        <div class="parameter-list">
          <div
            v-for="(param, index) in parameters.outputs"
            :key="`output-${index}`"
            class="parameter-item"
          >
            <div class="parameter-header">
              <input
                v-model="param.name"
                placeholder="参数名称"
                class="param-name"
              />
              <select v-model="param.type" class="param-type">
                <option value="string">字符串</option>
                <option value="number">数字</option>
                <option value="boolean">布尔值</option>
                <option value="object">对象</option>
                <option value="array">数组</option>
              </select>
            </div>
            <button
              @click="removeParameter('outputs', index)"
              class="remove-btn-icon"
              title="删除参数"
            >
              <i class="fas fa-times"></i>
            </button>
            <div class="parameter-details">
              <input
                v-model="param.description"
                placeholder="参数描述"
                class="param-description"
              />
            </div>
          </div>
          <button @click="addParameter('outputs')" class="add-btn">
            <i class="fas fa-plus"></i>
            添加输出参数
          </button>
        </div>
      </div>
    </div>

    <!-- 其他节点类型：显示输入和输出参数 -->
    <div v-else class="other-node-config">
      <!-- 输入参数配置 -->
      <div class="parameter-section">
        <h4 class="section-title">
          <i class="fas fa-sign-in-alt"></i>
          输入参数
        </h4>
        <div class="parameter-list">
          <div
            v-for="(param, index) in parameters.inputs"
            :key="`input-${index}`"
            class="parameter-item"
          >
            <div class="parameter-header">
              <input
                v-model="param.name"
                placeholder="参数名称"
                class="param-name"
              />
              <select v-model="param.type" class="param-type">
                <option value="string">字符串</option>
                <option value="number">数字</option>
                <option value="boolean">布尔值</option>
                <option value="object">对象</option>
                <option value="array">数组</option>
              </select>
            </div>
            <button
              @click="removeParameter('inputs', index)"
              class="remove-btn-icon"
              title="删除参数"
            >
              <i class="fas fa-times"></i>
            </button>
            <div class="parameter-details">
              <input
                v-model="param.description"
                placeholder="参数描述"
                class="param-description"
              />
              <div class="param-variable">
                <label class="variable-label">选择变量:</label>
                <select
                  v-model="param.variable_name"
                  class="variable-select"
                >
                  <option value="">选择变量</option>
                  <option
                    v-for="variable in availableVariables"
                    :key="variable.key"
                    :value="variable.key"
                  >
                    {{ variable.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          <button @click="addParameter('inputs')" class="add-btn">
            <i class="fas fa-plus"></i>
            添加输入参数
          </button>
        </div>
      </div>

      <!-- 输出参数配置 -->
      <div class="parameter-section">
        <h4 class="section-title">
          <i class="fas fa-sign-out-alt"></i>
          输出参数
        </h4>
        <div class="parameter-list">
          <div
            v-for="(param, index) in parameters.outputs"
            :key="`output-${index}`"
            class="parameter-item"
          >
            <div class="parameter-header">
              <input
                v-model="param.name"
                placeholder="参数名称"
                class="param-name"
              />
              <select v-model="param.type" class="param-type">
                <option value="string">字符串</option>
                <option value="number">数字</option>
                <option value="boolean">布尔值</option>
                <option value="object">对象</option>
                <option value="array">数组</option>
              </select>
            </div>
            <button
              @click="removeParameter('outputs', index)"
              class="remove-btn-icon"
              title="删除参数"
            >
              <i class="fas fa-times"></i>
            </button>
            <div class="parameter-details">
              <input
                v-model="param.description"
                placeholder="参数描述"
                class="param-description"
              />
            </div>
          </div>
          <button @click="addParameter('outputs')" class="add-btn">
            <i class="fas fa-plus"></i>
            添加输出参数
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { NodeInputOutput, NodeParameter, WorkflowNode } from '@/types'

interface Props {
  modelValue?: NodeInputOutput
  nodeType: string
  availableNodes: WorkflowNode[]
}

interface Emits {
  (e: 'update:modelValue', value: NodeInputOutput): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const parameters = ref<NodeInputOutput>({
  inputs: [...(props.modelValue?.inputs || [])],
  outputs: [...(props.modelValue?.outputs || [])]
})

// Prompt相关状态
const promptText = ref('')
const showVariableSelector = ref(false)
const cursorPosition = ref(0)

watch(
  parameters,
  (newValue) => {
    emit('update:modelValue', {
      inputs: [...newValue.inputs],
      outputs: [...newValue.outputs]
    })
  },
  { deep: true }
)

watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      parameters.value = {
        inputs: [...(newValue.inputs || [])],
        outputs: [...(newValue.outputs || [])]
      }
    }
  },
  { deep: true }
)

// 计算可用变量列表
const availableVariables = computed(() => {
  const variables: Array<{ key: string; label: string; nodeId: string; type: string }> = []
  
  // 遍历所有前置节点
  props.availableNodes.forEach(node => {
    // 为开始节点添加特殊的变量格式
    if (node.type === 'start') {
      if (node.parameters?.inputs) {
        node.parameters.inputs.forEach(input => {
          if (input.name) {
            // 开始节点的变量格式：start-1.data.user_input.input_name
            variables.push({
              key: `${node.id}.data.user_input.${input.name}`,
              label: `${node.name} - 输入: ${input.name} (${input.type})`,
              nodeId: node.id,
              type: input.type
            })
          }
        })
      }
    } else {
      // 其他节点的输入变量（通常不需要引用）
      if (node.parameters?.inputs) {
        node.parameters.inputs.forEach(input => {
          if (input.name) {
            variables.push({
              key: `${node.id}.input.${input.name}`,
              label: `${node.name} - 输入: ${input.name} (${input.type})`,
              nodeId: node.id,
              type: input.type
            })
          }
        })
      }
      
      // 其他节点的输出变量
      if (node.parameters?.outputs) {
        node.parameters.outputs.forEach(output => {
          if (output.name) {
            // 对于LLM节点，使用简化的response格式
            if (node.type === 'llm' && output.name === 'response') {
              variables.push({
                key: `${node.id}.response`,
                label: `${node.name} - 输出: ${output.name} (${output.type})`,
                nodeId: node.id,
                type: output.type
              })
            } else {
              variables.push({
                key: `${node.id}.output.${output.name}`,
                label: `${node.name} - 输出: ${output.name} (${output.type})`,
                nodeId: node.id,
                type: output.type
              })
            }
          }
        })
      }
    }
  })
  
  return variables
})

const createNewParameter = (): NodeParameter => {
  const baseParam = {
    name: '',
    type: 'string',
    description: '',
    required: false
  }
  
  if (props.nodeType === 'start') {
    return {
      ...baseParam,
      default_value: ''
    }
  } else if (props.nodeType === 'end') {
    // 结束节点的输出参数需要从前面节点变量中选择
    return {
      ...baseParam,
      variable_name: ''
    }
  } else {
    return {
      ...baseParam,
      variable_name: ''
    }
  }
}

const addParameter = (type: 'inputs' | 'outputs') => {
  parameters.value[type].push(createNewParameter())
}

const removeParameter = (type: 'inputs' | 'outputs', index: number) => {
  parameters.value[type].splice(index, 1)
}

// Prompt相关方法
const handlePromptKeydown = (event: KeyboardEvent) => {
  if (event.key === '/') {
    // 记录光标位置
    const textarea = event.target as HTMLTextAreaElement
    cursorPosition.value = textarea.selectionStart
    showVariableSelector.value = true
    event.preventDefault()
  } else if (event.key === 'Escape') {
    showVariableSelector.value = false
  }
}

const insertVariable = (variable: { key: string; label: string; type: string }) => {
  const variableText = `{${variable.key}}`
  const before = promptText.value.substring(0, cursorPosition.value)
  const after = promptText.value.substring(cursorPosition.value)
  promptText.value = before + variableText + after
  showVariableSelector.value = false
  
  // 更新光标位置到插入变量之后
  cursorPosition.value = before.length + variableText.length
}
</script>

<style scoped>
.node-parameter-config {
  padding: 16px;
  background: transparent;
  border-radius: 8px;
  max-height: 500px;
  overflow-y: auto;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.parameter-section {
  margin-bottom: 32px;
}

.parameter-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
}

.parameter-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.parameter-item {
  background: #3e4c5a;
  border: 1px solid #64748b;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
  position: relative;
}

.remove-btn-icon {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s;
  opacity: 0.7;
}

.remove-btn-icon:hover {
  background: rgba(239, 68, 68, 0.2);
  opacity: 1;
  transform: scale(1.1);
}

/* Prompt输入相关样式 */
.prompt-input-container {
  position: relative;
}

.prompt-textarea {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid #64748b;
  border-radius: 8px;
  font-size: 14px;
  background: #475569;
  color: #e2e8f0;
  resize: vertical;
  min-height: 120px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  line-height: 1.5;
}

.prompt-textarea:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.variable-selector {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #374151;
  border: 1px solid #64748b;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.variable-list {
  padding: 8px 0;
}

.variable-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.variable-item:hover {
  background: #4b5563;
}

.variable-name {
  color: #e2e8f0;
  font-size: 13px;
}

.variable-type {
  color: #94a3b8;
  font-size: 11px;
  background: #64748b;
  padding: 2px 6px;
  border-radius: 4px;
}

.parameter-item:hover {
  border-color: #8b5cf6;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
}

.parameter-header {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
  align-items: center;
  width: 100%;
  max-width: 100%;
}

.param-name {
  padding: 8px 12px;
  border: 1px solid #64748b;
  border-radius: 4px;
  font-size: 13px;
  background: #475569;
  color: #e2e8f0;
  min-height: 36px;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
}

.param-type {
  padding: 8px 12px;
  border: 1px solid #64748b;
  border-radius: 4px;
  font-size: 13px;
  background: #475569;
  color: #e2e8f0;
  min-height: 36px;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
}

.parameter-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.remove-btn {
  padding: 6px 12px;
  border: 1px solid #64748b;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  transition: all 0.2s;
  min-height: 32px;
}

.remove-btn:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.parameter-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.param-description {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #64748b;
  border-radius: 4px;
  font-size: 13px;
  background: #475569;
  color: #e2e8f0;
  min-height: 36px;
  box-sizing: border-box;
  resize: vertical;
  max-width: 100%;
}

.param-options {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 12px;
  align-items: center;
  width: 100%;
  max-width: 100%;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #cbd5e1;
  white-space: nowrap;
  flex-shrink: 0;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #8b5cf6;
  flex-shrink: 0;
}

.param-default {
  padding: 8px 12px;
  border: 1px solid #64748b;
  border-radius: 4px;
  font-size: 13px;
  background: #475569;
  color: #e2e8f0;
  min-height: 36px;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
}



.variable-label {
  font-size: 13px;
  color: #cbd5e1;
  white-space: nowrap;
  margin-right: 8px;
}

.param-variable {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.variable-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #64748b;
  border-radius: 4px;
  font-size: 13px;
  background: #475569;
  color: #e2e8f0;
  min-height: 36px;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
}

.param-value {
  margin-top: 8px;
}

.param-default-input {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  border: 1px solid #64748b;
  border-radius: 4px;
  font-size: 13px;
  background: #475569;
  color: #e2e8f0;
  min-height: 36px;
}



.add-btn {
  padding: 12px 16px;
  border: 2px dashed #64748b;
  background: transparent;
  color: #94a3b8;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  min-height: 48px;
}

.add-btn:hover {
  border-color: #8b5cf6;
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
  transform: translateY(-1px);
}

/* 响应式设计 */
@media (max-width: 400px) {
  .parameter-header {
    grid-template-columns: 1fr 80px;
    gap: 8px;
  }
  
  .param-options {
    grid-template-columns: 70px 1fr;
    gap: 8px;
  }
  
  .node-parameter-config {
    padding: 12px;
  }
  
  .parameter-item {
    padding: 12px;
  }
  
  .remove-btn-icon {
    width: 20px;
    height: 20px;
    font-size: 10px;
  }
}
</style>