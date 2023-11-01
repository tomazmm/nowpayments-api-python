"""Testing Module"""
import json
import os

import dotenv
import pytest
from pytest_mock.plugin import MockerFixture
from requests.exceptions import HTTPError

from nowpayments import NOWPayments, NowPaymentsException

config = dotenv.dotenv_values()


@pytest.fixture
def now_payments_api_key() -> NOWPayments:
    """
    NOWPayments class fixture.
    :return: NOWPayments class.
    """
    return NOWPayments(api_key=config["API_KEY"], sandbox=True)


@pytest.fixture
def now_payments_email_password() -> NOWPayments:
    """
    NOWPayments class fixture.
    :return: NOWPayments class.
    """
    return NOWPayments(
        api_key=config["API_KEY"],
        email=config["EMAIL"],
        password=config["PASSWORD"],
        sandbox=True)


def test_initialization() -> None:
    # Init just with Api key
    now_payments = NOWPayments(api_key=config["API_KEY"])
    assert now_payments.sandbox is False
    assert now_payments.api_uri == "https://api.nowpayments.io/v1/"
    assert now_payments._api_key == config["API_KEY"]
    assert now_payments._email == ""
    assert now_payments._password == ""
    # Init with additional email and password
    now_payments = NOWPayments(api_key=config["API_KEY"], email=config["EMAIL"], password=config["PASSWORD"])
    assert now_payments.sandbox is False
    assert now_payments.api_uri == "https://api.nowpayments.io/v1/"
    assert now_payments._api_key == config["API_KEY"]
    assert now_payments._email == config["EMAIL"]
    assert now_payments._password == config["PASSWORD"]
    # Create a sandbox instance with API key only
    now_payments = NOWPayments(api_key=config["API_KEY"], sandbox=True)
    assert now_payments.sandbox is True
    assert now_payments.api_uri == "https://api-sandbox.nowpayments.io/v1/"
    assert now_payments._api_key == config["API_KEY"]
    assert now_payments._email == ""
    assert now_payments._password == ""
    # Create a sandbox instance with all parameters
    now_payments = NOWPayments(api_key=config["API_KEY"], email=config["EMAIL"], password=config["PASSWORD"],
                               sandbox=True)
    assert now_payments.sandbox is True
    assert now_payments.api_uri == "https://api-sandbox.nowpayments.io/v1/"
    assert now_payments._api_key == config["API_KEY"]
    assert now_payments._email == config["EMAIL"]
    assert now_payments._password == config["PASSWORD"]


# -------------------------
# Auth and API status
# -------------------------
def test_get_api_status(now_payments_api_key: NOWPayments) -> None:
    assert now_payments_api_key.get_api_status() == {"message": "OK"}


def test_auth(now_payments_email_password: NOWPayments) -> None:
    payload = now_payments_email_password.auth()
    assert "token" in payload


def test_email_and_password_missing_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Email and password are missing"):
        assert now_payments_api_key.auth()


