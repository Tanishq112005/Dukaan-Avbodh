from typing import Dict, Any, List, Tuple
from datetime import datetime


def render_signup_otp_email(
    name: str,
    otp: str,
    ttl_minutes: int = 5,
) -> Tuple[str, str, str]:
    """
    Renders Signup OTP Verification email.
    Returns: (subject, html_content, text_content)
    """
    subject = f"Verify your Dukaan account - OTP: {otp}"
    display_name = name or "Customer"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify Your Email</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f6f3; color: #1c1917;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f7f6f3; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e7e5e4; box-shadow: 0 4px 20px rgba(0,0,0,0.04); overflow: hidden;">
          <!-- Header -->
          <tr>
            <td style="background-color: #1c1917; padding: 28px 32px; text-align: center;">
              <span style="font-family: 'Playfair Display', Georgia, serif; font-size: 24px; font-weight: 700; letter-spacing: 2px; color: #ffffff;">DUKAAN</span>
              <p style="margin: 4px 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #d6d3d1;">Autonomous Commerce</p>
            </td>
          </tr>
          
          <!-- Content Body -->
          <tr>
            <td style="padding: 36px 32px 28px;">
              <h1 style="margin: 0 0 12px; font-size: 20px; font-weight: 600; color: #1c1917;">Verify Your Email Address</h1>
              <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.6; color: #57534e;">
                Hello <strong>{display_name}</strong>, thank you for joining Dukaan! Use the 6-digit verification code below to verify your email and activate your account:
              </p>
              
              <!-- OTP Box -->
              <div style="background: #fafaf9; border: 1.5px dashed #d6d3d1; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0;">
                <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #0c0a09;">{otp}</span>
                <p style="margin: 8px 0 0; font-size: 12px; color: #78716c;">
                  Valid for <strong>{ttl_minutes} minutes</strong>
                </p>
              </div>

              <p style="margin: 0 0 16px; font-size: 13px; line-height: 1.5; color: #78716c;">
                If you did not initiate this signup, please ignore this email or reach out to our security team.
              </p>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="background-color: #fafaf9; border-top: 1px solid #f5f5f4; padding: 20px 32px; text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #a8a29e;">
                &copy; {datetime.now().year} Dukaan Luxury Commerce Inc. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text_content = f"""DUKAAN - Autonomous Commerce
=======================================

Verify Your Email Address

Hello {display_name},

Thank you for joining Dukaan! Use the following 6-digit verification code to complete your signup:

Verification Code: {otp}

(This code is valid for {ttl_minutes} minutes. Please do not share it with anyone.)

If you did not initiate this registration, please disregard this message.

(c) {datetime.now().year} Dukaan.
"""
    return subject, html_content, text_content


def render_forgot_password_otp_email(
    name: str,
    otp: str,
    ttl_minutes: int = 5,
) -> Tuple[str, str, str]:
    """
    Renders Forgot Password OTP Verification email.
    Returns: (subject, html_content, text_content)
    """
    subject = f"Reset your Dukaan password - OTP: {otp}"
    display_name = name or "Customer"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset Password</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f6f3; color: #1c1917;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f7f6f3; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e7e5e4; box-shadow: 0 4px 20px rgba(0,0,0,0.04); overflow: hidden;">
          <!-- Header -->
          <tr>
            <td style="background-color: #1c1917; padding: 28px 32px; text-align: center;">
              <span style="font-family: 'Playfair Display', Georgia, serif; font-size: 24px; font-weight: 700; letter-spacing: 2px; color: #ffffff;">DUKAAN</span>
              <p style="margin: 4px 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #d6d3d1;">Security Verification</p>
            </td>
          </tr>
          
          <!-- Content Body -->
          <tr>
            <td style="padding: 36px 32px 28px;">
              <h1 style="margin: 0 0 12px; font-size: 20px; font-weight: 600; color: #1c1917;">Password Reset Request</h1>
              <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.6; color: #57534e;">
                Hello <strong>{display_name}</strong>, we received a request to reset your password. Use the verification code below to authorize your password update:
              </p>
              
              <!-- OTP Box -->
              <div style="background: #fafaf9; border: 1.5px dashed #d6d3d1; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0;">
                <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #b91c1c;">{otp}</span>
                <p style="margin: 8px 0 0; font-size: 12px; color: #78716c;">
                  Expires in <strong>{ttl_minutes} minutes</strong>
                </p>
              </div>

              <p style="margin: 0 0 16px; font-size: 13px; line-height: 1.5; color: #78716c;">
                <strong>Didn't request this?</strong> Your account remains completely safe. Simply disregard this email and no changes will be made to your password.
              </p>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="background-color: #fafaf9; border-top: 1px solid #f5f5f4; padding: 20px 32px; text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #a8a29e;">
                &copy; {datetime.now().year} Dukaan Luxury Commerce Inc. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text_content = f"""DUKAAN - Security Verification
=======================================

Password Reset Request

Hello {display_name},

We received a request to reset the password for your Dukaan account.
Your 6-digit verification code is:

Verification Code: {otp}

(Expires in {ttl_minutes} minutes.)

If you did not request a password reset, please ignore this email.

(c) {datetime.now().year} Dukaan.
"""
    return subject, html_content, text_content


