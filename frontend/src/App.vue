<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// App root component
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f7fa;
  color: #303133;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f2f6fc;
}

::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

/* 强制覆盖表格滚动条样式 - 全局样式 */
.preview-table ::-webkit-scrollbar,
.preview-table .el-table ::-webkit-scrollbar,
.preview-table .el-table__body-wrapper ::-webkit-scrollbar,
.preview-table .el-table__body ::-webkit-scrollbar,
.preview-table .el-scrollbar ::-webkit-scrollbar,
.preview-table .el-scrollbar__wrap ::-webkit-scrollbar,
.preview-table .el-scrollbar__view ::-webkit-scrollbar,
.preview-table * ::-webkit-scrollbar {
  width: 16px !important;
  height: 16px !important;
}

.preview-table ::-webkit-scrollbar-track,
.preview-table .el-table ::-webkit-scrollbar-track,
.preview-table .el-table__body-wrapper ::-webkit-scrollbar-track,
.preview-table .el-table__body ::-webkit-scrollbar-track,
.preview-table .el-scrollbar ::-webkit-scrollbar-track,
.preview-table .el-scrollbar__wrap ::-webkit-scrollbar-track,
.preview-table .el-scrollbar__view ::-webkit-scrollbar-track,
.preview-table * ::-webkit-scrollbar-track {
  background: #000000 !important;
  border-radius: 8px !important;
  border: 2px solid #333333 !important;
}

.preview-table ::-webkit-scrollbar-thumb,
.preview-table .el-table ::-webkit-scrollbar-thumb,
.preview-table .el-table__body-wrapper ::-webkit-scrollbar-thumb,
.preview-table .el-table__body ::-webkit-scrollbar-thumb,
.preview-table .el-scrollbar ::-webkit-scrollbar-thumb,
.preview-table .el-scrollbar__wrap ::-webkit-scrollbar-thumb,
.preview-table .el-scrollbar__view ::-webkit-scrollbar-thumb,
.preview-table * ::-webkit-scrollbar-thumb {
  background: #ff0000 !important;
  border-radius: 8px !important;
  border: 3px solid #ffffff !important;
  box-shadow: 0 4px 12px rgba(255, 0, 0, 0.8) !important;
}

.preview-table ::-webkit-scrollbar-thumb:hover,
.preview-table .el-table ::-webkit-scrollbar-thumb:hover,
.preview-table .el-table__body-wrapper ::-webkit-scrollbar-thumb:hover,
.preview-table .el-table__body ::-webkit-scrollbar-thumb:hover,
.preview-table .el-scrollbar ::-webkit-scrollbar-thumb:hover,
.preview-table .el-scrollbar__wrap ::-webkit-scrollbar-thumb:hover,
.preview-table .el-scrollbar__view ::-webkit-scrollbar-thumb:hover,
.preview-table * ::-webkit-scrollbar-thumb:hover {
  background: #ff3333 !important;
  border-color: #ffffff !important;
  box-shadow: 0 6px 16px rgba(255, 0, 0, 1) !important;
}

.preview-table ::-webkit-scrollbar-corner,
.preview-table .el-table ::-webkit-scrollbar-corner,
.preview-table .el-table__body-wrapper ::-webkit-scrollbar-corner,
.preview-table .el-table__body ::-webkit-scrollbar-corner,
.preview-table .el-scrollbar ::-webkit-scrollbar-corner,
.preview-table .el-scrollbar__wrap ::-webkit-scrollbar-corner,
.preview-table .el-scrollbar__view ::-webkit-scrollbar-corner,
.preview-table * ::-webkit-scrollbar-corner {
  background: #000000 !important;
}
</style>