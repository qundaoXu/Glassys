/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GLASSYS_STATIC_SCENE?: string;
  readonly VITE_GLASSYS_STATIC_SCENE_NAME?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
