<template>
  <div class="min-h-screen border-2 border-[#84a65b] relative">
    <DockTitleBar title="助手" extraClass="bg-[#84A65B]" @close="closeFloat"/>
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
    <div class="w-full bg-[#a8a4a3]/65 flex flex-col" style="height: calc(100vh - 48px);">
      <!-- 对话记录区域 -->
      <div ref="chatHistoryRef" class="flex-1 overflow-y-auto p-4">
        <div class="max-w-6xl mx-auto">
          <div class="space-y-2 pr-2">
            <div v-for="(message, index) in messages" :key="index"
                 class="p-3 bg-[#E8E8E8]/80 rounded-lg shadow-sm border border-gray-100 space-y-2">
              <div>
                <span :class="{
                  'text-blue-500': message.sender === 'AI',
                  'text-green-500': message.sender === 'User',
                  'text-gray-500': message.sender === '系统'
                }" class="font-medium">
                  {{ message.sender }}:
                </span>
                <span v-if="message.text" class="text-gray-700 break-words whitespace-pre-wrap">{{ message.text }}</span>
              </div>
              <!-- 单张图片显示 -->
              <div v-if="message.imageData" class="max-w-sm">
                <img :src="message.imageData" :alt="message.imageName || 'image'" class="rounded border cursor-pointer max-h-60 object-contain" @click="openImagePreview(message)"/>
                <div v-if="message.imageName" class="text-xs text-gray-500 mt-1">{{ message.imageName }}</div>
              </div>
              <!-- 多张图片显示 -->
              <div v-if="message.images && message.images.length > 0" class="flex flex-wrap gap-2">
                <div v-for="(img, imgIdx) in message.images" :key="imgIdx" class="max-w-xs">
                  <img :src="img.data" :alt="img.name" class="rounded border cursor-pointer max-h-40 object-contain" @click="openImagePreview({imageData: img.data, imageName: img.name})"/>
                  <div class="text-xs text-gray-500 mt-1 truncate">{{ img.name }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="bg-[#E8E8E8]/80 border-t border-gray-200 shadow-lg backdrop-blur-sm">
        <div class="max-w-6xl mx-auto p-4">
          <!-- 隐藏图片选择器 -->
          <input ref="imageInputRef" type="file" accept="image/*" class="hidden" @change="onImageChange" />

          <div class="space-y-2">
            <!-- 顶部：导入图片和提示词按钮 -->
            <div class="flex gap-2">
              <button @click="triggerImageSelect('product')" class="px-3 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 whitespace-nowrap">
                导入产品
              </button>
              <button @click="triggerImageSelect('scene')" class="px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 whitespace-nowrap">
                导入场景
              </button>
              <button @click="triggerImageSelect('style')" class="px-3 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 whitespace-nowrap">
                导入样式
              </button>

              <div class="relative" @keydown.escape="hidePrompts">
                <button @click="togglePrompts" class="px-3 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 whitespace-nowrap">
                  提示词
                </button>
                <transition name="fade">
                  <div v-if="showPrompts" class="absolute bottom-full left-0 mb-2 w-64 max-h-72 overflow-y-auto bg-white/95 backdrop-blur border border-gray-200 rounded-lg shadow-lg p-2 space-y-1 z-50">
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-xs text-gray-500">常用提示词</span>
                      <button class="text-xs text-gray-400 hover:text-gray-600" @click="hidePrompts">关闭</button>
                    </div>
                    <template v-for="(p, i) in promptPresets" :key="i">
                      <button @click="applyPrompt(p)" class="w-full text-left text-sm px-2 py-1 rounded hover:bg-amber-100 focus:bg-amber-100 focus:outline-none">
                        {{ p.label }}
                      </button>
                    </template>
                  </div>
                </transition>
              </div>
            </div>

            <!-- 中间：输入框和待发送图片预览 -->
            <div class="bg-white rounded-lg border border-gray-300 p-2 space-y-2">
              <textarea v-model="userInput" placeholder="输入消息..." class="w-full p-2 border-none rounded-lg focus:ring-0 focus:outline-none transition-all resize-none" rows="3"></textarea>

              <div v-if="hasPendingImages" class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-gray-600">待发送图片</span>
                  <button @click="clearAllImages" class="text-xs text-red-500 hover:text-red-700">清空全部</button>
                </div>
                <div class="flex flex-wrap gap-4">
                  <div v-for="type in ['product', 'scene', 'style']" :key="type">
                    <div v-if="pendingImages[type]" class="relative group">
                      <img :src="pendingImages[type].data" :alt="pendingImages[type].name" class="h-20 w-20 object-cover rounded border border-blue-300" />
                      <button @click="removeImage(type)" class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600 opacity-0 group-hover:opacity-100 transition-opacity">×</button>
                      <div class="text-xs text-gray-600 mt-1 w-20 truncate capitalize" :title="pendingImages[type].name">{{ imageTypeLabels[type] }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 底部：发送按钮 -->
            <div class="flex justify-end">
              <button @click="sendMessage" class="px-5 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 whitespace-nowrap">
                发送
              </button>
            </div>

            <div v-if="imageError" class="text-xs text-red-500">{{ imageError }}</div>
          </div>
        </div>
      </div>

      <!-- 简单图片预览遮罩 -->
      <div v-if="imagePreview" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100]" @click.self="imagePreview = null">
        <div class="bg-white p-4 rounded shadow max-w-[90vw] max-h-[90vh] flex flex-col">
          <img :src="imagePreview.imageData" :alt="imagePreview.imageName" class="object-contain max-w-full max-h-[70vh]" />
          <div class="mt-2 flex justify-between items-center text-sm text-gray-600">
            <span>{{ imagePreview.imageName }}</span>
            <button class="px-3 py-1 bg-gray-800 text-white rounded hover:bg-gray-700" @click="imagePreview = null">关闭</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, computed, nextTick} from 'vue';
