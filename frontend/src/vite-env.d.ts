/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/react" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_PUBLIC_WEB_URL?: string;
  readonly VITE_PRIVACY_CONTACT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
