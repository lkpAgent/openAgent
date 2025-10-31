<template>
  <div class="paste-container">
    <h2>临时粘贴页面</h2>
    <p class="tip">点击下面的框，然后按 Ctrl+V 粘贴简历文本。</p>
    <div id="paste-box" class="paste-box" contenteditable="true" spellcheck="false"></div>
    <div class="meta">
      <span>字符数：{{ charCount }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const charCount = ref(0)

onMounted(() => {
  const box = document.getElementById('paste-box') as HTMLDivElement | null
  if (box) {
    box.addEventListener('input', () => {
      charCount.value = (box.innerText || '').length
    })
    box.addEventListener('paste', () => {
      // 延迟计算，确保粘贴内容已插入
      setTimeout(() => {
        charCount.value = (box.innerText || '').length
      }, 0)
    })
  }
})
</script>

<style scoped>
.paste-container {
  max-width: 900px;
  margin: 24px auto;
  padding: 16px;
}

.tip {
  color: #606266;
  margin-bottom: 8px;
}

.paste-box {
  min-height: 300px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 12px;
  background: #ffffff;
  outline: none;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.meta {
  margin-top: 8px;
  color: #909399;
}
</style>