import {useDragResize} from '@/components/ui/DragTitleBar.js';
import DockTitleBar from '@/components/ui/DockTitleBar.vue';

const {dragState, startResize, stopDrag, onDrag, stopResize, onResize} = useDragResize();

const messages = ref([
  {sender: "AI", text: "你好！我是 AI。"},
]);
const userInput = ref('');
const chatHistoryRef = ref(null);

// 图片相关
const imageInputRef = ref(null);
const imageError = ref('');
const imagePreview = ref(null); // {imageData, imageName}
const currentImageType = ref(null); // 'product', 'scene', 'style'
const pendingImages = ref({
  product: null,
  scene: null,
  style: null,
});

const imageTypeLabels = {
  product: '产品',
  scene: '场景',
  style: '样式',
};

const hasPendingImages = computed(() => {
  return Object.values(pendingImages.value).some(img => img !== null);
});

// 提示词相关
const showPrompts = ref(false);
const promptPresets = ref([
  {label: '总结以上内容', text: '请总结以上对话的要点。'},
  {label: '解释代码', text: '请详细解释下面这段代码的作用及时间复杂度:\n'},
  {label: '生成测试用例', text: '请为下面的函数编写单元测试（使用pytest）:\n'},
  {label: '优化提示', text: '请审查我的提示词并给出更明确、更可执行的改进建议：\n'},
  {label: '翻译为英文', text: '请将下面的内容准确翻译成英文：\n'},
  {label: '改写更专业', text: '请将下面的文本改写得更专业、清晰且结构良好：\n'}
]);

function togglePrompts() { showPrompts.value = !showPrompts.value; }
function hidePrompts() { showPrompts.value = false; }
function applyPrompt(p) {
  userInput.value = p.text;
  hidePrompts();
}

function triggerImageSelect(type) {
  imageError.value = '';
  currentImageType.value = type;
  imageInputRef.value && imageInputRef.value.click();
}

function openImagePreview(message) {
  imagePreview.value = {imageData: message.imageData, imageName: message.imageName};
}

function removeImage(type) {
  if (pendingImages.value[type]) {
    pendingImages.value[type] = null;
  }
}

function clearAllImages() {
  pendingImages.value.product = null;
  pendingImages.value.scene = null;
  pendingImages.value.style = null;
}

async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function onImageChange(e) {
  const file = e.target.files[0];
  if (!file) return;
  imageError.value = '';

  if (file.size > 20 * 1024 * 1024) {
    imageError.value = `图片 ${file.name} 大小超过 20MB。`;
    e.target.value = '';
    return;
  }

  if (!currentImageType.value) {
    console.error('图片类型未指定');
    e.target.value = '';
    return;
  }

  try {
    const base64 = await fileToBase64(file);
    pendingImages.value[currentImageType.value] = {
      name: file.name,
      data: base64,
      type: currentImageType.value,
    };
  } catch (err) {
    console.error('读取图片失败', err);
    imageError.value = '读取图片失败，请重试。';
  } finally {
    e.target.value = '';
    currentImageType.value = null; // 重置
  }
}

