<template>
  <div class="smart-query">
    <div class="query-header">
      <h2>智能问数</h2>
      <div class="header-actions">
        <el-button @click="clearAll">
          <el-icon><Delete /></el-icon>
          清空所有
        </el-button>
        <el-button type="primary" @click="exportResults">
          <el-icon><Download /></el-icon>
          导出结果
        </el-button>
      </div>
    </div>

    <div class="query-content">
      <!-- 左侧数据源管理面板 -->
      <div class="data-source-panel">
        <div class="panel-header">
          <h3>数据源管理</h3>
        </div>
        
        <div class="source-tabs">
          <el-tabs v-model="activeDataSource" @tab-change="handleDataSourceChange">
            <el-tab-pane label="Excel分析" name="excel">
              <div class="excel-panel">
                <div class="upload-section">
                  <h4>上传Excel文件</h4>
                  <el-upload
                    ref="excelUpload"
                    class="upload-demo"
                    drag
                    :auto-upload="false"
                    :on-change="handleExcelUploadSuccess"
                    :on-error="handleUploadError"
                    :before-upload="beforeExcelUpload"
                    accept=".xlsx,.xls,.csv"
                    :limit="5"
                    :show-file-list="false"
                  >
                    <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                    <div class="el-upload__text">
                      拖拽Excel文件到此处，或<em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">
                        支持 .xlsx, .xls, .csv 格式，文件大小不超过10MB
                      </div>
                    </template>
                  </el-upload>
                </div>

                <div class="file-list">
                  <h4>文件列表</h4>
                  <div v-if="fileListLoading" class="loading-list">
                    <el-skeleton :rows="3" animated />
                    <div class="loading-text">正在加载文件列表...</div>
                  </div>
                  <div v-else-if="excelFileList.length === 0" class="empty-list">
                    <el-empty description="暂无上传文件" :image-size="60" />
                  </div>
                  <div v-else class="files">
                    <div 
                      v-for="(file, index) in excelFileList" 
                      :key="index"
                      class="file-item"
                      :class="{ active: selectedFile === file }"
                      @click="selectFile(file)"
                    >
                      <el-icon class="file-icon"><Document /></el-icon>
                      <div class="file-info">
                        <div class="file-name" :title="file.name">{{ file.name }}</div>
                        <div class="file-meta">
                          <span class="file-size">{{ formatFileSize(file.size) }}</span>
                          <span class="file-time">{{ formatUploadTime(file.uploadTime) }}</span>
                        </div>
                        <div class="file-status">
                          <el-tag v-if="file.status === 'success'" type="success" size="small">已上传</el-tag>
                          <el-tag v-else-if="file.status === 'uploading'" type="warning" size="small">上传中</el-tag>
                          <el-tag v-else-if="file.status === 'error'" type="danger" size="small">上传失败</el-tag>
                        </div>
                      </div>
                      <div class="file-actions">
                        <el-button 
                          size="small" 
                          type="primary" 
                          text 
                          @click.stop="previewFile(file)"
                          :disabled="file.status !== 'success'"
                        >
                          <el-icon><View /></el-icon>
                        </el-button>
                        <el-button 
                          size="small" 
                          type="danger" 
                          text 
                          @click.stop="removeFile(file)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="数据库管理" name="database">
              <div class="database-panel">
                <div class="connection-section">
                  <h4>数据库配置</h4>
                  <el-form :model="dbConfig" label-width="60px" size="small">
                    <el-form-item label="配置名">
                      <el-input v-model="dbConfig.configName" placeholder="输入配置名称（可选）" />
                    </el-form-item>
                    <el-form-item label="类型">
                      <el-select v-model="dbConfig.type" placeholder="选择数据库类型">
                        <el-option label="PostgreSQL" value="postgresql" />
                        <el-option label="MySQL" value="mysql" />
                        <el-option label="SQLite" value="sqlite" />
                        <el-option label="SQL Server" value="sqlserver" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="主机">
                      <el-input v-model="dbConfig.host" placeholder="localhost" />
                    </el-form-item>
                    <el-form-item label="端口">
                      <el-input v-model="dbConfig.port" placeholder="3306" />
                    </el-form-item>
                    <el-form-item label="数据库">
                      <el-input v-model="dbConfig.database" placeholder="数据库名" />
                    </el-form-item>
                    <el-form-item label="用户名">
                      <el-input v-model="dbConfig.username" placeholder="用户名" />
                    </el-form-item>
                    <el-form-item label="密码">
                      <el-input v-model="dbConfig.password" type="password" placeholder="密码" show-password />
                    </el-form-item>
                    <el-form-item>
                      <div class="button-group">
                        <el-button @click="testConnection" size="small" :loading="testingConnection">
                          <el-icon><Connection /></el-icon>
                          测试连接
                        </el-button>
                        <el-button @click="connectDatabase" size="small">
                          连接
                        </el-button>
                        <el-button type="success" @click="saveDbConfig" :loading="savingConfig" size="small">
                          <el-icon><Check /></el-icon>
                          保存配置
                        </el-button>
                      </div>
                    </el-form-item>
                  </el-form>
                </div>

                <div class="table-list-section">
                  <div class="table-list-header">
                    <h4>数据库表列表</h4>
                    <el-button 
                      v-if="dbConnected"
                      type="primary" 
                      size="small" 
                      @click="collectTableMetadata"
                      :loading="collectingMetadata"
                    >
                      <el-icon><Collection /></el-icon>
                      收集表元数据
                    </el-button>
                  </div>
                  <div v-if="!dbConnected" class="empty-list">
                    <el-empty description="请先连接数据库" :image-size="60" />
                  </div>
                  <div v-else-if="dbTables.length === 0" class="empty-list">
                    <el-empty description="暂无数据表" :image-size="60" />
                  </div>
                  <div v-else class="tables">
                    <div 
                      v-for="table in dbTables" 
                      :key="table"
                      class="table-item"
                      :class="{ active: selectedTable === table }"
                      @click="selectTable(table)"
                    >
                      <el-icon class="table-icon"><Grid /></el-icon>
                      <div class="table-info">
                        <div class="table-name">{{ table }}</div>
                        <div class="table-meta">数据表</div>
                      </div>
                    </div>
                  </div>
                </div>


              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <!-- 中间数据预览区域 -->
      <div class="data-preview-panel">
        <div class="preview-header">
          <h3>数据预览</h3>
          <div class="preview-actions">
            <el-button size="small" @click="refreshPreview">
              <el-icon><RefreshLeft /></el-icon>
              刷新
            </el-button>
            <el-button size="small" @click="exportPreviewData">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button 
              v-if="activeDataSource === 'database' && selectedTable && dbConnected"
              size="small" 
              @click="toggleMetadataConfig" 
              :type="metadataConfigExpanded ? 'warning' : 'primary'"
            >
              <el-icon><Setting /></el-icon>
              {{ metadataConfigExpanded ? '收起配置' : '表配置' }}
            </el-button>
            <el-button size="small" @click="toggleCollapse" :type="isCollapsed ? 'primary' : 'warning'">
              <el-icon><Aim v-if="!isCollapsed" /><FullScreen v-else /></el-icon>
              {{ isCollapsed ? '折叠' : '展开' }}
            </el-button>
          </div>
        </div>
        
        <div class="preview-content">
          <div v-if="!selectedFile && !selectedTable" class="empty-preview">
            <el-empty description="请选择Excel文件或数据表进行预览">
              <template #image>
                <el-icon size="60"><DataAnalysis /></el-icon>
              </template>
            </el-empty>
          </div>
          
          <div v-else-if="previewLoading" class="loading-preview">
            <el-skeleton :rows="8" animated />
            <div class="loading-text">正在加载数据预览...</div>
          </div>
          
          <div v-else class="preview-data">
            <div class="preview-info">
              <div class="data-source-info">
                <el-tag v-if="selectedFile" type="primary">
                  <el-icon><Document /></el-icon>
                  {{ selectedFile.name }}
                </el-tag>
                <el-tag v-if="selectedTable" type="success">
                  <el-icon><Grid /></el-icon>
                  {{ selectedTable }}
                </el-tag>
              </div>
              <div class="data-stats">
                <el-tag>行数: {{ previewData?.rows || 0 }}</el-tag>
                <el-tag>列数: {{ previewData?.columns || 0 }}</el-tag>
              </div>
            </div>
            
            <div class="preview-table">
              <el-table 
                :data="previewData?.data || []" 
                height="320"
                stripe
                border
                size="small"
              >
                <el-table-column 
                  v-for="column in previewData?.column_names || []" 
                  :key="column"
                  :prop="column"
                  :label="column"
                  min-width="120"
                  show-overflow-tooltip
                />
              </el-table>
              <div class="preview-pagination">
                <el-pagination
                  v-if="previewData?.total > (previewData?.data?.length || 0)"
                  :current-page="previewCurrentPage"
                  :page-size="previewPageSize"
                  :total="previewData?.total || 0"
                  layout="total, prev, pager, next"
                  @current-change="handlePreviewPageChange"
                  size="small"
                />
              </div>
            </div>
          </div>
        </div>
        
        <!-- 表元数据编辑区域 -->
        <div v-if="activeDataSource === 'database' && selectedTable && dbConnected && metadataConfigExpanded" class="table-metadata-editor">
          <div class="metadata-editor-header">
            <h4>
              <el-icon><DataAnalysis /></el-icon>
              {{ selectedTable }} - 表元数据配置
            </h4>
            <div class="metadata-editor-actions">
              <el-button 
                size="small" 
                type="primary" 
                @click="saveTableMetadata"
                :loading="savingMetadata"
              >
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
              <el-button 
                size="small" 
                @click="loadCurrentTableMetadata"
                :loading="loadingMetadata"
              >
                <el-icon><RefreshLeft /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
          
          <div class="metadata-editor-content">
            <div v-if="loadingMetadata" class="loading-metadata">
              <el-skeleton :rows="4" animated />
              <div class="loading-text">正在加载表元数据...</div>
            </div>
            
            <div v-else-if="currentTableMetadata" class="metadata-form">
              <el-form :model="currentTableMetadata" label-width="100px" size="small">
                <el-form-item label="启用问答">
                  <el-switch 
                    v-model="currentTableMetadata.is_enabled_for_qa"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>
                
                <el-form-item label="表描述">
                  <el-input
                    v-model="currentTableMetadata.qa_description"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入表的功能描述，例如：用户信息表、订单表、产品表等"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
                
                <el-form-item label="业务上下文">
                  <el-input
                    v-model="currentTableMetadata.business_context"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入表的业务背景和使用场景"
                    maxlength="300"
                    show-word-limit
                  />
                </el-form-item>
                
                <el-form-item label="表信息">
                  <div class="table-info-display">
                    <el-tag>{{ currentTableMetadata.columns?.length || 0 }} 列</el-tag>
                    <el-tag type="success">{{ currentTableMetadata.row_count || 0 }} 行</el-tag>
                    <el-tag type="info" v-if="currentTableMetadata.last_synced_at">
                      更新时间: {{ formatDate(currentTableMetadata.last_synced_at) }}
                    </el-tag>
                  </div>
                </el-form-item>
              </el-form>
            </div>
            
            <div v-else class="empty-metadata">
              <el-empty description="暂无表元数据，请先收集表信息">
                <el-button type="primary" @click="collectCurrentTableMetadata">
                  <el-icon><Collection /></el-icon>
                  收集表元数据
                </el-button>
              </el-empty>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧智能查询区域 -->
       <div class="chat-panel" :class="{ 'chat-panel-compact': isCollapsed, 'chat-panel-expanded': isChatCollapsed }">
         <div class="chat-header">
  <h3>智能问数</h3>
  <div class="chat-actions">
    <el-button size="small" @click="clearChat">
      <el-icon><Delete /></el-icon>
      清空对话
    </el-button>
    <el-button size="small" @click.stop="toggleChatCollapse" :type="isChatCollapsed ? 'warning' : 'primary'">
      <el-icon><FullScreen v-if="!isChatCollapsed" /><Aim v-else /></el-icon>
      {{ isChatCollapsed ? '收起' : '展开' }}
    </el-button>
  </div>