# -------------------------
# Payments
# -------------------------
def test_get_estimated_price(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_estimated_price(500, "usd", "btc")
    assert response["amount_from"] == 500
    assert response["currency_from"] == "usd"
    assert response["currency_to"] == "btc"
    assert "estimated_amount" in response


def test_amount_greater_than_zero_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Amount must be greater than 0"):
        now_payments_api_key.get_estimated_price(0, "usd", "btc")


def test_unsupported_fiat_currency_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Unsupported fiat currency"):
        now_payments_api_key.get_estimated_price(1, "ustr", "btc")


def test_unsupported_cryptocurrency_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Unsupported cryptocurrency"):
        now_payments_api_key.get_estimated_price(1, "usd", "btccc")


def test_create_payment(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.create_payment(100, price_currency="usd", pay_currency="btc")
    assert "payment_id" in response
    assert response["payment_status"] == "waiting"
    assert "pay_address" in response
    assert response["price_amount"] == 100
    assert response["price_currency"] == "usd"
    assert "pay_amount" in response
    assert response["pay_currency"] == "btc"
    assert "order_id" in response
    assert "order_description" in response
    assert "ipn_callback_url" in response
    assert "created_at" in response
    assert "updated_at" in response
    assert "purchase_id" in response
    assert "amount_received" in response
    assert "payin_extra_id" in response  # BUG: Probably a typo
    assert "smart_contract" in response
    assert "network" in response
    assert "network_precision" in response
    assert "time_limit" in response
    assert "burning_percent" in response
    assert "expiration_estimate_date" in response


def test_create_payment_with_optional_paras(now_payments_api_key: NOWPayments) -> None:
    price = now_payments_api_key.get_estimated_price(100, "usd", "eth")
    response = now_payments_api_key.create_payment(
        100,
        price_currency="usd",
        pay_currency="eth",

        pay_amount=price["estimated_amount"],
        ipn_callback_url="https://example.org",
        order_id="Order_123456789",
        order_description="Roland TR-8S",
        # purchase_id= "", # I do not understand official documentation
        # payout_address="d8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # This always returns 400
        # payout_currency="eth",  # Returns 500 probably related to the 'payout_address'
        # payout_extra_id=0xbeef, # Returns same error as payout_currency
        fixed_rate=True,
        is_fee_paid_by_user=True
    )
    assert "payment_id" in response
    assert response["payment_status"] == "waiting"
    assert "pay_address" in response
    assert response["price_amount"] == 100
    assert response["price_currency"] == "usd"
    assert "pay_amount" in response
    assert response["pay_currency"] == "eth"
    assert response["order_id"] == "Order_123456789"
    assert response["order_description"] == "Roland TR-8S"
    assert response["ipn_callback_url"] == "https://example.org"
    assert "created_at" in response
    assert "updated_at" in response
    assert "purchase_id" in response
    assert "amount_received" in response
    assert "payin_extra_id" in response
    assert "smart_contract" in response
    assert "network" in response
    assert "network_precision" in response
    assert "time_limit" in response
    assert "burning_percent" in response
    assert "expiration_estimate_date" in response


def test_create_payment_with_unexpected_keyword_argument_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(TypeError):
        now_payments_api_key.create_payment(
            price_amount=100,
            price_currency="usd",
            pay_currency="btc",
            unexpected="argument",
        )


def test_create_payment_with_invalid_amount_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Amount must be greater than 0"):
        now_payments_api_key.get_estimated_price(0, "usd", "btc")


def test_create_payment_with_unsupported_fiat_currency_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Unsupported fiat currency"):
        now_payments_api_key.get_estimated_price(1, "ustr", "btc")


def test_create_payment_with_unsupported_cryptocurrency_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Unsupported cryptocurrency"):
        now_payments_api_key.get_estimated_price(1, "usd", "btccc")


def test_create_invoice(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.create_invoice(100, "usd", "btc")
    assert "id" in response
    assert "order_id" in response
    assert "order_description" in response
    assert "price_amount" in response
    assert "price_currency" in response
    assert "pay_currency" in response
    assert "ipn_callback_url" in response
    assert "invoice_url" in response
    assert "success_url" in response
    assert "cancel_url" in response
    assert "created_at" in response
    assert "updated_at" in response


def test_create_invoice_with_optional_paras(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.create_invoice(
        100,
        "usd",
        "btc",
        ipn_callback_url="https://example.org",
        order_id="Order_123456789",
        order_description="Juno 106",
        success_url="https://example.org/success",
        cancel_url="https://example.org/cancel"
    )
    assert "id" in response
    assert response["order_id"] == "Order_123456789"
    assert response["order_description"] == "Juno 106"
    assert "price_amount" in response
    assert "price_currency" in response
    assert "pay_currency" in response
    assert response["ipn_callback_url"] == "https://example.org"
    assert "invoice_url" in response
    assert response["success_url"] == "https://example.org/success"
    assert response["cancel_url"] == "https://example.org/cancel"
    assert "created_at" in response
    assert "updated_at" in response


def test_create_invoice_with_invalid_amount_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Amount must be greater than 0"):
        now_payments_api_key.create_invoice(0, "usd", "btc")
    with pytest.raises(NowPaymentsException, match="Amount must be greater than 0"):
        now_payments_api_key.create_invoice(-5.5, "usd", "btc")


def test_create_invoice_with_unsupported_fiat_currency_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Unsupported fiat currency"):
        now_payments_api_key.create_invoice(1, "ustr", "btc")


def test_create_invoice_with_unsupported_cryptocurrency_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Unsupported cryptocurrency"):
        now_payments_api_key.create_invoice(1, "usd", "btccc")


def test_create_payment_by_invoice(now_payments_api_key: NOWPayments) -> None:
    invoice = now_payments_api_key.create_invoice(100, "usd", "btc")
    response = now_payments_api_key.create_payment_by_invoice(invoice["id"], "btc")
    assert "payment_id" in response
    assert response["payment_status"] == "waiting"
    assert "pay_address" in response
    assert response["price_amount"] == 100
    assert response["price_currency"] == "usd"
    assert "pay_amount" in response
    assert response["pay_currency"] == "btc"
    assert "order_id" in response
    # assert "order_description" in response # Official docs is wrong. This property is not part of the response
    assert "ipn_callback_url" in response
    assert "created_at" in response
    assert "updated_at" in response
    assert "purchase_id" in response
    assert "amount_received" in response
    assert "payin_extra_id" in response  # BUG: Probably a typo
    assert "smart_contract" in response
    assert "network" in response
    assert "network_precision" in response
    assert "time_limit" in response
    assert "burning_percent" in response
    assert "expiration_estimate_date" in response


def test_create_payment_by_invoice_with_optional_paras(now_payments_api_key: NOWPayments) -> None:
    invoice = now_payments_api_key.create_invoice(100, "usd", "btc")
    response = now_payments_api_key.create_payment_by_invoice(invoice["id"], "btc")
    assert "payment_id" in response
    assert response["payment_status"] == "waiting"
    assert "pay_address" in response
    assert response["price_amount"] == 100
    assert response["price_currency"] == "usd"
    assert "pay_amount" in response
    assert response["pay_currency"] == "btc"
    assert "order_id" in response
    # assert "order_description" in response # Official docs is wrong. This property is not part of the response
    assert "ipn_callback_url" in response
    assert "created_at" in response
    assert "updated_at" in response
    assert "purchase_id" in response
    assert "amount_received" in response
    assert "payin_extra_id" in response  # BUG: Probably a typo
    assert "smart_contract" in response
    assert "network" in response
    assert "network_precision" in response
    assert "time_limit" in response
    assert "burning_percent" in response
    assert "expiration_estimate_date" in response


def test_create_payment_by_invoice_with_unsupported_cryptocurrency_error(now_payments_api_key: NOWPayments) -> None:
    invoice = now_payments_api_key.create_invoice(100, "usd", "btc")
    with pytest.raises(NowPaymentsException, match="Unsupported cryptocurrency"):
        now_payments_api_key.create_payment_by_invoice(invoice["id"], "btccc")


def test_get_payment_status(now_payments_api_key: NOWPayments) -> None:
    payment = now_payments_api_key.create_payment(100, price_currency="usd", pay_currency="btc")
    response = now_payments_api_key.get_payment_status(int(payment["payment_id"]))
    assert int(response["payment_id"]) == int(payment["payment_id"])
    assert response["payment_status"] in ["waiting", "finished"]  # In sandbox environment only two possibilities
    assert "pay_address" in response
    assert response["price_amount"] == 100
    assert response["price_currency"] == "usd"
    assert "pay_amount" in response
    assert "actually_paid" in response
    assert response["pay_currency"] == "btc"
    assert "order_id" in response
    assert "order_description" in response
    assert "purchase_id" in response
    assert "created_at" in response
    assert "updated_at" in response
    assert "outcome_amount" in response
    assert "outcome_currency" in response


def test_get_payment_status_with_invalid_payment_id_error(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Payment ID should be greater than zero"):
        now_payments_api_key.get_payment_status(0)
    with pytest.raises(NowPaymentsException, match="Payment ID should be greater than zero"):
        now_payments_api_key.get_payment_status(-192385)


def test_get_list_of_payments(now_payments_email_password: NOWPayments) -> None:
    payment_list = now_payments_email_password.get_list_of_payments()
    assert type(payment_list["data"]) == list
    assert len(payment_list["data"]) <= 10


def test_get_list_of_payments_limit_error(now_payments_email_password: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Limit must be a number between 1 and 500"):
        now_payments_email_password.get_list_of_payments(0)
    with pytest.raises(NowPaymentsException, match="Limit must be a number between 1 and 500"):
        now_payments_email_password.get_list_of_payments(-5)
    with pytest.raises(NowPaymentsException, match="Limit must be a number between 1 and 500"):
        now_payments_email_password.get_list_of_payments(501)


def test_get_list_of_payments_page_error(now_payments_email_password: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Page number must be equal or greater than 0"):
        now_payments_email_password.get_list_of_payments(page=-1)


def test_get_list_of_payments_sort_paras_error(now_payments_email_password: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Invalid sort parameter"):
        now_payments_email_password.get_list_of_payments(sort_by="invalid_sort_parameter")


def test_get_list_of_payments_sort_paras_error(now_payments_email_password: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Invalid order parameter"):
        now_payments_email_password.get_list_of_payments(order_by="invalid_order_parameter")


def test_get_minimum_payment_amount(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_minimum_payment_amount("eth", "btc")
    assert response["currency_from"] == "eth"
    assert response["currency_to"] == "btc"
    assert "min_amount" in response
    assert type(response["min_amount"]) is float


def test_get_minimum_payment_amount_with_optional_paras(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_minimum_payment_amount(
        "eth",
        "btc",
        fiat_equivalent="usd",
        # is_fixed_rate=True, # Seems like API is broken for this para. API responds always with 400
        is_fee_paid_by_user=True
    )
    assert response["currency_from"] == "eth"
    assert response["currency_to"] == "btc"
    assert "min_amount" in response
    assert type(response["min_amount"]) is float
    assert "fiat_equivalent" in response
    assert type(response["fiat_equivalent"]) is float


# -------------------------
# Currencies
# -------------------------
def test_get_available_currencies(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_available_currencies()
    assert "currencies" in response
    assert type(response["currencies"]) == list


def test_get_available_currencies_full(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_available_currencies_full()
    assert "currencies" in response
    assert type(response["currencies"]) == list


def test_get_available_checked_currencies(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_available_checked_currencies()
    assert "selectedCurrencies" in response
    assert type(response["selectedCurrencies"]) == list
