// Import the functions you need from the SDKs you need
import { initializeApp, getApp, getApps } from 'firebase/app'
// import { getAnalytics } from 'firebase/analytics'
import { getFirestore } from 'firebase/firestore'
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: 'AIzaSyBLNzsjHpPNf3fy_CYAHzj5wzYJKo5zkf8',
  authDomain: 'graduation-project-4d68b.firebaseapp.com',
  projectId: 'graduation-project-4d68b',
  storageBucket: 'graduation-project-4d68b.firebasestorage.app',
  messagingSenderId: '1063668846806',
  appId: '1:1063668846806:web:35b78ac0bb13ede7d43977',
  measurementId: 'G-W0BRCJKG8L',
}

// Initialize Firebase
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp()
// const analytics = getAnalytics(app)
const db = getFirestore(app)

export { app, db }
// export default db
