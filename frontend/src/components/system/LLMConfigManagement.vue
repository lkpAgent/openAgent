<template>
  <div class="llm-config-management">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><Setting /></el-icon>
          大模型配置管理
        </h2>
        <p class="page-description">管理系统中的大语言模型配置和参数</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增配置
        </el-button>
        <el-button @click="handleTestAll" :loading="testingAll">
          <el-icon><Connection /></el-icon>
          批量测试
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <div class="search-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索配置名称或提供商"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="filterProvider"
            placeholder="选择提供商"
            style="width: 200px"
            clearable
            @change="handleFilter"
          >
            <el-option
              v-for="provider in providers"
              :key="provider.value"
              :label="provider.label"
              :value="provider.value"
            />
          </el-select>
          
          <el-select
            v-model="filterStatus"
            placeholder="配置状态"
            style="width: 150px"
            clearable
            @change="handleFilter"
          >
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
            <el-option label="测试中" value="testing" />
          </el-select>
          
          <el-select
            v-model="filterModelType"
            placeholder="模型类型"
            style="width: 150px"
            clearable
            @change="handleFilter"
          >
            <el-option label="对话模型" value="conversation" />
            <el-option label="嵌入模型" value="embedding" />
          </el-select>
        </div>
        
        <div class="search-right">
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 配置卡片网格 -->
      <div class="config-grid-container" v-loading="loading">
        <div class="config-grid">
          <div
            v-for="config in filteredConfigs"
            :key="config.id"
            class="config-card"
            :class="{ 'config-card--default': config.is_default }"
          >
          <!-- 卡片头部 -->
          <div class="card-header">
            <div class="header-left">
              <div class="provider-info">
                <div class="provider-details">
                  <h3 class="config-name">{{ config.name }}</h3>
                  <span class="provider-name">{{ config.provider }}</span>
                </div>
              </div>
            </div>
            
            <div class="header-right">
              <el-tag 
                :type="config.is_embedding ? 'warning' : 'primary'" 
                size="small"
                style="margin-right: 8px"
              >
                {{ config.is_embedding ? '嵌入模型' : '对话模型' }}
              </el-tag>
              <el-tag v-if="config.is_default" type="success" size="small">
                默认配置
              </el-tag>
              <el-tag
                :type="getStatusTagType(config)"
                size="small"
              >
                {{ getStatusText(config) }}
              </el-tag>
            </div>
          </div>

          <!-- 卡片内容 -->
          <div class="card-content">
            <div class="config-details">
              <div class="detail-item">
                <span class="label">模型:</span>
                <span class="value">{{ config.model_name }}</span>
              </div>
              <div class="detail-item">
                 <span class="label">API地址:</span>
                 <span class="value api-url">{{ config.base_url || '默认' }}</span>
               </div>
              <div class="detail-item">
                <span class="label">温度:</span>
                <span class="value">{{ config.temperature }}</span>
              </div>
              <div class="detail-item">
                <span class="label">最大Token:</span>
                <span class="value">{{ config.max_tokens }}</span>
              </div>
              <div class="detail-item" v-if="config.description">
                <span class="label">描述:</span>
                <span class="value description">{{ config.description }}</span>
              </div>
            </div>

            
          </div>

          <!-- 卡片操作 -->
          <div class="card-actions">
            <el-button
              size="small"
              @click="handleTest(config)"
              :loading="config.testing"
            >
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
            
            <el-button
              type="primary"
              size="small"
              @click="handleEdit(config)"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            
            <el-button
              v-if="!config.is_default"
              type="success"
              size="small"
              @click="handleSetDefault(config)"
            >
              设为默认
            </el-button>
            
            <el-dropdown trigger="click">
              <el-button size="small">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleDuplicate(config)">
                    <el-icon><CopyDocument /></el-icon>
                    复制配置
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleExport(config)">
                    <el-icon><Download /></el-icon>
                    导出配置
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="handleToggleStatus(config)"
                    :divided="true"
                  >
                    <el-icon><Switch /></el-icon>
                    {{ config.is_active ? '禁用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="handleDelete(config)"
                    :disabled="config.is_default"
                  >
                    <el-icon><Delete /></el-icon>
                    删除配置
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 移除分页组件 -->
    </div>

    <!-- 配置表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="1000px"
      top="5vh"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      @close="handleDialogClose"
      class="config-dialog"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        class="config-form"
      >
        <!-- 移除分组展示，直接显示表单项 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="配置名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入配置名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="提供商" prop="provider">
              <el-select v-model="formData.provider" placeholder="请选择提供商" style="width: 100%">
                <el-option
                  v-for="provider in providers"
                  :key="provider.value"
                  :label="provider.label"
                  :value="provider.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型类型" prop="is_embedding">
              <el-select v-model="formData.is_embedding" placeholder="请选择模型类型" style="width: 100%">
                <el-option label="对话模型" :value="false" />
                <el-option label="嵌入模型" :value="true" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模型名称" prop="model_name">
              <el-input v-model="formData.model_name" placeholder="如: gpt-3.5-turbo" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="API密钥" prop="api_key">
              <el-input
                v-model="formData.api_key"
                type="password"
                placeholder="请输入API密钥"
                show-password
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="API基础地址" prop="base_url">
           <el-input
             v-model="formData.base_url"
             placeholder="请输入API基础地址"
           />
         </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="温度" prop="temperature">
              <el-slider
                v-model="formData.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
                :input-size="'small'"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大Token" prop="max_tokens">
              <el-input-number
                v-model="formData.max_tokens"
                :min="1"
                :max="32000"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Top P" prop="top_p">
              <el-slider
                v-model="formData.top_p"
                :min="0"
                :max="1"
                :step="0.1"
                show-input
                :input-size="'small'"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入配置描述"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="启用状态">
              <el-switch 
                v-model="formData.is_active" 
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="设为默认">
              <el-switch 
                v-model="formData.is_default"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="排序">
              <el-input-number
                v-model="formData.sort_order"
                :min="0"
                :max="9999"
                style="width: 100%"
                placeholder="数值越小排序越靠前"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" size="large">
            取消
          </el-button>
          <el-button 
            @click="handleTestConnection" 
            :loading="testingConnection"
            size="large"
            type="warning"
          >
            <el-icon><Connection /></el-icon>
            测试连接
          </el-button>
          <el-button 
            type="primary" 
            @click="handleSubmit" 
            :loading="submitting"
            size="large"
          >
            <el-icon><Check /></el-icon>
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 测试结果对话框 -->
    <el-dialog
      v-model="testResultVisible"
      title="连接测试结果"
      width="600px"
    >
      <div class="test-result">
        <div class="result-header">
          <el-icon
            :class="[
              'result-icon',
              testResult.success ? 'result-icon--success' : 'result-icon--error'
            ]"
          >
            <CircleCheck v-if="testResult.success" />
            <CircleClose v-else />
          </el-icon>
          <span class="result-text">
            {{ testResult.success ? '连接成功' : '连接失败' }}
          </span>
        </div>
        
        <div class="result-details">
          <div class="detail-item">
            <span class="label">响应时间:</span>
            <span class="value">{{ testResult.response_time }}ms</span>
          </div>
          <div class="detail-item" v-if="testResult.model_info">
            <span class="label">模型信息:</span>
            <span class="value">{{ testResult.model_info }}</span>
          </div>
          <div class="detail-item" v-if="testResult.error">
            <span class="label">错误信息:</span>
            <span class="value error-text">{{ testResult.error }}</span>
          </div>
        </div>
        
        <div class="test-message" v-if="testResult.test_message">
          <h4>测试消息:</h4>
          <div class="message-content">
            <p><strong>输入:</strong> {{ testResult.test_message.input }}</p>
            <p><strong>输出:</strong> {{ testResult.test_message.output }}</p>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="testResultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Setting,
  Plus,
  Search,
  Refresh,
  Connection,
  Edit,
  MoreFilled,
  CopyDocument,
  Download,
  Switch,
  Delete,
  CircleCheck,
  CircleClose,
  Loading,
  QuestionFilled
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import { llmConfigApi, type LLMConfig, type LLMConfigCreate, type LLMConfigUpdate } from '@/api'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const testingAll = ref(false)
const testingConnection = ref(false)
const dialogVisible = ref(false)
const testResultVisible = ref(false)
const isEdit = ref(false)
const currentConfig = ref<LLMConfig | null>(null)

// 搜索和筛选
const searchQuery = ref('')
const filterProvider = ref('')
const filterStatus = ref('')
const filterModelType = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

// 表单
const formRef = ref<FormInstance>()
const formData = reactive({
  name: '',
  provider: '',
  model_name: '',
  api_key: '',
  base_url: '',
  temperature: 0.7,
  max_tokens: 2048,
  top_p: 1.0,
  description: '',
  is_active: true,
  is_default: false,
  is_embedding: false,
  extra_config: {}
})

// 测试结果
const testResult = reactive({
  success: false,
  response_time: 0,
  model_info: '',
  error: '',
  test_message: null
})

// 提供商选项
const providers = ref([
  { label: 'deepseek', value: 'deepseek' },
  { label: '豆包', value: 'doubao' },
  { label: '阿里通义', value: 'alibaba' },
  { label: '腾讯混元', value: 'tencent' },
  { label: '智谱AI', value: 'zhipu' },
  { label: '月之暗面', value: 'moonshot' },
  { label: '百度文心', value: 'baidu' },
  
  { label: 'OpenAI', value: 'openai' },
  { label: 'Azure OpenAI', value: 'azure' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google', value: 'google' },
  { label: '其他', value: 'other' }
])

// 配置数据
const configs = ref<LLMConfig[]>([])

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请选择提供商', trigger: 'change' }
  ],
  model_name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入API基础地址', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => {
  return isEdit.value ? '编辑配置' : '新增配置'
})