def render_order_confirmation_email(order_data: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Renders comprehensive Order Confirmation invoice slip email.
    Returns: (subject, html_content, text_content)
    """
    order_id = order_data.get("order_id", "N/A")
    customer_name = order_data.get("customer_name") or order_data.get("name") or "Valued Customer"
    currency = order_data.get("currency", "INR")
    curr_symbol = "₹" if currency == "INR" else "$"
    
    total_amount = float(order_data.get("total_amount", 0.0))
    discount_applied = float(order_data.get("discount_applied", 0.0))
    raw_subtotal = float(order_data.get("subtotal", 0.0))
    
    # If subtotal not directly provided, derive from total and discount
    if raw_subtotal <= 0:
        if discount_applied > 0 and discount_applied < 100:
            raw_subtotal = round(total_amount / (1.0 - (discount_applied / 100.0)), 2)
        else:
            raw_subtotal = total_amount

    discount_amount = max(0.0, round(raw_subtotal - total_amount, 2))
    
    items: List[Dict[str, Any]] = order_data.get("items") or []
    shipping_address = order_data.get("shipping_address") or "Standard Shipping Address on File"
    payment_id = order_data.get("gateway_payment_id") or order_data.get("payment_id") or "Completed"
    order_date = order_data.get("order_date") or datetime.now().strftime("%B %d, %Y")

    subject = f"Order Confirmed: #{order_id} - Thank you for shopping with Dukaan"

    # Build items HTML table rows
    items_html = ""
    items_text = ""
    for item in items:
        p_name = item.get("name") or f"Product #{item.get('product_id', '')}"
        p_brand = item.get("brand") or "Dukaan Collection"
        p_qty = item.get("quantity") or 1
        p_price = float(item.get("price") or item.get("total_amount") or 0.0)
        item_total = round(p_price * p_qty, 2)
        p_img = item.get("image_url")

        img_col = ""
        if p_img:
            img_col = f"""<td style="width: 56px; padding: 12px 12px 12px 0;">
                <img src="{p_img}" alt="{p_name}" width="50" height="50" style="border-radius: 8px; object-fit: cover; border: 1px solid #e7e5e4; display: block;" />
            </td>"""

        items_html += f"""
        <tr style="border-bottom: 1px solid #f5f5f4;">
          {img_col}
          <td style="padding: 12px 0; vertical-align: middle;">
            <div style="font-size: 14px; font-weight: 600; color: #1c1917;">{p_name}</div>
            <div style="font-size: 12px; color: #78716c;">{p_brand} &bull; Qty: {p_qty}</div>
          </td>
          <td align="right" style="padding: 12px 0; vertical-align: middle; font-size: 14px; font-weight: 600; color: #1c1917;">
            {curr_symbol}{item_total:,.2f}
          </td>
        </tr>
        """
        items_text += f"- {p_name} ({p_brand}) x {p_qty} @ {curr_symbol}{p_price:,.2f} = {curr_symbol}{item_total:,.2f}\n"

    if not items_html:
        items_html = f"""
        <tr>
          <td colspan="2" style="padding: 16px 0; font-size: 14px; color: #1c1917;">
            Order Items (Reference #{order_id})
          </td>
          <td align="right" style="padding: 16px 0; font-size: 14px; font-weight: 600; color: #1c1917;">
            {curr_symbol}{total_amount:,.2f}
          </td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Order Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7f6f3; color: #1c1917;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f7f6f3; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e7e5e4; box-shadow: 0 4px 20px rgba(0,0,0,0.04); overflow: hidden;">
          
          <!-- Brand Header -->
          <tr>
            <td style="background-color: #1c1917; padding: 30px 36px; text-align: center;">
              <span style="font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; letter-spacing: 2px; color: #ffffff;">DUKAAN</span>
              <p style="margin: 4px 0 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #d6d3d1;">Order Receipt & Confirmation</p>
            </td>
          </tr>

          <!-- Confirmation Banner -->
          <tr>
            <td style="padding: 32px 36px 16px;">
              <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 14px 18px; margin-bottom: 24px;">
                <p style="margin: 0; font-size: 13px; font-weight: 600; color: #065f46;">
                  &check; Payment Successful &bull; Your order is being processed
                </p>
              </div>

              <h1 style="margin: 0 0 8px; font-size: 22px; font-weight: 700; color: #1c1917;">Thank you for your order, {customer_name}!</h1>
              <p style="margin: 0 0 24px; font-size: 14px; line-height: 1.6; color: #57534e;">
                We've received your payment and our team is preparing your package for dispatch. Here is your official order receipt slip:
              </p>

              <!-- Order Metadata Grid -->
              <table role="presentation" width="100%" style="background-color: #fafaf9; border-radius: 12px; border: 1px solid #e7e5e4; padding: 16px; margin-bottom: 28px;">
                <tr>
                  <td style="padding: 6px 12px; font-size: 12px; color: #78716c;">
                    <strong>Order Number:</strong> #{order_id}
                  </td>
                  <td align="right" style="padding: 6px 12px; font-size: 12px; color: #78716c;">
                    <strong>Date:</strong> {order_date}
                  </td>
                </tr>
                <tr>
                  <td style="padding: 6px 12px; font-size: 12px; color: #78716c;">
                    <strong>Payment ID:</strong> {payment_id}
                  </td>
                  <td align="right" style="padding: 6px 12px; font-size: 12px; color: #15803d; font-weight: 600;">
                    STATUS: PAID
                  </td>
                </tr>
              </table>

              <!-- Purchased Items -->
              <h2 style="margin: 0 0 12px; font-size: 16px; font-weight: 600; color: #1c1917; text-transform: uppercase; letter-spacing: 0.5px;">Order Items</h2>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
                {items_html}
              </table>

              <!-- Cost Breakdown / Slip -->
              <div style="background-color: #fafaf9; border-radius: 12px; border: 1px solid #e7e5e4; padding: 20px; margin-bottom: 28px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="4">
                  <tr>
                    <td style="font-size: 13px; color: #57534e;">Subtotal</td>
                    <td align="right" style="font-size: 13px; font-weight: 500; color: #1c1917;">{curr_symbol}{raw_subtotal:,.2f}</td>
                  </tr>
                  <tr>
                    <td style="font-size: 13px; color: #15803d;">Discount Applied {f"({discount_applied:.0f}%)" if discount_applied else ""}</td>
                    <td align="right" style="font-size: 13px; font-weight: 600; color: #15803d;">-{curr_symbol}{discount_amount:,.2f}</td>
                  </tr>
                  <tr>
                    <td style="font-size: 13px; color: #57534e;">Shipping</td>
                    <td align="right" style="font-size: 13px; font-weight: 600; color: #15803d;">FREE</td>
                  </tr>
                  <tr>
                    <td colspan="2" style="padding: 8px 0 4px;"><hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 0;"></td>
                  </tr>
                  <tr>
                    <td style="font-size: 16px; font-weight: 700; color: #0c0a09;">Total Paid</td>
                    <td align="right" style="font-size: 18px; font-weight: 800; color: #0c0a09;">{curr_symbol}{total_amount:,.2f}</td>
                  </tr>
                </table>
              </div>

              <!-- Shipping Info -->
              <div style="margin-bottom: 24px; padding: 16px; border: 1px solid #e7e5e4; border-radius: 10px;">
                <h3 style="margin: 0 0 6px; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #78716c;">Delivery Address</h3>
                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #1c1917;">{shipping_address}</p>
              </div>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #fafaf9; border-top: 1px solid #f5f5f4; padding: 24px 36px; text-align: center;">
              <p style="margin: 0 0 6px; font-size: 12px; color: #78716c;">
                Need help with your order? Reply directly to this email or chat with our 24/7 AI Stylist Assistant on the store.
              </p>
              <p style="margin: 0; font-size: 11px; color: #a8a29e;">
                &copy; {datetime.now().year} Dukaan Luxury Commerce Inc. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text_content = f"""DUKAAN - Order Confirmation & Receipt Slip
===================================================

Thank you for your order, {customer_name}!
Order ID: #{order_id}
Date: {order_date}
Payment Status: PAID (Reference: {payment_id})

Purchased Items:
{items_text}

Pricing Breakdown:
---------------------------------------------------
Subtotal: {curr_symbol}{raw_subtotal:,.2f}
Discount Applied: -{curr_symbol}{discount_amount:,.2f}
Shipping: FREE
TOTAL PAID: {curr_symbol}{total_amount:,.2f}

Delivery Address:
{shipping_address}

Thank you for shopping with Dukaan!
(c) {datetime.now().year} Dukaan Luxury Commerce.
"""
    return subject, html_content, text_content
