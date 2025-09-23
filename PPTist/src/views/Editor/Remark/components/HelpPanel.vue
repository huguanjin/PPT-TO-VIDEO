<template>
  <div class="help-panel">
    <!-- 分割帮助信息 -->
    <div class="split-help">
      <div class="help-content">
        <p>
          <kbd>Enter</kbd>
          手动换行分割
        </p>
        <p>
          <kbd>Shift</kbd> + <kbd>Enter</kbd>
          软回车（不分割）
        </p>
        <p>
          <kbd>Ctrl</kbd> + <kbd>D</kbd>
          按句号分割
        </p>
        <p>
          <kbd>Ctrl</kbd> + <kbd>M</kbd>
          合并所有行
        </p>
      </div>
    </div>

    <!-- 字符统计详情 -->
    <slot name="stats"></slot>
  </div>
</template>

<script setup lang="ts">
// 这个组件主要用于显示帮助信息
// 统计信息通过slot传入，保持组件的灵活性
</script>

<style lang="scss" scoped>
.help-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

// 分割帮助信息（侧边栏样式）
.split-help {
  background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid #c3e6c3;
}

.help-content p {
  margin: 4px 0;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  color: #155724;
  font-weight: 500;
  line-height: 1.4;
}

kbd {
  display: inline-block;
  padding: 2px 4px;
  font-size: 10px;
  line-height: 1;
  color: #495057;
  vertical-align: middle;
  background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
  border: solid 1px #ced4da;
  border-bottom-color: #adb5bd;
  border-radius: 3px;
  box-shadow: inset 0 -1px 0 #adb5bd, 0 1px 2px rgba(0,0,0,0.1);
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}
</style>