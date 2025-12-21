module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:react/jsx-runtime', // Add this for React 17+ JSX transform
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'node_modules'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  settings: { react: { version: 'detect' } }, // Use 'detect' to automatically detect the React version
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    'react/prop-types': 'off', // Disable prop-types validation if not using them
    'react/react-in-jsx-scope': 'off', // Disable for React 17+
    'react/jsx-uses-react': 'off', // Disable for React 17+
  },
  // Add an override for AuthContext.jsx
  overrides: [
    {
      files: ['src/context/AuthContext.jsx'],
      rules: {
        'react-refresh/only-export-components': 'off',
      },
    },
  ],
};