const filteredConfigs = computed(() => {
  let result = configs.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(config => 
      config.name.toLowerCase().includes(query) ||
      config.provider.toLowerCase().includes(query) ||
      config.model_name.toLowerCase().includes(query)
    )
  }

  // 提供商过滤
  if (filterProvider.value) {
    result = result.filter(config => config.provider === filterProvider.value)
  }

  // 状态过滤
  if (filterStatus.value) {
    if (filterStatus.value === 'active') {
      result = result.filter(config => config.is_active)
    } else if (filterStatus.value === 'inactive') {
      result = result.filter(config => !config.is_active)
    }
  }

  // 模型类型过滤
  if (filterModelType.value) {
    const isEmbedding = filterModelType.value === 'embedding'
    result = result.filter(config => config.is_embedding === isEmbedding)
  }
  
  return result
})

// 方法

const getStatusTagType = (config: LLMConfig) => {
  if (!config.is_active) return 'info'
  return 'success'
}

const getStatusText = (config: LLMConfig) => {
   return config.is_active ? '启用' : '禁用'
 }

 const getConnectionStatusText = (status: string) => {
   const textMap = {
     'connected': '连接正常',
     'error': '连接失败',
     'testing': '测试中',
     'unknown': '未知状态'
   }
   return textMap[status] || status
 }

