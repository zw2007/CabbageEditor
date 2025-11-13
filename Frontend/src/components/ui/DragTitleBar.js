import {ref} from 'vue';

export function useDragResize() {

    const isFloating = ref(false);

    // 简易节流函数，默认 20ms 一次
    const THROTTLE_MS = 1000/60;
    const throttle = (fn, wait = THROTTLE_MS) => {
        let last = 0;
        let timer = null;
        let lastArgs = null;
        return function throttled(...args) {
            const now = Date.now();
            const remaining = wait - (now - last);
            lastArgs = args;
            if (remaining <= 0) {
                if (timer) {
                    clearTimeout(timer);
                    timer = null;
                }
                last = now;
                fn.apply(this, args);
            } else if (!timer) {
                timer = setTimeout(() => {
                    last = Date.now();
                    timer = null;
                    fn.apply(this, lastArgs);
                }, remaining);
            }
        };
    };

    // 统一封装：通过 appService 发送到指定 routename 的 dock（旧路径，保留兼容）
    const safeForward = (eventName, payloadObj) => {
        const routename = window.__dockRouteName;
        if (!routename) return;
        const app = window.appService;
        if (!app || typeof app.send_message_to_dock !== 'function') return;
        try {
            const payload = JSON.stringify({ event: eventName, routename, ...payloadObj });
            app.send_message_to_dock(routename, payload);
        } catch (err) {
            console.warn('send_message_to_dock error:', err);
        }
    };

    // 拖拽状态管理
    const dragState = ref({
        isDragging: false,
        startX: 0,
        startY: 0,
    });

    const resizeState = ref({
        isResizing: false,
        direction: '',
        startWidth: 0,
        startHeight: 0,
        startX: 0,
        startY: 0,
        startDockX: 0,
        startDockY: 0
    });

    // 节流后的拖拽事件（dockBridge 路径）
    const sendDragMoveViaBridge = throttle((x, y) => {
        try {
            if (window.dockBridge && typeof window.dockBridge.drag_move === 'function') {
                window.dockBridge.drag_move(Math.floor(x), Math.floor(y));
            }
        } catch (e) { /* ignore */ }
    });

    // 节流后的拖拽事件（旧路径）
    const emitDragThrottled = throttle((deltaX, deltaY) => {
        safeForward('drag', {deltaX, deltaY});
    });

    const startDrag = (event) => {
        if (event.button !== 0) return;
        dragState.value.isDragging = true;
        dragState.value.startX = event.clientX;
        dragState.value.startY = event.clientY;

        // 优先使用 dockBridge：自动设为浮动并展示停靠预览区
        if (window.dockBridge && typeof window.dockBridge.start_drag === 'function') {
            try {
                window.dockBridge.start_drag(Math.floor(event.clientX), Math.floor(event.clientY));
            } catch (e) { /* ignore */ }
        } else {
            // 兼容旧路径：变成浮动 + 走 delta 拖拽
            if (!isFloating.value) {
                isFloating.value = true;
                safeForward('float', {isFloating: true});
            }
        }
        event.preventDefault();
    };

    const onDrag = (event) => {
        if (!dragState.value.isDragging) return;

        if (window.dockBridge && typeof window.dockBridge.drag_move === 'function') {
            sendDragMoveViaBridge(event.clientX, event.clientY);
        } else {
            const deltaX = event.clientX - dragState.value.startX;
            const deltaY = event.clientY - dragState.value.startY;
            emitDragThrottled(deltaX, deltaY);
        }
        event.preventDefault();
    };

    const stopDrag = (event) => {
        if (!dragState.value.isDragging) return;

        if (window.dockBridge && typeof window.dockBridge.end_drag === 'function') {
            try { window.dockBridge.end_drag(); } catch (e) { /* ignore */ }
        } else {
            const deltaX = event.clientX - dragState.value.startX;
            const deltaY = event.clientY - dragState.value.startY;
            // 结束时再补发一次，确保最终位置一致
            safeForward('drag', {deltaX, deltaY});
        }

        dragState.value.isDragging = false;
        dragState.value.startX = 0;
        dragState.value.startY = 0;

        event.preventDefault();
    };

    const startResize = (event, direction) => {
        if (event.button !== 0) return;

        resizeState.value.isResizing = true;
        resizeState.value.direction = direction;

        const rect = event.currentTarget.parentElement.getBoundingClientRect();
        resizeState.value.startWidth = rect.width;
        resizeState.value.startHeight = rect.height;
        // 使用屏幕绝对坐标
        resizeState.value.startDockX = rect.left + window.screenX;
        resizeState.value.startDockY = rect.top + window.screenY;

        resizeState.value.startX = event.clientX;
        resizeState.value.startY = event.clientY;

        // 优先走 dockBridge
        if (window.dockBridge && typeof window.dockBridge.start_resize === 'function') {
            try { window.dockBridge.start_resize(direction, Math.floor(event.clientX), Math.floor(event.clientY)); } catch (e) {}
        }

        event.preventDefault();
    };

    const sendResizeMoveViaBridge = throttle((x, y) => {
        try {
            if (window.dockBridge && typeof window.dockBridge.resize_move === 'function') {
                window.dockBridge.resize_move(Math.floor(x), Math.floor(y));
            }
        } catch (e) {}
    });

    const onResize = (event) => {
        if (!resizeState.value.isResizing) return;

        if (window.dockBridge && typeof window.dockBridge.resize_move === 'function') {
            sendResizeMoveViaBridge(event.clientX, event.clientY);
        } else {
            const deltaX = event.clientX - resizeState.value.startX;
            const deltaY = event.clientY - resizeState.value.startY;

            let newX = resizeState.value.startDockX;
            let newY = resizeState.value.startDockY;
            let newWidth = resizeState.value.startWidth;
            let newHeight = resizeState.value.startHeight;

            const direction = resizeState.value.direction;

            if (direction.includes('n')) {
                newY = resizeState.value.startDockY + deltaY;
                newHeight = resizeState.value.startHeight - deltaY;
            }
            if (direction.includes('s')) {
                newHeight = resizeState.value.startHeight + deltaY;
            }
            if (direction.includes('w')) {
                newX = resizeState.value.startDockX + deltaX;
                newWidth = resizeState.value.startWidth - deltaX;
            }
            if (direction.includes('e')) {
                newWidth = resizeState.value.startWidth + deltaX;
            }

            safeForward('resize', {
                x: newX,
                y: newY,
                width: newWidth,
                height: newHeight
            });
        }
        event.preventDefault();
    };

    const stopResize = () => {
        if (window.dockBridge && typeof window.dockBridge.end_resize === 'function') {
            try { window.dockBridge.end_resize(); } catch (e) {}
        }
        resizeState.value.isResizing = false;
    };

    return {
        dragState,
        resizeState,
        startDrag,
        startResize,
        stopDrag,
        onDrag,
        stopResize,
        onResize,
        isFloating
    };
}