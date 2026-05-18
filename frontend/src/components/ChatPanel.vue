<script setup>
import { ref, nextTick } from 'vue'
import { chatStream, confirm } from '../api.js'
import MessageBubble from './MessageBubble.vue'
import ToolCallCard from './ToolCallCard.vue'

const props = defineProps({ sessionId: String })

const messages = ref([])
const inputText = ref('')
const isThinking = ref(false)
const confirmVisible = ref(false)
const confirmData = ref(null)

function addMessage(role, content = '') {
  messages.value.push({ role, content, toolCalls: [], isStreaming: true })
  return messages.value[messages.value.length - 1]
}

async function send() {
  const text = inputText.value.trim()
  if (!text || isThinking.value) return
  inputText.value = ''

  addMessage('user', text)
  const agentMsg = addMessage('agent')
  isThinking.value = true

  chatStream(text, props.sessionId, {
    onEvent(event) {
      if (event.type === 'token') {
        agentMsg.content += event.data.text
      } else if (event.type === 'tool_start') {
        agentMsg.toolCalls.push({
          name: event.data.name,
          args: event.data.args,
          result: null,
          running: true,
        })
      } else if (event.type === 'tool_result') {
        const tc = agentMsg.toolCalls.find(
          t => t.name === event.data.name && t.running
        )
        if (tc) {
          tc.result = event.data.result
          tc.running = false
        }
      } else if (event.type === 'confirm_wait') {
        confirmData.value = event.data.tasks
        confirmVisible.value = true
      }
    },
    onDone() {
      agentMsg.isStreaming = false
      isThinking.value = false
    },
    onError(err) {
      agentMsg.content = `错误: ${err.message}`
      agentMsg.isStreaming = false
      isThinking.value = false
    },
  })
}

async function onConfirm(approved) {
  await confirm(props.sessionId, approved)
  confirmVisible.value = false
  confirmData.value = null
}

function scrollBottom() {
  nextTick(() => {
    const el = document.querySelector('.chat-messages')
    if (el) el.scrollTop = el.scrollHeight
  })
}
</script>

<template>
  <div class="chat-panel">
    <div class="chat-messages" @vue:updated="scrollBottom">
      <MessageBubble
        v-for="(msg, i) in messages" :key="i"
        :message="msg"
      >
        <template v-if="msg.toolCalls?.length">
          <ToolCallCard
            v-for="(tc, j) in msg.toolCalls" :key="j"
            :toolCall="tc"
          />
        </template>
      </MessageBubble>

      <div v-if="isThinking" class="thinking-dot">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </div>
    </div>

    <div v-if="confirmVisible" class="confirm-bar">
      <span>确认执行:
        <strong v-for="t in confirmData" :key="t.name">
          {{ t.name }}({{ JSON.stringify(t.args) }})
        </strong>
      </span>
      <button class="btn-yes" @click="onConfirm(true)">确认</button>
      <button class="btn-no" @click="onConfirm(false)">取消</button>
    </div>

    <div class="chat-input">
      <input
        v-model="inputText"
        @keyup.enter="send"
        placeholder="输入你的问题..."
        :disabled="isThinking"
      />
      <button @click="send" :disabled="isThinking">发送</button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel { flex: 1; display: flex; flex-direction: column; max-width: 800px; margin: 0 auto; width: 100%; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; }

.thinking-dot { display: flex; gap: 4px; padding: 12px 16px; }
.dot {
  width: 8px; height: 8px; border-radius: 50%; background: #999;
  animation: blink 1.4s infinite both;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.3; } 40% { opacity: 1; } }

.confirm-bar {
  background: #fff3cd; border-top: 1px solid #ffc107;
  padding: 12px 20px; display: flex; align-items: center; gap: 12px;
  font-size: 14px;
}
.btn-yes, .btn-no {
  padding: 6px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px;
}
.btn-yes { background: #28a745; color: #fff; }
.btn-no { background: #dc3545; color: #fff; }

.chat-input {
  display: flex; padding: 16px 20px; background: #fff;
  border-top: 1px solid #e0e0e0;
}
.chat-input input {
  flex: 1; padding: 10px 14px; border: 1px solid #ddd;
  border-radius: 8px; font-size: 14px; outline: none;
}
.chat-input input:focus { border-color: #4a9eff; }
.chat-input button {
  margin-left: 8px; padding: 10px 20px; background: #4a9eff;
  color: #fff; border: none; border-radius: 8px; cursor: pointer; font-size: 14px;
}
.chat-input button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
