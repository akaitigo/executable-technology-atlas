import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // The independent teaching distribution has its own manifest and runtime tests.
  globalIgnores(['.next/**', 'out/**', 'build/**', 'next-env.d.ts', 'portable-atlas/**']),
]);

export default eslintConfig;