</div>
        
        <div class="chat-content">
          <div class="chat-messages" ref="chatMessagesContainer">
            <div v-if="chatMessages.length === 0" class="empty-chat">
              <el-empty description="开始您的数据问答之旅">
                <template #image>
                  <el-icon size="60"><ChatDotRound /></el-icon>
                </template>
              </el-empty>
            </div>
            
            <div v-else>
              <div 
                v-for="(message, index) in chatMessages" 
                :key="index"
                class="message-item"
                :class="message.type"
              >
                <!-- 用户消息 -->
                <div v-if="message.type === 'user'" class="user-message">
                  <div class="message-header">
                    <el-avatar :size="28" class="user-avatar">
                      <el-icon><User /></el-icon>
                    </el-avatar>
                    <span class="message-sender">您</span>
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  </div>
                  <div class="message-content user-content">
                    <div class="message-text">{{ message.content }}</div>
                  </div>
                </div>
                
                <!-- 机器人消息 -->
                <div v-else class="bot-message">
                  <div class="message-header">
                    <el-avatar :size="28" class="bot-avatar">
                      <el-icon><Service /></el-icon>
                    </el-avatar>
                    <span class="message-sender">智能助手</span>
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  </div>
                  
                  <!-- 工作流步骤显示区域（仅在机器人回答中显示） -->
                  <div v-if="message.workflowSteps && message.workflowSteps.length > 0" class="workflow-steps-panel">
                    <div class="workflow-header" @click="toggleWorkflowCollapse(index)">
                      <div class="workflow-title">
                        <el-icon><PieChart /></el-icon>
                        <span>执行过程</span>
                        <el-tag :type="getWorkflowStatusType(message.workflowSteps)" size="small">
                          {{ getWorkflowStatusText(message.workflowSteps) }}
                        </el-tag>
                      </div>
                      <el-icon class="collapse-icon" :class="{ 'collapsed': message.workflowCollapsed }">
                        <View />
                      </el-icon>
                    </div>
                    <div v-show="!message.workflowCollapsed" class="workflow-steps">
                      <div 
                        v-for="(step, stepIndex) in message.workflowSteps" 
                        :key="stepIndex"
                        class="workflow-step"
                        :class="step.status"
                      >
                        <div class="step-icon">
                          <el-icon v-if="step.status === 'completed'"><Check /></el-icon>
                          <el-icon v-else-if="step.status === 'running'" class="rotating"><Loading /></el-icon>
                          <el-icon v-else-if="step.status === 'failed'"><Close /></el-icon>
                          <el-icon v-else><Clock /></el-icon>
                        </div>
                        <div class="step-content">
                          <div class="step-title">{{ getStepTitle(step.step) }}</div>
                          <div class="step-message">{{ step.message }}</div>
                          <div v-if="step.details" class="step-details">
                            <span v-if="step.details.file_count">文件数: {{ step.details.file_count }}</span>
                            <span v-if="step.details.dataframe_count">数据表: {{ step.details.dataframe_count }}</span>
                            <span v-if="step.details.total_rows">总行数: {{ step.details.total_rows }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 表格结果显示区域 -->
                  <div v-if="message.resultType === 'table_data' && message.tableData" class="table-result">
                    <h3>查询结果</h3>
                    <el-table 
                      :data="message.tableData.data" 
                      style="width: 100%"
                      :max-height="400"
                      stripe
                      border
                      size="small"
                      class="result-table"
                    >
                      <el-table-column 
                        v-for="column in message.tableData.columns" 
                        :key="column.prop"
                        :prop="column.prop" 
                        :label="column.label"
                        :width="column.width"
                        show-overflow-tooltip
                      >
                      </el-table-column>
                    </el-table>
                    <div class="table-info">
                      共 {{ message.tableData.total }} 行数据
                    </div>
                  </div>

                  <!-- 引用数据显示区域 -->
                  <div v-if="['text', 'scalar', 'other'].includes(message.resultType) && message.referenceData" class="reference-result">
                    <h3>{{ getResultTypeLabel(message.resultType) }}</h3>
                    <div class="reference-content">
                      <div class="reference-header">
                        <el-icon class="reference-icon"><Document /></el-icon>
                        <span class="reference-type">{{ message.resultType.toUpperCase() }}</span>
                      </div>
                      <div class="reference-data">
                        <pre v-if="typeof message.referenceData.data === 'object'">{{ JSON.stringify(message.referenceData.data, null, 2) }}</pre>
                        <div v-else class="reference-text">{{ message.referenceData.data }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="message-content bot-content">
                    <div class="message-text" v-html="formatMessage(message.content)"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="chat-input">
            <div class="query-suggestions" v-if="querySuggestions.length > 0">
              <div class="suggestions-title">推荐问题：</div>
              <div class="suggestions">
                <el-tag 
                  v-for="suggestion in querySuggestions" 
                  :key="suggestion"
                  class="suggestion-tag"
                  @click="applyQuerySuggestion(suggestion)"
                  size="small"
                >
                  {{ suggestion }}
                </el-tag>
              </div>
            </div>
            
            <div class="input-area">
              <el-input
                v-model="queryText"
                type="textarea"
                :rows="3"
                placeholder="请输入您的问题，例如：\n- 显示销售额最高的前10个产品\n- 查询最近一个月的订单总数和总金额"
                class="query-textarea"
                @keydown.enter.ctrl="executeQuery"
              />
              <div class="input-actions">
                <el-button 
                  type="primary" 
                  @click="executeQuery" 
                  :loading="queryLoading"
                  :disabled="!canExecuteQuery"
                >
                  <el-icon><Search /></el-icon>
                  发送
                </el-button>
                <el-button @click="clearQuery">
                  <el-icon><RefreshLeft /></el-icon>
                  清空
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      


    </div>
  </div>

  <!-- 问答设置编辑对话框 -->
  <el-dialog
    v-model="qaSettingsDialogVisible"
    :title="`编辑表 ${currentEditingMetadata?.table_name || ''} 的问答设置`"
    width="600px"
    :before-close="cancelQASettings"
    class="qa-settings-dialog"
  >
    <div class="qa-settings-form">
      <el-form :model="qaSettingsForm" label-width="120px" label-position="top">
        <el-form-item label="启用问答">
          <el-switch
            v-model="qaSettingsForm.is_enabled_for_qa"
            active-text="启用"
            inactive-text="禁用"
            active-color="#13ce66"
            inactive-color="#ff4949"
          />
        </el-form-item>
        
        <el-form-item label="问答描述">
          <el-input
            v-model="qaSettingsForm.qa_description"
            type="textarea"
            :rows="4"
            placeholder="请输入该表的业务说明和用途描述，例如：
            • 用户信息表：存储系统用户的基本信息，包括姓名、邮箱、注册时间等
            • 订单表：记录用户购买商品的订单信息，包含订单号、商品、金额、状态等
            • 产品表：管理商品信息，包括名称、价格、库存、分类等"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="业务上下文">
          <el-input
            v-model="qaSettingsForm.business_context"
            type="textarea"
            :rows="4"
            placeholder="请输入表的业务背景和使用场景，例如：
            • 该表用于电商系统的用户管理模块
            • 支持用户注册、登录、个人信息维护等功能
            • 与订单表、购物车表等有关联关系
            • 数据更新频率较高，主要在用户操作时更新"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="cancelQASettings">取消</el-button>
        <el-button type="primary" @click="saveQASettings">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, inject, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete,
  Download,
  UploadFilled,
  Search,
  RefreshLeft,
  PieChart,
  DataAnalysis,
  Document,
  Grid,
  ChatDotRound,
  User,
  Service,
  View,
  FullScreen,
  Aim,
  Loading,
  Check,
  Close,
  Clock,
  Collection,
  Setting,
  Connection
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import MarkdownIt from 'markdown-it'

// 配置Markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true
})

// 确保启用表格功能
md.enable(['table'])

