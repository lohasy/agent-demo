<script setup>
import { ref, onMounted } from 'vue'
import { createSession } from './api.js'
import ChatPanel from './components/ChatPanel.vue'

const sessionId = ref('')
const loading = ref(true)

onMounted(async () => {
  sessionId.value = await createSession()
  loading.value = false
})
</script>

<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-header">Agent Demo</div>
      <div class="sidebar-info">
        <div class="session-badge">会话: {{ sessionId }}</div>
      </div>
    </aside>
    <main class="main">
      <ChatPanel v-if="!loading" :sessionId="sessionId" />
      <div v-else class="loading">连接中...</div>
    </main>
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.app { display: flex; height: 100vh; background: #f5f5f5; }

.sidebar {
  width: 220px; background: #1e1e2e; color: #cdd6f4;
  display: flex; flex-direction: column; padding: 16px;
}
.sidebar-header { font-size: 18px; font-weight: bold; margin-bottom: 12px; }
.sidebar-info { font-size: 12px; color: #a6adc8; }
.session-badge {
  background: #313244; padding: 6px 10px; border-radius: 6px;
  font-family: monospace; word-break: break-all;
}

.main { flex: 1; display: flex; flex-direction: column; }
.loading { margin: auto; color: #666; font-size: 16px; }
</style>
