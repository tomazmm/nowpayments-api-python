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
# /status
# -------------------------
def test_get_api_status(now_payments_api_key: NOWPayments) -> None:
    assert now_payments_api_key.get_api_status() == {"message": "OK"}


# -------------------------
# POST /auth
# -------------------------
def test_auth(now_payments_email_password: NOWPayments) -> None:
    payload = now_payments_email_password.auth()
    assert "token" in payload


def test_email_and_password_missing(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Email and password are missing"):
        assert now_payments_api_key.auth()


# -------------------------
#       PAYMENTS API
# -------------------------
def test_get_estimated_price(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_estimated_price(500, "usd", "btc")
    assert response["amount_from"] == 500
    assert response["currency_from"] == "usd"
    assert response["currency_to"] == "btc"
    assert "estimated_amount" in response


def test_amount_greater_than_zero(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Amount must be greater than 0"):
        now_payments_api_key.get_estimated_price(0, "usd", "btc")


def test_unsupported_fiat_currency(now_payments_api_key: NOWPayments) -> None:
    with pytest.raises(NowPaymentsException, match="Unsupported fiat currency"):
        now_payments_api_key.get_estimated_price(1, "ustr", "btc")


def test_unsupported_cryptocurrency(now_payments_api_key: NOWPayments) -> None:
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
        # purchase_id= "", TODO: This is gibersih, I do not understand official documentation
        # payout_address="d8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # TODO: This always returns 400
        # payout_currency="eth",  # TODO: Returns 500 probably related to the 'payout_address'
        # payout_extra_id=0xbeef, #TODO: returns same error as payout_currency
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


# -------------------------
#       Currencies API
# -------------------------
def test_get_available_currencies(now_payments_api_key: NOWPayments) -> None:
    response = now_payments_api_key.get_available_currencies()
    assert "currencies" in response
    assert type(response["currencies"]) == list

# def test_estimate_amount_url_param(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
# ) -> None:
#     """
#     Estimate amount url param test.
#     """
#     assert (
#             now_payments._ESTIMATE_AMOUNT_URL  # pylint: disable=protected-access
#             == "estimate?amount={}&currency_from={}&currency_to={}"
#     )
#
#
# def test_min_amount_url_param(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
# ) -> None:
#     """
#     Min amount url param test.
#     """
#     assert (
#             now_payments._MIN_AMOUNT_URL  # pylint: disable=protected-access
#             == "min-amount?currency_from={}"
#     )
#
#
# def test_get_url(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
# ) -> None:
#     """
#     Get URL test
#     """
#     assert (
#             now_payments._get_url("endpoint")  # pylint: disable=protected-access
#             == "https://api.nowpayments.io/v1/endpoint"
#     )
#
#
# def test_get_requests(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
# ) -> None:
#     """
#     Get request test
#     """
#
#     response = now_payments._get_requests(  # pylint: disable=protected-access
#         "https://api.nowpayments.io/v1/status"
#     )
#     assert response.status_code == 200
#
#
# def test_get_available_currencies(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Get available currencies test.
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/currencies",
#         autospec=True,
#     )
#     assert (
#             now_payments.get_available_currencies().get("currencies", "Not found")
#             != "Not found"
#     )
#
#
# def test_get_available_checked_currencies(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Get available checked currencies test
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/merchant/coins",
#         autospec=True,
#     )
#     result = now_payments.get_available_checked_currencies()
#     assert result.get("selectedCurrencies", "Not found") != "Not found"
#
#
# def test_get_estimate_price(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Get estimate price test.
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/estimate?amount=\
#         100&currency_from=usd&currency_to=btc",
#         autospec=True,
#     )
#     result = now_payments.get_estimated_price(
#         amount=100, currency_from="usd", currency_to="btc"
#     )
#     assert result.get("estimated_amount", "Not found") != "Not found"
#
#
# def test_get_estimate_price_error(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Get estimate price test with error.
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/estimate?amount=\
#         100&currency_from=cup&currency_to=btc",
#         autospec=True,
#     )
#     with pytest.raises(HTTPError, match="Error 400: Currency CUP was not found"):
#         now_payments.get_estimated_price(
#             amount=100, currency_from="cup", currency_to="eur"
#         )
#
#
# def test_create_payment_unexpected_keyword_argument_error(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
# ) -> None:
#     """
#     Create payment test with unexpected keyword argument error
#     """
#     with pytest.raises(TypeError):
#         now_payments.create_payment(
#             price_amount=100,
#             price_currency="usd",
#             pay_currency="btc",
#             unexpected="argument",
#         )
#
#
# def test_create_payment(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Create payment test
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/payment",
#         autospec=True,
#     )
#     result = now_payments.create_payment(
#         price_amount=100, price_currency="usd", pay_currency="btc"
#     )
#     assert result.get("payment_id", "Not found") != "Not found"
#
#
# def test_create_payment_with_argument(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Create payment test with argument
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/payment",
#         autospec=True,
#     )
#     result = now_payments.create_payment(
#         price_amount=100,
#         price_currency="usd",
#         pay_currency="btc",
#         order_description="My order",
#     )
#     assert result.get("order_description", "Not found") == "My order"
#
#
# def test_create_payment_with_error(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Create payment test with error
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/payment",
#         autospec=True,
#     )
#     with pytest.raises(
#             HTTPError,
#             match="Error 400: Currency cup was not found",
#     ):
#         now_payments.create_payment(
#             price_amount=100, price_currency="usd", pay_currency="cup"
#         )
#
#
# def test_create_invoice(
#         now_payments: NOWPayments,  # pylint: disable=redefined-outer-name
#         mocker: MockerFixture,
# ) -> None:
#     """
#     Create invoice test
#     """
#     mocker.patch.object(
#         NOWPayments,
#         "_get_url",
#         return_value="https://api.nowpayments.io/v1/invoice",
#         autospec=True,
#     )
#     result = now_payments.create_invoice(
#         price_amount=100, price_currency="usd", pay_currency="btc"
#     )
#     assert result.get("invoice_url") is not None
