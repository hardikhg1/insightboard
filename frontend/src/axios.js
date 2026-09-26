/**
 * axios.js — Axios instance with a pre-configured base URL.
 *
 * What is Axios?
 * Axios is a library that makes HTTP requests from JavaScript easy.
 * Think of it as fetch() but with nicer error handling and less
 * boilerplate. Every API call in this app imports from this file
 * so the base URL is defined in exactly one place.
 *
 * Why /api/ and not http://localhost:8000/api/?
 * vite.config.js has a proxy rule: any request to /api/... is
 * automatically forwarded to http://localhost:8000 during development.
 * That removes the need to hardcode the backend port everywhere.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',          // vite proxy forwards this to Django :8000
  headers: {
    'Content-Type': 'application/json'
  }
})

export default api
