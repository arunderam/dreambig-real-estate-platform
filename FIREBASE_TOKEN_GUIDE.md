# 🔥 Firebase Token Guide - How to Get User Tokens

This guide explains how to get Firebase tokens to authenticate with your API.

## 📋 Overview

Your API uses Firebase Authentication. To access protected endpoints, you need:
1. **Custom Token** (created server-side) → Used to sign in to Firebase
2. **ID Token** (obtained client-side) → Used to authenticate API requests

## 🚀 Quick Start Methods

### Method 1: Using the Python Script (Easiest for Testing)

1. **Run the token generator:**
   ```bash
   python get_firebase_token.py
   ```

2. **Select a user** from the list of registered Firebase users

3. **Copy the custom token** that's generated

4. **Use the HTML test tool:**
   - Open `test_firebase_token.html` in your browser
   - Paste your Firebase config
   - Paste the custom token
   - Sign in and get the ID token
   - Test your API endpoints

### Method 2: Frontend JavaScript (Production Method)

```javascript
// Initialize Firebase
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  // ... other config
};
firebase.initializeApp(firebaseConfig);

// Sign in with email/password
firebase.auth().signInWithEmailAndPassword(email, password)
  .then((userCredential) => {
    // Get ID token
    return userCredential.user.getIdToken();
  })
  .then((idToken) => {
    // Use token in API calls
    fetch('http://127.0.0.1:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${idToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ id_token: idToken })
    });
  });
```

### Method 3: Using Custom Tokens (Development)

```javascript
// Use custom token from Python script
const customToken = "eyJhbGciOiAiUlMyNTYi..."; // From Python script

firebase.auth().signInWithCustomToken(customToken)
  .then((userCredential) => {
    return userCredential.user.getIdToken();
  })
  .then((idToken) => {
    // Use this ID token in your API calls
    console.log('ID Token:', idToken);
  });
```

## 🔧 Available Tools

The DreamBig platform includes built-in Firebase authentication integration. You can test authentication using:

### 1. **Web Interface**
- Navigate to `http://localhost:8000/login` for the login page
- Navigate to `http://localhost:8000/register` for registration
- Use the built-in authentication system

### 2. **API Documentation**
- Visit `http://localhost:8000/api/docs` for interactive API testing
- Test authentication endpoints directly from the Swagger UI

### 3. **Development Testing**
- Use the built-in test suite: `python -m pytest`
- Test authentication flows through the web interface

## 📊 Current Firebase Users

Run this to see available users:
```bash
curl http://127.0.0.1:8000/api/v1/auth/users-firebase-status
```

Example users created:
- `firebase_test2@example.com` (ID: 11)
- `firebase_test3@example.com` (ID: 12)
- `complete_test@example.com` (ID: 13)

## 🔐 API Authentication Flow

1. **Register User** → Creates user in Firebase + Database
2. **Get Custom Token** → Use Python script or admin SDK
3. **Sign In to Firebase** → Use custom token in frontend
4. **Get ID Token** → Call `user.getIdToken()`
5. **Make API Calls** → Include ID token in Authorization header

## 📝 Example API Calls

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id_token": "YOUR_ID_TOKEN"}'
```

### Get Recommendations
```bash
curl -X GET http://127.0.0.1:8000/api/v1/users/recommendations \
  -H "Authorization: Bearer YOUR_ID_TOKEN"
```

### Search Properties
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/search/?query=apartment" \
  -H "Authorization: Bearer YOUR_ID_TOKEN"
```

## 🎯 Token Types Explained

### Custom Token
- **Created by:** Server-side (Python script)
- **Used for:** Signing in to Firebase
- **Lifetime:** 1 hour
- **Example:** `eyJhbGciOiAiUlMyNTYi...`

### ID Token
- **Created by:** Firebase client SDK
- **Used for:** API authentication
- **Lifetime:** 1 hour (auto-refreshed)
- **Contains:** User claims, role, email, etc.

## 🚨 Security Notes

1. **Custom tokens** should only be created server-side
2. **ID tokens** should be obtained client-side
3. **Never expose** Firebase private keys
4. **Always validate** tokens on the server
5. **Use HTTPS** in production

## 🔄 Token Refresh

ID tokens expire after 1 hour. Refresh them:

```javascript
// Force refresh
user.getIdToken(true).then((newToken) => {
  // Use new token
});

// Auto-refresh (recommended)
firebase.auth().onIdTokenChanged((user) => {
  if (user) {
    user.getIdToken().then((token) => {
      // Updated token
    });
  }
});
```

## 🐛 Troubleshooting

### "Invalid token" errors
- Check token expiration
- Verify Firebase config
- Ensure user exists in Firebase

### "User not found" errors
- Register user first: `POST /api/v1/auth/register`
- Check Firebase user status: `GET /api/v1/auth/users-firebase-status`

### CORS errors
- Add your domain to Firebase Auth settings
- Check API CORS configuration

## 📞 Support

If you need help:
1. Check the browser console for errors
2. Verify Firebase configuration
3. Test with the provided HTML tools
4. Check server logs for authentication errors
