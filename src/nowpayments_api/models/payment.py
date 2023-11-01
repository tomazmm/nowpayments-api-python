"""
Dataclasses for the NowPayments API.
"""
from dataclasses import dataclass
from inspect import signature
from typing import Dict, Union


@dataclass
class Base:
    def clean_data_to_dict(self) -> Dict[str, Union[str, float, int]]:
        """
        Delete None types and return dictionary
        """
        data = {}
        for field in signature(self.__class__).parameters:
            if getattr(self, field):
                data[field] = getattr(self, field)
        return data


@dataclass
class PaymentData(Base):  # pylint: disable=too-many-instance-attributes
    """
    The PaymentData class is a container for the data that is used to make a payment.
    """

    price_amount: float
    price_currency: str
    pay_currency: str
    pay_amount: float = None
    ipn_callback_url: str = None
    order_id: str = None
    order_description: str = None
    purchase_id: int = None
    payout_address: str = None
    payout_currency: str = None
    payout_extra_id: str = None
    fixed_rate: bool = None
    is_fee_paid_by_user: bool = None


@dataclass
class InvoiceData(Base):
    """
    The InvoiceData class is a container for the data that is used to make a invoice.
    """

    price_amount: float
    price_currency: str
    pay_currency: str
    ipn_callback_url: str = None
    order_id: str = None  # User can get notified, when payment is received
    order_description: str = None
    success_url: int = None
    cancel_url: str = None


@dataclass
class InvoicePaymentData(Base):
    """
    The InvoicePaymentData class is a container for the data that is used to make a payment by invoice.
    """

    iid: int
    pay_currency: str
    order_description: str = None
    customer_email: str = None  # User can get notified, when payment is received
    payout_address: str = None
    payout_extra_id: int = None
    payout_currency: str = None
