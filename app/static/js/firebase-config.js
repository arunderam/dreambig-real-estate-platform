// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyCzhyGXIVMPtMcpSPZPR-q8keBVkeBvySM",
    authDomain: "dreambig-6d10e.firebaseapp.com",
    projectId: "dreambig-6d10e",
    storageBucket: "dreambig-6d10e.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef123456789"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Firebase Auth
const auth = firebase.auth();

// Configure Auth settings
auth.useDeviceLanguage();

// Export for use in other files
window.firebaseAuth = auth;
window.firebaseConfig = firebaseConfig;