async function waitWebChannel() {
  if (window.aiService || window.appService) return true;
  if (window.webChannelReady) {
    try {
      await window.webChannelReady;
    } catch {
    }
  }
  return !!(window.aiService || window.appService);
}

const SendMessageToAI = async (query, extra = {}) => {
  await waitWebChannel();
  const payloadObj = {message: query, ...extra};
  const payload = JSON.stringify(payloadObj);
  if (window.aiService && typeof window.aiService.send_message_to_ai === 'function') {
    window.aiService.send_message_to_ai(payload);
  } else {
    console.error("未发现 AI 通道 (aiService/pyBridge)");
  }
};

const sendMessage = () => {
  const text = userInput.value.trim();
  const imagesToSend = Object.values(pendingImages.value).filter(img => img !== null);

  // 至少要有文字或图片之一
  if (!text && imagesToSend.length === 0) return;

  // 构建消息对象
  const messageObj = {sender: "User"};
  let displayText = text || '';

  if (imagesToSend.length > 0) {
    // 如果有多个图片，显示图片列表
    const imageList = imagesToSend.map(img => img.name).join(', ');
    displayText = displayText
      ? `${displayText}\n[${imagesToSend.length}张图片: ${imageList}]`
      : `[${imagesToSend.length}张图片: ${imageList}]`;

    // 如果只有一张图片，直接显示在消息中
    if (imagesToSend.length === 1) {
      messageObj.imageData = imagesToSend[0].data;
      messageObj.imageName = imagesToSend[0].name;
    } else {
      // 多张图片暂存为数组
      messageObj.images = imagesToSend.map(img => ({data: img.data, name: img.name}));
    }
  }

  messageObj.text = displayText;
  messages.value.push(messageObj);

  // 滚动到底部
  nextTick(() => {
    const chatHistory = chatHistoryRef.value;
    if (chatHistory) {
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }
  });

  // 发送到后端
  const extra = {};
  if (imagesToSend.length > 0) {
    extra.type = 'images';
    extra.images = imagesToSend.map(img => ({
      name: img.name,
      data: img.data,
      type: img.type, // 附带图片类型
    }));
  }
  SendMessageToAI(text || '[图片]', extra);

  // 清空输入
  userInput.value = '';
  clearAllImages();
  imageError.value = '';
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

    // 如果返回包含 image_base64 也展示图片
    const msgObj = {
      sender: "AI",
      text: message.content || message.text || (message.type === 'image' ? '[图片]' : JSON.stringify(message))
    };
    if (message.image_base64) {
      msgObj.imageData = message.image_base64;
      msgObj.imageName = message.image_name || 'image';
    }
    messages.value.push(msgObj);

    // 滚动到底部
    nextTick(() => {
      const chatHistory = chatHistoryRef.value;
      if (chatHistory) {
        chatHistory.scrollTop = chatHistory.scrollHeight;
      }
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
    try {
      window.pyBridge.dock_event.connect(handleDockEvent);
    } catch {
    }
  }
  // 点击外部关闭提示词面板
  document.addEventListener('click', handleGlobalClick, true);
});

function handleGlobalClick(e) {
  // 如果点击不在提示词区域且不是按钮
  if (!showPrompts.value) return;
  const pop = document.querySelector('.prompt-popover-flag');
  if (pop && !pop.contains(e.target)) {
    // 通过 ref/ class 控制更精准，这里简单判断
    // 但我们已添加捕获监听, 若为按钮也会触发, 用 closest 判断
    const target = e.target;
    if (!target.closest || !target.closest('.prompt-popover-exclude')) {
      hidePrompts();
    }
  }
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleResizeMove);
  document.removeEventListener('mouseup', handleResizeUp);
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
  document.removeEventListener('mousemove', onResize);
  document.removeEventListener('mouseup', stopResize);
  if (window.pyBridge && window.pyBridge.dock_event) {
    try {
      window.pyBridge.dock_event.disconnect(handleDockEvent);
    } catch {
    }
  }
  document.removeEventListener('click', handleGlobalClick, true);
});
</script>

<style scoped>
/* 可选过渡 */
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