// Store
const userStore = useUserStore()

// 响应式数据
const activeDataSource = ref('excel')
const queryText = ref('')
const queryLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)

// Excel相关
const excelFileList = ref([])
const excelData = ref(null)
const selectedFile = ref(null)
const fileListLoading = ref(false)
const uploadUrl = computed(() => `${import.meta.env.VITE_API_BASE_URL}/smart-query/upload-excel`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
}))

// 数据库相关
// 数据库配置相关
const savingConfig = ref(false)
const loadingConfig = ref(false)
const savedConfigs = ref([])
const selectedConfig = ref(null)
const isConnecting = ref(false) // 添加这行

// 修改dbConfig结构，添加配置名称
const isConnected = ref(false) // 添加数据库连接状态

const dbConfig = ref({
  configName: '',
  type: 'postgresql',
  host: 'localhost',
  port: '5432',
  database: '',
  username: '',
  password: ''
})
const testingConnection = ref(false)
const connectionValid = ref(false)
const dbConnected = ref(false)
const dbTables = ref([])
const tables = ref([]) // 如果模板中使用了tables变量，添加这行
const selectedTable = ref('')
const tableSchema = ref(null)

// 表元数据管理相关
const tableMetadataList = ref([])
const selectedMetadata = ref(null)
const collectingMetadata = ref(false)
const loadingMetadata = ref(false)

// 表元数据编辑相关
const currentTableMetadata = ref(null)
const savingMetadata = ref(false)
const metadataConfigExpanded = ref(false)

// 数据预览相关
const previewData = ref(null)
const previewLoading = ref(false)
const previewCurrentPage = ref(1)
const previewPageSize = ref(20)

// 聊天相关
const chatMessages = ref([])
const currentConversationId = ref(null)
const workflowSteps = ref([])

// 查询结果
const queryResult = ref(null)
const querySuggestions = ref([])
const isCollapsed = ref(false)
const isChatCollapsed = ref(false)

// 注入父组件的方法
const parentToggleSidebar = inject('toggleSidebar', null)

// 计算属性
const canExecuteQuery = computed(() => {
  if (activeDataSource.value === 'excel') {
    return selectedFile.value && queryText.value.trim()
  } else {
    return selectedConfig.value && queryText.value.trim()
  }
})

// 方法
const handleDataSourceChange = async (tab: string) => {
  activeDataSource.value = tab
  queryText.value = ''
  queryResult.value = null
  selectedFile.value = null
  selectedTable.value = ''
  previewData.value = null
  updateQuerySuggestions()
  
  // 如果切换到数据库tab，自动连接第一个配置
  if (tab === 'database') {
    await autoConnectFirstConfig()
  }
}

// 文件相关方法
const loadFileList = async () => {
  fileListLoading.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-query/files?page=1&page_size=50`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    const result = await response.json()
    
    if (result.success && result.data) {
      excelFileList.value = result.data.files.map(file => ({
        id: file.id,
        name: file.filename,
        size: file.file_size,
        status: file.is_processed ? 'success' : 'error',
        uploadTime: new Date(file.upload_time).getTime(),
        data: {
          file_id: file.id,
          original_filename: file.filename,
          file_size_mb: file.file_size_mb,
          sheet_names: file.sheet_names,
          upload_time: file.upload_time
        }
      }))
      
      // 如果有文件且没有选中的文件，自动选择第一个
      if (excelFileList.value.length > 0 && !selectedFile.value) {
        const firstSuccessFile = excelFileList.value.find(f => f.status === 'success')
        if (firstSuccessFile) {
          selectFile(firstSuccessFile)
        }
      }
    } else {
      ElMessage.error(result.message || '加载文件列表失败')
    }
  } catch (error) {
    console.error('加载文件列表失败:', error)
    ElMessage.error('加载文件列表失败')
  } finally {
    fileListLoading.value = false
  }
}

const selectFile = (file: any) => {
  selectedFile.value = file
  selectedTable.value = ''
  // 重置分页和清除之前的预览数据
  previewCurrentPage.value = 1
  previewData.value = null
  loadFilePreview(file)
}



const formatFileSize = (size: number) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatUploadTime = (timestamp: number) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return date.toLocaleDateString()
}

const previewFile = (file: any) => {
  if (file.status === 'success') {
    selectFile(file)
    ElMessage.success('正在加载文件预览...')
  }
}

const removeFile = async (file: any) => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-query/files/${file.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    const result = await response.json()
    
    if (result.success) {
      // 如果删除的是当前预览的文件，清空预览
      if (selectedFile.value && selectedFile.value.id === file.id) {
        selectedFile.value = null
        previewData.value = null
        excelData.value = null
      }
      
      // 重新加载文件列表
      await loadFileList()
      
      ElMessage.success('文件已删除')
    } else {
      ElMessage.error(result.message || '删除文件失败')
    }
  } catch (error) {
    console.error('删除文件失败:', error)
    ElMessage.error('删除文件失败')
  }
}

// 表格相关方法
const selectTable = (table: string) => {
  selectedTable.value = table
  selectedFile.value = null
  loadTablePreview(table)
  // 自动加载表元数据
  loadCurrentTableMetadata()
}

// 数据预览相关方法
const loadFilePreview = async (file: any) => {
  console.log('开始加载文件预览:', file)
  if (!file || file.status !== 'success') {
    console.log('文件状态不正确，跳过预览:', file?.status)
    previewData.value = null
    return
  }
  
  previewLoading.value = true
  console.log('设置预览加载状态为true')
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-query/preview-excel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        file_id: String(file.id),
        page: previewCurrentPage.value,
        page_size: previewPageSize.value
      })
    })
    
    const result = await response.json()
    console.log('API响应结果:', result)
    if (result.success) {
      previewData.value = {
        rows: result.data.total_rows,
        columns: result.data.columns.length,
        column_names: result.data.columns,
        data: result.data.data,
        total: result.data.total_rows
      }
      console.log('设置预览数据:', previewData.value)
      ElMessage.success('文件预览加载成功')
    } else {
      console.log('API调用失败:', result.message)
      ElMessage.error(result.message || '加载文件预览失败')
      // 如果API调用失败，使用模拟数据
      previewData.value = {
        rows: 100,
        columns: 5,
        column_names: ['日期', '产品', '地区', '销售额', '销售量'],
        data: [
          { '日期': '2023-10-01', '产品': '产品A', '地区': '华北', '销售额': '¥12,500', '销售量': 250 },
          { '日期': '2023-10-01', '产品': '产品B', '地区': '华东', '销售额': '¥8,700', '销售量': 174 },
          { '日期': '2023-10-02', '产品': '产品A', '地区': '华南', '销售额': '¥9,800', '销售量': 196 },
          { '日期': '2023-10-02', '产品': '产品C', '地区': '华北', '销售额': '¥15,200', '销售量': 304 },
          { '日期': '2023-10-03', '产品': '产品B', '地区': '华东', '销售额': '¥11,300', '销售量': 226 }
        ],
        total: 100
      }
    }
  } catch (error) {
    console.log('API调用失败，使用模拟数据:', error)
    ElMessage.error('加载文件预览失败')
    // 网络错误时使用模拟数据
    previewData.value = {
      rows: 100,
      columns: 5,
      column_names: ['日期', '产品', '地区', '销售额', '销售量'],
      data: [
        { '日期': '2023-10-01', '产品': '产品A', '地区': '华北', '销售额': '¥12,500', '销售量': 250 },
        { '日期': '2023-10-01', '产品': '产品B', '地区': '华东', '销售额': '¥8,700', '销售量': 174 },
        { '日期': '2023-10-02', '产品': '产品A', '地区': '华南', '销售额': '¥9,800', '销售量': 196 },
        { '日期': '2023-10-02', '产品': '产品C', '地区': '华北', '销售额': '¥15,200', '销售量': 304 },
        { '日期': '2023-10-03', '产品': '产品B', '地区': '华东', '销售额': '¥11,300', '销售量': 226 }
      ],
      total: 100
    }
  } finally {
    previewLoading.value = false
    console.log('预览加载完成，当前预览数据:', previewData.value)
  }
}

const loadTablePreview = async (table: string) => {
  previewLoading.value = true
  try {
    // 调用后端API获取表格预览数据
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/database-config/tables/${encodeURIComponent(table)}/data?limit=100`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    const result = await response.json()
    
    if (result.success && result.data) {
      // 转换API返回的数据格式为前端预览组件需要的格式
      const tableData = result.data
      
      previewData.value = {
        rows: tableData.total_rows || tableData.data?.length || 0,
        columns: tableData.columns?.length || 0,
        column_names: tableData.columns || [],
        data: tableData.data || [],
        total: tableData.total_rows || tableData.data?.length || 0
      }
      
      ElMessage.success('表格预览加载成功')
    } else {
      ElMessage.error(result.message || '加载表格预览失败')
      // 如果API调用失败，清空预览数据
      previewData.value = null
    }
  } catch (error) {
    console.error('加载表格预览失败:', error)
    ElMessage.error('加载表格预览失败')
    previewData.value = null
  } finally {
    previewLoading.value = false
  }
}

const refreshPreview = () => {
  if (selectedFile.value) {
    loadFilePreview(selectedFile.value)
  } else if (selectedTable.value) {
    loadTablePreview(selectedTable.value)
  }
}

const exportPreviewData = () => {
  ElMessage.info('导出功能开发中...')
}

const handlePreviewPageChange = (page: number) => {
  previewCurrentPage.value = page
  // 重新加载对应页的数据
  if (selectedFile.value) {
    loadFilePreview(selectedFile.value)
  }
}

// 聊天相关方法
const clearChat = () => {
  chatMessages.value = []
}

