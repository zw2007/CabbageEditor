<template>
  <div
    class="titlebar flex items-center w-full p-2 justify-between cursor-move select-none"
    :class="extraClass"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @lostpointercapture="onPointerUp"
    @mousedown.prevent.stop
    style="touch-action: none; -webkit-user-select: none; user-select: none;"
  >
    <div class="text-white font-medium w-auto whitespace-nowrap">{{ title }}</div>
    <div class="flex w-full space-x-2 justify-end">
      <!-- 可插入其他 action -->
      <slot name="actions"></slot>

      <!-- 仅保留一个 浮动/停靠 切换按钮 + 关闭按钮 -->
      <div class="flex items-center space-x-1">
        <!-- toggle floating -->
        <button @click.stop="onToggleFloat"
                title="切换浮动/停靠"
                class="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200">
          ⤢
        </button>

        <button @click.stop="$emit('close')"
                class="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200">
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {defineProps, defineEmits} from 'vue';
import {useDragResize} from '@/components/ui/DragTitleBar.js';

const props = defineProps({
  title: { type: String, default: '' },
  extraClass: { type: String, default: '' }
});

// 新增事件：toggleFloat（仅保留此事件）
const emit = defineEmits(['close', 'toggleFloat']);

const { startDrag, onDrag, stopDrag } = useDragResize();

function onPointerDown(e) {
  try { e.currentTarget.setPointerCapture && e.currentTarget.setPointerCapture(e.pointerId); } catch(_) {}
  startDrag(e);
}
function onPointerMove(e) {
  onDrag(e);
}
function onPointerUp(e) {
  try { e.currentTarget.releasePointerCapture && e.currentTarget.releasePointerCapture(e.pointerId); } catch(_) {}
  stopDrag(e);
}

function onToggleFloat() {
  try { emit('toggleFloat'); } catch (_) {}
}
</script>

<style scoped>
 /* ...existing style... */
</style>
