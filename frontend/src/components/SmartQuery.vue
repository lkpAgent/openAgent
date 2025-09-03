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
      <!-- 左侧数据源选择 -->
      <div class="data-source-panel">
        <div class="panel-header">
          <h3>数据源</h3>
        </div>
        
        <div class="source-tabs">
          <el-tabs v-model="activeDataSource" @tab-change="handleDataSourceChange">
            <el-tab-pane label="Excel分析" name="excel">
              <div class="excel-panel">
                <div class="upload-section">
                  <el-upload
                    ref="excelUpload"
                    class="upload-demo"
                    drag
                    :action="uploadUrl"
                    :headers="uploadHeaders"
                    :on-success="handleExcelUploadSuccess"
                    :on-error="handleUploadError"
                    :before-upload="beforeExcelUpload"
                    accept=".xlsx,.xls,.csv"
                    :limit="1"
                    :file-list="excelFileList"
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

                <div v-if="excelData" class="excel-info">
                  <h4>数据预览</h4>
                  <div class="data-stats">
                    <el-tag>行数: {{ excelData.rows }}</el-tag>
                    <el-tag>列数: {{ excelData.columns }}</el-tag>
                    <el-tag>文件: {{ excelData.filename }}</el-tag>
                  </div>
                  
                  <div class="column-list">
                    <h5>列信息</h5>
                    <div class="columns">
                      <el-tag 
                        v-for="column in excelData.column_names" 
                        :key="column"
                        size="small"
                        class="column-tag"
                      >
                        {{ column }}
                      </el-tag>
                    </div>
                  </div>

                  <div class="data-preview">
                    <h5>数据预览 (前5行)</h5>
                    <el-table 
                      :data="excelData.preview" 
                      size="small" 
                      max-height="200"
                      stripe
                    >
                      <el-table-column 
                        v-for="column in excelData.column_names" 
                        :key="column"
                        :prop="column"
                        :label="column"
                        min-width="100"
                        show-overflow-tooltip
                      />
                    </el-table>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="数据库查询" name="database">
              <div class="database-panel">
                <div class="connection-section">
                  <h4>数据库连接</h4>
                  <el-form :model="dbConfig" label-width="80px" size="small">
                    <el-form-item label="类型">
                      <el-select v-model="dbConfig.type" placeholder="选择数据库类型">
                        <el-option label="MySQL" value="mysql" />
                        <el-option label="PostgreSQL" value="postgresql" />
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
                      <el-button type="primary" @click="testConnection" :loading="testingConnection">
                        测试连接
                      </el-button>
                      <el-button @click="connectDatabase" :disabled="!connectionValid">
                        连接
                      </el-button>
                    </el-form-item>
                  </el-form>
                </div>

                <div v-if="dbConnected" class="database-info">
                  <h4>数据库信息</h4>
                  <div class="db-stats">
                    <el-tag type="success">已连接</el-tag>
                    <el-tag>{{ dbConfig.type }}</el-tag>
                    <el-tag>{{ dbConfig.database }}</el-tag>
                  </div>
                  
                  <div class="table-list">
                    <h5>数据表</h5>
                    <el-select v-model="selectedTable" placeholder="选择数据表" @change="loadTableSchema">
                      <el-option 
                        v-for="table in dbTables" 
                        :key="table"
                        :label="table"
                        :value="table"
                      />
                    </el-select>
                  </div>

                  <div v-if="tableSchema" class="table-schema">
                    <h5>表结构</h5>
                    <el-table :data="tableSchema" size="small" max-height="200">
                      <el-table-column prop="column_name" label="列名" />
                      <el-table-column prop="data_type" label="数据类型" />
                      <el-table-column prop="is_nullable" label="可空" />
                    </el-table>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <!-- 右侧查询和结果区域 -->
      <div class="query-result-panel">
        <div class="query-section">
          <div class="query-input">
            <h3>自然语言查询</h3>
            <el-input
              v-model="queryText"
              type="textarea"
              :rows="3"
              placeholder="请输入您的问题，例如：\n- Excel: '显示销售额最高的前10个产品'\n- 数据库: '查询最近一个月的订单总数和总金额'"
              class="query-textarea"
            />
            <div class="query-actions">
              <el-button 
                type="primary" 
                @click="executeQuery" 
                :loading="queryLoading"
                :disabled="!canExecuteQuery"
              >
                <el-icon><Search /></el-icon>
                执行查询
              </el-button>
              <el-button @click="clearQuery">
                <el-icon><RefreshLeft /></el-icon>
                清空
              </el-button>
            </div>
          </div>

          <!-- 查询建议 -->
          <div v-if="querySuggestions.length > 0" class="query-suggestions">
            <h4>查询建议</h4>
            <div class="suggestions">
              <el-tag 
                v-for="suggestion in querySuggestions" 
                :key="suggestion"
                class="suggestion-tag"
                @click="applyQuerySuggestion(suggestion)"
              >
                {{ suggestion }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 查询结果 -->
        <div class="result-section">
          <div class="result-header">
            <h3>查询结果</h3>
            <div class="result-actions" v-if="queryResult">
              <el-button size="small" @click="exportCurrentResult">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
              <el-button size="small" @click="visualizeResult">
                <el-icon><PieChart /></el-icon>
                可视化
              </el-button>
            </div>
          </div>

          <div v-if="queryLoading" class="loading-state">
            <el-skeleton :rows="5" animated />
            <div class="loading-text">正在分析查询并生成结果...</div>
          </div>

          <div v-else-if="queryResult" class="result-content">
            <!-- 生成的代码 -->
            <div class="generated-code">
              <h4>生成的代码</h4>
              <el-collapse>
                <el-collapse-item title="查看生成的代码" name="code">
                  <pre><code>{{ queryResult.generated_code }}</code></pre>
                </el-collapse-item>
              </el-collapse>
            </div>

            <!-- 数据结果 -->
            <div class="data-result">
              <h4>数据结果</h4>
              <el-table 
                :data="queryResult.data" 
                max-height="400"
                stripe
                border
              >
                <el-table-column 
                  v-for="column in queryResult.columns" 
                  :key="column"
                  :prop="column"
                  :label="column"
                  min-width="120"
                  show-overflow-tooltip
                />
              </el-table>
              <div class="result-pagination">
                <el-pagination
                  v-if="queryResult.total > queryResult.data.length"
                  :current-page="currentPage"
                  :page-size="pageSize"
                  :total="queryResult.total"
                  layout="total, prev, pager, next, jumper"
                  @current-change="handlePageChange"
                />
              </div>
            </div>

            <!-- AI总结 -->
            <div class="ai-summary">
              <h4>AI分析总结</h4>
              <div class="summary-content">
                <el-card>
                  <div v-html="formatSummary(queryResult.summary)"></div>
                </el-card>
              </div>
            </div>
          </div>

          <div v-else class="empty-result">
            <el-empty description="暂无查询结果">
              <template #image>
                <el-icon size="60"><DataAnalysis /></el-icon>
              </template>
            </el-empty>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete,
  Download,
  UploadFilled,
  Search,
  RefreshLeft,
  PieChart,
  DataAnalysis
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

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
const uploadUrl = computed(() => `${import.meta.env.VITE_API_BASE_URL}/api/smart-query/upload-excel`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`
}))

// 数据库相关
const dbConfig = ref({
  type: 'mysql',
  host: 'localhost',
  port: '3306',
  database: '',
  username: '',
  password: ''
})
const testingConnection = ref(false)
const connectionValid = ref(false)
const dbConnected = ref(false)
const dbTables = ref([])
const selectedTable = ref('')
const tableSchema = ref(null)

// 查询结果
const queryResult = ref(null)
const querySuggestions = ref([])

// 计算属性
const canExecuteQuery = computed(() => {
  if (activeDataSource.value === 'excel') {
    return excelData.value && queryText.value.trim()
  } else {
    return dbConnected.value && selectedTable.value && queryText.value.trim()
  }
})

// 方法
const handleDataSourceChange = (tab: string) => {
  activeDataSource.value = tab
  queryText.value = ''
  queryResult.value = null
  updateQuerySuggestions()
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

const handleExcelUploadSuccess = (response: any) => {
  if (response.success) {
    excelData.value = response.data
    ElMessage.success('Excel文件上传成功')
    updateQuerySuggestions()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleUploadError = () => {
  ElMessage.error('文件上传失败')
}

const testConnection = async () => {
  testingConnection.value = true
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/smart-query/test-db-connection`, {
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

const connectDatabase = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/smart-query/connect-database`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(dbConfig.value)
    })
    
    const result = await response.json()
    if (result.success) {
      dbConnected.value = true
      dbTables.value = result.data.tables
      ElMessage.success('数据库连接成功')
      updateQuerySuggestions()
    } else {
      ElMessage.error(result.message || '连接失败')
    }
  } catch (error) {
    ElMessage.error('连接失败')
  }
}

const loadTableSchema = async () => {
  if (!selectedTable.value) return
  
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/smart-query/table-schema`, {
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

const applyQuerySuggestion = (suggestion: string) => {
  queryText.value = suggestion
}

const executeQuery = async () => {
  if (!canExecuteQuery.value) return
  
  queryLoading.value = true
  try {
    const endpoint = activeDataSource.value === 'excel' 
      ? '/api/smart-query/execute-excel-query'
      : '/api/smart-query/execute-db-query'
    
    const requestBody = {
      query: queryText.value,
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (activeDataSource.value === 'database') {
      requestBody.table_name = selectedTable.value
    }
    
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}${endpoint}`, {
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
      ElMessage.success('查询执行成功')
    } else {
      ElMessage.error(result.message || '查询执行失败')
    }
  } catch (error) {
    ElMessage.error('查询执行失败')
  } finally {
    queryLoading.value = false
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

const exportResults = () => {
  ElMessage.info('批量导出功能开发中')
}

const visualizeResult = () => {
  ElMessage.info('数据可视化功能开发中')
}

const formatSummary = (summary: string) => {
  if (!summary) return ''
  return summary.replace(/\n/g, '<br>')
}

onMounted(() => {
  updateQuerySuggestions()
})
</script>

<style scoped>
.smart-query {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.query-header {
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.query-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧数据源面板 */
.data-source-panel {
  width: 400px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafbfc;
}

.panel-header h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.source-tabs {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.excel-panel,
.database-panel {
  height: 100%;
}

.upload-section {
  margin-bottom: 20px;
}

.excel-info,
.database-info {
  margin-top: 20px;
}

.data-stats,
.db-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.column-list,
.table-list {
  margin-bottom: 16px;
}

.column-list h5,
.table-list h5,
.database-info h5 {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
}

.columns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.column-tag {
  cursor: pointer;
}

.data-preview {
  margin-top: 16px;
}

.connection-section {
  margin-bottom: 20px;
}

.connection-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
}

/* 右侧查询结果面板 */
.query-result-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.query-section {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.query-input h3 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
}

.query-textarea {
  margin-bottom: 12px;
}

.query-actions {
  display: flex;
  gap: 12px;
}

.query-suggestions {
  margin-top: 20px;
}

.query-suggestions h4 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
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

.result-section {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-header h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.loading-state {
  text-align: center;
}

.loading-text {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.generated-code h4,
.data-result h4,
.ai-summary h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.generated-code pre {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
}

.result-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.summary-content {
  line-height: 1.6;
}

.empty-result {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .data-source-panel {
    width: 350px;
  }
}

@media (max-width: 768px) {
  .query-content {
    flex-direction: column;
  }
  
  .data-source-panel {
    width: 100%;
    height: 400px;
  }
  
  .query-result-panel {
    height: calc(100vh - 400px);
  }
}
</style>