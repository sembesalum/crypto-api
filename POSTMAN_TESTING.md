# Postman Testing Guide

## Base URL
```
http://localhost:8000
```

---

## 1. Check User Status

**Method:** `GET`

**URL:**
```
http://localhost:8000/api/user/status/255712345678/
```

**Headers:**
```
None required
```

**Body:**
```
None (GET request)
```

**Example Response:**
```json
{
    "exists": true,
    "is_active": false,
    "phone_number": "255712345678",
    "name": "John Doe",
    "subscription_start_date": null,
    "subscription_end_date": null,
    "package_type": null
}
```

---

## 2. Initiate Payment

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/payment/initiate/
```

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "phone_number": "255712345678",
    "amount": 150000,
    "name": "John Doe",
    "email": "john@example.com"
}
```

**Body Examples for Different Packages:**

**1 Month Package (150,000 TZS):**
```json
{
    "phone_number": "255712345678",
    "amount": 150000,
    "name": "John Doe"
}
```

**2 Months Package (250,000 TZS):**
```json
{
    "phone_number": "255712345678",
    "amount": 250000,
    "name": "John Doe",
    "email": "john@example.com"
}
```

**3 Months Package (500,000 TZS):**
```json
{
    "phone_number": "255712345678",
    "amount": 500000,
    "name": "John Doe"
}
```

**Example Response:**
```json
{
    "status": "success",
    "message": "Payment initiated successfully",
    "order_id": "TXN_ABC123DEF456",
    "transaction_id": "TXNQ5V8K2L9N3XM1",
    "payment_url": "https://Biasharapay.com/payment/...",
    "phone_number": "255712345678",
    "amount": 150000,
    "package_type": 1
}
```

---

## 3. Verify Payment

**Method:** `GET`

**URL:**
```
http://localhost:8000/api/payment/verify/TXNQ5V8K2L9N3XM1/
```

**Note:** Replace `TXNQ5V8K2L9N3XM1` with the actual transaction_id from the payment initiation response.

**Headers:**
```
None required
```

**Body:**
```
None (GET request)
```

**Example Response:**
```json
{
    "status": "success",
    "transaction_id": "TXNQ5V8K2L9N3XM1",
    "is_payment_successful": true,
    "verification_data": {
        "success": true,
        "data": {
            "transaction_id": "TXNQ5V8K2L9N3XM1",
            "status": "completed",
            "payment_amount": 150000
        }
    }
}
```

---

## 4. Webhook (Biashara Pay Callback)

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/webhook/biashara/
```

**Headers:**
```
Content-Type: application/json
```

**Body (JSON) - Example Webhook Payload:**
```json
{
    "ref_trx": "TXN_ABC123DEF456",
    "transaction_id": "TXNQ5V8K2L9N3XM1",
    "status": "success",
    "payment_amount": 150000,
    "customer_phone": "255712345678"
}
```

**Note:** This endpoint is called by Biashara Pay. You can test it manually in Postman, but in production, Biashara Pay will call this URL automatically.

---

## Complete Testing Flow

### Step 1: Check User Status (New User)
```
GET http://localhost:8000/api/user/status/255712345678/
```
Expected: `"exists": false`

### Step 2: Initiate Payment
```
POST http://localhost:8000/api/payment/initiate/
Body: {
    "phone_number": "255712345678",
    "amount": 150000,
    "name": "John Doe"
}
```
Expected: Returns `order_id` and `payment_url`

### Step 3: Verify Payment (Optional)
```
GET http://localhost:8000/api/payment/verify/{transaction_id}/
```
Replace `{transaction_id}` with the transaction_id from Step 2 response.

### Step 4: Check User Status Again
```
GET http://localhost:8000/api/user/status/255712345678/
```
Expected: `"exists": true`, `"is_active": true` (after payment is completed)

---

## Postman Collection JSON

You can import this into Postman:

```json
{
    "info": {
        "name": "Crypto API - Subscription Management",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Check User Status",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "http://localhost:8000/api/user/status/255712345678/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "user", "status", "255712345678", ""]
                }
            }
        },
        {
            "name": "Initiate Payment - 1 Month",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"phone_number\": \"255712345678\",\n    \"amount\": 150000,\n    \"name\": \"John Doe\"\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/payment/initiate/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "payment", "initiate", ""]
                }
            }
        },
        {
            "name": "Initiate Payment - 2 Months",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"phone_number\": \"255712345678\",\n    \"amount\": 250000,\n    \"name\": \"John Doe\"\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/payment/initiate/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "payment", "initiate", ""]
                }
            }
        },
        {
            "name": "Initiate Payment - 3 Months",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"phone_number\": \"255712345678\",\n    \"amount\": 500000,\n    \"name\": \"John Doe\"\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/payment/initiate/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "payment", "initiate", ""]
                }
            }
        },
        {
            "name": "Verify Payment",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "http://localhost:8000/api/payment/verify/TXNQ5V8K2L9N3XM1/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "payment", "verify", "TXNQ5V8K2L9N3XM1", ""]
                }
            }
        },
        {
            "name": "Webhook - Biashara Pay",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"ref_trx\": \"TXN_ABC123DEF456\",\n    \"transaction_id\": \"TXNQ5V8K2L9N3XM1\",\n    \"status\": \"success\",\n    \"payment_amount\": 150000,\n    \"customer_phone\": \"255712345678\"\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/webhook/biashara/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "webhook", "biashara", ""]
                }
            }
        }
    ]
}
```

---

## Quick Copy-Paste for Postman

### 1. Check User Status
```
GET http://localhost:8000/api/user/status/255712345678/
```

### 2. Initiate Payment (1 Month)
```
POST http://localhost:8000/api/payment/initiate/
Content-Type: application/json

{
    "phone_number": "255712345678",
    "amount": 150000,
    "name": "John Doe"
}
```

### 3. Initiate Payment (2 Months)
```
POST http://localhost:8000/api/payment/initiate/
Content-Type: application/json

{
    "phone_number": "255712345678",
    "amount": 250000,
    "name": "John Doe"
}
```

### 4. Initiate Payment (3 Months)
```
POST http://localhost:8000/api/payment/initiate/
Content-Type: application/json

{
    "phone_number": "255712345678",
    "amount": 500000,
    "name": "John Doe"
}
```

### 5. Verify Payment
```
GET http://localhost:8000/api/payment/verify/TXNQ5V8K2L9N3XM1/
```
*(Replace TXNQ5V8K2L9N3XM1 with actual transaction_id)*

### 6. Webhook Test
```
POST http://localhost:8000/api/webhook/biashara/
Content-Type: application/json

{
    "ref_trx": "TXN_ABC123DEF456",
    "transaction_id": "TXNQ5V8K2L9N3XM1",
    "status": "success",
    "payment_amount": 150000,
    "customer_phone": "255712345678"
}
```
