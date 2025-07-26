move # 📚 DreamBig API Documentation

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://your-domain.com/api/v1
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```http
Authorization: Bearer <your-jwt-token>
```

### Authentication Flow

1. **Register/Login** to get access token
2. **Include token** in subsequent requests
3. **Refresh token** when expired

## 🔐 Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe",
  "phone": "+1234567890",
  "role": "tenant"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "tenant"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Login User
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### Forgot Password
```http
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Reset Password
```http
POST /auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "new_password": "newsecurepassword"
}
```

### Verify Email
```http
POST /auth/verify-email
Content-Type: application/json

{
  "token": "verification-token-from-email"
}
```

## 🏠 Property Endpoints

### List Properties
```http
GET /properties?skip=0&limit=20&city=bangalore&property_type=apartment&min_price=1000000&max_price=5000000
```

**Query Parameters:**
- `skip` (int): Number of records to skip (pagination)
- `limit` (int): Number of records to return (max 100)
- `city` (string): Filter by city
- `property_type` (string): apartment, house, villa, plot, commercial
- `min_price` (float): Minimum price filter
- `max_price` (float): Maximum price filter
- `bhk` (int): Number of bedrooms
- `furnishing` (string): furnished, semi_furnished, unfurnished

**Response:**
```json
{
  "properties": [
    {
      "id": 1,
      "title": "Luxury 3BHK Apartment",
      "description": "Beautiful apartment with modern amenities",
      "price": 2500000,
      "bhk": 3,
      "area": 1200,
      "property_type": "apartment",
      "furnishing": "furnished",
      "address": "123 Main Street",
      "city": "Bangalore",
      "state": "Karnataka",
      "images": [
        {"url": "/static/uploads/property1_1.jpg"},
        {"url": "/static/uploads/property1_2.jpg"}
      ],
      "features": [
        {"name": "parking", "value": "2"},
        {"name": "balcony", "value": "1"}
      ],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

### Create Property
```http
POST /properties
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Luxury 3BHK Apartment",
  "description": "Beautiful apartment with modern amenities",
  "price": 2500000,
  "bhk": 3,
  "area": 1200,
  "property_type": "apartment",
  "furnishing": "furnished",
  "address": "123 Main Street",
  "city": "Bangalore",
  "state": "Karnataka",
  "pincode": "560001",
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

### Get Property Details
```http
GET /properties/{property_id}
```

**Response:**
```json
{
  "id": 1,
  "title": "Luxury 3BHK Apartment",
  "description": "Beautiful apartment with modern amenities",
  "price": 2500000,
  "bhk": 3,
  "area": 1200,
  "property_type": "apartment",
  "furnishing": "furnished",
  "address": "123 Main Street",
  "city": "Bangalore",
  "state": "Karnataka",
  "images": [...],
  "videos": [...],
  "features": [...],
  "owner": {
    "id": 5,
    "name": "Property Owner",
    "email": "owner@example.com",
    "phone": "+1234567890"
  },
  "similar_properties": [...],
  "view_count": 245,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Update Property
```http
PUT /properties/{property_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Property Title",
  "price": 2600000
}
```

### Delete Property
```http
DELETE /properties/{property_id}
Authorization: Bearer <token>
```

### Upload Property Images
```http
POST /properties/{property_id}/images
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: [image1.jpg, image2.jpg, ...]
```

### Upload Property Videos
```http
POST /properties/{property_id}/videos
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: [video1.mp4]
title: "Property Tour"
description: "Virtual tour of the property"
```

## 👥 User Endpoints

### Get Current User Profile
```http
GET /users/me
Authorization: Bearer <token>
```

### Update User Profile
```http
PUT /users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "phone": "+9876543210"
}
```

### Submit KYC Documents
```http
POST /users/kyc
Authorization: Bearer <token>
Content-Type: multipart/form-data

id_proof: [id_document.pdf]
address_proof: [address_document.pdf]
kyc_details: {
  "id_number": "ABCD1234E",
  "address": "Full address"
}
```

### Get User Favorites
```http
GET /users/favorites
Authorization: Bearer <token>
```

### Add to Favorites
```http
POST /users/favorites
Authorization: Bearer <token>
Content-Type: application/json

{
  "property_id": 123
}
```

### Remove from Favorites
```http
DELETE /users/favorites/{property_id}
Authorization: Bearer <token>
```

## 💰 Investment Endpoints

### List Investments
```http
GET /investments?skip=0&limit=20&risk_level=low&investment_type=property
```

### Create Investment Opportunity
```http
POST /investments
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Premium Property Investment",
  "amount": 5000000,
  "expected_roi": 12.5,
  "risk_level": "medium",
  "investment_type": "property",
  "duration_months": 24,
  "description": "Investment in premium residential property",
  "location": "Bangalore",
  "property_id": 123
}
```

### Get Investment Details
```http
GET /investments/{investment_id}
```

### Invest in Opportunity
```http
POST /investments/{investment_id}/invest
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 100000
}
```

## 🛠️ Service Endpoints

### List Service Providers
```http
GET /services?category=cleaning&skip=0&limit=20
```

**Query Parameters:**
- `category` (string): cleaning, maintenance, security, legal, etc.
- `service_type` (string): Specific service type
- `skip` (int): Pagination offset
- `limit` (int): Number of results

**Response:**
```json
{
  "services": [
    {
      "id": 1,
      "name": "Premium Cleaning Services",
      "service_type": "cleaning",
      "description": "Professional home and office cleaning",
      "contact_number": "+1234567890",
      "email": "contact@cleaningservice.com",
      "is_verified": true,
      "rating": 4.8,
      "reviews_count": 156
    }
  ]
}
```

### Register Service Provider
```http
POST /services/providers
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Premium Cleaning Services",
  "service_type": "cleaning",
  "description": "Professional home and office cleaning",
  "contact_number": "+1234567890",
  "email": "contact@cleaningservice.com"
}
```

### Book Service
```http
POST /services/bookings
Authorization: Bearer <token>
Content-Type: application/json

{
  "service_provider_id": 1,
  "service_type": "cleaning",
  "property_id": 123,
  "details": {
    "preferred_date": "2024-02-15",
    "preferred_time": "10:00",
    "special_instructions": "Deep cleaning required"
  }
}
```

### List User Bookings
```http
GET /services/bookings
Authorization: Bearer <token>
```

### Update Booking Status
```http
PUT /services/bookings/{booking_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "completed"
}
```

## 🔍 Search Endpoints

### Search Properties
```http
GET /search/properties?q=luxury apartment bangalore&filters={"price_range":[1000000,5000000],"bhk":[2,3]}
```

**Query Parameters:**
- `q` (string): Search query
- `filters` (JSON): Advanced filters
- `sort_by` (string): price, date, relevance
- `sort_order` (string): asc, desc

### Get Search Suggestions
```http
GET /search/suggestions?q=bangal
```

**Response:**
```json
{
  "suggestions": [
    "Bangalore",
    "Bangalore East",
    "Bangalore North"
  ]
}
```

### Advanced Search
```http
POST /search/advanced
Content-Type: application/json

{
  "location": {
    "city": "Bangalore",
    "radius_km": 10,
    "coordinates": [12.9716, 77.5946]
  },
  "property_filters": {
    "type": ["apartment", "house"],
    "bhk": [2, 3, 4],
    "price_range": [1000000, 5000000],
    "area_range": [800, 2000],
    "furnishing": ["furnished", "semi_furnished"]
  },
  "amenities": ["parking", "gym", "swimming_pool"],
  "sort_by": "price",
  "sort_order": "asc"
}
```

## 📊 Analytics Endpoints

### Property Analytics
```http
GET /analytics/properties/{property_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "property_id": 123,
  "views": {
    "total": 1250,
    "this_week": 45,
    "this_month": 180
  },
  "inquiries": {
    "total": 25,
    "this_week": 3,
    "this_month": 8
  },
  "favorites": 15,
  "performance_score": 8.5
}
```

### User Analytics
```http
GET /analytics/users/me
Authorization: Bearer <token>
```

### Platform Analytics (Admin Only)
```http
GET /analytics/platform
Authorization: Bearer <admin-token>
```

## 💬 Chat Endpoints

### Get Chat Rooms
```http
GET /chat/rooms
Authorization: Bearer <token>
```

### Create Chat Room
```http
POST /chat/rooms
Authorization: Bearer <token>
Content-Type: application/json

{
  "participant_id": 456,
  "property_id": 123
}
```

### Send Message
```http
POST /chat/rooms/{room_id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Hello, I'm interested in this property",
  "message_type": "text"
}
```

### Get Messages
```http
GET /chat/rooms/{room_id}/messages?skip=0&limit=50
Authorization: Bearer <token>
```

## 🔔 Notification Endpoints

### Get Notifications
```http
GET /notifications?skip=0&limit=20&unread_only=true
Authorization: Bearer <token>
```

### Mark as Read
```http
PUT /notifications/{notification_id}/read
Authorization: Bearer <token>
```

### Update Notification Preferences
```http
PUT /notifications/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "email_notifications": true,
  "sms_notifications": false,
  "push_notifications": true,
  "notification_types": ["property_updates", "messages", "bookings"]
}
```

## 📈 Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR` (400): Invalid input data
- `UNAUTHORIZED` (401): Authentication required
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `CONFLICT` (409): Resource already exists
- `RATE_LIMITED` (429): Too many requests
- `INTERNAL_ERROR` (500): Server error

## 🔄 Rate Limiting

All endpoints are rate-limited:
- **Default**: 60 requests per minute
- **Authentication**: 10 requests per minute
- **File Upload**: 5 requests per minute

Rate limit headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## 📝 Response Formats

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

### Paginated Response
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "skip": 0,
    "limit": 20,
    "has_next": true,
    "has_prev": false
  }
}
```

## 🔧 Development Tools

### Health Check
```http
GET /health
```

### API Status
```http
GET /api/v1/status
```

### Database Health
```http
GET /api/v1/db/health
```
```
