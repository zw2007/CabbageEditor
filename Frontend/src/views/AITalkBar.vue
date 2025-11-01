<template>
  <div class="border-2 border-[#84a65b] rounded-md relative">
    <DockTitleBar title="助手" extraClass="bg-[#84A65B]" @close="closeFloat" />
    <!-- 四周拖动边框 -->
    <div class="absolute top-0 left-0 w-full h-2 cursor-n-resize z-40" @mousedown="(e) => startResize(e, 'n')"></div>
    <div class="absolute bottom-0 left-0 w-full h-2 cursor-s-resize z-40" @mousedown="(e) => startResize(e, 's')"></div>
    <div class="absolute top-0 left-0 h-full w-2 cursor-w-resize z-40" @mousedown="(e) => startResize(e, 'w')"></div>
    <div class="absolute top-0 right-0 h-full w-2 cursor-e-resize z-40" @mousedown="(e) => startResize(e, 'e')"></div>
    <div class="absolute top-0 left-0 w-4 h-4 cursor-nw-resize z-40" @mousedown="(e) => startResize(e, 'nw')"></div>
    <div class="absolute top-0 right-0 w-4 h-4 cursor-ne-resize z-40" @mousedown="(e) => startResize(e, 'ne')"></div>
    <div class="absolute bottom-0 left-0 w-4 h-4 cursor-sw-resize z-40" @mousedown="(e) => startResize(e, 'sw')"></div>
    <div class="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize z-40" @mousedown="(e) => startResize(e, 'se')"></div>

    <!-- 主内容区域 -->
    <div class="flex flex-col h-screen overflow-hidden bg-[#a8a4a3]/65 pt-12">
      <!-- 对话记录区域 -->
      <div class="flex-1 overflow-hidden">
        <div class="h-full max-w-6xl mx-auto p-6">
          <div class="h-full overflow-y-auto no-scrollbar space-y-2 pr-2">
            <div v-for="(message, index) in messages" :key="index"
                 class="p-3 bg-[#E8E8E8]/80 rounded-lg shadow-sm border border-gray-100">
              <span :class="{
                'text-blue-500': message.sender === 'AI',
                'text-green-500': message.sender === 'User'
              }" class="font-medium">
                {{ message.sender }}:
                <span class="text-gray-700">{{ message.text }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="absolute bottom-0 left-0 right-0 bg-[#E8E8E8]/80 border-t border-gray-200 shadow-lg backdrop-blur-sm">
        <div class="max-w-6xl mx-auto p-4">
          <div class="flex space-x-2">
            <input v-model="userInput" @keyup.enter="sendMessage" placeholder="输入消息..." class="flex-1 p-2 border rounded-lg focus:ring-2 focus:ring-blue-400 
                  focus:outline-none transition-all border-gray-300
                  hover:border-blue-300 focus:border-blue-400"/>
            <button @click="sendMessage" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 
                  transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 
                  focus:ring-offset-2 whitespace-nowrap">
              发送
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import {ref, inject, onMounted, onUnmounted} from 'vue';
import {useDragResize} from '@/composables/useDragResize';
import DockTitleBar from '@/components/DockTitleBar.vue'

const {dragState, startDrag, startResize, stopDrag, onDrag, stopResize, onResize, handleDoubleClick} = useDragResize();

const messages = ref([
  {sender: "AI", text: "你好！我是 AI。"},
]);
const userInput = ref('');

async function waitWebChannel() {
  if (window.pyBridge || window.aiService || window.appService) return true;
  if (window.webChannelReady) {
    try { await window.webChannelReady; } catch {}
  }
  return !!(window.pyBridge || window.aiService || window.appService);
}

const SendMessageToAI = async (query) => {
  await waitWebChannel();
  const payload = JSON.stringify({message: query});
  if (window.aiService && typeof window.aiService.send_message_to_ai === 'function') {
    window.aiService.send_message_to_ai(payload);
  } else if (window.pyBridge && typeof window.pyBridge.send_message_to_ai === 'function') {
    window.pyBridge.send_message_to_ai(payload);
  } else {
    console.error("未发现 AI 通道 (aiService/pyBridge)");
  }
};

const sendMessage = () => {
  if (userInput.value.trim()) {
    messages.value.push({sender: "User", text: userInput.value});
    SendMessageToAI(userInput.value);
    userInput.value = '';
  }
};

window.receiveAIMessage = (data) => {
  try {
    let message = data;
    if (typeof data === 'string') {
      try {
        message = JSON.parse(data);
      } catch {
        message = {content: data};
      }
    }

    if (message.type === 'error') {
      console.error('AI处理错误:', message.content);
    }

    messages.value.push({
      sender: "AI",
      text: message.content || JSON.stringify(message)
    });
  } catch (e) {
    console.error('处理AI消息失败:', e);
    messages.value.push({
      sender: "系统",
      text: `无法处理AI响应: ${typeof data === 'string' ? data : JSON.stringify(data)}`
    });
  }
};

//关闭浮动窗口
const closeFloat = async () => {
  await waitWebChannel();
  if (window.appService && typeof window.appService.remove_dock_widget === 'function') {
    window.appService.remove_dock_widget("AITalkBar");
  } else if (window.pyBridge && typeof window.pyBridge.remove_dock_widget === 'function') {
    window.pyBridge.remove_dock_widget("AITalkBar");
  } else {
    console.error("未发现 Dock 控制通道 (appService/pyBridge)");
  }
};
/*
// 双击事件处理
const handleDoubleClick = () => {
  if (window.pyBridge) {
    window.pyBridge.forwardDockEvent('open', JSON.stringify({
      widgetId: "AITalkBar"
    }));
  } else {
    console.error("Python SendMessageToDock 未连接！");
  }
};
*/
const handleResizeMove = (e) => {
  if (dragState.value.isResizing) onResize(e);
};

const handleResizeUp = () => {
  if (dragState.value.isResizing) stopResize();
};

const handleDockEvent = (eventType, eventData) => {
  if (eventType === 'jsonData') {
    try {
      const data = JSON.parse(eventData);
      console.error(data['content'])
    } catch (error) {
      console.error('处理Dock事件失败:', error);
    }
  }
}

onMounted(async () => {
  await waitWebChannel();
  document.addEventListener('mousemove', handleResizeMove);
  document.addEventListener('mouseup', handleResizeUp);
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', stopDrag);
  document.addEventListener('mousemove', onResize);
  document.addEventListener('mouseup', stopResize);
  if (window.pyBridge && window.pyBridge.dock_event) {
    try { window.pyBridge.dock_event.connect(handleDockEvent); } catch {}
  }
});

onUnmounted(() => {
  document.removeEventListener('mousemove', handleResizeMove);
  document.removeEventListener('mouseup', handleResizeUp);
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
  if (window.pyBridge && window.pyBridge.dock_event) {
    try { window.pyBridge.dock_event.disconnect(handleDockEvent); } catch {}
  }
});
</script>