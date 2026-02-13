# Crypto API - Subscription Management with Zeno Pay

Django REST API for managing user subscriptions with Zeno Pay payment integration.

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

5. **Run development server:**
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
Initiate a payment with Zeno Pay. Creates user automatically if they don't exist.

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
    "order_id": "ORDER123456",
    "payment_url": "https://...",
    "phone_number": "255712345678",
    "amount": 150000,
    "package_type": 1
}
```

### 3. Zeno Pay Webhook
Webhook endpoint for Zeno Pay payment callbacks. This endpoint is called by Zeno Pay when payment status changes.

**Endpoint:** `POST /api/webhook/zeno/`

**Note:** Configure this URL in your Zeno Pay dashboard.

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
- ✅ Zeno Pay integration
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
- `order_id` (from Zeno Pay)
- `transaction_id` (from Zeno Pay)
- `created_at`, `updated_at`

## Configuration

Zeno Pay credentials are configured in `cryptoapi/settings.py`. For production, use environment variables via `.env` file.

## Testing

1. Check user status (should return exists: false for new number)
2. Initiate payment with valid amount
3. Complete payment via Zeno Pay
4. Webhook will automatically activate user subscription
5. Check user status again (should show is_active: true)
