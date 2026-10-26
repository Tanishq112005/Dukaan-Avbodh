import sys
import os
import asyncio
import random
from pathlib import Path

# Ensure backend root is on sys.path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from Notification import (
    notificationService,
    render_signup_otp_email,
    render_forgot_password_otp_email,
    render_order_confirmation_email,
)
from rabbitmq import rabbitProducer
from Auth.otp import otpService, generate_otp
from Auth.controller import authController
from Auth.schemas import (
    SignupRequest,
    VerifySignupOtpRequest,
    ForgotPasswordRequest,
    VerifyForgotPasswordOtpRequest,
    ResetPasswordRequest,
    LoginRequest,
)
from Order.models import Order as OrderModel, PaymentStatus
from Order.notifications import enqueue_order_confirmation_notification


async def test_notification_templates():
    # 1. Signup OTP template
    subj1, html1, text1 = render_signup_otp_email("Jane Doe", "554433", ttl_minutes=5)
    assert "554433" in subj1
    assert "554433" in html1
    assert "5 minutes" in html1

    # 2. Forgot Password OTP template
    subj2, html2, text2 = render_forgot_password_otp_email("Jane Doe", "998877", ttl_minutes=5)
    assert "998877" in subj2
    assert "998877" in html2
    assert "Reset your Dukaan password" in subj2

    # 3. Order confirmation slip template
    sample_order = {
        "order_id": 404,
        "customer_name": "Jane Doe",
        "total_amount": 3200.0,
        "discount_applied": 20.0,
        "subtotal": 4000.0,
        "currency": "INR",
        "shipping_address": "123 Fashion Street, Mumbai",
        "gateway_payment_id": "pay_test_abc123",
        "items": [
            {
                "product_id": 10,
                "name": "Luxury Silk Robe",
                "brand": "Dukaan Couture",
                "quantity": 1,
                "price": 4000.0,
            }
        ],
    }
    subj3, html3, text3 = render_order_confirmation_email(sample_order)
    assert "404" in subj3
    assert "Luxury Silk Robe" in html3
    assert "3,200.00" in html3
    assert "123 Fashion Street" in html3


async def test_redis_otp_service():
    test_id = f"test_{random.randint(10000, 99999)}@example.com"
    otp = generate_otp(6)
    assert len(otp) == 6
    assert otp.isdigit()

    # Store OTP
    saved = otpService.store_otp("unit_test", test_id, otp, {"test": True}, ttl_seconds=60)
    assert saved is True

    # Failed attempt
    ok, msg, _ = otpService.verify_otp("unit_test", test_id, "000000", delete_on_success=False)
    assert ok is False
    assert "Incorrect" in msg

    # Correct attempt
    ok2, msg2, extra = otpService.verify_otp("unit_test", test_id, otp, delete_on_success=True)
    assert ok2 is True
    assert extra.get("test") is True

    # Re-verify should fail since deleted on success
    ok3, msg3, _ = otpService.verify_otp("unit_test", test_id, otp)
    assert ok3 is False


async def test_auth_otp_flow_and_password_reset():
    rand_int = random.randint(10000, 99999)
    email = f"authtest_{rand_int}@dukaan-test.com"
    initial_pass = "FirstPass#123"
    updated_pass = "UpdatedSecret#456"

    # Step 1: Request Signup OTP
    signup_req = SignupRequest(name="Auto Tester", email=email, password=initial_pass)
    signup_init = await authController.request_signup_otp(signup_req)
    assert signup_init["success"] is True

    # Retrieve OTP directly from Redis for automated verification
    info = otpService.get_otp_info("signup", email)
    assert info is not None
    otp_code = info["otp"]

    # Step 2: Verify Signup OTP
    ver_req = VerifySignupOtpRequest(email=email, otp=otp_code)
    ver_res = await authController.verify_signup_otp(ver_req)
    assert ver_res.status_code == 201

    # Step 3: Request Forgot Password OTP
    fp_req = ForgotPasswordRequest(email=email)
    fp_res = await authController.request_forgot_password_otp(fp_req)
    assert fp_res["success"] is True

    # Retrieve FP OTP from Redis
    fp_info = otpService.get_otp_info("forgot_password", email)
    assert fp_info is not None
    fp_otp = fp_info["otp"]

    # Step 4: Verify Forgot Password OTP
    vfp_req = VerifyForgotPasswordOtpRequest(email=email, otp=fp_otp)
    vfp_res = await authController.verify_forgot_password_otp(vfp_req)
    assert vfp_res["success"] is True
    reset_token = vfp_res["reset_token"]
    assert len(reset_token) > 10

    # Step 5: Reset Password
    rp_req = ResetPasswordRequest(email=email, new_password=updated_pass, reset_token=reset_token)
    rp_res = await authController.reset_password(rp_req)
    assert rp_res["success"] is True

    # Step 6: Log in with new credentials
    login_req = LoginRequest(email=email, password=updated_pass)
    login_res = await authController.login(login_req)
    assert login_res["email"] == email
    assert "access_token" in login_res


async def test_order_notification_enqueueing():
    dummy_order = OrderModel(
        id=777,
        product_id=1,
        user_id=1,
        quantity=3,
        total_amount=5499.0,
        discount_applied=10.0,
        payment_status=PaymentStatus.PAID,
        gateway_payment_id="pay_automated_test",
    )
    res = await enqueue_order_confirmation_notification(
        orders=[dummy_order],
        customer_email="verified_shopper@example.com",
        customer_name="Shopper",
        shipping_address="45 Marine Drive, Mumbai",
    )
    assert res is True


async def run_all_tests():
    print("--> [1/4] Running test_notification_templates...")
    await test_notification_templates()
    print("    [PASS] test_notification_templates")

    print("--> [2/4] Running test_redis_otp_service...")
    await test_redis_otp_service()
    print("    [PASS] test_redis_otp_service")

    print("--> [3/4] Running test_auth_otp_flow_and_password_reset...")
    await test_auth_otp_flow_and_password_reset()
    print("    [PASS] test_auth_otp_flow_and_password_reset")

    print("--> [4/4] Running test_order_notification_enqueueing...")
    await test_order_notification_enqueueing()
    print("    [PASS] test_order_notification_enqueueing")

    print("\n=======================================================")
    print("  ALL 4 INTEGRATION TEST SUITES PASSED SUCCESSFULLY!")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
