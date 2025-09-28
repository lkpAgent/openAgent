<template>
  <el-dialog
    v-model="visible"
    title="输入参数"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <div class="parameter-input-dialog">
      <div class="dialog-header">
        <h3>请为工作流输入参数</h3>
        <p class="description">工作流需要以下参数才能开始执行：</p>
      </div>
      
      <div class="parameter-form">
        <div
          v-for="(param, index) in parameters"
          :key="index"
          class="parameter-item"
        >
          <div class="param-label">
            <span class="param-name">{{ param.name }}</span>
            <span v-if="param.required" class="required-mark">*</span>
            <span class="param-type">({{ getTypeLabel(param.type) }})</span>
          </div>
          
          <div class="param-description" v-if="param.description">
            {{ param.description }}
          </div>
          
          <div class="param-input">
            <!-- 字符串类型 -->
            <el-input
              v-if="param.type === 'string'"
              v-model="parameterValues[param.name]"
              :placeholder="param.default_value || `请输入${param.name}`"
              clearable
            />
            
            <!-- 数字类型 -->
            <el-input-number
              v-else-if="param.type === 'number'"
              v-model="parameterValues[param.name]"
              :placeholder="param.default_value || `请输入${param.name}`"
              style="width: 100%"
            />
            
            <!-- 布尔类型 -->
            <el-switch
              v-else-if="param.type === 'boolean'"
              v-model="parameterValues[param.name]"
              active-text="是"
              inactive-text="否"
            />
            
            <!-- 对象类型 -->
            <el-input
              v-else-if="param.type === 'object'"
              v-model="parameterValues[param.name]"
              type="textarea"
              :rows="3"
              :placeholder="param.default_value || `请输入JSON格式的${param.name}`"
            />
            
            <!-- 数组类型 -->
            <el-input
              v-else-if="param.type === 'array'"
              v-model="parameterValues[param.name]"
              type="textarea"
              :rows="3"
              :placeholder="param.default_value || `请输入JSON数组格式的${param.name}`"
            />
            
            <!-- 默认字符串输入 -->
            <el-input
              v-else
              v-model="parameterValues[param.name]"
              :placeholder="param.default_value || `请输入${param.name}`"
              clearable
            />
          </div>
          
          <div class="param-error" v-if="errors[param.name]">
            {{ errors[param.name] }}
          </div>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="loading">
          开始运行
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'

interface Parameter {
  name: string
  type: string
  description?: string
  required?: boolean
  default_value?: any
}

interface Props {
  modelValue: boolean
  parameters: Parameter[]
  loading?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', values: Record<string, any>): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<Emits>()

const visible = ref(false)
const parameterValues = reactive<Record<string, any>>({})
const errors = reactive<Record<string, string>>({})

// 监听modelValue变化
watch(
  () => props.modelValue,
  (newValue) => {
    visible.value = newValue
    if (newValue) {
      initializeValues()
    }
  },
  { immediate: true }
)

// 监听visible变化
watch(visible, (newValue) => {
  emit('update:modelValue', newValue)
})

// 初始化参数值
const initializeValues = () => {
  // 清空之前的值和错误
  Object.keys(parameterValues).forEach(key => {
    delete parameterValues[key]
  })
  Object.keys(errors).forEach(key => {
    delete errors[key]
  })
  
  // 设置默认值
  props.parameters.forEach(param => {
    if (param.default_value !== undefined && param.default_value !== null) {
      parameterValues[param.name] = param.default_value
    } else {
      // 根据类型设置默认值
      switch (param.type) {
        case 'string':
          parameterValues[param.name] = ''
          break
        case 'number':
          parameterValues[param.name] = 0
          break
        case 'boolean':
          parameterValues[param.name] = false
          break
        case 'object':
          parameterValues[param.name] = ''
          break
        case 'array':
          parameterValues[param.name] = ''
          break
        default:
          parameterValues[param.name] = ''
      }
    }
  })
}

// 获取类型标签
const getTypeLabel = (type: string): string => {
  const typeLabels: Record<string, string> = {
    string: '字符串',
    number: '数字',
    boolean: '布尔值',
    object: '对象',
    array: '数组'
  }
  return typeLabels[type] || type
}

// 验证参数
const validateParameters = (): boolean => {
  // 清空之前的错误
  Object.keys(errors).forEach(key => {
    delete errors[key]
  })
  
  let isValid = true
  
  props.parameters.forEach(param => {
    const value = parameterValues[param.name]
    
    // 检查必填项
    if (param.required && (value === undefined || value === null || value === '')) {
      errors[param.name] = `${param.name} 是必填项`
      isValid = false
      return
    }
    
    // 跳过空值的类型检查
    if (value === undefined || value === null || value === '') {
      return
    }
    
    // 类型验证
    try {
      switch (param.type) {
        case 'number':
          if (isNaN(Number(value))) {
            errors[param.name] = `${param.name} 必须是有效的数字`
            isValid = false
          }
          break
        case 'object':
          if (typeof value === 'string' && value.trim()) {
            JSON.parse(value)
          }
          break
        case 'array':
          if (typeof value === 'string' && value.trim()) {
            const parsed = JSON.parse(value)
            if (!Array.isArray(parsed)) {
              errors[param.name] = `${param.name} 必须是有效的数组格式`
              isValid = false
            }
          }
          break
      }
    } catch (error) {
      if (param.type === 'object') {
        errors[param.name] = `${param.name} 必须是有效的JSON格式`
      } else if (param.type === 'array') {
        errors[param.name] = `${param.name} 必须是有效的JSON数组格式`
      }
      isValid = false
    }
  })
  
  return isValid
}

// 处理确认
const handleConfirm = () => {
  if (!validateParameters()) {
    return
  }
  
  // 转换参数值
  const values: Record<string, any> = {}
  props.parameters.forEach(param => {
    let value = parameterValues[param.name]
    
    // 类型转换
    switch (param.type) {
      case 'number':
        values[param.name] = value === '' ? null : Number(value)
        break
      case 'boolean':
        values[param.name] = Boolean(value)
        break
      case 'object':
        if (typeof value === 'string' && value.trim()) {
          try {
            values[param.name] = JSON.parse(value)
          } catch {
            values[param.name] = null
          }
        } else {
          values[param.name] = null
        }
        break
      case 'array':
        if (typeof value === 'string' && value.trim()) {
          try {
            values[param.name] = JSON.parse(value)
          } catch {
            values[param.name] = []
          }
        } else {
          values[param.name] = []
        }
        break
      default:
        values[param.name] = value
    }
  })
  
  emit('confirm', values)
}

// 处理取消
const handleCancel = () => {
  emit('cancel')
}

// 处理关闭
const handleClose = () => {
  emit('cancel')
}
</script>

<style scoped>
.parameter-input-dialog {
  padding: 0;
}

.dialog-header {
  margin-bottom: 24px;
}

.dialog-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.description {
  margin: 0;
  font-size: 14px;
  color: #606266;
}

.parameter-form {
  max-height: 400px;
  overflow-y: auto;
}

.parameter-item {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: #fafafa;
}

.parameter-item:last-child {
  margin-bottom: 0;
}

.param-label {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 500;
}

.param-name {
  color: #303133;
  font-size: 14px;
}

.required-mark {
  color: #f56c6c;
  margin-left: 4px;
}

.param-type {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.param-description {
  margin-bottom: 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.param-input {
  margin-bottom: 8px;
}

.param-error {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 滚动条样式 */
.parameter-form::-webkit-scrollbar {
  width: 6px;
}

.parameter-form::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.parameter-form::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.parameter-form::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>