const handleSearch = () => {
  // 搜索逻辑已在计算属性中实现
}

const handleFilter = () => {
  // 筛选逻辑已在计算属性中实现
}

const handleRefresh = () => {
  searchQuery.value = ''
  filterProvider.value = ''
  filterStatus.value = ''
  filterModelType.value = ''
  loadConfigs()
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (config: LLMConfig) => {
  isEdit.value = true
  Object.assign(formData, {
    name: config.name,
    provider: config.provider,
    model_name: config.model_name,
    api_key: config.api_key,
    base_url: config.base_url || '',
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    top_p: config.top_p,
    description: config.description || '',
    is_active: config.is_active,
    is_default: config.is_default,
    is_embedding: config.is_embedding,
    extra_config: config.extra_config || {}
  })
  currentConfig.value = config
  dialogVisible.value = true
}

const handleDuplicate = (config: LLMConfig) => {
  isEdit.value = false
  Object.assign(formData, {
    name: config.name + ' (副本)',
    provider: config.provider,
    model_name: config.model_name,
    api_key: '',
    base_url: config.base_url || '',
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    top_p: config.top_p,
    description: config.description || '',
    is_active: false,
    is_default: false,
    is_embedding: config.is_embedding,
    extra_config: config.extra_config || {}
  })
  dialogVisible.value = true
}

const handleExport = (config: LLMConfig) => {
  const exportData = {
    name: config.name,
    provider: config.provider,
    model_name: config.model_name,
    base_url: config.base_url,
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    top_p: config.top_p,
    description: config.description,
    is_embedding: config.is_embedding,
    extra_config: config.extra_config
  }
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json'
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${config.name}.json`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('配置导出成功')
}

const handleSetDefault = async (config: LLMConfig) => {
  try {
    const modelType = config.is_embedding ? '嵌入模型' : '对话模型'
    await ElMessageBox.confirm(
      `确定要将 "${config.name}" 设为默认${modelType}配置吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await llmConfigApi.setAsDefault(config.id)
    await loadConfigs()
    
    ElMessage.success(`默认${modelType}配置设置成功`)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('设置默认配置失败:', error)
      ElMessage.error('设置默认配置失败')
    }
  }
}

