<script setup>
defineProps({ message: Object })
</script>

<template>
  <div :class="['bubble', message.role]">
    <div class="bubble-role">{{ message.role === 'user' ? '你' : 'Agent' }}</div>
    <div class="bubble-content" v-html="message.content || ''"></div>
    <div v-if="message.isStreaming" class="cursor">|</div>
    <slot></slot>
  </div>
</template>

<style scoped>
.bubble { margin-bottom: 16px; max-width: 85%; }
.bubble.user { margin-left: auto; }
.bubble.agent { margin-right: auto; }

.bubble-role { font-size: 12px; color: #888; margin-bottom: 4px; }
.bubble.user .bubble-role { text-align: right; }

.bubble-content {
  padding: 10px 14px; border-radius: 12px; font-size: 14px;
  line-height: 1.6; white-space: pre-wrap; word-break: break-word;
  min-height: 20px;
}
.bubble.user .bubble-content { background: #4a9eff; color: #fff; }
.bubble.agent .bubble-content { background: #fff; color: #333; border: 1px solid #e8e8e8; }

.cursor { display: inline; color: #4a9eff; animation: blink 1s infinite; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }
</style>
