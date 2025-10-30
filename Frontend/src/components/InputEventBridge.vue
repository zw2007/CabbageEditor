<template>
  <!-- 隐藏桥接组件：无界面显示 -->
  <span style="display:none" aria-hidden="true"></span>
</template>

<script setup>
import {onMounted, onUnmounted, ref, computed} from 'vue'
import {useRoute} from 'vue-router'

// 组件属性：用于启用/禁用和场景信息（如：scene）
const props = defineProps({
  enabled: {type: Boolean, default: true}, // 是否启用输入事件捕获
  sceneName: {type: String, default: 'scene1'}, // 场景名称
})

const route = useRoute()
// 当前场景名称，优先使用路由参数
const currentSceneName = computed(() => (route?.query?.sceneName) || props.sceneName)

const isPointerDown = ref(false) // 鼠标是否按下
let rafIdMove = null // requestAnimationFrame ID（鼠标移动）
let rafIdWheel = null // requestAnimationFrame ID（滚轮）
let pendingMove = null // 待处理的鼠标移动事件
let pendingWheel = null // 待处理的滚轮事件

// 判断事件目标是否为输入区域（如输入框、文本域、可编辑内容）
function isTypingTarget(target) {
  if (!target) return false
  const tag = (target.tagName || '').toLowerCase()
  if (tag === 'input' || tag === 'textarea' || target.isContentEditable) return true
  // 避免捕获显式排除的元素
  return !!target.closest?.('[data-no-global-input]')
}

// 向 Python 端发送事件（通过 pyBridge）
function sendToPython(commandName, payload) {
  try {
    if (window.pyBridge) {
      window.pyBridge.send_message_to_main(commandName, JSON.stringify(payload))
    }
  } catch (e) {
    // 通道未准备好时静默忽略
  }
}

// 基础事件字段（时间戳、修饰键、场景名等）
function baseEventFields(e) {
  return {
    // 键盘修饰键
    altKey: !!e.altKey,
    ctrlKey: !!e.ctrlKey,
    metaKey: !!e.metaKey,
    shiftKey: !!e.shiftKey,
    // 路由场景信息
    sceneName: currentSceneName.value,
  }
}

// 键盘事件：按下
function onKeyDown(e) {
  // 全局 ESC：通过 Python 桥接打开设置 Dock（浮动居中）
  if (props.enabled && (e.key === 'Escape' || e.code === 'Escape')) {
    if (window.pyBridge && typeof window.pyBridge.add_dock_widget === 'function') {
      // 注意：重复调用后端会切换 Dock（存在则关闭），这里直接调用，保持与后端行为一致
      window.pyBridge.add_dock_widget('SetUp', '/SetUp', 'float', 'center')
    }
  }
  // 普通键盘事件上报：避免打断输入框编辑
  if (!props.enabled || isTypingTarget(e.target)) return
  const data = {
    kind: 'keyboard', // 事件类型：键盘
    type: 'keydown', // 事件动作：按下
    key: e.key, // 键值
    code: e.code, // 键码
    repeat: e.repeat, // 是否为重复按键
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

// 键盘事件：松开
function onKeyUp(e) {
  if (!props.enabled || isTypingTarget(e.target)) return
  const data = {
    kind: 'keyboard',
    type: 'keyup',
    key: e.key,
    code: e.code,
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

// 鼠标事件：按下
function onMouseDown(e) {
  if (!props.enabled) return
  isPointerDown.value = true
  const data = {
    kind: 'mouse',
    type: 'mousedown',
    button: e.button, // 鼠标按键
    buttons: e.buttons, // 当前所有按下的按钮
    clientX: e.clientX, // 鼠标位置 X
    clientY: e.clientY, // 鼠标位置 Y
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

// 鼠标事件：松开
function onMouseUp(e) {
  if (!props.enabled) return
  isPointerDown.value = false
  const data = {
    kind: 'mouse',
    type: 'mouseup',
    button: e.button,
    buttons: e.buttons,
    clientX: e.clientX,
    clientY: e.clientY,
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

// 刷新并发送鼠标移动事件（节流处理）
function flushMove() {
  if (!pendingMove) return
  const e = pendingMove
  pendingMove = null
  rafIdMove = null
  const data = {
    kind: 'mouse',
    type: 'mousemove',
    buttons: e.buttons,
    clientX: e.clientX,
    clientY: e.clientY,
    movementX: e.movementX, // 移动距离 X
    movementY: e.movementY, // 移动距离 Y
    dragging: isPointerDown.value, // 是否拖拽
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

// 鼠标移动事件（节流处理）
function onMouseMove(e) {
  if (!props.enabled) return
  pendingMove = e
  if (rafIdMove == null) rafIdMove = requestAnimationFrame(flushMove)
}

// 刷新并发送滚轮事件（节流处理）
function flushWheel() {
  if (!pendingWheel) return
  const e = pendingWheel
  pendingWheel = null
  rafIdWheel = null
  const data = {
    kind: 'mouse',
    type: 'wheel', // 滚轮事件
    deltaX: e.deltaX, // 横向滚动
    deltaY: e.deltaY, // 纵向滚动
    deltaMode: e.deltaMode, // 滚动模式
    clientX: e.clientX,
    clientY: e.clientY,
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

// 鼠标滚轮事件（节流处理）
function onWheel(e) {
  if (!props.enabled) return
  pendingWheel = e
  if (rafIdWheel == null) rafIdWheel = requestAnimationFrame(flushWheel)
}

// 鼠标双击事件
function onDblClick(e) {
  if (!props.enabled) return
  const data = {
    kind: 'mouse',
    type: 'dblclick',
    button: e.button,
    buttons: e.buttons,
    clientX: e.clientX,
    clientY: e.clientY,
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

// 鼠标右键菜单事件
function onContextMenu(e) {
  if (!props.enabled) return
  const data = {
    kind: 'mouse',
    type: 'contextmenu', // 右键菜单事件
    clientX: e.clientX,
    clientY: e.clientY,
    ...baseEventFields(e),
  }
  sendToPython('input_event', data)
}

onMounted(() => {
  // 键盘事件监听
  document.addEventListener('keydown', onKeyDown, {passive: true})
  document.addEventListener('keyup', onKeyUp, {passive: true})
  // 鼠标事件监听（如需启用请取消注释）
  // document.addEventListener('mousedown', onMouseDown, { passive: true })
  // document.addEventListener('mouseup', onMouseUp, { passive: true })
  // document.addEventListener('mousemove', onMouseMove, { passive: true })
  // document.addEventListener('wheel', onWheel, { passive: true })
  // document.addEventListener('dblclick', onDblClick, { passive: true })
  // document.addEventListener('contextmenu', onContextMenu, { passive: true })
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown)
  document.removeEventListener('keyup', onKeyUp)
  // document.removeEventListener('mousedown', onMouseDown)
  // document.removeEventListener('mouseup', onMouseUp)
  // document.removeEventListener('mousemove', onMouseMove)
  // document.removeEventListener('wheel', onWheel)
  // document.removeEventListener('dblclick', onDblClick)
  // document.removeEventListener('contextmenu', onContextMenu)
  if (rafIdMove != null) cancelAnimationFrame(rafIdMove)
  if (rafIdWheel != null) cancelAnimationFrame(rafIdWheel)
})
</script>

<style scoped>
/* 无视觉样式 */
</style>
