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
        </div>
        
        <div class="search-right">
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 配置卡片网格 -->
      <div class="config-grid" v-loading="loading">
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
                <img
                  :src="getProviderIcon(config.provider)"
                  :alt="config.provider"
                  class="provider-icon"
                />
                <div class="provider-details">
                  <h3 class="config-name">{{ config.name }}</h3>
                  <span class="provider-name">{{ config.provider }}</span>
                </div>
              </div>
            </div>
            
            <div class="header-right">
              <el-tag v-if="config.is_default" type="success" size="small">
                默认配置
              </el-tag>
              <el-tag
                :type="getStatusTagType(config.status)"
                size="small"
              >
                {{ getStatusText(config.status) }}
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
                <span class="value api-url">{{ config.api_base || '默认' }}</span>
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

            <!-- 连接状态 -->
            <div class="connection-status">
              <div class="status-indicator">
                <el-icon
                  :class="[
                    'status-icon',
                    `status-icon--${config.connection_status}`
                  ]"
                >
                  <CircleCheck v-if="config.connection_status === 'connected'" />
                  <CircleClose v-else-if="config.connection_status === 'error'" />
                  <Loading v-else-if="config.connection_status === 'testing'" />
                  <QuestionFilled v-else />
                </el-icon>
                <span class="status-text">
                  {{ getConnectionStatusText(config.connection_status) }}
                </span>
              </div>
              <div class="last-test" v-if="config.last_test_at">
                最后测试: {{ formatDateTime(config.last_test_at) }}
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

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 配置表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
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
            <el-form-item label="模型名称" prop="model_name">
              <el-input v-model="formData.model_name" placeholder="如: gpt-3.5-turbo" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
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
        
        <el-form-item label="API基础地址" prop="api_base">
          <el-input
            v-model="formData.api_base"
            placeholder="可选，留空使用默认地址"
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
              <el-switch v-model="formData.is_active" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="设为默认">
              <el-switch v-model="formData.is_default" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="排序">
              <el-input-number
                v-model="formData.sort_order"
                :min="0"
                :max="9999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button @click="handleTestConnection" :loading="testingConnection">
          测试连接
        </el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
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

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const testingAll = ref(false)
const testingConnection = ref(false)
const dialogVisible = ref(false)
const testResultVisible = ref(false)
const isEdit = ref(false)
const currentConfig = ref(null)

// 搜索和筛选
const searchQuery = ref('')
const filterProvider = ref('')
const filterStatus = ref('')

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
  api_base: '',
  temperature: 0.7,
  max_tokens: 2048,
  top_p: 1.0,
  description: '',
  is_active: true,
  is_default: false,
  sort_order: 0
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
  { label: 'OpenAI', value: 'openai' },
  { label: 'Azure OpenAI', value: 'azure' },
  { label: 'Anthropic', value: 'anthropic' },
  { label: 'Google', value: 'google' },
  { label: '百度文心', value: 'baidu' },
  { label: '阿里通义', value: 'alibaba' },
  { label: '腾讯混元', value: 'tencent' },
  { label: '智谱AI', value: 'zhipu' },
  { label: '月之暗面', value: 'moonshot' },
  { label: '其他', value: 'other' }
])

