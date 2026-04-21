import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './theme.css'

import CampaignList from './components/CampaignList.vue'
import CampaignDetail from './components/CampaignDetail.vue'
import SubRulesView from './components/SubRulesView.vue'
import PostsView from './components/PostsView.vue'
import OpportunitiesView from './components/OpportunitiesView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/opportunities' },
    { path: '/opportunities', component: OpportunitiesView },
    { path: '/campaigns', component: CampaignList },
    { path: '/campaigns/:id', component: CampaignDetail },
    { path: '/subs', component: SubRulesView },
    { path: '/posts', component: PostsView },
  ],
})

createApp(App).use(createPinia()).use(router).mount('#app')
