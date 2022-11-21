import pytest
from Checkout import *


@pytest.fixture
def product():
    return Product(name="X")


@pytest.fixture
def basket():
    return [
        BasketItem(Product("A"), 3),
        BasketItem(Product("B"), 3),
        BasketItem(Product("C"), 1),
        BasketItem(Product("D"), 2),
    ]


@pytest.fixture
def combo_price_modifier():
    # 3 for 140
    return ComboDealPriceModifier(combo_price=140, per_amount=3)


@pytest.fixture
def pricing_info():
    # pricing info as defined in task
    pricing_info = PricingInfo(
        [
            ProductPricing(
                Product("A"),
                unit_price=50,
                price_modifier=ComboDealPriceModifier(140, 3),
            ),
            ProductPricing(
                Product("B"),
                unit_price=35,
                price_modifier=ComboDealPriceModifier(60, 2),
            ),
            ProductPricing(Product("C"), unit_price=25),
            ProductPricing(Product("D"), unit_price=12),
        ]
    )
    return pricing_info


@pytest.fixture
def input_as_json():
    return '[{"code":"A","quantity":3},{"code":"B","quantity":3},{"code":"C","quantity":1},{"code":"D","quantity":2}'


@pytest.fixture
def input_as_object():
    return [
        {"code": "A", "quantity": 3},
        {"code": "B", "quantity": 3},
        {"code": "C", "quantity": 1},
        {"code": "D", "quantity": 2},
    ]


def test_product_id_is_name(product):
    assert type(product) is Product
    assert product.id == product.name


def test_combo_price_modifier_calculation(combo_price_modifier: ComboDealPriceModifier):
    unit_price = 50

    assert combo_price_modifier.modified_price(unit_price, 1) == unit_price
    assert combo_price_modifier.modified_price(unit_price, 3) == 140
    assert combo_price_modifier.modified_price(unit_price, 4) == 190


def test_pricing_info(pricing_info, input_as_json, input_as_object):
    pass
