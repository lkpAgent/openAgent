<template>
  <el-dialog
    v-model="visible"
    title="个人信息"
    width="500px"
    :before-close="handleClose"
  >
    <el-tabs v-model="activeTab" class="profile-tabs">
      <!-- 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <el-form
          ref="basicFormRef"
          :model="basicForm"
          :rules="basicRules"
          label-width="80px"
          class="profile-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="basicForm.username"
              placeholder="请输入用户名"
            />
          </el-form-item>
          
          <el-form-item label="姓名" prop="full_name">
            <el-input
              v-model="basicForm.full_name"
              placeholder="请输入姓名"
            />
          </el-form-item>
          
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="basicForm.email"
              placeholder="请输入邮箱"
            />
          </el-form-item>
          
          <el-form-item label="注册时间">
            <el-input
              :value="formatTime(userStore.user?.created_at)"
              readonly
            />
          </el-form-item>
        </el-form>
        
        <div class="form-actions">
          <el-button @click="handleClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleBasicSubmit"
            :loading="basicSubmitting"
          >
            保存
          </el-button>
        </div>
      </el-tab-pane>
      
      <!-- 修改密码 -->
      <el-tab-pane label="修改密码" name="password">
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="80px"
          class="profile-form"
        >
          <el-form-item label="当前密码" prop="currentPassword">
            <el-input
              v-model="passwordForm.currentPassword"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>
        </el-form>
        
        <div class="form-actions">
          <el-button @click="handleClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="handlePasswordSubmit"
            :loading="passwordSubmitting"
          >
            修改密码
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

// Props
interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// Store
const userStore = useUserStore()

// 响应式数据
const visible = ref(false)
const activeTab = ref('basic')
const basicSubmitting = ref(false)
const passwordSubmitting = ref(false)

// 表单引用
const basicFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

// 基本信息表单
const basicForm = reactive({
  username: '',
  full_name: '',
  email: ''
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单验证规则
const basicRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在2-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

const passwordRules: FormRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6-20个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    initForm()
  }
})

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 初始化表单
const initForm = () => {
  if (userStore.user) {
    basicForm.username = userStore.user.username || ''
    basicForm.full_name = userStore.user.full_name || ''
    basicForm.email = userStore.user.email || ''
  }
  
  // 重置密码表单
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  
  // 重置表单验证状态
  basicFormRef.value?.clearValidate()
  passwordFormRef.value?.clearValidate()
}

// 格式化时间
const formatTime = (timeStr?: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 处理基本信息提交
const handleBasicSubmit = async () => {
  if (!basicFormRef.value) return
  
  try {
    await basicFormRef.value.validate()
    basicSubmitting.value = true
    
    await userStore.updateProfile({
      username: basicForm.username,
      full_name: basicForm.full_name,
      email: basicForm.email
    })
    
    ElMessage.success('个人信息更新成功')
    handleClose()
  } catch (error) {
    console.error('更新个人信息失败:', error)
    ElMessage.error('更新个人信息失败')
  } finally {
    basicSubmitting.value = false
  }
}

// 处理密码修改提交
const handlePasswordSubmit = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    passwordSubmitting.value = true
    
    const success = await userStore.changePassword({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    })
    
    if (success) {
      handleClose()
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    // userStore.changePassword 已经处理了错误消息显示，这里不需要重复显示
  } finally {
    passwordSubmitting.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.profile-tabs {
  margin-top: 20px;
}

.profile-form {
  padding: 20px 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

:deep(.el-dialog__body) {
  padding: 10px 20px 20px;
}

:deep(.el-tabs__content) {
  padding: 0;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-input) {
  width: 100%;
}
</style>