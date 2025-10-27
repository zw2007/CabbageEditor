<template>
  <div class="border-2 border-[#84a65b] rounded-md relative">
    <!-- 标题栏 -->
    <div class="titlebar flex items-center w-full p-2 rounded-t-md justify-between bg-[#84A65B] cursor-move select-none"
      @mousedown="startDrag" @mousemove="onDrag" @mouseup="stopDrag" @mouseleave="stopDrag" @dblclick="handleDoubleClick">
      <div class="text-white font-medium w-auto whitespace-nowrap">场景</div>
      <!-- 按钮组 -->
      <div class="flex w-full space-x-2 justify-end">
        <button @click.stop="CloseFloat"
          class="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200">
          ×
        </button>
      </div>
    </div>

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
    <div class="p-4 shadow-md w-full bg-[#a8a4a3]/65 flex flex-col" style="height: calc(100vh - 56px);">
      <div class="flex flex-wrap gap-2 mb-4">
        <div class="relative">
        <button @click.stop="ToggleModelDropdown"
          class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200 flex items-center">
            导入模型
            <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </button>
          <div v-if="ShowModelDropdown" 
              v-click-outside="CloseModelDropdown"
              class="absolute z-10 mt-1 w-40 bg-[#a8a4a3]/65 rounded-md shadow-lg">
            <div class="py-1">
              <button @click.stop="ImportLightSource"
                class="block w-full px-4 py-2 text-sm text-white hover:bg-gray-600 hover:text-gray-900 text-left">
                光源
              </button>
              <button @click.stop="ImportCamera"
                class="block w-full px-4 py-2 text-sm text-white hover:bg-gray-600 hover:text-gray-900 text-left">
                摄像头
              </button>
              <button @click.stop="HandleFileImport"
                class="block w-full px-4 py-2 text-sm text-white hover:bg-gray-600 hover:text-gray-900 text-left">
                自定义模型
              </button>
            </div>
          </div>
        </div>

        <button @click.stop="HandleSceneImport"
          class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200">
          导入场景
        </button>
        <button @click.stop="SaveScene"
          class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200">
          保存场景
        </button>
        <button @click.stop="DayNightCycle"
          class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200">
          昼夜变换
        </button>
        </div>
      <div class="flex items-center justify-between gap-2 mb-4">
        <label class="text-write whitespace-nowrap">光照方向：</label>
        <label class="text-write">x</label>
        <input type="number" step="0.1" @change="UpdateSunPosition" @input="e => px = e.target.value"
          class="w-20 p-1 text-center border rounded-md focus:outline-none focus:ring-2 text-write focus:ring-blue-400 bg-[#686868]/70"
          :value="px" />
        <label class="text-write">y</label>
        <input type="number" step="0.1" @change="UpdateSunPosition" @input="e => py = e.target.value"
          class="w-20 p-1 text-center border rounded-md focus:outline-none focus:ring-2 text-write focus:ring-blue-400 bg-[#686868]/70"
          :value="py" />
        <label class="text-write">z</label>
        <input type="number" step="0.1" @change="UpdateSunPosition" @input="e => pz = e.target.value"
          class="w-20 p-1 text-center border rounded-md focus:outline-none focus:ring-2 text-write focus:ring-blue-400 bg-[#686868]/70"
          :value="pz" />
      </div>

      <div class="flex-1 overflow-y-auto">
        <!-- 场景列表 - 瀑布流布局 -->
        <div class="grid grid-cols-1 gap-4">
          <div v-for="scene in sceneImages" :key="scene.name" class="mb-4 break-inside-avoid">
            <div class="bg-[#E8E8E8]/80 rounded-lg shadow-sm overflow-hidden hover:bg-[#E8E8E8]/80 transition-all duration-200">
              <div class="p-3 flex justify-between items-center">
                <div class="flex flex-col w-full">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium text-gray-900 truncate" :title="scene.name"
                      @dblclick="ControlObject(scene)">
                      {{ scene.name }}
                    </span>
                    <button @click.stop="DeleteActor(scene)" 
                      class="ml-2 w-4 h-4 flex items-center justify-center text-red-500 hover:text-red-700">
                      ×
                    </button>
                  </div>
                  <span class="text-xs text-gray-500 truncate" :title="scene.path">
                    {{ scene.type === 'obj' ? 'OBJ模型' : '其他类型' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useDragResize } from '@/composables/useDragResize';

const { dragState,startDrag,startResize,stopDrag,onDrag,stopResize,onResize, handleDoubleClick } = useDragResize();
const sceneImages = ref([]);
const route = useRoute();
const currentSceneName = ref('');
const px=ref('1.0'), py=ref('1.0'), pz=ref('1.0');


const ControlObject = (scene) => {
  if (window.pyBridge) {
    const widgetName = `Object_${scene.name}`;
    window.pyBridge.add_dock_widget(widgetName, `/Object?sceneName=${currentSceneName.value}&objectName=${scene.name}&path=${encodeURIComponent(scene.path)}&routename=${widgetName}`, "right");
  }
};const HandleResizeMove = (e) => {
  if (dragState.value.isResizing) onResize(e);
};

const HandleResizeUp = () => {
  if (dragState.value.isResizing) stopResize();
};

const UpdateSunPosition = () => {
  if (window.pyBridge) {
    window.pyBridge.sun_direction(JSON.stringify({
      sceneName: currentSceneName.value,
      px: parseFloat(px.value),
      py: parseFloat(py.value),
      pz: parseFloat(pz.value)
    }));
    console.error('updateSunDirection', px.value, py.value, pz.value); 
  } 
}

const SaveScene = () => {
  if (window.pyBridge && window.pyBridge.scene_save) {
    const sceneData = {
      actors: sceneImages.value.map(scene => ({
        name: scene.name,
        path: scene.path,
        type: scene.type
      }))
    };
    window.pyBridge.scene_save(JSON.stringify(sceneData));
  }
};

// 下拉菜单
const showModelDropdown = ref(false);
const ToggleModelDropdown = () => {
  showModelDropdown.value = !showModelDropdown.value;
}
// 导入光源
const ImportLightSource = () => {
  showModelDropdown.value = false;
  if (window.pyBridge && window.pyBridge.createLight) {
    window.pyBridge.createLight(currentSceneName.value);
  }
};
// 导入摄像头
const ImportCamera = () => {
  showModelDropdown.value = false;
  if (window.pyBridge && window.pyBridge.createCamera) {
    window.pyBridge.createCamera(currentSceneName.value);
  }
};

const HandleFileImport = () => { 
  showModelDropdown.value = false;
  if (window.pyBridge && window.pyBridge.open_file_dialog) {
    window.pyBridge.open_file_dialog(currentSceneName.value, 'model');
  }
};

const HandleSceneImport = () => {
  if (window.pyBridge && window.pyBridge.open_file_dialog) {
    window.pyBridge.open_file_dialog(currentSceneName.value, 'scene');
  }
};

const HandleDockEvent = (event_type, event_data) => {
  if (event_type === 'actorCreated') {
    try {
      const data = JSON.parse(event_data);
      // 使用后端返回的数据创建场景项
      sceneImages.value.push({
        name: data.name,         // 使用返回的名称
        path: data.path,         // 使用返回的完整路径
        type: 'obj'
      });
    } catch (error) {
      console.error('处理Actor创建响应失败:', error);
    }
  } else if (event_type === 'sceneLoaded') {
    try {
      const data = JSON.parse(event_data);
      if (data.actors && Array.isArray(data.actors)) {
        sceneImages.value = data.actors.map(actor => ({
          name: actor.path.split('/').pop().split('.')[0], 
          path: actor.path,
          type: 'obj'
        }));
      }
    } catch (error) {
      console.error('处理场景加载响应失败:', error);
    }
  } else if (event_type === 'message'){
    console.log(event_data)
  }
};

const DeleteActor = (scene) => {
  try {
    if (window.pyBridge && window.pyBridge.remove_actor) {
      window.pyBridge.remove_actor(currentSceneName.value,scene.name);
      // 删除关联的Dock窗口
      const widgetName = `Object_${scene.name}`;
      window.pyBridge.remove_dock_widget(widgetName);
    }
    // 从场景列表中移除
    sceneImages.value = sceneImages.value.filter(item => item.name !== scene.name);
  } catch (error) {
    console.error('删除角色失败:', error);
  }
}

const DayNightCycle = () => {
  let currentTime = 0;
  const interval = setInterval(() => {
    if(currentTime === 1440){
      currentTime = 0;
    } else {
      currentTime++;
      const x = Math.cos(currentTime * Math.PI * 2 / 1440);
      const y = Math.sin(currentTime * Math.PI * 2 / 1440);
      const z = 0.0;
      
      px.value = x.toFixed(2);
      py.value = y.toFixed(2);
      pz.value = z.toFixed(2);
      
      if(window.pyBridge){
        window.pyBridge.sun_direction(JSON.stringify({
          px: x,
          py: y,
          pz: z
        }));
      }
    }
  }, 100); // Update every 100ms
  
  return () => clearInterval(interval);
};

//关闭浮动窗口
const CloseFloat = () => {
  if (window.pyBridge) {
    window.pyBridge.remove_dock_widget("SceneBar");
  }
};

const HandleResizeMove = (e) => {
  if (dragState.value.isResizing) onResize(e);
};

const HandleResizeUp = () => {
  if (dragState.value.isResizing) stopResize();
};

onMounted(() => {
  currentSceneName.value = route.query.sceneName || 'scene1';
  document.addEventListener('mousemove', HandleResizeMove);
  document.addEventListener('mouseup', HandleResizeUp);
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', stopDrag);
  if (window.pyBridge) {
    window.pyBridge.dock_event.connect(HandleDockEvent);
  };
});

onUnmounted(() => {
  document.removeEventListener('mousemove', HandleResizeMove);
  document.removeEventListener('mouseup', HandleResizeUp);
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
  if (window.pyBridge) {
    window.pyBridge.dock_event.disconnect(HandleDockEvent);
  };
});
</script>