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
    @dblclick="handleDoubleClick"
    style="touch-action: none; -webkit-user-select: none; user-select: none;"
  >
    <div class="text-white font-medium w-auto whitespace-nowrap">{{ title }}</div>
    <div class="flex w-full space-x-2 justify-end">
      <slot name="actions"></slot>
      <button @click.stop="$emit('close')"
              class="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded transition-colors duration-200">
        ×
      </button>
    </div>
  </div>
</template>

<script setup>
import {defineProps, defineEmits} from 'vue';
import {useDragResize} from '@/composables/useDragResize';

const props = defineProps({
  title: { type: String, default: '' },
  extraClass: { type: String, default: '' }
});

defineEmits(['close']);

const { startDrag, onDrag, stopDrag, handleDoubleClick } = useDragResize();

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
</script>
