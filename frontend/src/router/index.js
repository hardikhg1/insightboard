/**
 * router/index.js — Vue Router configuration.
 *
 * Vue Router maps URL paths to Vue components (called "views").
 * It makes this a Single Page Application (SPA): clicking a link
 * swaps the component shown on screen WITHOUT doing a full browser
 * page reload.
 *
 * Routes defined here:
 *  /              → HomeView   (list of all uploaded datasets)
 *  /upload        → UploadView (CSV upload form)
 *  /datasets/:id  → DatasetView (detail, table, charts)
 */
import { createRouter, createWebHistory } from 'vue-router'
import HomeView    from '@/views/HomeView.vue'
import UploadView  from '@/views/UploadView.vue'
import DatasetView from '@/views/DatasetView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/upload',
    name: 'upload',
    component: UploadView
  },
  {
    path: '/datasets/:id',
    name: 'dataset',
    component: DatasetView,
    props: true   // passes :id as a prop to the component automatically
  }
]

const router = createRouter({
  history: createWebHistory(),  // uses real URLs (no #hash)
  routes
})

export default router
