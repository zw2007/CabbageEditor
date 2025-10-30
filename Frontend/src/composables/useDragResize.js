import {ref} from 'vue';

export function useDragResize() {

    const isFloating = ref(false);

    // 简易节流函数，默认 30ms 一次
    const THROTTLE_MS = 20;
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

    // 统一封装 bridge 调用，捕获 DOMException，避免刷屏
    const safeForward = (type, payloadObj) => {
        if (!window.pyBridge || typeof window.pyBridge.forward_dock_event !== 'function') return;
        try {
            const routename = window.__dockRouteName;
            const payload = JSON.stringify({...payloadObj, routename});
            window.pyBridge.forward_dock_event(type, payload);
        } catch (err) {
            console.warn('pyBridge.forward_dock_event error:', err);
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

    // 节流后的拖拽事件发送
    const emitDragThrottled = throttle((deltaX, deltaY) => {
        safeForward('drag', {deltaX, deltaY});
    });

    const startDrag = (event) => {
        if (event.button !== 0) return;
        dragState.value.isDragging = true;
        dragState.value.startX = event.clientX;
        dragState.value.startY = event.clientY;

        // 拖动标题栏时自动变成浮动状态
        if (!isFloating.value) {
            isFloating.value = true;
            safeForward('float', {isFloating: true});
        }
        // 移除无效的空 className 操作，避免 DOMException
        // event.currentTarget.classList.add('dragging'); // 若需要样式，可解注释
        event.preventDefault();
    };

    const onDrag = (event) => {
        if (!dragState.value.isDragging) return;

        const deltaX = event.clientX - dragState.value.startX;
        const deltaY = event.clientY - dragState.value.startY;

        // 拖拽过程中发送，使用节流
        emitDragThrottled(deltaX, deltaY);

        event.preventDefault();
    };

    const stopDrag = (event) => {
        if (!dragState.value.isDragging) return;

        const deltaX = event.clientX - dragState.value.startX;
        const deltaY = event.clientY - dragState.value.startY;

        // 结束时再补发一次，确保最终位置一致
        safeForward('drag', {deltaX, deltaY});

        dragState.value.isDragging = false;
        dragState.value.startX = 0;
        dragState.value.startY = 0;

        // event.currentTarget.classList.remove('dragging'); // 若添加了 dragging，则在此移除
        event.preventDefault();
    };

    // 双击处理逻辑
    const handleDoubleClick = () => {
        if (isFloating.value) {
            isFloating.value = false;
            safeForward('float', {isFloating: false});
        }
    };

    const startResize = (event, direction) => {
        if (event.button !== 0) return;

        resizeState.value.isResizing = true;
        resizeState.value.direction = direction;

        const rect = event.currentTarget.parentElement.getBoundingClientRect();
        resizeState.value.startWidth = rect.width;
        resizeState.value.startHeight = rect.height;
        // 关键修正：加上 screenX/Y 获取绝对屏幕坐标
        resizeState.value.startDockX = rect.left + window.screenX;
        resizeState.value.startDockY = rect.top + window.screenY;

        resizeState.value.startX = event.clientX;
        resizeState.value.startY = event.clientY;

        event.preventDefault();
    };

    const onResize = (event) => {
        if (!resizeState.value.isResizing) return;

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
        event.preventDefault();
    };

    const stopResize = () => {
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
        handleDoubleClick,
        isFloating
    };
}