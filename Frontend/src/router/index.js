// 路由文件
import {createRouter, createWebHashHistory} from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'WelcomePage',
        component: () => import('../views/layout/WelcomePage.vue')
    },
    {
        path: '/MainPage',
        name: 'MainPage',
        component: () => import('../views/layout/MainPage.vue')
    },
    {
        path: '/AITalkBar',
        name: 'AITalkBar',
        component: () => import('../views/sidebar/AITalkBar.vue')
    },
    {
        path: '/SceneBar',
        name: 'SceneBar',
        component: () => import('../views/sidebar/SceneBar.vue')
    },
    {
        path: '/Object',
        name: 'Object',
        component: () => import('../views/sidebar/Object.vue')
    },
    {
        path: '/Pet',
        name: 'Pet',
        component: () => import('../views/tools/Pet.vue')
    },
    {
        path: '/SetUp',
        name: 'SetUp',
        component: () => import('../views/sidebar/SetUp.vue')
    },
]

const router = createRouter({
    history: createWebHashHistory(),
    routes,
})

router.beforeEach((to, from) => {
})

window.__ROUTES__ = routes;

export default router