const formatMessage = (content: string) => {
  // 检测是否包含Markdown表格
  const hasTable = content.includes('|') && (
    content.includes('---') || 
    content.match(/\|.*\|.*\n.*\|.*\|/)
  )
  
  if (hasTable) {
    // 手动转换Markdown表格为HTML
    const lines = content.split('\n')
    let htmlContent = ''
    let inTable = false
    let isFirstRow = true
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      
      // 检测表格行（包含|但不是分隔行）
      if (line.includes('|') && !line.includes('---')) {
        if (!inTable) {
          htmlContent += '<div class="table-container"><table class="markdown-table"><tbody>'
          inTable = true
        }
        
        const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell)
        const tag = isFirstRow ? 'th' : 'td'
        
        htmlContent += `<tr>${cells.map(cell => `<${tag}>${cell}</${tag}>`).join('')}</tr>`
        isFirstRow = false
      } else if (line.includes('---') && inTable) {
        // 跳过分隔行
        continue
      } else {
        if (inTable) {
          htmlContent += '</tbody></table></div>'
          inTable = false
          isFirstRow = true
        }
        
        // 处理其他内容（如标题）
        if (line.startsWith('##')) {
          htmlContent += `<h2>${line.substring(2).trim()}</h2>`
        } else if (line.startsWith('#')) {
          htmlContent += `<h1>${line.substring(1).trim()}</h1>`
        } else if (line.trim()) {
          htmlContent += `<p>${line}</p>`
        }
      }
    }
    
    if (inTable) {
      htmlContent += '</tbody></table></div>'
    }
    
    return htmlContent
  }
  
  // 其他Markdown语法处理
  if (content.includes('#') || content.includes('**') || content.includes('```')) {
    return md.render(content)
  }
  
  return content.replace(/\n/g, '<br>')
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString()
}

const beforeExcelUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                  file.type === 'application/vnd.ms-excel' ||
                  file.type === 'text/csv'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 或 CSV 文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

const handleExcelUploadSuccess = async (file: any) => {
  console.log('文件上传开始:', file.name)
  
  const formData = new FormData()
  formData.append('file', file.raw)
  
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-query/upload-excel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: formData
    })
    
    const result = await response.json()
    
    if (result.success) {
      ElMessage.success('Excel文件上传成功')
      
      // 重新加载文件列表
      await loadFileList()
      
      // 自动选择刚上传的文件
      const uploadedFile = excelFileList.value.find(f => f.id === result.file_id)
      if (uploadedFile) {
        selectFile(uploadedFile)
      }
      
      updateQuerySuggestions()
    } else {
      ElMessage.error(result.message || '上传失败')
    }
  } catch (error) {
    console.error('上传文件失败:', error)
    ElMessage.error('上传文件失败')
  }
}

const handleUploadError = (error: any, file: any) => {
  // 更新文件状态为失败
  const existingIndex = excelFileList.value.findIndex(f => f.name === file.name && f.size === file.size)
  if (existingIndex >= 0) {
    excelFileList.value[existingIndex].status = 'error'
  }
  ElMessage.error('文件上传失败')
}



const testConnection = async () => {
  testingConnection.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-query/test-db-connection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(dbConfig.value)
    })
    
    const result = await response.json()
    if (result.success) {
      connectionValid.value = true
      ElMessage.success('数据库连接测试成功')
    } else {
      connectionValid.value = false
      ElMessage.error(result.message || '连接测试失败')
    }
  } catch (error) {
    connectionValid.value = false
    ElMessage.error('连接测试失败')
  } finally {
    testingConnection.value = false
  }
}

// 保存数据库配置
const saveDbConfig = async () => {
  if (!dbConfig.value.configName?.trim()) {
    ElMessage.warning('请输入配置名称')
    return
  }
  
  savingConfig.value = true
  try {
    const configData = {
      name: dbConfig.value.configName,
      db_type: dbConfig.value.type,
      host: dbConfig.value.host,
      port: parseInt(dbConfig.value.port),
      database: dbConfig.value.database,
      username: dbConfig.value.username,
      password: dbConfig.value.password,
      is_default: false
    }
    
    // 使用现有的database-config API
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/database-config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(configData)
    })
    
    const result = await response.json()
    if (response.ok) {
      ElMessage.success('数据库配置保存成功')
      await loadSavedConfigs() // 重新加载配置列表
    } else {
      ElMessage.error(result.detail || '保存配置失败')
    }
  } catch (error) {
    console.error('保存数据库配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    savingConfig.value = false
  }
}

// 加载数据库配置
const loadDbConfig = async (configId) => {
  try {
    loadingConfig.value = true
    await loadSavedConfigs()
    
    // 将局部变量改为响应式变量赋值
    selectedConfig.value = savedConfigs.value.find(config => config.id === configId)
    if (selectedConfig.value) {
      dbConfig.value = {
        type: selectedConfig.value.db_type,
        host: selectedConfig.value.host,
        port: selectedConfig.value.port,
        database: selectedConfig.value.database,
        username: selectedConfig.value.username,
        password: '', // 密码不回填
        configName: selectedConfig.value.config_name
      }
      ElMessage.success(`已加载配置: ${selectedConfig.value.config_name}`)
      return true
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败')
    return false
  } finally {
    loadingConfig.value = false
  }
}

// 加载保存的配置列表
const loadSavedConfigs = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/database-config`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    if (response.ok) {
      const configs = await response.json()
      savedConfigs.value = configs.map(config => ({
        id: config.id,
        config_name: config.name,
        db_type: config.db_type,
        host: config.host,
        port: config.port.toString(),
        database: config.database,
        username: config.username,
        created_at: config.created_at
      }))
    }
  } catch (error) {
    console.error('加载配置列表失败:', error)
  }
}

// 加载指定类型的配置
const loadConfigByType = async (dbType) => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/database-config/by-type/${dbType}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    if (response.ok) {
      const config = await response.json()
      // 设置selectedConfig
      selectedConfig.value = {
        id: config.id,
        db_type: config.db_type,
        host: config.host,
        port: config.port,
        database: config.database,
        username: config.username,
        config_name: config.name
      }
      
      // 自动填充所有配置，包括密码
      dbConfig.value = {
        ...dbConfig.value,
        type: dbType,
        configName: config.name,
        host: config.host,
        port: config.port.toString(),
        database: config.database,
        username: config.username,
        password: config.password
      }
      return true
    } else if (response.status === 404) {
      // 没有找到该类型的配置时，清空selectedConfig
      selectedConfig.value = null
      
      // 使用默认值
      const defaultPorts = {
        'postgresql': '5432',
        'mysql': '3306',
        'sqlserver': '1433',
        'sqlite': ''
      }
      
      dbConfig.value = {
        ...dbConfig.value,
        type: dbType,
        configName: '',
        host: 'localhost',
        port: defaultPorts[dbType] || '',
        database: '',
        username: '',
        password: ''
      }
      return false
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    selectedConfig.value = null // 出错时也要清空
    ElMessage.error('加载配置失败')
    return false
  }
}

// 监听数据库类型变化，自动加载对应配置
watch(() => dbConfig.value.type, async (newType) => {
  await loadConfigByType(newType)
})

const connectDatabase = async () => {
  if (!selectedConfig.value?.id) {
    ElMessage.error('请先选择数据库配置');
    return;
  }
  
  try {
    isConnecting.value = true;
    // 修改URL路径，使用database-config的接口
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/database-config/${selectedConfig.value.id}/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
      // 不需要body，config_id已经在URL路径中
    });
    
    const result = await response.json();
    if (result.success) {
        isConnected.value = true;
        dbConnected.value = true;  // 添加这一行
        // 从对象数组中提取表名
        const tableList = result.data.tables || [];
        dbTables.value = tableList.map(table => table.table_name);
        ElMessage.success('数据库连接成功');
    } else {
      ElMessage.error(result.message || '连接失败');
    }
  } catch (error) {
    ElMessage.error('连接失败: ' + error.message);
  } finally {
    isConnecting.value = false; // 连接完成，设置为false 
  }
}

// 自动连接第一个配置
const autoConnectFirstConfig = async () => {
  try {
    // 如果没有加载配置，先加载
    if (savedConfigs.value.length === 0) {
      await loadSavedConfigs()
    }
    
    // 如果有配置，自动选择第一个并连接
    if (savedConfigs.value.length > 0) {
      selectedConfig.value = savedConfigs.value[0]
      
      // 自动连接数据库
      await connectDatabase()
      
      // 连接成功后自动收集表元数据
      if (isConnected.value) {
        await collectTableMetadata()
      }
    } else {
      ElMessage.warning('没有找到数据库配置，请先添加配置')
    }
  } catch (error) {
    console.error('自动连接失败:', error)
    ElMessage.error('自动连接失败')
  }
}

// 表元数据管理相关方法
const collectTableMetadata = async () => {
  if (!selectedConfig.value?.id) {
    ElMessage.error('请先连接数据库')
    return
  }
  
  if (!dbTables.value || dbTables.value.length === 0) {
    ElMessage.error('没有可收集的表，请先连接数据库获取表列表')
    return
  }
  
  collectingMetadata.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/table-metadata/collect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        database_config_id: selectedConfig.value.id,
        table_names: dbTables.value
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success(`成功收集了 ${result.total_collected} 个表的元数据`)
      await refreshTableMetadata()
    } else {
      ElMessage.error(result.message || '收集表元数据失败')
    }
  } catch (error) {
    console.error('收集表元数据失败:', error)
    ElMessage.error('收集表元数据失败')
  } finally {
    collectingMetadata.value = false
  }
}

const refreshTableMetadata = async () => {
  loadingMetadata.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/table-metadata/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    const result = await response.json()
    if (result.success) {
      tableMetadataList.value = result.data.map(metadata => ({
        id: metadata.id,
        table_name: metadata.table_name,
        column_count: metadata.columns?.length || 0,
        created_at: metadata.created_at,
        updated_at: metadata.updated_at,
        qa_settings: metadata.qa_settings
      }))
    } else {
      ElMessage.error(result.message || '加载表元数据失败')
    }
  } catch (error) {
    console.error('加载表元数据失败:', error)
    ElMessage.error('加载表元数据失败')
  } finally {
    loadingMetadata.value = false
  }
}

const selectMetadata = (metadata) => {
  selectedMetadata.value = metadata
}

// 问答设置编辑对话框相关状态
const qaSettingsDialogVisible = ref(false)
const currentEditingMetadata = ref(null)
const qaSettingsForm = ref({
  is_enabled_for_qa: true,
  qa_description: '',
  business_context: ''
})

const editMetadataSettings = async (metadata) => {
  currentEditingMetadata.value = metadata
  qaSettingsForm.value = {
    is_enabled_for_qa: metadata.qa_settings?.is_enabled_for_qa ?? true,
    qa_description: metadata.qa_settings?.qa_description || '',
    business_context: metadata.qa_settings?.business_context || ''
  }
  qaSettingsDialogVisible.value = true
}

const saveQASettings = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/table-metadata/${currentEditingMetadata.value.id}/qa-settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(qaSettingsForm.value)
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('问答设置更新成功')
      qaSettingsDialogVisible.value = false
      await refreshTableMetadata()
    } else {
      ElMessage.error(result.message || '更新问答设置失败')
    }
  } catch (error) {
    console.error('更新问答设置失败:', error)
    ElMessage.error('更新问答设置失败')
  }
}

const cancelQASettings = () => {
  qaSettingsDialogVisible.value = false
  currentEditingMetadata.value = null
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const loadTableSchema = async () => {
  if (!selectedTable.value) return
  
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-query/table-schema`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        table_name: selectedTable.value
      })
    })
    
    const result = await response.json()
    if (result.success) {
      tableSchema.value = result.data.schema
      updateQuerySuggestions()
    }
  } catch (error) {
    ElMessage.error('获取表结构失败')
  }
}

