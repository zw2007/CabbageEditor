import {createApp} from 'vue'
import App from './App.vue'
import Router from './router/index.js'
import './style.css'
import './blockly/generators/index.js'


let pyBridge;
if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, (channel) => {
        pyBridge = channel.objects.pybridge
        window.pyBridge = pyBridge
    })
}

const app = createApp(App)
app.use(Router)
app.mount('#app')