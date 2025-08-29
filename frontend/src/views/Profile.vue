<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1>个人资料</h1>
      <el-button @click="$router.go(-1)">
        返回
      </el-button>
    </div>
    
    <div class="profile-content">
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        
        <el-form
          ref="profileFormRef"
          :model="profileForm"
          :rules="profileRules"
          label-width="100px"
          class="profile-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="profileForm.username"
              placeholder="请输入用户名"
            />
          </el-form-item>
          
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="profileForm.email"
              placeholder="请输入邮箱"
              disabled
            />
          </el-form-item>
          
          <el-form-item label="注册时间">
            <el-input
              :value="formatTime(userStore.user?.created_at)"
              disabled
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              :loading="updating"
              @click="updateProfile"
            >
              保存修改
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <el-card class="password-card">
        <template #header>
          <div class="card-header">
            <span>修改密码</span>
          </div>
        </template>
        
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
          class="password-form"
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
              placeholder="请确认新密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              :loading="changingPassword"
              @click="changePassword"
            >
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <el-card class="danger-card">
        <template #header>
          <div class="card-header">
            <span>危险操作</span>
          </div>
        </template>
        
        <div class="danger-content">
          <div class="danger-item">
            <div class="danger-info">
              <h4>删除账户</h4>
              <p>删除账户后，所有数据将无法恢复，请谨慎操作。</p>
            </div>
            <el-button
              type="danger"
              :loading="deleting"
              @click="deleteAccount"
            >
              删除账户
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { formatTime } from '@/utils'

const router = useRouter()
const userStore = useUserStore()

const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const updating = ref(false)
const changingPassword = ref(false)
const deleting = ref(false)

const profileForm = reactive({
  username: '',
  email: ''
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const profileRules: FormRules = {
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
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

onMounted(() => {
  if (userStore.user) {
    profileForm.username = userStore.user.username
    profileForm.email = userStore.user.email
  }
})

const updateProfile = async () => {
  if (!profileFormRef.value) return
  
  try {
    await profileFormRef.value.validate()
    updating.value = true
    
    await userStore.updateProfile({
      username: profileForm.username
    })
    
    ElMessage.success('资料更新成功')
  } catch (error) {
    console.error('更新失败:', error)
  } finally {
    updating.value = false
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true
    
    // 这里应该调用修改密码的API
    // await userStore.changePassword({
    //   currentPassword: passwordForm.currentPassword,
    //   newPassword: passwordForm.newPassword
    // })
    
    ElMessage.success('密码修改成功')
    
    // 重置表单
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    passwordFormRef.value.resetFields()
  } catch (error) {
    console.error('修改密码失败:', error)
  } finally {
    changingPassword.value = false
  }
}

const deleteAccount = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除账户吗？此操作不可恢复，所有数据将被永久删除。',
      '确认删除账户',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    // 二次确认
    await ElMessageBox.prompt(
      '请输入您的用户名以确认删除操作',
      '确认删除',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        inputValidator: (value) => {
          if (value !== userStore.user?.username) {
            return '用户名不匹配'
          }
          return true
        }
      }
    )
    
    deleting.value = true
    
    await userStore.deleteAccount()
    ElMessage.success('账户已删除')
    router.push('/login')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除账户失败:', error)
    }
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.profile-header h1 {
  margin: 0;
  color: #333;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-card,
.password-card,
.danger-card {
  width: 100%;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.profile-form,
.password-form {
  max-width: 400px;
}

.danger-content {
  padding: 20px 0;
}

.danger-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border: 1px solid #f56c6c;
  border-radius: 8px;
  background: #fef0f0;
}

.danger-info h4 {
  margin: 0 0 8px 0;
  color: #f56c6c;
  font-size: 16px;
}

.danger-info p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 10px;
  }
  
  .danger-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}
</style>