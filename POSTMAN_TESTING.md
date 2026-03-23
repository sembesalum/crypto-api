# Postman Testing Guide

## Base URL
```
http://localhost:8000
```

**Note:** Endpoints za API hizi zote hutumia **POST** na `Content-Type: application/json`. **Namba ya simu (username) iko kwenye JSON body, si kwenye URL** (isipokuwa webhook inayoweza kutumwa na Biashara Pay).

---

## 1. Check / Register User (status)

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/user/status/
```

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "phone_number": "255616107670"
}
```

**Example Response (user exists):**
```json
{
    "exists": true,
    "is_active": false,
    "phone_number": "255616107670",
    "name": "255616107670",
    "subscription_start_date": null,
    "subscription_end_date": null,
    "package_type": null,
    "message": "Karibu tena, account yako haiko active. Tafadhali lipia kuendelea kupata huduma zetu."
}
```

**Example Response (new user — account created):**
```json
{
    "exists": true,
    "is_active": false,
    "phone_number": "255616107670",
    "name": "255616107670",
    "subscription_start_date": null,
    "subscription_end_date": null,
    "package_type": null,
    "message": "Karibu sana, account yako imetengenezwa endelea kufurahia huduma zetu."
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

**Body (JSON):** Lazima `package_id` na `amount` ziendane (angalia jedwali hapa chini).

```json
{
    "phone_number": "255616107670",
    "package_id": 1,
    "amount": 150000,
    "name": "John Doe",
    "email": "john@example.com"
}
```

**Body Examples for Different Packages:**

**1 Month Package (`package_id`: 1, 150,000 TZS):**
```json
{
    "phone_number": "255616107670",
    "package_id": 1,
    "amount": 150000,
    "name": "John Doe"
}
```

**2 Months Package (`package_id`: 2, 250,000 TZS):**
```json
{
    "phone_number": "255616107670",
    "package_id": 2,
    "amount": 250000,
    "name": "John Doe",
    "email": "john@example.com"
}
```

**3 Months Package (`package_id`: 3, 500,000 TZS):**
```json
{
    "phone_number": "255616107670",
    "package_id": 3,
    "amount": 500000,
    "name": "John Doe"
}
```

**Example Response:**
```json
{
    "status": "success",
    "message": "Gusa link hapa chini kufanya malipo yako ya Tsh 150,000 https://Biasharapay.com/payment/...",
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

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/payment/verify/
```

**Note:** Badilisha `transaction_id` na thamani halisi kutoka majibu ya initiate payment.

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "transaction_id": "TXNQ5V8K2L9N3XM1"
}
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

## 4. Payment Status (within 6 hours)

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/payment/status/
```

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "phone_number": "255616107670"
}
```

**Example Response (paid within last 6 hours):**
```json
{
    "exists": true,
    "paid_within_6_hours": true,
    "message": "Hongera malipo yamekamilika sasa unaweza kupata signal zetu kila siku.",
    "phone_number": "255712345678"
}
```

**Example Response (no recent payment):**
```json
{
    "exists": true,
    "paid_within_6_hours": false,
    "message": "Pole, hakuna malipo yaliyofanyika kwenye account yako.",
    "phone_number": "255712345678"
}
```

---

## 5. Webhook (Biashara Pay Callback)

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

### Step 1: Check / Register User
```
POST http://localhost:8000/api/user/status/
Content-Type: application/json

{
    "phone_number": "255616107670"
}
```
Expected: `message` in Kiswahili; new users get an account created automatically.

### Step 2: Initiate Payment
```
POST http://localhost:8000/api/payment/initiate/
Content-Type: application/json

{
    "phone_number": "255616107670",
    "package_id": 1,
    "amount": 150000,
    "name": "John Doe"
}
```
Expected: Returns `order_id`, `payment_url`, na `message` ya Kiswahili.

### Step 3: Verify Payment (Optional)
```
POST http://localhost:8000/api/payment/verify/
Content-Type: application/json

{
    "transaction_id": "TXNQ5V8K2L9N3XM1"
}
```
Replace `transaction_id` with the value from Step 2 response.

### Step 4: Payment Status (Optional)
```
POST http://localhost:8000/api/payment/status/
Content-Type: application/json

{
    "phone_number": "255616107670"
}
```
Expected: `paid_within_6_hours: true` baada ya malipo yaliyothibitishwa (webhook au verify).

### Step 5: Check User Again
```
POST http://localhost:8000/api/user/status/
Content-Type: application/json

{
    "phone_number": "255616107670"
}
```
Expected: `"is_active": true` (baada ya malipo yamekamilika).

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
            "name": "Check / Register User",
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
                    "raw": "{\n    \"phone_number\": \"255616107670\"\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/user/status/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "user", "status", ""]
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
                    "raw": "{\n    \"phone_number\": \"255616107670\",\n    \"package_id\": 1,\n    \"amount\": 150000,\n    \"name\": \"John Doe\"\n}"
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
                    "raw": "{\n    \"phone_number\": \"255616107670\",\n    \"package_id\": 2,\n    \"amount\": 250000,\n    \"name\": \"John Doe\"\n}"
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
                    "raw": "{\n    \"phone_number\": \"255616107670\",\n    \"package_id\": 3,\n    \"amount\": 500000,\n    \"name\": \"John Doe\"\n}"
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
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"transaction_id\": \"TXNQ5V8K2L9N3XM1\"\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/payment/verify/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "payment", "verify", ""]
                }
            }
        },
        {
            "name": "Payment Status (6h)",
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
                    "raw": "{\n    \"phone_number\": \"255616107670\"\n}"
                },
                "url": {
                    "raw": "http://localhost:8000/api/payment/status/",
                    "protocol": "http",
                    "host": ["localhost"],
                    "port": "8000",
                    "path": ["api", "payment", "status", ""]
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

### 1. Check / Register User
```
POST http://localhost:8000/api/user/status/
Content-Type: application/json

{
    "phone_number": "255616107670"
}
```

### 2. Initiate Payment (1 Month)
```
POST http://localhost:8000/api/payment/initiate/
Content-Type: application/json

{
    "phone_number": "255616107670",
    "package_id": 1,
    "amount": 150000,
    "name": "John Doe"
}
```

### 3. Initiate Payment (2 Months)
```
POST http://localhost:8000/api/payment/initiate/
Content-Type: application/json

{
    "phone_number": "255616107670",
    "package_id": 2,
    "amount": 250000,
    "name": "John Doe"
}
```

### 4. Initiate Payment (3 Months)
```
POST http://localhost:8000/api/payment/initiate/
Content-Type: application/json

{
    "phone_number": "255616107670",
    "package_id": 3,
    "amount": 500000,
    "name": "John Doe"
}
```

### 5. Verify Payment
```
POST http://localhost:8000/api/payment/verify/
Content-Type: application/json

{
    "transaction_id": "TXNQ5V8K2L9N3XM1"
}
```
*(Replace TXNQ5V8K2L9N3XM1 with actual transaction_id)*

### 6. Payment Status (6 hours)
```
POST http://localhost:8000/api/payment/status/
Content-Type: application/json

{
    "phone_number": "255616107670"
}
```

### 7. Webhook Test
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
