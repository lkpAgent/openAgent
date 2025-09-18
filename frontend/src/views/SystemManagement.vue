<template>
  <div class="system-management">
    <div class="system-header">
      <h1>系统管理</h1>
      <p class="system-description">管理系统用户、部门、角色权限和大模型配置</p>
    </div>
    
    <div class="system-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
// 系统管理主页面，导航功能已移至左侧菜单
</script>

<style scoped>
.system-management {
  padding: 20px 24px;
  width: 100%;
  min-height: calc(100vh - 60px);
  background: transparent;
  box-sizing: border-box;
}

.system-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.system-header h1 {
  margin: 0;
  color: #e2e8f0;
  font-size: 24px;
  font-weight: 600;
}

.system-description {
  color: #94a3b8;
  margin: 8px 0 0 0;
  font-size: 14px;
}

.system-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .system-management {
    padding: 15px;
  }
}
</style>