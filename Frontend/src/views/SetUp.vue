<template>
  <div class="relative min-w-[300px] min-h-screen border-2 border-[#84a65b] bg-black/70">
    <!-- 标题栏 -->
    <div class="titlebar flex items-center w-full cursor-move select-none justify-between rounded-t-md bg-black p-2">
      <div class="w-auto whitespace-nowrap font-medium text-white">设置</div>
      <!-- 关闭按钮 -->
      <button @click.stop="CloseDock"
              class="rounded px-2 py-1 text-sm text-white transition-colors duration-200 hover:bg-gray-600 bg-gray-700">
        ×
      </button>
    </div>

    <!-- 按钮容器 -->
    <div class="button-group flex flex-col items-center space-y-4 p-4">
      <button
          @click.stop="Archive"
          class="w-full max-w-xs rounded-md bg-[#5f9dc6]/50 px-6 py-3 font-bold text-black/80 hover:bg-[#5f9dc6]/70">
        <p class="text-center text-sm sm:text-base md:text-lg">存档</p>
      </button>
      <button
          @click="GoWelcome"
          class="w-full max-w-xs rounded-md bg-[#5f9dc6]/50 px-6 py-3 font-bold text-black/80 hover:bg-[#5f9dc6]/70">
        <p class="text-center text-sm sm:text-base md:text-lg">返回初始页面</p>
      </button>
      <button
          @click.stop="Out"
          class="w-full max-w-xs rounded-md bg-[#5f9dc6]/50 px-6 py-3 font-bold text-black/80 hover:bg-[#5f9dc6]/70">
        <p class="text-center text-sm sm:text-base md:text-lg">退出引擎</p>
      </button>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted} from 'vue';
import {useDragResize} from '@/composables/useDragResize';
import {useRouter} from 'vue-router';

const router = useRouter();
const {stopDrag, onDrag} = useDragResize();
const showContextMenu = ref(false);
const sceneImages = ref([]);
const showArchiveDialog = ref(false);
const archiveName = ref('');

const CloseDock = () => {
  if (window.pyBridge) {
    window.pyBridge.remove_dock_widget("SetUp");
  }
};

// 避免连接/断开 dock_event 时引用未定义
const HandleDockEvent = (event_type, event_data) => {
  try {
    // 可按需处理 SetUp 的 dock 事件，这里默认忽略
    return;
  } catch (_) {
  }
};

const Archive = () => {
  if (window.pyBridge && window.pyBridge.scene_save) {
    const SceneData = {
      actors: sceneImages.value.map(scene => ({
        name: scene.name,
        path: scene.path,
        type: scene.type
      }))
    };
    window.pyBridge.scene_save(JSON.stringify(SceneData));
  }
  ;

  try {
    const NewArchive = {
      id: Date.now(),
      name: '未命名存档',
      time: new Date().toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      }),
      sceneData: sceneImages.value.map(scene => ({
        name: scene.name,
        path: scene.path,
        type: scene.type
      }))
    };
    // 存储到 localStorage
    const existingSaves = JSON.parse(localStorage.getItem('archives') || '[]');
    existingSaves.unshift(NewArchive);
    localStorage.setItem('archives', JSON.stringify(existingSaves));

    window.pyBridge.send_message_to_main("go_home", "");
    window.pyBridge.remove_dock_widget("Pet");
    window.pyBridge.remove_dock_widget("AITalkBar");
    window.pyBridge.remove_dock_widget("Object");
    window.pyBridge.remove_dock_widget("SceneBar");
    window.pyBridge.remove_dock_widget("SetUp");
  } catch (error) {
    console.error('存档失败:', error);
  }
}

const GoWelcome = () => {
  window.pyBridge.send_message_to_main("go_home", "");
  window.pyBridge.remove_dock_widget("Pet");
  window.pyBridge.remove_dock_widget("AITalkBar");
  window.pyBridge.remove_dock_widget("Object");
  window.pyBridge.remove_dock_widget("SceneBar");
  window.pyBridge.remove_dock_widget("SetUp");
};

const Out = () => {
  if (window.pyBridge) {
    window.pyBridge.close_process();
  } else {
    console.error("Python SendMessageToDock 未连接！");
  }
}

onMounted(() => {
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', stopDrag);
  if (window.pyBridge) {
    window.pyBridge.dock_event.connect(HandleDockEvent);
  }
  ;
});

onUnmounted(() => {
  if (window.pyBridge) {
    window.pyBridge.dock_event.disconnect(HandleDockEvent);
  }
  ;
});
</script>
