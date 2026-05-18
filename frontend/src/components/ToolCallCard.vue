<script setup>
defineProps({ toolCall: Object })
</script>

<template>
  <div :class="['tool-card', { done: toolCall.result }]">
    <div class="tool-header">
      <span class="tool-icon">{{ toolCall.running ? '⟳' : '✓' }}</span>
      <span class="tool-name">{{ toolCall.name }}</span>
    </div>
    <div class="tool-body">
      <div class="tool-args">{{ JSON.stringify(toolCall.args) }}</div>
      <div v-if="toolCall.result" class="tool-result">{{ toolCall.result }}</div>
    </div>
  </div>
</template>

<style scoped>
.tool-card {
  margin-top: 8px; border: 1px solid #e0e0e0;
  border-radius: 8px; overflow: hidden; font-size: 12px;
}
.tool-card.done { border-color: #c8e6c9; }

.tool-header {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; background: #f5f5f5;
}
.tool-card.done .tool-header { background: #e8f5e9; }
.tool-icon { color: #ff9800; }
.tool-card.done .tool-icon { color: #4caf50; }
.tool-name { font-weight: 600; }

.tool-body { padding: 6px 10px; }
.tool-args { color: #666; font-family: monospace; }
.tool-result {
  margin-top: 6px; padding: 6px 8px; background: #f9f9f9;
  border-radius: 4px; color: #333; white-space: pre-wrap;
  max-height: 120px; overflow-y: auto;
}
</style>
