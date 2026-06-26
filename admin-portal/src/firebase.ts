import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "placeholder-api-key",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "style-with-us-49180.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "style-with-us-49180",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "style-with-us-49180.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "placeholder-sender-id",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "placeholder-app-id"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
