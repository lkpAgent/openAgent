<template>
  <div class="creative-studio">
    <div class="studio-header">
      <h2>智能创作</h2>
      <div class="header-actions">
        <el-button @click="showHistory = !showHistory">
          <el-icon><Clock /></el-icon>
          创作历史
        </el-button>
        <el-button type="primary" @click="createNewProject">
          <el-icon><Plus /></el-icon>
          新建创作
        </el-button>
      </div>
    </div>

    <div class="studio-content">
      <!-- 左侧模板选择区域 -->
      <div class="template-panel">
        <div class="panel-header">
          <h3>创作模板</h3>
          <el-input
            v-model="templateSearchQuery"
            placeholder="搜索模板..."
            size="small"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="template-categories">
          <el-tabs v-model="activeTemplateCategory" @tab-change="handleCategoryChange">
            <el-tab-pane label="图片生成" name="image">
              <div class="template-grid">
                <div 
                  v-for="template in imageTemplates" 
                  :key="template.id"
                  :class="['template-card', { active: selectedTemplate?.id === template.id }]"
                  @click="selectTemplate(template)"
                >
                  <div class="template-preview">
                    <div class="preview-placeholder">
                      <el-icon><Picture /></el-icon>
                    </div>
                  </div>
                  <div class="template-info">
                    <h4>{{ template.name }}</h4>
                    <p>{{ template.description }}</p>
                    <div class="template-tags">
                      <el-tag v-for="tag in template.tags" :key="tag" size="small">{{ tag }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="PPT生成" name="ppt">
              <div class="template-grid">
                <div 
                  v-for="template in pptTemplates" 
                  :key="template.id"
                  :class="['template-card', { active: selectedTemplate?.id === template.id }]"
                  @click="selectTemplate(template)"
                >
                  <div class="template-preview">
                    <div class="preview-placeholder">
                      <el-icon><Document /></el-icon>
                    </div>
                  </div>
                  <div class="template-info">
                    <h4>{{ template.name }}</h4>
                    <p>{{ template.description }}</p>
                    <div class="template-tags">
                      <el-tag v-for="tag in template.tags" :key="tag" size="small">{{ tag }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="Word文档" name="word">
              <div class="template-grid">
                <div 
                  v-for="template in wordTemplates" 
                  :key="template.id"
                  :class="['template-card', { active: selectedTemplate?.id === template.id }]"
                  @click="selectTemplate(template)"
                >
                  <div class="template-preview">
                    <div class="preview-placeholder">
                      <el-icon><Document /></el-icon>
                    </div>
                  </div>
                  <div class="template-info">
                    <h4>{{ template.name }}</h4>
                    <p>{{ template.description }}</p>
                    <div class="template-tags">
                      <el-tag v-for="tag in template.tags" :key="tag" size="small">{{ tag }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="视频生成" name="video">
              <div class="template-grid">
                <div 
                  v-for="template in videoTemplates" 
                  :key="template.id"
                  :class="['template-card', { active: selectedTemplate?.id === template.id }]"
                  @click="selectTemplate(template)"
                >
                  <div class="template-preview">
                    <div class="preview-placeholder">
                      <el-icon><VideoPlay /></el-icon>
                    </div>
                  </div>
                  <div class="template-info">
                    <h4>{{ template.name }}</h4>
                    <p>{{ template.description }}</p>
                    <div class="template-tags">
                      <el-tag v-for="tag in template.tags" :key="tag" size="small">{{ tag }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <!-- 中间创作配置区域 -->
      <div class="creation-panel">
        <div class="panel-header">
          <h3>创作配置</h3>
          <el-button v-if="selectedTemplate" type="primary" @click="startCreation" :loading="isCreating">
            <el-icon><Magic /></el-icon>
            开始创作
          </el-button>
        </div>

        <div v-if="!selectedTemplate" class="no-template">
          <el-empty description="请先选择一个创作模板" />
        </div>

        <div v-else class="creation-config">
          <!-- 需求描述 -->
          <div class="config-section">
            <h4>创作需求</h4>
            <el-input
              v-model="creationRequirement"
              type="textarea"
              :rows="4"
              placeholder="请详细描述您的创作需求，例如：为新产品制作一张现代简约风格的宣传海报，突出产品的科技感和品质感..."
              maxlength="1000"
              show-word-limit
            />
          </div>

          <!-- 文件上传 -->
          <div class="config-section">
            <h4>素材上传</h4>
            <el-upload
              class="upload-demo"
              drag
              :auto-upload="false"
              :limit="5"
              multiple
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                拖拽文件到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 JPG、PNG、WebP 格式，建议尺寸不小于 800x600
                </div>
              </template>
            </el-upload>
          </div>

          <!-- 高级配置 -->
          <div class="config-section">
            <h4>高级配置</h4>
            <el-collapse v-model="activeAdvancedConfig">
              <el-collapse-item title="样式设置" name="style">
                <div class="style-config">
                  <el-form :model="styleConfig" label-width="100px">
                    <el-form-item label="色彩风格">
                      <el-select v-model="styleConfig.colorScheme" placeholder="选择色彩风格">
                        <el-option label="现代简约" value="modern" />
                        <el-option label="商务专业" value="business" />
                        <el-option label="活力青春" value="vibrant" />
                        <el-option label="温馨自然" value="natural" />
                        <el-option label="科技未来" value="tech" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="尺寸规格">
                      <el-select v-model="styleConfig.dimensions" placeholder="选择尺寸">
                        <el-option label="方形 (1:1)" value="1080x1080" />
                        <el-option label="横版 (16:9)" value="1920x1080" />
                        <el-option label="竖版 (9:16)" value="1080x1920" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="质量等级">
                      <el-radio-group v-model="styleConfig.quality">
                        <el-radio label="standard">标准</el-radio>
                        <el-radio label="high">高清</el-radio>
                        <el-radio label="ultra">超高清</el-radio>
                      </el-radio-group>
                    </el-form-item>
                  </el-form>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>

      <!-- 右侧结果展示区域 -->
      <div class="result-panel">
        <div class="panel-header">
          <h3>创作结果</h3>
          <div class="result-actions" v-if="creationResults.length > 0">
            <el-button size="small" @click="downloadAll">
              <el-icon><Download /></el-icon>
              下载全部
            </el-button>
          </div>
        </div>

        <div v-if="isCreating" class="creation-progress">
          <div class="progress-info">
            <h4>正在创作中...</h4>
            <p>{{ currentStep }}</p>
          </div>
          <el-progress :percentage="creationProgress" />
        </div>

        <div v-else-if="creationResults.length === 0" class="no-results">
          <el-empty description="暂无创作结果" />
        </div>

        <div v-else class="results-grid">
          <div 
            v-for="result in creationResults" 
            :key="result.id"
            class="result-item"
          >
            <div class="result-preview">
              <div class="preview-placeholder">
                <el-icon><Picture /></el-icon>
              </div>
            </div>
            <div class="result-info">
              <h5>{{ result.name }}</h5>
              <p>{{ result.description }}</p>
              <div class="result-actions">
                <el-button size="small" @click="downloadResult(result)">
                  <el-icon><Download /></el-icon>
                </el-button>
                <el-button size="small" type="danger" @click="deleteResult(result)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录侧边栏 -->
    <el-drawer v-model="showHistory" title="创作历史" direction="rtl" size="400px">
      <div class="history-content">
        <div class="history-search">
          <el-input
            v-model="historySearchQuery"
            placeholder="搜索历史记录..."
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div class="history-list">
          <div 
            v-for="history in creationHistory" 
            :key="history.id"
            class="history-item"
            @click="loadHistoryProject(history)"
          >
            <div class="history-preview">
              <div class="preview-placeholder">
                <el-icon><Document /></el-icon>
              </div>
            </div>
            <div class="history-info">
              <h5>{{ history.name }}</h5>
              <p>{{ history.template }}</p>
              <span class="history-time">{{ formatTime(history.createdAt) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Clock,
  Document,
  VideoPlay,
  UploadFilled,
  Download,
  Delete,
  Picture
} from '@element-plus/icons-vue'

// 响应式数据
const templateSearchQuery = ref('')
const activeTemplateCategory = ref('image')
const selectedTemplate = ref(null)
const creationRequirement = ref('')
const activeAdvancedConfig = ref(['style'])
const styleConfig = ref({
  colorScheme: 'modern',
  dimensions: '1920x1080',
  quality: 'high'
})
const isCreating = ref(false)
const creationProgress = ref(0)
const currentStep = ref('')
const creationResults = ref([])
const showHistory = ref(false)
const historySearchQuery = ref('')

// 模板数据
const imageTemplates = ref([
  {
    id: 'img-ad-1',
    name: '商品广告海报',
    description: '适用于电商产品宣传，支持多种商品类型',
    tags: ['电商', '广告', '海报']
  },
  {
    id: 'img-social-1',
    name: '社交媒体配图',
    description: '为社交平台定制的图片模板',
    tags: ['社交', '配图', '营销']
  },
  {
    id: 'img-brand-1',
    name: '品牌视觉设计',
    description: '企业品牌形象设计模板',
    tags: ['品牌', '设计', '企业']
  }
])

const pptTemplates = ref([
  {
    id: 'ppt-business-1',
    name: '商务汇报PPT',
    description: '适用于商务汇报、项目展示',
    tags: ['商务', '汇报', '专业']
  },
  {
    id: 'ppt-education-1',
    name: '教育培训PPT',
    description: '教学课件、培训材料制作',
    tags: ['教育', '培训', '课件']
  }
])

const wordTemplates = ref([
  {
    id: 'word-report-1',
    name: '工作报告',
    description: '标准化工作报告模板',
    tags: ['报告', '工作', '文档']
  },
  {
    id: 'word-proposal-1',
    name: '项目提案',
    description: '项目提案书模板',
    tags: ['提案', '项目', '商务']
  }
])

const videoTemplates = ref([
  {
    id: 'video-promo-1',
    name: '产品宣传视频',
    description: '产品介绍和宣传视频制作',
    tags: ['宣传', '产品', '营销']
  },
  {
    id: 'video-tutorial-1',
    name: '教程演示视频',
    description: '操作教程和演示视频',
    tags: ['教程', '演示', '教育']
  }
])

// 历史记录数据
const creationHistory = ref([
  {
    id: 'history-1',
    name: '春季新品海报',
    template: '商品广告海报',
    createdAt: new Date(Date.now() - 1000 * 60 * 30)
  },
  {
    id: 'history-2',
    name: '季度总结PPT',
    template: '商务汇报PPT',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2)
  }
])

// 方法
const handleCategoryChange = () => {
  selectedTemplate.value = null
  creationRequirement.value = ''
}

const selectTemplate = (template: any) => {
  selectedTemplate.value = template
  creationRequirement.value = ''
  styleConfig.value = {
    colorScheme: 'modern',
    dimensions: '1920x1080',
    quality: 'high'
  }
}

const createNewProject = () => {
  selectedTemplate.value = null
  creationRequirement.value = ''
  creationResults.value = []
  activeTemplateCategory.value = 'image'
}

const startCreation = async () => {
  if (!selectedTemplate.value) {
    ElMessage.error('请选择创作模板')
    return
  }
  
  if (!creationRequirement.value.trim()) {
    ElMessage.error('请输入创作需求')
    return
  }
  
  isCreating.value = true
  creationProgress.value = 0
  
  try {
    // 模拟创作流程
    await simulateCreationProcess()
    
    // 模拟生成结果
    const mockResults = generateMockResults()
    creationResults.value = mockResults
    
    ElMessage.success('创作完成！')
  } catch (error) {
    ElMessage.error('创作失败，请重试')
    console.error('Creation error:', error)
  } finally {
    isCreating.value = false
  }
}

const simulateCreationProcess = async () => {
  const steps = [
    { progress: 25, message: '正在解析创作需求...' },
    { progress: 50, message: '正在处理上传素材...' },
    { progress: 75, message: '正在执行创作工作流...' },
    { progress: 100, message: '正在生成最终结果...' }
  ]
  
  for (const stepInfo of steps) {
    creationProgress.value = stepInfo.progress
    currentStep.value = stepInfo.message
    await new Promise(resolve => setTimeout(resolve, 1500))
  }
}

const generateMockResults = () => {
  return [
    {
      id: `result-${Date.now()}`,
      name: `${selectedTemplate.value.name}_1`,
      description: `基于您的需求生成的${selectedTemplate.value.name}`,
      type: activeTemplateCategory.value,
      createdAt: new Date()
    }
  ]
}

const downloadResult = (result: any) => {
  ElMessage.success(`正在下载 ${result.name}`)
}

const downloadAll = () => {
  ElMessage.success('正在打包下载所有结果')
}

const deleteResult = (result: any) => {
  ElMessageBox.confirm('确定要删除这个创作结果吗？', '确认删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const index = creationResults.value.findIndex(r => r.id === result.id)
    if (index > -1) {
      creationResults.value.splice(index, 1)
      ElMessage.success('删除成功')
    }
  })
}

const loadHistoryProject = (history: any) => {
  ElMessage.success(`正在加载 ${history.name}`)
  showHistory.value = false
}

const formatTime = (date: Date) => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMins < 60) {
    return `${diffMins}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 生命周期
onMounted(() => {
  // 初始化数据
})
</script>

<style scoped>
.creative-studio {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.studio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.studio-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.studio-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

.template-panel {
  width: 350px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.creation-panel {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.result-panel {
  width: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.template-categories {
  flex: 1;
  overflow: hidden;
}

.template-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.template-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.template-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.template-card.active {
  border-color: #409eff;
  background: #f0f9ff;
}

.template-preview {
  width: 100%;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 12px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-placeholder {
  color: #909399;
  font-size: 32px;
}

.template-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.template-info p {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 12px;
  line-height: 1.4;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.creation-config {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.config-section {
  margin-bottom: 24px;
}

.config-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.no-template {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.creation-progress {
  padding: 20px;
}

.progress-info {
  text-align: center;
  margin-bottom: 20px;
}

.progress-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.progress-info p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.results-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  overflow-y: auto;
}

.result-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.result-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-preview {
  width: 100%;
  height: 150px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-info {
  padding: 12px;
}

.result-info h5 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.result-info p {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 12px;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.history-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-search {
  margin-bottom: 16px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.history-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-preview {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-info h5 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-info p {
  margin: 0 0 4px 0;
  color: #606266;
  font-size: 12px;
}

.history-time {
  color: #909399;
  font-size: 11px;
}

.no-results {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .studio-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .template-panel,
  .result-panel {
    width: 100%;
    height: 300px;
  }
  
  .creation-panel {
    min-height: 400px;
  }
}
</style>