const updateQuerySuggestions = () => {
  if (activeDataSource.value === 'excel' && excelData.value) {
    querySuggestions.value = [
      '显示前10行数据',
      '统计各列的基本信息',
      '查找缺失值',
      '计算数值列的平均值',
      '按某列分组统计'
    ]
  } else if (activeDataSource.value === 'database' && selectedTable.value) {
    querySuggestions.value = [
      '查询表中所有数据',
      '统计记录总数',
      '查询最近的记录',
      '按某字段分组统计',
      '查找重复记录'
    ]
  } else {
    querySuggestions.value = []
  }
}

// 表元数据编辑相关方法
const loadCurrentTableMetadata = async () => {
  if (!selectedTable.value || !selectedConfig.value?.id) {
    currentTableMetadata.value = null
    return
  }
  
  loadingMetadata.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/table-metadata/by-table`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        database_config_id: selectedConfig.value.id,
        table_name: selectedTable.value
      })
    })
    
    const result = await response.json()
    if (result.success && result.data) {
      currentTableMetadata.value = {
        id: result.data.id,
        table_name: result.data.table_name,
        columns: result.data.columns,
        row_count: result.data.row_count,
        last_synced_at: result.data.last_synced_at,
        is_enabled_for_qa: result.data.qa_settings?.is_enabled_for_qa ?? true,
        qa_description: result.data.qa_settings?.qa_description || '',
        business_context: result.data.qa_settings?.business_context || ''
      }
    } else {
      currentTableMetadata.value = null
    }
  } catch (error) {
    console.error('加载表元数据失败:', error)
    currentTableMetadata.value = null
  } finally {
    loadingMetadata.value = false
  }
}

// 切换表元数据配置区域的展开/收起状态
const toggleMetadataConfig = () => {
  metadataConfigExpanded.value = !metadataConfigExpanded.value
  if (metadataConfigExpanded.value && selectedTable.value) {
    loadCurrentTableMetadata()
  }
}

const saveTableMetadata = async () => {
  if (!currentTableMetadata.value?.id) {
    ElMessage.error('没有可保存的表元数据')
    return
  }
  
  savingMetadata.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/table-metadata/${currentTableMetadata.value.id}/qa-settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        is_enabled_for_qa: currentTableMetadata.value.is_enabled_for_qa,
        qa_description: currentTableMetadata.value.qa_description,
        business_context: currentTableMetadata.value.business_context
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('表元数据配置保存成功')
      // 保存成功后自动收起配置区域
      metadataConfigExpanded.value = false
    } else {
      ElMessage.error(result.message || '保存表元数据配置失败')
    }
  } catch (error) {
    console.error('保存表元数据配置失败:', error)
    ElMessage.error('保存表元数据配置失败')
  } finally {
    savingMetadata.value = false
  }
}



const collectCurrentTableMetadata = async () => {
  if (!selectedTable.value || !selectedConfig.value?.id) {
    ElMessage.error('请先选择数据表')
    return
  }
  
  collectingMetadata.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/table-metadata/collect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        database_config_id: selectedConfig.value.id,
        table_names: [selectedTable.value]
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('表元数据收集成功')
      await loadCurrentTableMetadata()
    } else {
      ElMessage.error(result.message || '收集表元数据失败')
    }
  } catch (error) {
    console.error('收集表元数据失败:', error)
    ElMessage.error('收集表元数据失败')
  } finally {
    collectingMetadata.value = false
  }
}

const applyQuerySuggestion = (suggestion: string) => {
  queryText.value = suggestion
}

const executeQuery = async () => {
  if (!canExecuteQuery.value) return
  
  queryLoading.value = true
  workflowSteps.value = []
  
  try {
    await executeSmartQuery()
  } catch (error) {
    console.error('查询执行失败:', error)
    ElMessage.error('查询执行失败')
  } finally {
    queryLoading.value = false
  }
}



// 新的智能工作流查询
const executeSmartQuery = async () => {
  const requestBody = {
    query: queryText.value,
    conversation_id: currentConversationId.value,
    is_new_conversation: !currentConversationId.value
  }
  
  // 如果是数据库查询，添加database_config_id参数
  if (activeDataSource.value === 'database' && selectedConfig.value) {
    requestBody.database_config_id = selectedConfig.value.id
  }
  
  // 添加用户消息到聊天历史
  addChatMessage('user', queryText.value)
  
  // 添加一个初始的机器人消息用于显示工作流进度
  const botMessageIndex = chatMessages.value.length
  addChatMessage('assistant', '正在处理您的查询...', {
    type: 'smart_query_processing'
  })
  
  // 设置工作流步骤为展开状态（执行过程中显示）
  if (chatMessages.value[botMessageIndex]) {
    chatMessages.value[botMessageIndex].workflowCollapsed = false
  }
  
  try {
    // 根据数据源类型选择不同的接口
    let apiEndpoint
    if (activeDataSource.value === 'excel') {
      apiEndpoint = `${import.meta.env.VITE_API_BASE_URL}/smart-query/execute-excel-query`
    } else if (activeDataSource.value === 'database') {
      apiEndpoint = `${import.meta.env.VITE_API_BASE_URL}/smart-query/execute-db-query`
    } else {
      throw new Error('未知的数据源类型')
    }
    
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(requestBody)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留不完整的行
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.type === 'workflow_step') {
              // 更新工作流步骤
              const existingStepIndex = workflowSteps.value.findIndex(
                step => step.step === data.step
              )
              
              if (existingStepIndex >= 0) {
                workflowSteps.value[existingStepIndex] = data
              } else {
                workflowSteps.value.push(data)
              }
              
              // 实时更新机器人消息中的工作流步骤
              if (chatMessages.value[botMessageIndex]) {
                chatMessages.value[botMessageIndex].workflowSteps = [...workflowSteps.value]
              }
            } else if (data.type === 'final_result') {
              // 处理最终结果
              if (data.success) {
                queryResult.value = data.data
                if (data.conversation_id) {
                  currentConversationId.value = data.conversation_id
                }
                
                // 更新机器人消息的内容为最终结果
                if (chatMessages.value[botMessageIndex]) {
                  // 格式化显示内容：先显示数据，再显示摘要
                  let formattedContent = ''
                  
                  // 处理数据结果
                  if (data.data?.result_type === 'table_data') {
                    // 处理表格数据
                    chatMessages.value[botMessageIndex].resultType = 'table_data'
                    chatMessages.value[botMessageIndex].tableData = {
                      columns: data.data.columns,
                      data: data.data.data,
                      total: data.data.total
                    }
                    
                    // 设置显示内容
                    let formattedContent = ''
                    if (data.data.summary) {
                      formattedContent += `## 分析摘要\n\n${data.data.summary}\n\n`
                    }
                    formattedContent += '查询结果已在上方表格中展示。'
                    
                    chatMessages.value[botMessageIndex].content = formattedContent
                  } else if (['text', 'scalar', 'other'].includes(data.data?.result_type)) {
                    // 处理其他类型数据，按引用数据样式展示
                    chatMessages.value[botMessageIndex].resultType = data.data.result_type
                    chatMessages.value[botMessageIndex].referenceData = {
                      type: data.data.result_type,
                      data: data.data.data,
                      summary: data.data.summary
                    }
                    
                    // 设置显示内容
                    let formattedContent = ''
                    if (data.data.summary) {
                      formattedContent += `## 分析摘要\n\n${data.data.summary}\n\n`
                    }
                    formattedContent += '查询结果已在上方引用区域中展示。'
                    
                    chatMessages.value[botMessageIndex].content = formattedContent
                  }
                  
                  // 添加摘要信息
                  if (data.data?.summary) {
                    formattedContent += '## 分析摘要\n\n' + data.data.summary
                  }
                  
                  chatMessages.value[botMessageIndex].content = formattedContent || '查询完成'
                  chatMessages.value[botMessageIndex].metadata = {
                    type: 'smart_query_result',
                    data: data.data,
                    workflow_steps: workflowSteps.value
                  }
                  // 执行完成后自动收起工作流步骤
                  chatMessages.value[botMessageIndex].workflowCollapsed = true
                }
                
                ElMessage.success('智能查询执行成功')
              } else {
                throw new Error(data.message || '查询失败')
              }
            }
          } catch (parseError) {
            console.warn('解析SSE数据失败:', parseError)
          }
        }
      }
    }
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败: ' + error.message)
    
    // 更新机器人消息为错误信息
    if (chatMessages.value[botMessageIndex]) {
      chatMessages.value[botMessageIndex].content = '抱歉，查询过程中出现错误：' + error.message
      chatMessages.value[botMessageIndex].workflowSteps = [...workflowSteps.value]
      // 查询失败时也要收起工作流步骤
      chatMessages.value[botMessageIndex].workflowCollapsed = true
    }
  }
}

