// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAfABSwdwkar8w09e1xoWad6zvrhE3Hy9U",
  authDomain: "webster-a6928.firebaseapp.com",
  projectId: "webster-a6928",
  storageBucket: "webster-a6928.firebasestorage.app",
  messagingSenderId: "285234445366",
  appId: "1:285234445366:web:127bcbfd9e73c6075cec97",
  measurementId: "G-QH6H8FC7CT"
};
// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service 
export const auth = getAuth(app);

export default app;