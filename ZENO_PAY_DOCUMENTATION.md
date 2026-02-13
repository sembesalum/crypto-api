# Zeno Pay Integration Documentation

This documentation provides all the configuration details and implementation patterns for integrating Zeno Pay (Zeno Africa) payment gateway in your PHP project.

## Table of Contents
1. [Configuration Parameters](#configuration-parameters)
2. [API Endpoint](#api-endpoint)
3. [Payment Initiation](#payment-initiation)
4. [Webhook Handling](#webhook-handling)
5. [PHP Implementation Examples](#php-implementation-examples)

---

## Configuration Parameters

### Required Credentials

```php
// Zeno Pay Configuration
define('ZENO_API_URL', 'https://api.zeno.africa');
define('ZENO_ACCOUNT_ID', 'zp04692');
define('ZENO_API_KEY', '77fb7aca50600ecfaa254234f122191e');
define('ZENO_SECRET_KEY', '347196786218b91d50f76b474598d19b74952e398f4dc209fb474598d19b74952e398');
```

### Configuration Details

| Parameter | Value | Description |
|-----------|-------|-------------|
| **ZENO_API_URL** | `https://api.zeno.africa` | Base URL for Zeno Africa API |
| **ZENO_ACCOUNT_ID** | `zp04692` | Your Zeno account identifier |
| **ZENO_API_KEY** | `77fb7aca50600ecfaa254234f122191e` | API key for authentication |
| **ZENO_SECRET_KEY** | `347196786218b91d50f76b474598d19b74952e398f4dc209fb474598d19b74952e398` | Secret key for secure requests |

---

## API Endpoint

**Base URL:** `https://api.zeno.africa`

**Method:** `POST`

**Content-Type:** `application/x-www-form-urlencoded`

**Timeout:** 10 seconds (recommended)

---

## Payment Initiation

### Request Format

To initiate a payment, send a POST request to the Zeno API URL with the following parameters:

#### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `create_order` | string | Must be set to `"1"` to create an order | `"1"` |
| `buyer_email` | string | Buyer's email address | `"255712345678@forexbot.com"` |
| `buyer_name` | string | Buyer's full name | `"John Doe"` |
| `buyer_phone` | string | Buyer's phone number (with country code) | `"255712345678"` |
| `amount` | string | Payment amount (as string) | `"150000"` |
| `account_id` | string | Your Zeno account ID | `"zp04692"` |
| `api_key` | string | Your Zeno API key | `"77fb7aca50600ecfaa254234f122191e"` |
| `secret_key` | string | Your Zeno secret key | `"347196786218b91d50f76b474598d19b74952e398f4dc209fb474598d19b74952e398"` |

#### Optional Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `currency` | string | Currency code (default: TZS) | `"TZS"` |
| `payment_method` | string | Payment method preference | `"ussd"` |

### Request Example

```php
$payload = [
    'create_order' => '1',
    'buyer_email' => '255712345678@forexbot.com',
    'buyer_name' => 'John Doe',
    'buyer_phone' => '255712345678',
    'amount' => '150000',
    'account_id' => ZENO_ACCOUNT_ID,
    'api_key' => ZENO_API_KEY,
    'secret_key' => ZENO_SECRET_KEY,
    'currency' => 'TZS',
    'payment_method' => 'ussd'
];
```

### Response Format

#### Success Response

```json
{
    "status": "success",
    "message": "Order created successfully",
    "order_id": "ORDER123456",
    "payment_url": "https://..."
}
```

#### Error Response

```json
{
    "status": "error",
    "message": "Error description here"
}
```

### HTTP Status Codes

- `200` - Request successful (check `status` field in response body)
- `400` - Bad request
- `401` - Unauthorized
- `500` - Server error

---

## Webhook Handling

Zeno Pay sends payment status updates to your webhook endpoint when payment status changes.

### Webhook Endpoint

**URL Pattern:** `https://yourdomain.com/zeno-webhook/`

**Method:** `POST`

**Content-Type:** `application/json`

### Webhook Payload Structure

```json
{
    "status": "success",
    "buyer_phone": "255712345678",
    "amount": "150000",
    "order_id": "ORDER123456",
    "transaction_id": "TXN789012",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Webhook Response

Your webhook endpoint should return:

- **Success:** HTTP `200 OK` with response body `"OK"`
- **Error:** HTTP `400` or `500` with error message

### Webhook Status Values

| Status | Description |
|--------|-------------|
| `success` | Payment completed successfully |
| `pending` | Payment is being processed |
| `failed` | Payment failed |
| `cancelled` | Payment was cancelled |

---

## PHP Implementation Examples

### 1. Configuration Class

```php
<?php
// config/ZenoConfig.php

class ZenoConfig {
    const API_URL = 'https://api.zeno.africa';
    const ACCOUNT_ID = 'zp04692';
    const API_KEY = '77fb7aca50600ecfaa254234f122191e';
    const SECRET_KEY = '347196786218b91d50f76b474598d19b74952e398f4dc209fb474598d19b74952e398';
    const CURRENCY = 'TZS';
    const PAYMENT_METHOD = 'ussd';
    const REQUEST_TIMEOUT = 10;
}
```

### 2. Payment Initiation Service

```php
<?php
// services/ZenoPaymentService.php

require_once 'config/ZenoConfig.php';

class ZenoPaymentService {
    
    /**
     * Initiate a payment with Zeno Pay
     * 
     * @param string $buyerPhone Phone number with country code (e.g., "255712345678")
     * @param string $buyerName Buyer's full name
     * @param float|int $amount Payment amount
     * @param string|null $buyerEmail Optional email (defaults to phone@forexbot.com)
     * @return array Response data from Zeno API
     * @throws Exception If payment initiation fails
     */
    public static function initiatePayment(
        string $buyerPhone,
        string $buyerName,
        $amount,
        ?string $buyerEmail = null
    ): array {
        // Generate email if not provided
        if (!$buyerEmail) {
            $buyerEmail = $buyerPhone . '@forexbot.com';
        }
        
        // Prepare payload
        $payload = [
            'create_order' => '1',
            'buyer_email' => $buyerEmail,
            'buyer_name' => $buyerName,
            'buyer_phone' => $buyerPhone,
            'amount' => (string)$amount,
            'account_id' => ZenoConfig::ACCOUNT_ID,
            'api_key' => ZenoConfig::API_KEY,
            'secret_key' => ZenoConfig::SECRET_KEY,
            'currency' => ZenoConfig::CURRENCY,
            'payment_method' => ZenoConfig::PAYMENT_METHOD
        ];
        
        // Initialize cURL
        $ch = curl_init(ZenoConfig::API_URL);
        
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => http_build_query($payload),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => ZenoConfig::REQUEST_TIMEOUT,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/x-www-form-urlencoded'
            ]
        ]);
        
        // Execute request
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        // Handle cURL errors
        if ($error) {
            throw new Exception("cURL Error: " . $error);
        }
        
        // Handle HTTP errors
        if ($httpCode !== 200) {
            throw new Exception("HTTP Error {$httpCode}: {$response}");
        }
        
        // Parse JSON response
        $data = json_decode($response, true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception("Invalid JSON response: " . json_last_error_msg());
        }
        
        return $data;
    }
    
    /**
     * Check if payment was successful
     * 
     * @param array $response Response from initiatePayment()
     * @return bool
     */
    public static function isPaymentSuccessful(array $response): bool {
        return isset($response['status']) && $response['status'] === 'success';
    }
}
```

### 3. Webhook Handler

```php
<?php
// webhooks/zeno_webhook.php

require_once '../config/ZenoConfig.php';
require_once '../services/ZenoPaymentService.php';

/**
 * Zeno Pay Webhook Handler
 * 
 * This endpoint receives payment status updates from Zeno Africa
 * URL: https://yourdomain.com/webhooks/zeno_webhook.php
 */

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo 'Method not allowed';
    exit;
}

try {
    // Get raw POST data
    $rawData = file_get_contents('php://input');
    
    // Log webhook data (for debugging)
    error_log("Zeno Webhook Received: " . $rawData);
    
    // Parse JSON payload
    $data = json_decode($rawData, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception("Invalid JSON: " . json_last_error_msg());
    }
    
    // Verify payment status
    if (isset($data['status']) && $data['status'] === 'success') {
        $phoneNumber = $data['buyer_phone'] ?? null;
        $amount = isset($data['amount']) ? (int)$data['amount'] : null;
        $orderId = $data['order_id'] ?? null;
        $transactionId = $data['transaction_id'] ?? null;
        
        if (!$phoneNumber || !$amount) {
            throw new Exception("Missing required fields: buyer_phone or amount");
        }
        
        // Process successful payment
        processSuccessfulPayment($phoneNumber, $amount, $orderId, $transactionId);
    }
    
    // Always return 200 OK to acknowledge receipt
    http_response_code(200);
    echo 'OK';
    
} catch (Exception $e) {
    error_log("Webhook error: " . $e->getMessage());
    http_response_code(400);
    echo 'Error';
}

/**
 * Process successful payment
 * 
 * @param string $phoneNumber Buyer's phone number
 * @param int $amount Payment amount
 * @param string|null $orderId Order ID from Zeno
 * @param string|null $transactionId Transaction ID from Zeno
 */
function processSuccessfulPayment(
    string $phoneNumber,
    int $amount,
    ?string $orderId = null,
    ?string $transactionId = null
): void {
    // TODO: Implement your business logic here
    // Examples:
    // - Update user payment status in database
    // - Activate user subscription
    // - Send confirmation notification
    // - Log transaction
    
    error_log("Processing payment for {$phoneNumber}: Amount {$amount}, Order: {$orderId}");
    
    // Example: Update database
    // $db = new PDO(...);
    // $stmt = $db->prepare("UPDATE users SET payment_status = 'paid', payment_date = NOW() WHERE phone = ?");
    // $stmt->execute([$phoneNumber]);
}
```

### 4. Complete Usage Example

```php
<?php
// examples/payment_example.php

require_once '../services/ZenoPaymentService.php';

try {
    // Initiate payment
    $response = ZenoPaymentService::initiatePayment(
        buyerPhone: '255712345678',
        buyerName: 'John Doe',
        amount: 150000,
        buyerEmail: 'john@example.com' // Optional
    );
    
    // Check if successful
    if (ZenoPaymentService::isPaymentSuccessful($response)) {
        echo "Payment initiated successfully!\n";
        echo "Order ID: " . ($response['order_id'] ?? 'N/A') . "\n";
        echo "Payment URL: " . ($response['payment_url'] ?? 'N/A') . "\n";
        
        // Save order_id to database for tracking
        // $orderId = $response['order_id'];
        // saveOrderToDatabase($orderId, $phoneNumber, $amount);
        
    } else {
        $errorMessage = $response['message'] ?? 'Unknown error';
        echo "Payment failed: {$errorMessage}\n";
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
```

### 5. Phone Number Formatting Helper

```php
<?php
// utils/PhoneFormatter.php

class PhoneFormatter {
    /**
     * Format phone number for Zeno Pay
     * Removes spaces, dashes, and ensures country code format
     * 
     * @param string $phoneNumber Raw phone number
     * @return string Formatted phone number
     */
    public static function formatForZeno(string $phoneNumber): string {
        // Remove all non-digit characters
        $cleaned = preg_replace('/[^0-9]/', '', $phoneNumber);
        
        // If starts with 0, replace with country code (255 for Tanzania)
        if (substr($cleaned, 0, 1) === '0') {
            $cleaned = '255' . substr($cleaned, 1);
        }
        
        // If doesn't start with country code, add it
        if (substr($cleaned, 0, 3) !== '255') {
            $cleaned = '255' . $cleaned;
        }
        
        return $cleaned;
    }
}

// Usage
$phone = PhoneFormatter::formatForZeno('0712 345 678'); // Returns: 255712345678
```

---

## Security Best Practices

1. **Store Credentials Securely**
   - Never commit credentials to version control
   - Use environment variables or secure configuration files
   - Restrict file permissions on config files

2. **Validate Webhook Data**
   - Verify webhook payload structure
   - Validate phone numbers and amounts
   - Check for duplicate transactions

3. **Error Handling**
   - Always use try-catch blocks
   - Log errors for debugging
   - Return appropriate HTTP status codes

4. **HTTPS Only**
   - Always use HTTPS for webhook endpoints
   - Verify SSL certificates

---

## Testing

### Test Payment Flow

1. Use test credentials (if provided by Zeno)
2. Test with small amounts first
3. Verify webhook receives callbacks
4. Test error scenarios (invalid phone, insufficient funds, etc.)

### Webhook Testing

You can test webhooks locally using tools like:
- **ngrok** - Expose local server to internet
- **Postman** - Send test webhook payloads
- **Zeno Dashboard** - If webhook testing is available

---

## Troubleshooting

### Common Issues

1. **Payment Not Initiating**
   - Verify all credentials are correct
   - Check phone number format (must include country code)
   - Ensure amount is sent as string

2. **Webhook Not Receiving Callbacks**
   - Verify webhook URL is publicly accessible
   - Check webhook endpoint returns 200 OK
   - Verify webhook URL is configured in Zeno dashboard

3. **Invalid Response Format**
   - Check Content-Type header is correct
   - Verify JSON parsing
   - Log raw response for debugging

---

## Support

For Zeno Pay API support:
- **API Documentation:** Check Zeno Africa official documentation
- **Support Email:** Contact Zeno Africa support team
- **Dashboard:** Access your Zeno account dashboard for transaction logs

---

## Notes

- All amounts should be sent as **strings** (not integers)
- Phone numbers must include **country code** (e.g., 255 for Tanzania)
- Webhook endpoint must be **publicly accessible** (HTTPS recommended)
- Always return **200 OK** to webhook requests to acknowledge receipt
- Currency defaults to **TZS** (Tanzanian Shilling) if not specified

---

**Last Updated:** Based on implementation in forex-bot project
**Version:** 1.0

