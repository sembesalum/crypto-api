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

### 1. Check User Status
Check if a user exists and their subscription status.

**Endpoint:** `GET /api/user/status/{phone_number}/`

**Example:**
```bash
curl http://localhost:8000/api/user/status/255712345678/
```

**Response:**
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

### 2. Initiate Payment
Initiate a payment with Biashara Pay. Creates user automatically if they don't exist.

**Endpoint:** `POST /api/payment/initiate/`

**Request Body:**
```json
{
    "phone_number": "255712345678",
    "amount": 150000,
    "name": "John Doe",
    "email": "john@example.com"  // optional
}
```

**Valid Amounts:**
- `150000` - 1 month package
- `250000` - 2 months package
- `500000` - 3 months package

**Example:**
```bash
curl -X POST http://localhost:8000/api/payment/initiate/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "255712345678",
    "amount": 150000,
    "name": "John Doe"
  }'
```

**Response:**
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

### 3. Verify Payment
Verify a payment transaction with Biashara Pay.

**Endpoint:** `GET /api/payment/verify/{transaction_id}/`

**Example:**
```bash
curl http://localhost:8000/api/payment/verify/TXNQ5V8K2L9N3XM1/
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

### 4. Biashara Pay Webhook
Webhook endpoint for Biashara Pay payment callbacks (IPN). This endpoint is called by Biashara Pay when payment status changes.

**Endpoint:** `POST /api/webhook/biashara/`

**Note:** Configure this URL (`https://yourdomain.com/api/webhook/biashara/`) in your Biashara Pay dashboard as the IPN URL.

## Package Types

- **1 month** - Tsh 150,000
- **2 months** - Tsh 250,000
- **3 months** - Tsh 500,000

## Features

- ✅ Automatic user creation on payment initiation
- ✅ Phone number-based authentication
- ✅ Subscription status tracking (active/inactive)
- ✅ Automatic subscription extension if user already has active subscription
- ✅ Amount validation (only accepts valid package prices)
- ✅ Biashara Pay integration
- ✅ Payment verification endpoint
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

1. Check user status (should return exists: false for new number)
2. Initiate payment with valid amount
3. Complete payment via Biashara Pay payment URL
4. Verify payment using transaction ID
5. Webhook will automatically activate user subscription
6. Check user status again (should show is_active: true)
