// 生成器前置代码（Prelude）注册表（支持多插入点）
// 用法：
// - 在某个积木的生成器中：import { need } from './prelude'; need('keyboard')
// - 生成流程中：resetPrelude()；然后在不同位置 renderPreludeAt('global'|'runPrologue'|'runEpilogue')

// 已请求的前置段集合
const _required = new Set()

// 预设的前置片段清单（可按需扩展/修改）
// 每个键支持：
// - 字符串：仅用于 global 位置；
// - 或对象：{ global?: string, runPrologue?: string, runEpilogue?: string }
const PRELUDE_SNIPPETS = {
  // 键盘事件支持：当使用键盘事件积木时加入
  keyboard: {
    global: [
      '# 键盘/事件桥接初始化',
      'from PySide6.QtCore import pyqtSlot',
      'from utils.bridge import get_bridge',
    ].join('\n'),
    runPrologue: [
      '# 连接前端事件到后端处理函数',
      'bridge = get_bridge()',
      'try:',
      '    # 如果之前已连接过旧的 handle，则先断开旧的，再连接新的，确保仅保留一次有效连接',
      '    prev = getattr(bridge, "_blockly_handle_slot", None)',
      '    if prev is not None:',
      '        try:',
      '            bridge.key_event.disconnect(prev)',
      '        except Exception:',
      '            pass',
      '    bridge.key_event.connect(handle)',
      '    bridge._blockly_handle_slot = handle',
      'except Exception:',
      '    # 某些环境下可能尚未初始化 UI 桥接，忽略连接错误',
      '    pass',
    ].join('\n'),
    runEpilogue: [
      '# 键盘事件已就绪（如需，可在此处添加收尾逻辑）',
    ].join('\n')
  }
}

// 标记需要某个前置片段
export function need(name) {
  _required.add(name)
}

// 重置（在一次 workspaceToCode 开始前调用）
export function resetPrelude() {
  _required.clear()
}

// 渲染所有已请求的前置片段（旧接口：仅 global）
export function renderPrelude() {
  return renderPreludeAt('global')
}

// 渲染指定插入点的片段并返回文本（以单个换行结尾，或空串）
export function renderPreludeAt(where /* 'global' | 'runPrologue' | 'runEpilogue' */) {
  const parts = []
  for (const name of _required) {
    const entry = PRELUDE_SNIPPETS[name]
    if (!entry) continue
    let text = ''
    if (typeof entry === 'string') {
      if (where === 'global') text = entry
    } else if (typeof entry === 'object') {
      text = entry[where] || ''
    }
    if (text) parts.push(String(text).replace(/[\r\n]+$/, '')) // 去除尾部多余换行
  }
  if (parts.length === 0) return ''
  return parts.join('\n') + '\n'
}