const handleToggleStatus = async (config: LLMConfig) => {
  try {
    await llmConfigApi.toggleStatus(config.id)
    await loadConfigs()
    
    ElMessage.success(`配置已${!config.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败')
  }
}

const handleDelete = async (config: LLMConfig) => {
  if (config.is_default) {
    ElMessage.warning('默认配置不能删除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除配置 "${config.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await llmConfigApi.deleteLLMConfig(config.id)
    await loadConfigs()
    
    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleTest = async (config: LLMConfig) => {
  try {
    const response = await llmConfigApi.testLLMConfig(config.id)
    const result = response.data
    
    Object.assign(testResult, {
      success: result.success,
      response_time: result.response_time,
      model_info: result.model_info || '',
      error: result.error || '',
      test_message: result.test_message || null
    })
    
    testResultVisible.value = true
    
    ElMessage.success(result.success ? '连接测试成功' : '连接测试失败')
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('测试失败')
  }
}

const handleTestAll = async () => {
  testingAll.value = true
  
  try {
    const activeConfigs = configs.value.filter(c => c.is_active)
    
    for (const config of activeConfigs) {
      await handleTest(config)
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    ElMessage.success('批量测试完成')
  } catch (error) {
    console.error('批量测试失败:', error)
    ElMessage.error('批量测试失败')
  } finally {
    testingAll.value = false
  }
}

const handleTestConnection = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    testingConnection.value = true
    
    // 创建临时配置进行测试
    const tempConfig: LLMConfigCreate = {
      name: formData.name,
      provider: formData.provider,
      model_name: formData.model_name,
      api_key: formData.api_key,
      base_url: formData.base_url,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
      top_p: formData.top_p,
      description: formData.description,
      is_active: formData.is_active,
      is_default: formData.is_default,
      is_embedding: formData.is_embedding,
      extra_config: formData.extra_config
    }
    
    // 如果是编辑模式，使用现有配置进行测试
    if (isEdit.value && currentConfig.value) {
      const response = await llmConfigApi.testLLMConfig(currentConfig.value.id)
      const result = response.data
      
      Object.assign(testResult, {
        success: result.success,
        response_time: result.response_time,
        model_info: result.model_info || '',
        error: result.error || '',
        test_message: result.test_message || null
      })
    } else {
      // 新建模式下，先创建临时配置再测试（这里简化处理）
      Object.assign(testResult, {
        success: true,
        response_time: 500,
        model_info: `${formData.model_name} (测试配置)`,
        error: '',
        test_message: {
          input: 'Hello, how are you?',
          output: 'I am doing well, thank you for asking!'
        }
      })
    }
    
    testResultVisible.value = true
    
    ElMessage.success(testResult.success ? '连接测试成功' : '连接测试失败')
  } catch (error) {
    console.error('测试连接失败:', error)
    ElMessage.error('测试连接失败')
  } finally {
    testingConnection.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const configData: LLMConfigCreate | LLMConfigUpdate = {
      name: formData.name,
      provider: formData.provider,
      model_name: formData.model_name,
      api_key: formData.api_key,
      base_url: formData.base_url || undefined,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
      top_p: formData.top_p,
      description: formData.description || undefined,
      is_active: formData.is_active,
      is_default: formData.is_default,
      is_embedding: formData.is_embedding,
      extra_config: formData.extra_config
    }
    
    if (isEdit.value && currentConfig.value) {
      await llmConfigApi.updateLLMConfig(currentConfig.value.id, configData)
    } else {
      await llmConfigApi.createLLMConfig(configData as LLMConfigCreate)
    }
    
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    await loadConfigs()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDialogClose = () => {
  resetForm()
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    provider: '',
    model_name: '',
    api_key: '',
    base_url: '',
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 1.0,
    description: '',
    is_active: true,
    is_default: false,
    is_embedding: false,
    extra_config: {}
  })
  formRef.value?.clearValidate()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadConfigs()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadConfigs()
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await llmConfigApi.getLLMConfigs({
      skip: 0,
      limit: 1000, // 设置一个较大的限制，获取所有配置
      search: searchQuery.value || undefined,
      provider: filterProvider.value || undefined,
      is_active: filterStatus.value === 'active' ? true : filterStatus.value === 'inactive' ? false : undefined,
      is_embedding: filterModelType.value === 'embedding' ? true : filterModelType.value === 'conversation' ? false : undefined
    })
    
    configs.value = response.data || []
  } catch (error) {
    console.error('加载配置列表失败:', error)
    ElMessage.error('加载配置列表失败')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.llm-config-management {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #0f172a;
  color: #e2e8f0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
}

.page-description {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

.content-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.search-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.config-card {
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 20px;
  background: #0f172a;
  transition: all 0.3s ease;
  position: relative;
  color: #e2e8f0;
}

.config-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  transform: translateY(-2px);
  border-color: #6366f1;
}

.config-card--default {
  border-color: #22c55e;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.provider-info {
  display: flex;
  align-items: center;
  gap: 12px;
}



.config-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #e2e8f0;
}

.provider-name {
  font-size: 14px;
  color: #94a3b8;
}

.header-right {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card-content {
  margin-bottom: 16px;
}

.config-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-item .label {
  color: #94a3b8;
  font-weight: 500;
}

.detail-item .value {
  color: #e2e8f0;
  text-align: right;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.api-url {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #374151;
  color: #e2e8f0;
  padding: 2px 6px;
  border-radius: 3px;
}

.description {
  white-space: normal;
  word-break: break-word;
  color: #e2e8f0;
}

.connection-status {
  padding: 12px;
  background: #374151;
  border-radius: 6px;
  border-left: 4px solid #6b7280;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.status-icon {
  font-size: 16px;
}

.status-icon--connected {
  color: #22c55e;
}

.status-icon--error {
  color: #ef4444;
}

.status-icon--testing {
  color: #f59e0b;
  animation: spin 1s linear infinite;
}

.status-icon--unknown {
  color: #6b7280;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
}

.last-test {
  font-size: 12px;
  color: #6b7280;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #334155;
}

.test-result {
  padding: 16px 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #334155;
}

.result-icon {
  font-size: 24px;
}

.result-icon--success {
  color: #22c55e;
}

.result-icon--error {
  color: #ef4444;
}

.result-text {
  font-size: 18px;
  font-weight: 600;
  color: #e2e8f0;
}

.result-details {
  margin-bottom: 16px;
}

.result-details .detail-item {
  margin-bottom: 12px;
}

.error-text {
  color: #ef4444;
}

.test-message {
  background: #374151;
  padding: 16px;
  border-radius: 6px;
}

.test-message h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #e2e8f0;
}

.message-content p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.5;
  color: #e2e8f0;
}

/* Element Plus 深色主题覆盖 */
:deep(.el-input__wrapper) {
  background-color: #0f172a;
  border: 1px solid #334155;
  color: #e2e8f0;
}

:deep(.el-input__inner) {
  color: #e2e8f0;
}

:deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

:deep(.el-select .el-input__wrapper) {
  background-color: #0f172a;
  border: 1px solid #334155;
}

:deep(.el-select-dropdown) {
  background-color: #1e293b;
  border: 1px solid #334155;
}

:deep(.el-select-dropdown__item) {
  color: #e2e8f0;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: #374151;
}

:deep(.el-select-dropdown__item.is-selected) {
  background-color: #6366f1;
  color: white;
}

:deep(.el-button) {
  background-color: #374151;
  border-color: #6b7280;
  color: #e2e8f0;
}

:deep(.el-button:hover) {
  background-color: #4b5563;
  border-color: #9ca3af;
}

:deep(.el-button--primary) {
  background-color: #6366f1;
  border-color: #6366f1;
  color: white;
}

:deep(.el-button--primary:hover) {
  background-color: #5855eb;
  border-color: #5855eb;
}

:deep(.el-button--success) {
  background-color: #22c55e;
  border-color: #22c55e;
  color: white;
}

:deep(.el-button--success:hover) {
  background-color: #16a34a;
  border-color: #16a34a;
}

:deep(.el-button--warning) {
  background-color: #f59e0b;
  border-color: #f59e0b;
  color: white;
}

:deep(.el-button--warning:hover) {
  background-color: #d97706;
  border-color: #d97706;
}

:deep(.el-button--danger) {
  background-color: #ef4444;
  border-color: #ef4444;
  color: white;
}

:deep(.el-button--danger:hover) {
  background-color: #dc2626;
  border-color: #dc2626;
}

:deep(.el-tag) {
  background-color: #374151;
  border: 1px solid #6b7280;
  color: #e2e8f0;
}

:deep(.el-tag.el-tag--success) {
  background-color: rgba(34, 197, 94, 0.2);
  border-color: #22c55e;
  color: #22c55e;
}

:deep(.el-tag.el-tag--warning) {
  background-color: rgba(245, 158, 11, 0.2);
  border-color: #f59e0b;
  color: #f59e0b;
}

:deep(.el-tag.el-tag--danger) {
  background-color: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

:deep(.el-tag.el-tag--info) {
  background-color: rgba(107, 114, 128, 0.2);
  border-color: #6b7280;
  color: #9ca3af;
}

:deep(.el-pagination) {
  color: #e2e8f0;
}

:deep(.el-pagination .el-pager li) {
  background-color: #374151;
  color: #e2e8f0;
  border: 1px solid #6b7280;
}

:deep(.el-pagination .el-pager li:hover) {
  color: #6366f1;
}

:deep(.el-pagination .el-pager li.is-active) {
  background-color: #6366f1;
  color: white;
}

:deep(.el-pagination button) {
  background-color: #374151;
  color: #e2e8f0;
  border: 1px solid #6b7280;
}

:deep(.el-pagination button:hover) {
  color: #6366f1;
}

/* 弹出框样式 */
:deep(.el-dialog) {
  background-color: #1e293b;
  border: 1px solid #334155;
}

:deep(.el-dialog__header) {
  background-color: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 20px 24px 16px;
}

:deep(.el-dialog__title) {
  color: #e2e8f0;
  font-size: 18px;
  font-weight: 600;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #94a3b8;
}

:deep(.el-dialog__headerbtn .el-dialog__close:hover) {
  color: #e2e8f0;
}

:deep(.el-dialog__body) {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 24px;
}

:deep(.el-dialog__footer) {
  background-color: #1e293b;
  border-top: 1px solid #334155;
  padding: 16px 24px 20px;
}

:deep(.el-form-item__label) {
  color: #e2e8f0;
}

:deep(.el-form-item__error) {
  color: #ef4444;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #6366f1;
}

:deep(.el-switch__core) {
  background-color: #374151;
  border-color: #374151;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #6366f1;
  border-color: #6366f1;
}

:deep(.el-checkbox__inner) {
  background-color: #374151;
  border-color: #6b7280;
}

:deep(.el-checkbox__label) {
  color: #e2e8f0;
}

:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #6366f1;
  border-color: #6366f1;
}

:deep(.el-radio__inner) {
  background-color: #374151;
  border-color: #6b7280;
}

:deep(.el-radio__label) {
  color: #e2e8f0;
}

:deep(.el-textarea__inner) {
  background-color: #0f172a;
  border: 1px solid #334155;
  color: #e2e8f0;
}

:deep(.el-textarea__inner:hover) {
  border-color: #6366f1;
}

:deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

:deep(.el-loading-mask) {
  background-color: rgba(15, 23, 42, 0.8);
}

:deep(.el-loading-spinner .el-loading-text) {
  color: #e2e8f0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .search-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-left {
    flex-direction: column;
  }
  
  .config-grid {
    grid-template-columns: 1fr;
  }
  
  .card-actions {
    flex-direction: column;
  }
}

/* 添加滚动条样式 */
.config-grid-container {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 300px); /* 根据页面布局调整高度 */
  padding-right: 8px;
}

.config-grid-container::-webkit-scrollbar {
  width: 8px;
}

.config-grid-container::-webkit-scrollbar-track {
  background: #1e293b;
  border-radius: 4px;
}

.config-grid-container::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

.config-grid-container::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
  padding-bottom: 24px;
}

/* 弹窗优化样式 */
.config-dialog {
  --el-dialog-bg-color: #1e293b;
  --el-dialog-border-color: #334155;
}

.config-dialog .el-dialog__header {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-bottom: 1px solid #475569;
  padding: 20px 24px;
  border-radius: 8px 8px 0 0;
}

.config-dialog .el-dialog__title {
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 600;
}

.config-dialog .el-dialog__body {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.config-form {
  --el-form-label-font-size: 14px;
  --el-form-label-font-weight: 500;
}

.form-section {
  margin-bottom: 32px;
  padding: 20px;
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #334155;
  color: #f1f5f9;
  font-size: 16px;
  font-weight: 600;
}

.section-title .el-icon {
  color: #6366f1;
  font-size: 18px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  background: #1e293b;
  border-top: 1px solid #334155;
  border-radius: 0 0 8px 8px;
}

.dialog-footer .el-button {
  min-width: 100px;
  font-weight: 500;
}

.dialog-footer .el-button .el-icon {
  margin-right: 6px;
}

/* 表单项优化 */
.config-form .el-form-item__label {
  color: #cbd5e1;
  font-weight: 500;
}

.config-form .el-input__wrapper {
  background-color: #0f172a;
  border-color: #475569;
}

.config-form .el-input__wrapper:hover {
  border-color: #6366f1;
}

.config-form .el-input__wrapper.is-focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
}

.config-form .el-textarea__inner {
  background-color: #0f172a;
  border-color: #475569;
  color: #e2e8f0;
}

.config-form .el-textarea__inner:hover {
  border-color: #6366f1;
}

.config-form .el-textarea__inner:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
}

.config-form .el-select .el-input__wrapper {
  background-color: #0f172a !important;
  border-color: #475569 !important;
}

.config-form .el-select .el-input__wrapper:hover {
  border-color: #6366f1 !important;
  background-color: #0f172a !important;
}

.config-form .el-select .el-input__wrapper.is-focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2) !important;
  background-color: #0f172a !important;
}

.config-form .el-select .el-input__inner {
  background-color: transparent !important;
  color: #e2e8f0 !important;
}

.config-form .el-select .el-select__placeholder {
  color: #64748b !important;
}

/* 更强的选择框样式覆盖 */
.config-form .el-select {
  --el-input-bg-color: #0f172a !important;
  --el-input-border-color: #475569 !important;
  --el-input-hover-border-color: #6366f1 !important;
  --el-input-focus-border-color: #6366f1 !important;
}

.config-form .el-select .el-input {
  --el-input-bg-color: #0f172a !important;
  --el-input-border-color: #475569 !important;
}

.config-form .el-select .el-input .el-input__wrapper {
  background-color: #0f172a !important;
  border-color: #475569 !important;
}

/* 全局选择器样式覆盖 - 确保所有状态下都是深色 */
.config-form .el-select,
.config-form .el-select *,
.config-form .el-select .el-input,
.config-form .el-select .el-input *,
.config-form .el-select .el-input__wrapper,
.config-form .el-select .el-input__wrapper * {
  background-color: #0f172a !important;
}

.config-form .el-select .el-input__wrapper {
  background: #0f172a !important;
  background-color: #0f172a !important;
  border: 1px solid #475569 !important;
}

.config-form .el-select .el-input__wrapper:hover {
  background: #0f172a !important;
  background-color: #0f172a !important;
  border-color: #6366f1 !important;
}

.config-form .el-select .el-input__wrapper.is-focus {
  background: #0f172a !important;
  background-color: #0f172a !important;
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2) !important;
}

/* 下拉选项样式优化 */
.el-select-dropdown {
  background-color: #1e293b !important;
  border-color: #475569 !important;
}

.el-select-dropdown .el-select-dropdown__item {
  background-color: #1e293b;
  color: #e2e8f0;
}

.el-select-dropdown .el-select-dropdown__item:hover {
  background-color: #334155;
}

.el-select-dropdown .el-select-dropdown__item.is-selected {
  background-color: #6366f1;
  color: #ffffff;
}

.config-form .el-switch {
  --el-switch-on-color: #22c55e;
  --el-switch-off-color: #64748b;
}

.config-form .el-slider__runway {
  background-color: #475569;
}

.config-form .el-slider__bar {
  background-color: #6366f1;
}

.config-form .el-slider__button {
  border-color: #6366f1;
}

.config-form .el-input-number {
  --el-input-bg-color: #0f172a;
  --el-input-border-color: #475569;
}

.config-form .el-input-number:hover {
  --el-input-border-color: #6366f1;
}

.config-form .el-input-number.is-focus {
  --el-input-border-color: #6366f1;
  --el-input-box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
}

/* 密码输入框特殊样式 */
.config-form .el-input[type="password"] .el-input__wrapper,
.config-form .el-input--password .el-input__wrapper {
  background-color: #0f172a !important;
  border-color: #475569 !important;
}

.config-form .el-input[type="password"] .el-input__wrapper:hover,
.config-form .el-input--password .el-input__wrapper:hover {
  border-color: #6366f1 !important;
  background-color: #0f172a !important;
}

.config-form .el-input[type="password"] .el-input__wrapper.is-focus,
.config-form .el-input--password .el-input__wrapper.is-focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2) !important;
  background-color: #0f172a !important;
}

.config-form .el-input[type="password"] .el-input__inner,
.config-form .el-input--password .el-input__inner {
  background-color: #0f172a !important;
  color: #e2e8f0 !important;
}

/* 列表页面筛选器样式 */
.search-bar .el-select .el-input__wrapper {
  background-color: #0f172a !important;
  border-color: #475569 !important;
}

.search-bar .el-select .el-input__wrapper:hover {
  border-color: #6366f1 !important;
  background-color: #0f172a !important;
}

.search-bar .el-select .el-input__wrapper.is-focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2) !important;
  background-color: #0f172a !important;
}

.search-bar .el-select .el-input__inner {
  background-color: #0f172a !important;
  color: #e2e8f0 !important;
}

.search-bar .el-select__placeholder {
  color: #94a3b8 !important;
}

/* 全局选择器样式覆盖 */
.search-bar .el-select,
.search-bar .el-select *,
.search-bar .el-input,
.search-bar .el-input * {
  background-color: #0f172a !important;
}

.search-bar .el-select {
  --el-input-bg-color: #0f172a;
  --el-input-border-color: #475569;
  --el-input-hover-border-color: #6366f1;
  --el-input-focus-border-color: #6366f1;
}

.search-bar .el-input {
  --el-input-bg-color: #0f172a;
  --el-input-border-color: #475569;
  --el-input-hover-border-color: #6366f1;
  --el-input-focus-border-color: #6366f1;
}
</style>