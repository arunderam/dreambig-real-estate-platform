# 🔑 Firebase Token Types Explained

## ❌ **The Problem You Encountered**

You tried to use a **Custom Token** directly with the API, but the API expects an **ID Token**.

**Error Message:**
```
"Error verifying Firebase ID token: verify_id_token() expects an ID token, but was given a custom token."
```

## 🔍 **Token Types Explained**

### 🏭 **Custom Token** (Server-side)
- **Created by:** Firebase Admin SDK (server-side)
- **Purpose:** Sign in to Firebase from client-side
- **Lifetime:** 1 hour
- **Usage:** `firebase.auth().signInWithCustomToken(customToken)`
- **Example:** `eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCIs...`

### 🎫 **ID Token** (Client-side)
- **Created by:** Firebase Client SDK (after signing in)
- **Purpose:** Authenticate API requests
- **Lifetime:** 1 hour (auto-refreshed)
- **Usage:** `Authorization: Bearer <id_token>`
- **Example:** `eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcwZGM...`

## 🔄 **Conversion Process**

```
Custom Token → Sign in to Firebase → Get ID Token → Use in API
```

### Step-by-Step:

1. **Get Custom Token** (from Python script)
   ```python
   custom_token = "eyJhbGciOiAiUlMyNTYi..."
   ```

2. **Sign in to Firebase** (in browser/frontend)
   ```javascript
   firebase.auth().signInWithCustomToken(customToken)
   ```

3. **Get ID Token** (after successful sign-in)
   ```javascript
   user.getIdToken().then(idToken => {
     // This is what you use for API calls
   })
   ```

4. **Use ID Token in API** (for authentication)
   ```bash
   curl -H "Authorization: Bearer <id_token>" \
        http://127.0.0.1:8000/api/v1/auth/login
   ```

## 🛠️ **Solution Tools Created**

### 1. **custom_to_id_token_converter.html**
- **Purpose:** Convert custom tokens to ID tokens
- **How to use:**
  1. Open in browser
  2. Update Firebase config
  3. Click "Convert to ID Token"
  4. Copy the ID token for API use

### 2. **Quick Test Method**
```bash
# 1. Generate custom token
python get_firebase_token.py

# 2. Convert to ID token
# Open custom_to_id_token_converter.html

# 3. Test API with ID token
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id_token": "YOUR_ID_TOKEN"}'
```

## 🎯 **What You Need for API Calls**

### ✅ **Correct Usage (ID Token):**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcw..." \
  -H "Content-Type: application/json" \
  -d '{"id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcw..."}'
```

### ❌ **Incorrect Usage (Custom Token):**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Authorization: Bearer eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCIs..." \
  -H "Content-Type: application/json" \
  -d '{"id_token": "eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCIs..."}'
```

## 🔧 **Firebase Config Needed**

To convert tokens, you need your Firebase project configuration:

```json
{
  "apiKey": "AIzaSyC...",
  "authDomain": "your-project.firebaseapp.com",
  "projectId": "your-project-id",
  "storageBucket": "your-project.appspot.com",
  "messagingSenderId": "123456789",
  "appId": "1:123456789:web:abc123def456"
}
```

**Where to find this:**
1. Go to Firebase Console
2. Select your project
3. Go to Project Settings
4. Scroll down to "Your apps"
5. Click on your web app
6. Copy the config object

## 🚀 **Quick Solution**

1. **Open:** `custom_to_id_token_converter.html`
2. **Update:** Firebase config with your project settings
3. **Convert:** Custom token to ID token
4. **Use:** ID token in your API calls

## 💡 **Pro Tips**

1. **ID tokens expire** after 1 hour - generate new ones as needed
2. **Custom tokens are reusable** until they expire
3. **Always use ID tokens** for API authentication
4. **Keep Firebase config secure** but it's safe to use client-side
5. **Test with the HTML converter** before implementing in your app

## 🎉 **Summary**

- ❌ **Custom Token** = Sign in to Firebase
- ✅ **ID Token** = Authenticate with API
- 🔄 **Conversion** = Use the HTML tool provided
- 🎯 **Result** = Working API authentication
