import {createApp} from 'vue'
import App from './App.vue'
import Router from './router/index.js'
import './style.css'
import './blockly/generators/index.js'

// 将 QWebChannel 对象导出到全局，并提供一个就绪 Promise
(function bootstrapWebChannel(){
  if (typeof window === 'undefined') return;
  if (!window.webChannelReady) {
    let _resolve;
    window.webChannelReady = new Promise((resolve)=>{ _resolve = resolve; });
    window._resolveWebChannelReady = _resolve;
  }

  function attachChannel(channel){
    try {
      const objects = channel.objects || {};
      // 不再导出 pyBridge
      window.sceneService = objects.sceneService || null;
      window.aiService = objects.aiService || null;
      window.scriptingService = objects.scriptingService || null;
      window.projectService = objects.projectService || null;
      window.appService = objects.appService || null;
      // 触发就绪
      if (window._resolveWebChannelReady) {
        window._resolveWebChannelReady({channel, objects});
        window._resolveWebChannelReady = null;
      }
      // 派发自定义事件，便于组件监听
      try { window.dispatchEvent(new CustomEvent('qwebchannel-ready', {detail:{channel, objects}})); } catch {}
    } catch (e) { /* 静默 */ }
  }

  // 如果 Qt 注入已就绪
  if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined' && qt.webChannelTransport) {
    try { new QWebChannel(qt.webChannelTransport, attachChannel); } catch {}
  }
})();

const app = createApp(App)
app.use(Router)
app.mount('#app')