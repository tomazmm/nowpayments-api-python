"""
A Python wrapper for the NOWPayments API.
"""
from typing import Any, Dict, Union

import requests

from nowpayments.models.payment import PaymentData, InvoicePaymentData, InvoiceData
from requests import Response
from requests.exceptions import HTTPError


class NowPaymentsException(Exception):
    pass


class NOWPayments:
    _ESTIMATE_AMOUNT_URL = "estimate?amount={}&currency_from={}&currency_to={}"
    _MIN_AMOUNT_URL = "min-amount?currency_from={}"

    def __init__(self, api_key: str, email: str = "", password: str = "", sandbox=False) -> None:
        """
        Class construct.

        :param str api_key: API key
        """

        self.api_uri = "https://api.nowpayments.io/v1/" if not sandbox else "https://api-sandbox.nowpayments.io/v1/"

        self.session = requests.Session()
        self._api_key = api_key
        self._email = email
        self._password = password
        self.sandbox = sandbox

    # -------------------------------
    # Request Session Method Wrappers
    # -------------------------------
    def _get_requests(self, url: str, bearer: str = None) -> Response:
        headers = {"x-api-key": self._api_key}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer['token']}"
        return self.session.get(url=url, headers=headers)

    def _post_requests(self, url: str, data: Dict = None) -> Response:
        """
        Make get requests with your header and data

        :param url: URL to which the request is made
        :param data: Data to which the request is made
        """
        headers = {"x-api-key": self._api_key}
        return self.session.post(url=url, headers=headers, data=data)

    def _get_url(self, endpoint: str) -> str:
        """
        Set the url to be used

        :param str endpoint: Endpoint to be used
        """
        return f"{self.api_uri}{endpoint}"

    # -------------------------
    # GET /status
    # -------------------------
    def get_api_status(self) -> Dict:
        """
        https://documenter.getpostman.com/view/7907941/S1a32n38#99Torej98079f-dcc8-4e07-9ac7-3d52f0fd733a
        """
        resp = requests.get(f"{self.api_uri}status")
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "No description")}'
        )

    # -------------------------
    # POST /auth
    # -------------------------
    def auth(self):
        if not self._email or not self._password:
            raise NowPaymentsException("Email and password are missing")
        resp = self._post_requests(self._get_url("auth"), {
            "email": self._email,
            "password": self._password
        })
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    # -------------------------
    #       PAYMENTS API
    # -------------------------
    def get_estimated_price(self, amount: float, currency_from: str, currency_to: str) -> Dict:
        """
        This is a method for calculating the approximate price in cryptocurrency for a given value in Fiat currency.
        You will need to provide the initial cost in the Fiat currency (amount, currency_from) and the necessary
        cryptocurrency (currency_to) Currently following fiat currencies are available: usd, eur, nzd, brl, gbp.
         :param  float amount: Cost value in fiat currency
         :param  str currency_from: Fiat currency acronym
         :param  str currency_to: Cryptocurrency.
         :return:
        """
        if amount <= 0:
            raise NowPaymentsException("Amount must be greater than 0")
        if currency_from not in ["usd", "eur", "nzd", "brl", "gbp"]:
            raise NowPaymentsException("Unsupported fiat currency")
        if currency_to not in self.get_available_currencies()["currencies"]:
            raise NowPaymentsException("Unsupported cryptocurrency")

        endpoint = f"{self.api_uri}estimate?amount={amount}&currency_from={currency_from}&currency_to={currency_to}"
        resp: Response = self._get_requests(endpoint)
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    def create_payment(
            self,
            price_amount: float,
            price_currency: str,
            pay_currency: str,
            **kwargs: Union[str, float, bool, int],
    ) -> Dict:
        """
        With this method, your customer will be able to complete the payment without leaving your website.

        :param float price_amount: The fiat equivalent of the price to be paid in crypto.
        :param str price_currency: The fiat currency in which the price_amount is specified.
        :param str pay_currency: The crypto currency in which the pay_amount is specified.

        :param float pay_amount: The amount that users have to pay for the order stated in crypto.
        :param str ipn_callback_url: Url to receive callbacks, should contain "http" or "https".
        :param str order_id: Inner store order ID.
        :param str order_description: Inner store order description.
        :param int purchase_id: id of purchase for which you want to create other payment,
            only used for several payments for one order
        :param str payout_address: Receive funds on another address.
        :param str payout_currency: Currency of your external payout_address.
        :param int payout_extra_id: Extra id or memo or tag for external payout_address.
        :param bool fixed_rate: Required for fixed-rate exchanges.
        :param bool is_fee_paid_by_user: Required for fixed-rate exchanges with all fees paid by users.

        :return: dict
        {
          "payment_id": "5745459419",
          "payment_status": "waiting",
          "pay_address": "3EZ2uTdVDAMFXTfc6uLDDKR6o8qKBZXVkj",
          "price_amount": 3999.5,
          "price_currency": "usd",
          "pay_amount": 0.17070286,
          "pay_currency": "btc",
          "order_id": "RGDBP-21314",
          "order_description": "Apple Macbook Pro 2019 x 1",
          "ipn_callback_url": "https://nowpayments.io",
          "created_at": "2020-12-22T15:00:22.742Z",
          "updated_at": "2020-12-22T15:00:22.742Z",
          "purchase_id": "5837122679",
          "amount_received": null,
          "payin_extra_id": null,
          "smart_contract": "",
          "network": "btc",
          "network_precision": 8,
          "time_limit": null,
          "burning_percent": null,
          "expiration_estimate_date": "2020-12-23T15:00:22.742Z"
        }
        """
        if price_amount <= 0:
            raise NowPaymentsException("Amount must be greater than 0")
        if price_currency not in ["usd", "eur", "nzd", "brl", "gbp"]:
            raise NowPaymentsException("Unsupported fiat currency")
        if pay_currency not in self.get_available_currencies()["currencies"]:
            raise NowPaymentsException("Unsupported cryptocurrency")

        payload = PaymentData(
            price_amount=price_amount,
            price_currency=price_currency,
            pay_currency=pay_currency,
            **kwargs,
        )
        resp = self._post_requests(
            f"{self.api_uri}payment",
            data=payload.clean_data_to_dict(is_sandbox=self.sandbox)
        )
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    def create_invoice(
            self,
            price_amount: float,
            price_currency: str,
            pay_currency: str,
            **kwargs: Union[str, float, bool, int],
    ) -> Dict:
        """
        Creates an invoice. With this method, the customer is required to follow the generated url to complete the payment. Data must be sent as a JSON-object payload.

        :param float price_amount: the amount that users have to pay for the order stated in fiat currency. In case
            you do not indicate the price in crypto, our system will automatically convert this fiat amount into its
            crypto equivalent. NOTE: Some of the assets (KISHU, NWC, FTT, CHR, XYM, SRK, KLV, SUPER, OM, XCUR, NOW, SHIB
            SAND, MATIC, CTSI, MANA, FRONT, FTM, DAO, LGCY), have a maximum price limit of ~$2000.
        :param str price_currency: The fiat currency in which the price_amount is specified.
        :param str pay_currency: The cryptocurrency in which the pay_amount is specified.
        :param float pay_amount: The amount that users have to pay for the order stated in crypto.
        :param str ipn_callback_url: Url to receive callbacks, should contain "http" or "https".
        :param str order_id: Inner store order ID.
        :param str order_description: Inner store order description.
        :param str success_url:  Url where the customer will be redirected after successful payment.
        :param str cancel_url: Url where the customer will be redirected after failed payment.
        :retunr dict:
        {
          "id": "4522625843",
          "order_id": "RGDBP-21314",
          "order_description": "Apple Macbook Pro 2019 x 1",
          "price_amount": "1000",
          "price_currency": "usd",
          "pay_currency": null,
          "ipn_callback_url": "https://nowpayments.io",
          "invoice_url": "https://nowpayments.io/payment/?iid=4522625843",
          "success_url": "https://nowpayments.io",
          "cancel_url": "https://nowpayments.io",
          "created_at": "2020-12-22T15:05:58.290Z",
          "updated_at": "2020-12-22T15:05:58.290Z"
        }
        """
        if price_amount <= 0:
            raise NowPaymentsException("Amount must be greater than 0")
        if price_currency not in ["usd", "eur", "nzd", "brl", "gbp"]:
            raise NowPaymentsException("Unsupported fiat currency")
        if pay_currency not in self.get_available_currencies()["currencies"]:
            raise NowPaymentsException("Unsupported cryptocurrency")
        payload = InvoiceData(
            price_amount=price_amount,
            price_currency=price_currency,
            pay_currency=pay_currency,
            **kwargs,
        )
        resp = self._post_requests(
            f"{self.api_uri}invoice",
            data=payload.clean_data_to_dict(is_sandbox=self.sandbox)
        )
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    def create_payment_by_invoice(
            self,
            invoice_id: int,
            pay_currency: str,
            **kwargs: Union[str, str, int, str]
    ) -> Dict:
        """
        Creates payment by invoice. With this method, your customer will be able to complete the payment without leaving your website.
        Data must be sent as a JSON-object payload.
        Required request fields:

        :param int iid: invoice id
        :param str pay_currency: The cryptocurrency in which the pay_amount is specified (btc, eth, etc).
            NOTE: some of the currencies require a Memo, Destination Tag, etc., to complete a payment  (AVA, EOS,
            BNBMAINNET, XLM, XRP). This is unique for each payment. This ID is received in “payin_extra_id” parameter of
            the response. Payments made without "payin_extra_id" cannot be detected automatically.
        :parm int purchase_id: id of purchase for which you want to create aother payment, only used for several
            payments for one order
        :param str order_description: Inner store order description, e.g. "Apple Macbook Pro 2019 x 1"
        :param str customer_email: User email to which a notification about the successful completion of the payment
            will be sent
        :param str payout_address:  Usually the funds will go to the address you specify in your Personal account.
            In case you want to receive funds on another address, you can specify it in this parameter.
        :param int payout_extra_id: Extra id or memo or tag for external payout_address.
        :param str payout_currency:  currency of your external payout_address, required when payout_adress is specified.
        :return dict:
        {
          "payment_id": "5745459419",
          "payment_status": "waiting",
          "pay_address": "3EZ2uTdVDAMFXTfc6uLDDKR6o8qKBZXVkj",
          "price_amount": 3999.5,
          "price_currency": "usd",
          "pay_amount": 0.17070286,
          "pay_currency": "btc",
          "order_id": "RGDBP-21314",
          "order_description": "Apple Macbook Pro 2019 x 1",
          "ipn_callback_url": "https://nowpayments.io",
          "created_at": "2020-12-22T15:00:22.742Z",
          "updated_at": "2020-12-22T15:00:22.742Z",
          "purchase_id": "5837122679",
          "amount_received": null,
          "payin_extra_id": null,
          "smart_contract": "",
          "network": "btc",
          "network_precision": 8,
          "time_limit": null,
          "burning_percent": null,
          "expiration_estimate_date": "2020-12-23T15:00:22.742Z"
        }
        """
        if pay_currency not in self.get_available_currencies()["currencies"]:
            raise NowPaymentsException("Unsupported cryptocurrency")
        data = InvoicePaymentData(
            iid=invoice_id,
            pay_currency=pay_currency,
            **kwargs
        )
        resp = self._post_requests(f"{self.api_uri}invoice-payment",
                                   data=data.clean_data_to_dict(is_sandbox=self.sandbox))
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    # -------------------------
    #      CURRENCIES API
    # -------------------------
    def get_available_currencies(self, fixed_rate: bool = True) -> Dict:
        """
        This is a method for obtaining information about all cryptocurrencies available for payments.
        :param boolean fixed_rate:
        """
        resp = self._get_requests(f"{self.api_uri}currencies?fixed_rate={fixed_rate}")
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    def get_available_checked_currencies(self) -> Dict:
        """
        This is a method for obtaining information about the cryptocurrencies available
         for payments. Shows the coins you set as available for payments in the "coins settings"
          tab on your personal account.
        """
        endpoint = "merchant/coins"
        url = self._get_url(endpoint)
        resp = self._get_requests(url)
        if resp.status_code == 200:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )


        :param str ipn_callback_url: Url to receive callbacks, should contain "http" or "https".

        :param str order_id: Inner store order ID.

        :param str order_description: Inner store order description.

        :param int purchase_id: Id of purchase for which you want to create a other payment.

        :param str payout_address: Receive funds on another address.

        :param str payout_currency: Currency of your external payout_address.

        :param int payout_extra_id: Extra id or memo or tag for external payout_address.

        :param bool fixed_rate: Required for fixed-rate exchanges.
        """
        endpoint = "invoice"
        data = PaymentData(
            price_amount=price_amount,
            price_currency=price_currency,
            pay_currency=pay_currency,
            **kwargs,
        )
        url = self._get_url(endpoint)
        resp = self._post_requests(
            url, data=data.clean_data_to_dict(is_sandbox=self._IS_SANDBOX)
        )
        if resp.ok:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    def get_payment_status(self, payment_id: int) -> Any:
        """
        Get the actual information about the payment.

        :param int payment_id: ID of the payment in the request.
        """
        endpoint = f"payment/{payment_id}"
        url = self._get_url(endpoint)
        resp: Response = self._get_requests(url)
        if resp.status_code == 200:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )

    def get_minimum_payment_amount(
        self, currency_from: str, currency_to: str = None, fiat_equivalent: str = None
    ) -> Any:
        """
        Get the minimum payment amount for a specific pair.

        :param currency_from: Currency from
        :param currency_to: Currency to
        """
        endpoint = self._MIN_AMOUNT_URL.format(currency_from)
        if currency_to is not None:
            endpoint += f"&currency_to={currency_to}"
        if fiat_equivalent is not None:
            endpoint += f"&fiat_equivalent={fiat_equivalent}"
        url = self._get_url(endpoint)
        resp: Response = self._get_requests(url)
        if resp.status_code == 200:
            return resp.json()
        raise HTTPError(
            f'Error {resp.status_code}: {resp.json().get("message", "Not descriptions")}'
        )