// 原有的数据库查询逻辑
const executeDatabaseQuery = async () => {
  const requestBody = {
    query: queryText.value,
    page: currentPage.value,
    page_size: pageSize.value,
    table_name: selectedTable.value
  }
  
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-query/execute-db-query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    },
    body: JSON.stringify(requestBody)
  })
  
  const result = await response.json()
  if (result.success) {
    queryResult.value = result.data
    ElMessage.success('数据库查询执行成功')
  } else {
    ElMessage.error(result.message || '数据库查询执行失败')
  }
}

const clearQuery = () => {
  queryText.value = ''
  queryResult.value = null
}

const clearAll = () => {
  queryText.value = ''
  queryResult.value = null
  excelData.value = null
  excelFileList.value = []
  dbConnected.value = false
  selectedTable.value = ''
  tableSchema.value = null
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  executeQuery()
}

const exportCurrentResult = () => {
  if (!queryResult.value) return
  
  // 导出CSV格式
  const csvContent = [queryResult.value.columns.join(',')]
    .concat(queryResult.value.data.map(row => 
      queryResult.value.columns.map(col => row[col]).join(',')
    ))
    .join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `query_result_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

const getResultTypeLabel = (type: string) => {
  const labels = {
    'text': '文本结果',
    'scalar': '标量结果', 
    'other': '其他结果'
  }
  return labels[type] || '查询结果'
}

const exportResults = () => {
  ElMessage.info('批量导出功能开发中')
}

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  
  // 如果展开数据预览区域，同时折叠导航栏
  if (isCollapsed.value && parentToggleSidebar) {
    parentToggleSidebar()
  }
  
  ElMessage.success(isCollapsed.value ? '已展开数据预览区域' : '已恢复默认布局')
}
const toggleChatCollapse = () => {
  console.log('toggleChatCollapse 被调用，当前状态:', isChatCollapsed.value)
  
  isChatCollapsed.value = !isChatCollapsed.value
  
  console.log('新状态:', isChatCollapsed.value)
  
  // 如果展开聊天面板，同时折叠导航栏
  if (isChatCollapsed.value && parentToggleSidebar) {
    try {
      parentToggleSidebar()
    } catch (error) {
      console.warn('调用 parentToggleSidebar 失败:', error)
    }
  }
  
  // 强制触发DOM更新
  nextTick(() => {
    console.log('DOM更新完成，当前状态:', isChatCollapsed.value)
  })
  
  ElMessage.success(isChatCollapsed.value ? '已展开智能查询区域' : '已恢复默认布局')
}
const visualizeResult = () => {
  ElMessage.info('数据可视化功能开发中')
}

// 聊天消息处理
const addChatMessage = (role: string, content: string, metadata?: any) => {
  // 确保chatMessages是数组类型
  if (!Array.isArray(chatMessages.value)) {
    console.warn('chatMessages.value is not an array, resetting to empty array')
    chatMessages.value = []
  }
  
  const message = {
    id: Date.now(),
    type: role === 'user' ? 'user' : 'assistant',
    content,
    metadata,
    timestamp: new Date().toISOString(),
    workflowSteps: role === 'assistant' ? [...workflowSteps.value] : undefined,
    workflowCollapsed: true // 默认折叠工作流步骤
  }
  chatMessages.value.push(message)
  
  // 清空当前工作流步骤（为下次查询准备）
  if (role === 'assistant') {
    workflowSteps.value = []
  }
}

// 切换工作流折叠状态
const toggleWorkflowCollapse = (messageIndex: number) => {
  if (chatMessages.value[messageIndex]) {
    chatMessages.value[messageIndex].workflowCollapsed = !chatMessages.value[messageIndex].workflowCollapsed
  }
}

// 获取工作流状态类型
const getWorkflowStatusType = (steps: any[]) => {
  if (!steps || steps.length === 0) return 'info'
  
  const hasRunning = steps.some(step => step.status === 'running')
  const hasFailed = steps.some(step => step.status === 'failed')
  const allCompleted = steps.every(step => step.status === 'completed')
  
  if (hasRunning) return 'warning'
  if (hasFailed) return 'danger'
  if (allCompleted) return 'success'
  return 'info'
}

// 获取工作流状态文本
const getWorkflowStatusText = (steps: any[]) => {
  if (!steps || steps.length === 0) return '无步骤'
  
  const hasRunning = steps.some(step => step.status === 'running')
  const hasFailed = steps.some(step => step.status === 'failed')
  const allCompleted = steps.every(step => step.status === 'completed')
  const completedCount = steps.filter(step => step.status === 'completed').length
  
  if (hasRunning) return '执行中'
  if (hasFailed) return '执行失败'
  if (allCompleted) return '执行完成'
  return `${completedCount}/${steps.length} 完成`
}

// 清除聊天历史
const clearChatHistory = () => {
  chatMessages.value = []
  currentConversationId.value = null
  workflowSteps.value = []
  ElMessage.success('聊天历史已清除')
}

// 获取文件状态
const getFilesStatus = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-chat/files/status`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    const result = await response.json()
    if (result.success) {
      return result.data
    }
  } catch (error) {
    console.error('获取文件状态失败:', error)
  }
  return null
}

