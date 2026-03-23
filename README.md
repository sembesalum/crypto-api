# Crypto API - Subscription Management with Biashara Pay

Django REST API for managing user subscriptions with Biashara Pay payment integration.

## Setup

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies (if needed):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Configure environment variables:**
   Create a `.env` file with your Biashara Pay credentials:
   ```env
   BIASHARA_API_URL=https://Biasharapay.com/api/v1
   BIASHARA_ENVIRONMENT=sandbox  # or 'production' for live
   BIASHARA_MERCHANT_KEY=test_merchant_key  # Use 'test_' prefix for sandbox
   BIASHARA_API_KEY=test_api_key  # Use 'test_' prefix for sandbox
   BASE_URL=http://localhost:8000  # Your base URL for webhooks
   ```

6. **Run development server:**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

All public subscription endpoints use **POST** with `Content-Type: application/json`.

### 1. Check / Register User (status)

Check subscription state and **create the user** if the phone number is new (jina la msingi kwenye DB ni namba yenyewe). Responses include a Kiswahili `message` for clients (for example WhatsApp bots).

**Endpoint:** `POST /api/user/status/`

**Request body:**
```json
{
    "phone_number": "255616107670"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/user/status/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "255616107670"}'
```

**Response (example):**
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

### 2. Initiate Payment

Initiate a payment with Biashara Pay. Creates the user automatically if they do not exist. You must send **`package_id`** and **`amount`** together; the amount must match the configured price for that package.

**Endpoint:** `POST /api/payment/initiate/`

**Request body:**
```json
{
    "phone_number": "255616107670",
    "package_id": 1,
    "amount": 150000,
    "name": "John Doe",
    "email": "john@example.com"
}
```

`name` and `email` are optional; if omitted, defaults are derived from the phone number.

**Valid packages (`package_id` → amount):**
- `1` → `150000` (1 month)
- `2` → `250000` (2 months)
- `3` → `500000` (3 months)

**Example:**
```bash
curl -X POST http://localhost:8000/api/payment/initiate/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "255616107670",
    "package_id": 1,
    "amount": 150000,
    "name": "John Doe"
  }'
```

**Response:**
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

### 3. Verify Payment

Verify a payment transaction with Biashara Pay. On success, the user subscription may be activated when the response can be matched to an existing order.

**Endpoint:** `POST /api/payment/verify/`

**Request body:**
```json
{
    "transaction_id": "TXNQ5V8K2L9N3XM1"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/payment/verify/ \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "TXNQ5V8K2L9N3XM1"}'
```

**Response:**
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

### 4. Payment Status (last 6 hours)

Check whether a **completed** payment was recorded for this phone number within the **last 6 hours** (uses `last_successful_payment_at` set when subscription is activated via verify or webhook).

**Endpoint:** `POST /api/payment/status/`

**Request body:**
```json
{
    "phone_number": "255616107670"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/payment/status/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "255616107670"}'
```

**Response:**
```json
{
    "exists": true,
    "paid_within_6_hours": true,
    "message": "Hongera malipo yamekamilika sasa unaweza kupata signal zetu kila siku.",
    "phone_number": "255712345678"
}
```

### 5. Biashara Pay Webhook

Webhook endpoint for Biashara Pay payment callbacks (IPN). This endpoint is called by Biashara Pay when payment status changes.

**Endpoint:** `POST /api/webhook/biashara/`

**Note:** Configure this URL (`https://yourdomain.com/api/webhook/biashara/`) in your Biashara Pay dashboard as the IPN URL.

## Package Types

- **package_id 1** — Tsh 150,000 (1 month)
- **package_id 2** — Tsh 250,000 (2 months)
- **package_id 3** — Tsh 500,000 (3 months)

## Features

- ✅ Check / register user by phone only (`POST /api/user/status/`)
- ✅ Automatic user creation on payment initiation
- ✅ Phone number-based identification
- ✅ Subscription status tracking (active/inactive)
- ✅ Automatic subscription extension if user already has an active subscription
- ✅ `package_id` and matching amount validation
- ✅ Kiswahili `message` fields on key user and payment flows
- ✅ Biashara Pay integration
- ✅ Payment verification (`POST /api/payment/verify/`)
- ✅ Recent payment check (`POST /api/payment/status/`)
- ✅ Webhook handling for payment confirmations

## Database Model

The `User` model includes:
- `phone_number` (primary key)
- `name`
- `email`
- `is_active` (boolean)
- `subscription_start_date`
- `subscription_end_date`
- `package_type` (1, 2, or 3)
- `order_id` (transaction reference from Biashara Pay)
- `transaction_id` (transaction ID from Biashara Pay)
- `last_successful_payment_at` (set when a payment completes and subscription is activated)
- `created_at`, `updated_at`

## Configuration

Biashara Pay credentials are configured in `cryptoapi/settings.py` and can be overridden via environment variables in `.env` file.

### Environment Variables

- `BIASHARA_API_URL` - API base URL (default: `https://Biasharapay.com/api/v1`)
- `BIASHARA_ENVIRONMENT` - Environment mode: `sandbox` or `production`
- `BIASHARA_MERCHANT_KEY` - Your merchant key (use `test_` prefix for sandbox)
- `BIASHARA_API_KEY` - Your API key (use `test_` prefix for sandbox)
- `BASE_URL` - Your base URL for webhook callbacks

## Biashara Pay Integration

This API integrates with [Biashara Pay](https://biasharapay.com/api-docs) payment gateway:

- **Payment Initiation**: Creates payment requests and returns payment URLs
- **Payment Verification**: Verifies payment status using transaction IDs
- **Webhook Handling**: Receives IPN callbacks for payment status updates

### Sandbox vs Production

- **Sandbox**: Use for testing. Credentials must have `test_` prefix
- **Production**: Use for live payments. Credentials have no prefix

## Testing

1. `POST /api/user/status/` with `phone_number` only (new numbers get an account created; `name` defaults to the phone).
2. `POST /api/payment/initiate/` with `phone_number`, `package_id`, matching `amount`, and optional `name`.
3. Complete payment via the Biashara Pay `payment_url`.
4. Optionally `POST /api/payment/verify/` with `transaction_id`.
5. The webhook activates the subscription when Biashara Pay calls your IPN URL.
6. `POST /api/payment/status/` with `phone_number` to confirm a completed payment in the last 6 hours.
7. `POST /api/user/status/` again with the same `phone_number`; expect `is_active: true` after a successful payment flow.

For Postman examples and a ready-to-import collection, see [POSTMAN_TESTING.md](POSTMAN_TESTING.md).