// 模拟数据
const configs = ref([
  {
    id: 1,
    name: 'GPT-3.5 Turbo',
    provider: 'openai',
    model_name: 'gpt-3.5-turbo',
    api_key: 'sk-***',
    api_base: '',
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 1.0,
    description: '默认的GPT-3.5模型配置',
    is_active: true,
    is_default: true,
    sort_order: 1,
    status: 'active',
    connection_status: 'connected',
    last_test_at: '2024-01-15 14:30:00',
    created_at: '2024-01-01 09:00:00',
    testing: false
  },
  {
    id: 2,
    name: 'GPT-4',
    provider: 'openai',
    model_name: 'gpt-4',
    api_key: 'sk-***',
    api_base: '',
    temperature: 0.5,
    max_tokens: 4096,
    top_p: 1.0,
    description: '高级GPT-4模型配置',
    is_active: true,
    is_default: false,
    sort_order: 2,
    status: 'active',
    connection_status: 'connected',
    last_test_at: '2024-01-15 14:25:00',
    created_at: '2024-01-01 10:00:00',
    testing: false
  },
  {
    id: 3,
    name: '文心一言',
    provider: 'baidu',
    model_name: 'ernie-bot',
    api_key: 'xxx',
    api_base: 'https://aip.baidubce.com',
    temperature: 0.8,
    max_tokens: 2000,
    top_p: 0.9,
    description: '百度文心一言模型',
    is_active: true,
    is_default: false,
    sort_order: 3,
    status: 'active',
    connection_status: 'error',
    last_test_at: '2024-01-15 14:20:00',
    created_at: '2024-01-01 11:00:00',
    testing: false
  },
  {
    id: 4,
    name: '通义千问',
    provider: 'alibaba',
    model_name: 'qwen-turbo',
    api_key: 'xxx',
    api_base: '',
    temperature: 0.7,
    max_tokens: 1500,
    top_p: 1.0,
    description: '阿里通义千问模型',
    is_active: false,
    is_default: false,
    sort_order: 4,
    status: 'inactive',
    connection_status: 'unknown',
    last_test_at: null,
    created_at: '2024-01-01 12:00:00',
    testing: false
  }
])

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { min: 2, max: 50, message: '配置名称长度在 2 到 50 个字符', trigger: 'blur' }
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
  temperature: [
    { type: 'number', min: 0, max: 2, message: '温度值应在 0 到 2 之间', trigger: 'change' }
  ],
  max_tokens: [
    { type: 'number', min: 1, max: 32000, message: 'Token数量应在 1 到 32000 之间', trigger: 'change' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑配置' : '新增配置')

const filteredConfigs = computed(() => {
  let result = configs.value
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(config => 
      config.name.toLowerCase().includes(query) ||
      config.provider.toLowerCase().includes(query) ||
      config.model_name.toLowerCase().includes(query)
    )
  }
  
  if (filterProvider.value) {
    result = result.filter(config => config.provider === filterProvider.value)
  }
  
  if (filterStatus.value) {
    result = result.filter(config => config.status === filterStatus.value)
  }
  
  return result
})

// 方法
const getProviderIcon = (provider: string) => {
  const iconMap = {
    'openai': '/icons/openai.svg',
    'azure': '/icons/azure.svg',
    'anthropic': '/icons/anthropic.svg',
    'google': '/icons/google.svg',
    'baidu': '/icons/baidu.svg',
    'alibaba': '/icons/alibaba.svg',
    'tencent': '/icons/tencent.svg',
    'zhipu': '/icons/zhipu.svg',
    'moonshot': '/icons/moonshot.svg'
  }
  return iconMap[provider] || '/icons/default.svg'
}

const getStatusTagType = (status: string) => {
  const typeMap = {
    'active': 'success',
    'inactive': 'info',
    'testing': 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const textMap = {
    'active': '启用',
    'inactive': '禁用',
    'testing': '测试中'
  }
  return textMap[status] || status
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
  loadConfigs()
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (config: any) => {
  isEdit.value = true
  Object.assign(formData, {
    name: config.name,
    provider: config.provider,
    model_name: config.model_name,
    api_key: config.api_key,
    api_base: config.api_base,
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    top_p: config.top_p,
    description: config.description,
    is_active: config.is_active,
    is_default: config.is_default,
    sort_order: config.sort_order
  })
  currentConfig.value = config
  dialogVisible.value = true
}

const handleDuplicate = (config: any) => {
  isEdit.value = false
  Object.assign(formData, {
    name: config.name + ' (副本)',
    provider: config.provider,
    model_name: config.model_name,
    api_key: '',
    api_base: config.api_base,
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    top_p: config.top_p,
    description: config.description,
    is_active: false,
    is_default: false,
    sort_order: config.sort_order + 1
  })
  dialogVisible.value = true
}

const handleExport = (config: any) => {
  const exportData = {
    name: config.name,
    provider: config.provider,
    model_name: config.model_name,
    api_base: config.api_base,
    temperature: config.temperature,
    max_tokens: config.max_tokens,
    top_p: config.top_p,
    description: config.description
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

const handleSetDefault = async (config: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要将 "${config.name}" 设为默认配置吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 实际项目中这里会调用API
    configs.value.forEach(c => c.is_default = false)
    config.is_default = true
    
    ElMessage.success('默认配置设置成功')
  } catch {
    // 用户取消操作
  }
}

const handleToggleStatus = async (config: any) => {
  try {
    config.is_active = !config.is_active
    config.status = config.is_active ? 'active' : 'inactive'
    
    // 实际项目中这里会调用API
    ElMessage.success(`配置已${config.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    // 恢复原状态
    config.is_active = !config.is_active
    config.status = config.is_active ? 'active' : 'inactive'
    ElMessage.error('状态更新失败')
  }
}

const handleDelete = async (config: any) => {
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
    
    // 实际项目中这里会调用删除API
    const index = configs.value.findIndex(c => c.id === config.id)
    if (index > -1) {
      configs.value.splice(index, 1)
    }
    
    ElMessage.success('删除成功')
  } catch {
    // 用户取消删除
  }
}

const handleTest = async (config: any) => {
  config.testing = true
  config.connection_status = 'testing'
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟测试结果
    const success = Math.random() > 0.3
    config.connection_status = success ? 'connected' : 'error'
    config.last_test_at = new Date().toLocaleString()
    
    Object.assign(testResult, {
      success,
      response_time: Math.floor(Math.random() * 1000) + 100,
      model_info: success ? `${config.model_name} v1.0` : '',
      error: success ? '' : '连接超时或API密钥无效',
      test_message: success ? {
        input: 'Hello, how are you?',
        output: 'I am doing well, thank you for asking!'
      } : null
    })
    
    testResultVisible.value = true
    
    ElMessage.success(success ? '连接测试成功' : '连接测试失败')
  } catch (error) {
    config.connection_status = 'error'
    ElMessage.error('测试失败')
  } finally {
    config.testing = false
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
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const success = Math.random() > 0.3
    
    Object.assign(testResult, {
      success,
      response_time: Math.floor(Math.random() * 1000) + 100,
      model_info: success ? `${formData.model_name} v1.0` : '',
      error: success ? '' : '连接超时或API密钥无效',
      test_message: success ? {
        input: 'Hello, how are you?',
        output: 'I am doing well, thank you for asking!'
      } : null
    })
    
    testResultVisible.value = true
    
    ElMessage.success(success ? '连接测试成功' : '连接测试失败')
  } catch (error) {
    console.error('测试连接失败:', error)
  } finally {
    testingConnection.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    // 如果设为默认，取消其他配置的默认状态
    if (formData.is_default) {
      configs.value.forEach(c => c.is_default = false)
    }
    
    // 实际项目中这里会调用API
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    loadConfigs()
  } catch (error) {
    console.error('提交失败:', error)
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
    api_base: '',
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 1.0,
    description: '',
    is_active: true,
    is_default: false,
    sort_order: 0
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
    // 实际项目中这里会调用API
    await new Promise(resolve => setTimeout(resolve, 500))
    total.value = configs.value.length
  } catch (error) {
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
  height: 100%;
  display: flex;
  flex-direction: column;
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
  color: #303133;
}

.page-description {
  font-size: 14px;
  color: #606266;
  margin: 0;
}

.content-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s ease;
  position: relative;
}

.config-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.config-card--default {
  border-color: #67c23a;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
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

.provider-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  object-fit: contain;
}

.config-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #303133;
}

.provider-name {
  font-size: 14px;
  color: #606266;
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
  color: #606266;
  font-weight: 500;
}

.detail-item .value {
  color: #303133;
  text-align: right;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.api-url {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}

.description {
  white-space: normal;
  word-break: break-word;
}

.connection-status {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #e4e7ed;
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
  color: #67c23a;
}

.status-icon--error {
  color: #f56c6c;
}

.status-icon--testing {
  color: #e6a23c;
  animation: spin 1s linear infinite;
}

.status-icon--unknown {
  color: #909399;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  font-size: 14px;
  font-weight: 500;
}

.last-test {
  font-size: 12px;
  color: #909399;
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
  border-top: 1px solid #ebeef5;
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
  border-bottom: 1px solid #ebeef5;
}

.result-icon {
  font-size: 24px;
}

.result-icon--success {
  color: #67c23a;
}

.result-icon--error {
  color: #f56c6c;
}

.result-text {
  font-size: 18px;
  font-weight: 600;
}

.result-details {
  margin-bottom: 16px;
}

.result-details .detail-item {
  margin-bottom: 12px;
}

.error-text {
  color: #f56c6c;
}

.test-message {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
}

.test-message h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.message-content p {
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.5;
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
</style>