// 重置对话上下文
const resetConversationContext = async () => {
  if (!currentConversationId.value) {
    clearChatHistory()
    return
  }
  
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/smart-chat/conversation/${currentConversationId.value}/reset`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })
    
    const result = await response.json()
    if (result.success) {
      clearChatHistory()
      ElMessage.success('对话上下文已重置')
    } else {
      ElMessage.error(result.message || '重置失败')
    }
  } catch (error) {
    console.error('重置对话上下文失败:', error)
    ElMessage.error('重置对话上下文失败')
  }
}

// 获取工作流步骤标题
const getStepTitle = (step: string) => {
  const stepTitles = {
    'file_loading': '📁 加载文件列表',
    'file_selection': '🎯 智能文件选择',
    'data_loading': '📊 加载数据表',
    'code_execution': '⚡ 执行代码分析',
    'result_processing': '📋 处理分析结果'
  }
  return stepTitles[step] || step
}

const formatSummary = (summary: string) => {
  if (!summary) return ''
  return summary.replace(/\n/g, '<br>')
}

// 监听数据库类型变化，自动加载对应配置
watch(() => dbConfig.value.type, async (newType) => {
  await loadConfigByType(newType)
})

onMounted(async () => {
  updateQuerySuggestions()
  loadFileList()
  // 加载保存的数据库配置
  await loadSavedConfigs()
  
  // 初始化时自动加载默认类型（PostgreSQL）的配置
  if (dbConfig.value.type === 'postgresql') {
    await loadConfigByType('postgresql')
  }
  
  // 初始化表元数据列表
  await refreshTableMetadata()
})
</script>

<style scoped>
.smart-query {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0f172a;
}

.query-header {
  padding: 16px 24px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-header h2 {
  margin: 0;
  color: #e4e7ed;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.query-content {
  flex: 1;
  display: flex;
  gap: 0;
  padding: 0;
  overflow: hidden;
  height: calc(100vh - 80px);
}

/* 左侧数据源面板 */
.data-source-panel {
  width: 320px;
  background: #1e293b;
  border-right: 1px solid #334155;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
}

/* 折叠模式下的左侧面板 */
.query-content:has(.chat-panel-compact) .data-source-panel {
  width: 240px;
}

/* 中间数据预览面板 */
.data-preview-panel {
  flex: 1;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-right: 1px solid #334155;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* 右侧聊天面板 */
.chat-panel {
  width: 450px;
  background: #1e293b;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
}

/* 折叠模式下的右侧面板（数据预览展开时） */
.chat-panel-compact {
  width: 400px !important;
}

/* 展开模式下的右侧面板（智能查询展开时） */
.chat-panel-expanded {
  width: 60% !important;
  transition: width 0.3s ease;
}

/* 折叠模式下的左侧面板（数据预览展开时） */
.query-content:has(.chat-panel-compact) .data-source-panel {
  width: 240px;
}

/* 展开模式下缩小其他面板（智能查询展开时） */
.query-content:has(.chat-panel-expanded) .data-source-panel {
  width: 200px !important;
  transition: width 0.3s ease;
}

.query-content:has(.chat-panel-expanded) .data-preview-panel {
  width: 40% !important;
  transition: width 0.3s ease;
}

/* 表格滚动条样式优化 - 强制覆盖所有可能的选择器 */
/* 专门针对表格预览区域的横向滚动条样式 */
:deep(.preview-table .el-table) {
  overflow-x: auto !important;
  width: 100% !important;
}

:deep(.preview-table .el-table::-webkit-scrollbar) {
  height: 16px !important;
  width: 16px !important;
}

:deep(.preview-table .el-table::-webkit-scrollbar-track) {
  background: #1e293b !important;
  border-radius: 8px !important;
  border: 1px solid #334155 !important;
}

:deep(.preview-table .el-table::-webkit-scrollbar-thumb) {
  background: #ff0000 !important;
  border-radius: 8px !important;
  border: 2px solid #ffffff !important;
  box-shadow: 0 2px 8px rgba(255, 0, 0, 0.6) !important;
}

:deep(.preview-table .el-table::-webkit-scrollbar-thumb:hover) {
      background: #1a3b7e !important;
      border-color: #ffffff !important;
      box-shadow: 0 4px 12px rgba(26, 59, 126, 0.8) !important;
    }
    
    :deep(.preview-table .el-scrollbar:hover .el-scrollbar__thumb) {
      background-color: #1a3b7e !important;
    }
    
    :deep(.preview-table .el-scrollbar__thumb:hover) {
      background-color: #1a3b7e !important;
    }

:deep(.preview-table .el-table::-webkit-scrollbar-corner) {
  background: #1e293b !important;
}

/* 确保表头和表体同步滚动 */
:deep(.preview-table .el-table .el-table__header-wrapper),
:deep(.preview-table .el-table .el-table__body-wrapper) {
  overflow-x: hidden !important;
}



.panel-header {
  padding: 16px;
  border-bottom: 1px solid #334155;
  font-weight: 600;
  color: #e2e8f0;
  background: rgba(30, 41, 59, 0.5);
}

.panel-header h3 {
  margin: 0;
  color: #e4e7ed;
  font-size: 16px;
}

.source-tabs {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  color: #e4e7ed;
}

.excel-panel,
.database-panel {
  height: 100%;
}

.upload-section {
  margin-bottom: 20px;
}

.file-list {
  margin-top: 16px;
}

.file-list h4 {
  margin: 0 0 16px 0;
  color: #e4e7ed;
  font-size: 14px;
}

.empty-list {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.loading-list {
  padding: 20px;
  text-align: center;
}

.loading-text {
  margin-top: 12px;
  color: #909399;
  font-size: 12px;
}

.files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #334155;
  border: 1px solid #475569;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.file-item:hover {
  background: #475569;
  border-color: #409eff;
}

.file-item.active {
  background: #1e3a8a;
  border-color: #409eff;
  color: #409eff;
}

.file-icon {
  margin-right: 8px;
  color: #909399;
}

.file-info {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #e4e7ed;
  margin-bottom: 2px;
  font-size: 13px;
  max-width: 180px;
  word-break: break-all;
  white-space: normal;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.file-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-size {
  color: #94a3b8;
}

.file-time {
  color: #64748b;
}

.file-status {
  margin-top: 4px;
}

.file-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.file-item:not(:hover) .file-actions {
  opacity: 0.6;
}

.file-item:hover .file-actions {
  opacity: 1;
}

.connection-section {
  margin-bottom: 20px;
}

.connection-section h4 {
  margin: 0 0 16px 0;
  color: #e4e7ed;
  font-size: 14px;
}

.table-list-section {
  margin-top: 20px;
}

.table-list-section h4 {
  margin: 0 0 16px 0;
  color: #e4e7ed;
  font-size: 14px;
}

.tables {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.table-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #334155;
  border: 1px solid #475569;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.table-item:hover {
  background: #475569;
  border-color: #409eff;
}

.table-item.active {
  background: #1e3a8a;
  border-color: #409eff;
  color: #409eff;
}

.table-icon {
  margin-right: 8px;
  color: #909399;
}

.table-info {
  flex: 1;
}

.table-name {
  font-weight: 500;
  color: #e4e7ed;
  margin-bottom: 2px;
}

.table-meta {
  font-size: 12px;
  color: #909399;
}

/* 数据预览面板样式 */
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #475569;
  background: linear-gradient(90deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.preview-header h3 {
  margin: 0;
  color: #e4e7ed;
  font-size: 16px;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  color: #e4e7ed;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 8px;
  margin: 8px;
  max-height: calc(100vh - 200px);
}

.empty-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
}

.loading-preview {
  padding: 20px;
}

.loading-text {
  text-align: center;
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.preview-data {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.preview-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #334155 0%, #475569 100%);
  border-radius: 12px;
  border: 1px solid rgba(100, 116, 139, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  min-height: 60px;
}

.data-source-info {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  max-width: 60%;
}

.data-stats {
  display: flex;
  gap: 8px;
}

.preview-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(30, 41, 59, 0.4);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(71, 85, 105, 0.5);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  min-height: 420px;
}

.preview-pagination {
  margin-top: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%);
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

/* 聊天面板样式 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #334155;
  background: rgba(30, 41, 59, 0.5);
}

.chat-header h3 {
  margin: 0;
  color: #e4e7ed;
  font-size: 16px;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-chat {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
}

.message-item {
  display: flex;
  gap: 8px;
  max-width: 100%;
}

.message-item.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-item.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.message-content {
  background: #334155;
  border: 1px solid #475569;
  border-radius: 8px;
  padding: 12px;
  color: #e2e8f0;
  line-height: 1.5;
}

.message-item.user .message-content {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.message-text {
  margin-bottom: 4px;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.chat-input {
  padding: 16px;
  border-top: 1px solid #334155;
  background: rgba(30, 41, 59, 0.7);
}

.query-suggestions {
  margin-bottom: 12px;
}

.suggestions-title {
  color: #e4e7ed;
  font-size: 14px;
  margin-bottom: 8px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.suggestion-tag:hover {
  background: #409eff;
  color: white;
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.query-textarea {
  margin-bottom: 8px;
}

.input-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* Element Plus 组件深色主题覆盖 */
:deep(.el-tabs__header) {
  background: #334155;
  margin: 0;
}

:deep(.el-tabs__nav-wrap::after) {
  background: #475569;
}

:deep(.el-tabs__item) {
  color: #c0c4cc;
  border-bottom: 2px solid transparent;
}

:deep(.el-tabs__item.is-active) {
  color: #409eff;
  border-bottom-color: #409eff;
}

:deep(.el-tabs__item:hover) {
  color: #409eff;
}

:deep(.el-form-item__label) {
  color: #606266;
}

:deep(.el-input__wrapper) {
  background: #334155;
  border: 1px solid #475569;
  box-shadow: none;
}

:deep(.el-input__wrapper:hover) {
  border-color: #409eff;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

:deep(.el-input__inner) {
  color: #e4e7ed;
  background: transparent;
}

:deep(.el-input__inner::placeholder) {
  color: #909399;
}

:deep(.el-select .el-input__wrapper) {
  background: #334155;
}

:deep(.el-button) {
  border-color: #475569;
  background: #334155;
  color: #e2e8f0;
}

:deep(.el-button:hover) {
  border-color: #409eff;
  background: #409eff;
  color: white;
}

:deep(.el-button--primary) {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

:deep(.el-button--primary:hover) {
  background: #66b1ff;
  border-color: #66b1ff;
}

:deep(.el-table) {
  background: rgba(30, 41, 59, 0.6);
  color: #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(71, 85, 105, 0.3);
  font-size: 12px;
}

:deep(.el-table th.el-table__cell) {
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  color: #f1f5f9;
  border-bottom: 1px solid rgba(100, 116, 139, 0.4);
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  font-size: 12px;
  padding: 8px 6px;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
  background: rgba(30, 41, 59, 0.3);
  font-size: 12px;
  padding: 6px 8px;
}

:deep(.el-table tr:hover > td) {
  background: rgba(51, 65, 85, 0.6);
  transition: background-color 0.2s ease;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(15, 23, 42, 0.4);
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover td) {
  background: rgba(51, 65, 85, 0.6);
}

:deep(.el-pagination) {
  color: #f1f5f9;
  font-weight: 500;
}

:deep(.el-pagination .el-pagination__total) {
  color: #f1f5f9;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.8) 0%, rgba(29, 78, 216, 0.6) 100%);
  padding: 4px 10px;
  border-radius: 16px;
  border: 1px solid rgba(59, 130, 246, 0.5);
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.2);
  font-size: 12px;
}

:deep(.el-pagination .el-pager li) {
  background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%);
  color: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.8);
  border-radius: 6px;
  margin: 0 2px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  font-weight: 500;
  min-width: 28px;
  height: 28px;
  font-size: 12px;
}

:deep(.el-pagination .el-pager li:hover) {
  color: #ffffff;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
  border-color: #3b82f6;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: 1px solid #d97706;
  box-shadow: 0 3px 8px rgba(217, 119, 6, 0.4), 0 0 0 2px rgba(245, 158, 11, 0.2);
  transform: scale(1.05);
  font-weight: 600;
}

:deep(.el-pagination button) {
  background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%);
  color: #ffffff;
  border: 1px solid rgba(148, 163, 184, 0.8);
  border-radius: 6px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  font-weight: 500;
  min-width: 28px;
  height: 28px;
  font-size: 12px;
}

:deep(.el-pagination button:hover) {
  color: #ffffff;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
  border-color: #3b82f6;
}

:deep(.el-pagination button:disabled) {
  background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
  color: #6b7280;
  border-color: rgba(75, 85, 99, 0.4);
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-pagination button:disabled:hover) {
  background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
  color: #6b7280;
  transform: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-textarea__inner) {
  background: #334155;
  border: 1px solid #475569;
  color: #e2e8f0;
}

:deep(.el-textarea__inner:hover) {
  border-color: #409eff;
}

:deep(.el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  background: #334155;
  border: 2px dashed #64748b;
  color: #e2e8f0;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

:deep(.el-upload__text) {
  color: #c0c4cc;
}

:deep(.el-upload__tip) {
  color: #909399;
}

:deep(.el-empty__description) {
  color: #909399;
}

:deep(.el-tag) {
  background: #334155;
  border-color: #475569;
  color: #e2e8f0;
  font-size: 12px;
  max-width: 200px;
  word-break: break-all;
  white-space: normal;
  line-height: 1.4;
  padding: 6px 8px;
}

:deep(.el-tag--primary) {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

:deep(.el-tag--success) {
  background: #67c23a;
  border-color: #67c23a;
  color: white;
}

:deep(.el-skeleton__item) {
  background: #334155;
}

:deep(.el-avatar) {
  background: #409eff;
  color: white;
}

/* 消息布局样式 */
.message-item {
  margin-bottom: 20px;
  width: 100%;
}

.user-message {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  width: 100%;
}

.bot-message {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  width: 100%;
}

/* 用户消息header右对齐 */
.user-message .message-header {
  justify-content: flex-end;
  width: fit-content;
  margin-left: auto;
}

.user-avatar {
  background: #409eff;
  color: white;
}

.bot-avatar {
  background: #6366f1;
  color: white;
}

.message-sender {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 14px;
}

.message-time {
  color: #94a3b8;
  font-size: 12px;
  margin-left: auto;
}

/* 用户消息时间样式调整 */
.user-message .message-time {
  margin-left: 0;
  margin-right: 8px;
  order: -1;
}

.user-content {
  background: linear-gradient(135deg, #409eff 0%, #3b82f6 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 18px 18px 4px 18px;
  max-width: 85%;
  width: fit-content;
  margin: 0;
}

.bot-content {
  background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
  color: #e2e8f0;
  padding: 12px 16px;
  border-radius: 18px 18px 18px 4px;
  max-width: 85%;
  margin-right: auto;
  overflow-x: auto;
  overflow-y: visible;
  width: fit-content;
  min-width: 60%;
}

.message-text {
  line-height: 1.6;
  word-wrap: break-word;
  min-width: 0;
  white-space: normal;
}

/* Markdown表格样式 */
.table-container {
  overflow-x: auto;
  overflow-y: visible;
  max-width: 100%;
  margin: 12px 0;
}

.table-result {
  margin: 16px 0;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  padding: 16px;
  width: 500px; /* 新增：设置表格容器宽度为500px */
  max-width: 500px; /* 新增：确保最大宽度不超过500px */
}

.table-result h3 {
  margin: 0 0 12px 0;
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 600;
}

.result-table {
  background: transparent;
}

.result-table :deep(.el-table__header) {
  background: rgba(51, 65, 85, 0.8);
}

.result-table :deep(.el-table__header th) {
  background: rgba(51, 65, 85, 0.8);
  color: #e2e8f0;
  border-color: rgba(100, 116, 139, 0.3);
}

.result-table :deep(.el-table__body tr) {
  background: rgba(30, 41, 59, 0.3);
}

.result-table :deep(.el-table__body tr:nth-child(even)) {
  background: rgba(30, 41, 59, 0.5);
}

.result-table :deep(.el-table__body td) {
  color: #cbd5e1;
  border-color: rgba(100, 116, 139, 0.3);
}

.table-info {
  margin-top: 8px;
  color: #94a3b8;
  font-size: 12px;
  text-align: right;
}

/* 引用数据样式 */
.reference-result {
  margin: 16px 0;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  padding: 16px;
  width: 500px;
  max-width: 500px;
  border-left: 4px solid #3b82f6;
}

.reference-result h3 {
  margin: 0 0 12px 0;
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 600;
}

.reference-content {
  background: rgba(15, 23, 42, 0.6);
  border-radius: 6px;
  padding: 12px;
  border: 1px solid rgba(100, 116, 139, 0.3);
}

.reference-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(100, 116, 139, 0.2);
}

.reference-icon {
  color: #3b82f6;
  font-size: 16px;
}

.reference-type {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.reference-data {
  color: #cbd5e1;
  line-height: 1.6;
}

.reference-data pre {
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.reference-text {
  padding: 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  font-family: inherit;
}

/* 工作流步骤面板样式 */
.workflow-steps-panel {
  margin: 12px 0;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 12px;
  border: 1px solid rgba(100, 116, 139, 0.3);
  overflow: hidden;
  max-width: 98%;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid rgba(100, 116, 139, 0.2);
  cursor: pointer;
  transition: background-color 0.2s;
}

.workflow-header:hover {
  background: rgba(30, 41, 59, 0.9);
}

.workflow-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 600;
}

.collapse-icon {
  transition: transform 0.3s;
}

.collapse-icon.collapsed {
  transform: rotate(180deg);
}

.workflow-steps {
  padding: 12px;
}

.workflow-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(100, 116, 139, 0.1);
}

.workflow-step:last-child {
  border-bottom: none;
}

.step-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 2px;
}

.workflow-step.completed .step-icon {
  background: #10b981;
  color: white;
}

.workflow-step.running .step-icon {
  background: #f59e0b;
  color: white;
}

.workflow-step.failed .step-icon {
  background: #ef4444;
  color: white;
}

.workflow-step.pending .step-icon {
  background: #6b7280;
  color: white;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 13px;
  margin-bottom: 4px;
}

.step-message {
  color: #94a3b8;
  font-size: 12px;
  margin-bottom: 4px;
}

.step-details {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.step-details span {
  background: rgba(100, 116, 139, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .data-source-panel {
    width: 280px;
  }
  
  .chat-panel {
    width: 460px;
  }
}

@media (max-width: 768px) {
  .query-content {
    flex-direction: column;
  }
  
  .data-source-panel,
  .data-preview-panel,
  .chat-panel {
    width: 100%;
    height: 300px;
  }
}

/* 按钮组样式 */
.button-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 修复按钮组表单项的左边距 */
:deep(.el-form-item:has(.button-group) .el-form-item__content) {
  margin-left: 0 !important;
}

/* 表列表标题样式 */
.table-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-list-header h4 {
  margin: 0;
  color: #e4e7ed;
  font-size: 14px;
  font-weight: 600;
}

/* 表元数据管理样式 */
.table-metadata-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #334155;
}

.metadata-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.metadata-header h4 {
  margin: 0;
  color: #e4e7ed;
  font-size: 14px;
  font-weight: 600;
}

.metadata-actions {
  display: flex;
  gap: 8px;
}

.metadata-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.metadata-item {
  padding: 12px;
  background: #334155;
  border: 1px solid #475569;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.metadata-item:hover {
  background: #475569;
  border-color: #409eff;
}

.metadata-item.selected {
  background: #1e3a8a;
  border-color: #409eff;
}

/* 问答设置对话框样式 */
:deep(.qa-settings-dialog) {
  .el-dialog {
    background: #1e293b;
    border: 1px solid #334155;
  }
  
  .el-dialog__header {
    background: #334155;
    border-bottom: 1px solid #475569;
    padding: 16px 20px;
  }
  
  .el-dialog__title {
    color: #e4e7ed;
    font-weight: 600;
  }
  
  .el-dialog__body {
    padding: 20px;
    background: #1e293b;
  }
  
  .el-dialog__footer {
    background: #334155;
    border-top: 1px solid #475569;
    padding: 16px 20px;
  }
}

.qa-settings-form {
  .el-form-item__label {
    font-weight: 500;
    margin-bottom: 8px;
  }
  
  .el-form-item {
     color: #e4e7ed !important;
   }
  
  .el-form-item .el-form-item__content {
    color: #e4e7ed !important;
  }
  
  .el-input__wrapper {
    background: #334155 !important;
    border: 1px solid #475569 !important;
    box-shadow: none !important;
  }
  
  .el-input__inner {
    color: #e4e7ed !important;
    background: transparent !important;
  }
  
  .el-input__wrapper:hover {
    border-color: #409eff !important;
  }
  
  .el-input__wrapper.is-focus {
    border-color: #409eff !important;
    box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2) !important;
  }
  
  .el-textarea__inner {
    background: #334155 !important;
    border: 1px solid #475569 !important;
    color: #e4e7ed !important;
    resize: vertical;
  }
  
  .el-textarea__inner:hover {
    border-color: #409eff !important;
  }
  
  .el-textarea__inner:focus {
    border-color: #409eff !important;
    box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2) !important;
  }
  
  .el-input__count {
    color: #94a3b8 !important;
    background: transparent !important;
  }
  
  .el-switch__label {
    color: #e4e7ed !important;
  }
  
  .el-switch__label.is-active {
    color: #13ce66 !important;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  
  .el-button {
    padding: 8px 16px;
  }
  
  .el-button--primary {
    background: #409eff;
    border-color: #409eff;
  }
  
  .el-button--primary:hover {
    background: #66b1ff;
    border-color: #66b1ff;
  }
}

.metadata-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metadata-table-name {
  font-weight: 600;
  color: #e4e7ed;
  font-size: 13px;
}

.metadata-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #10b981;
  color: white;
}

.metadata-info {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metadata-description {
  color: #cbd5e1;
  line-height: 1.4;
}

.metadata-updated {
  color: #64748b;
}

.empty-metadata {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
  font-size: 13px;
}

.loading-metadata {
  text-align: center;
  padding: 20px;
  color: #909399;
}

/* 表元数据编辑界面样式 */
.table-metadata-editor {
  margin-top: 16px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}

.metadata-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.6) 100%);
  border-bottom: 1px solid #475569;
}

.metadata-editor-header h4 {
  margin: 0;
  color: #e4e7ed;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.metadata-editor-actions {
  display: flex;
  gap: 8px;
}

.metadata-editor-content {
  padding: 16px;
}

.metadata-form {
  max-width: 100%;
}

.metadata-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.metadata-form :deep(.el-form-item__label) {
  color: #e4e7ed !important;
  font-weight: 500;
}

.metadata-form :deep(.el-input__wrapper) {
  background: rgba(51, 65, 85, 0.6) !important;
  border: 1px solid #475569 !important;
  box-shadow: none !important;
}

.metadata-form :deep(.el-input__wrapper:hover) {
  border-color: #64748b !important;
}

.metadata-form :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff !important;
}

.metadata-form :deep(.el-input__inner) {
  color: #e4e7ed !important;
  background: transparent !important;
}

.metadata-form :deep(.el-textarea__inner) {
  color: #e4e7ed !important;
  background: rgba(51, 65, 85, 0.6) !important;
  border: 1px solid #475569 !important;
}

.metadata-form :deep(.el-textarea__inner:hover) {
  border-color: #64748b !important;
}

.metadata-form :deep(.el-textarea__inner:focus) {
  border-color: #409eff !important;
}

.metadata-form :deep(.el-switch__core) {
  background: #475569 !important;
  border-color: #475569 !important;
}

.metadata-form :deep(.el-switch.is-checked .el-switch__core) {
  background: #409eff !important;
  border-color: #409eff !important;
}

.metadata-form :deep(.el-switch__label) {
  color: #e4e7ed !important;
}

.metadata-form :deep(.el-switch__label.is-active) {
  color: #409eff !important;
}

.table-info-display {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.table-info-display .el-tag {
  font-size: 12px;
}

.empty-metadata {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-metadata .el-button {
  margin-top: 16px;
}

.loading-metadata {
  padding: 20px;
}

.loading-metadata .loading-text {
  margin-top: 12px;
  color: #94a3b8;
  font-size: 13px;
  text-align: center;
}
</style>