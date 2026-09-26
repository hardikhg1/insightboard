module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  extends: [
    'plugin:vue/vue3-recommended',
    'eslint:recommended'
  ],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  rules: {
    // Allow single-word component names (NavBar, DataTable etc.)
    'vue/multi-word-component-names': 'off',
    // Allow unused vars that start with _ (common convention for ignored params)
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    // Relax some Vue rules for beginner-friendly code
    'vue/html-self-closing': ['warn', { html: { void: 'always', normal: 'never' } }]
  }
}
