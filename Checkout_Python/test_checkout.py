# Task Comment: For a more complex project one should seperate fixtures into conftest.py
# .. But for a short test file like this, it's better to keep the file whole
# .. As pytest uses the same name for fixtures as names and parameters
# .. Pylint must be told to be quiet about this or it will whine every time a fixture is used
# pylint: disable=redefined-outer-name

import pytest
from .Checkout import *


@pytest.fixture
def product() -> Product:
    """Pytest fixture providing a basic Product instance with name "X"

    Returns:
        Product: A basic product instance with name "X"
    """
    return Product(name="X")


@pytest.fixture
def basket() -> List[BasketItem]:
    """Pytest fixture providing a basic basket list

    Returns:
        List[BasketItem]: A list of BasketItems
    """
    return [
        BasketItem("A", 3),
        BasketItem("A", 3),
        BasketItem("C", 1),
        BasketItem("D", 2),
    ]


@pytest.fixture
def combo_price_modifier() -> ComboDealPriceModifier:
    """Pytest fixture providing a basic ComboDealPriceModifier

    Returns:
        ComboDealPriceModifier: A 3 for 140 ComboDealPriceModifier
    """
    # 3 for 140
    return ComboDealPriceModifier(combo_price=140, per_amount=3)


@pytest.fixture
def pricing_info() -> PricingInfo:
    """Pytest fixture providing a basic PricingInfo

    Returns:
        PricingInfo: PricingInfo initialised to values given for task
    """
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
def input_as_json() -> str:
    """Pytest fixture providing a basic JSON input

    Returns:
        str: A basic basket in JSON
    """
    return '[{"code":"A","quantity":3},{"code":"B","quantity":3},{"code":"C","quantity":1},{"code":"D","quantity":2}]'


@pytest.fixture
def input_as_object() -> List:
    """Pytest fixture providing a basic input

    Returns:
        str: A basic basket
    """
    return [
        {"code": "A", "quantity": 3},
        {"code": "B", "quantity": 3},
        {"code": "C", "quantity": 1},
        {"code": "D", "quantity": 2},
    ]


def test_product_id_is_name(product: Product):
    """Checks the product id is the product name."""
    assert product.id == product.name


def test_combo_price_modifier_calculation(combo_price_modifier: ComboDealPriceModifier):
    """Checks the ComboPriceModifier performs the calculations correctly"""
    unit_price = 50

    assert combo_price_modifier.modified_price(unit_price, 1) == unit_price
    assert combo_price_modifier.modified_price(unit_price, 3) == 140
    assert combo_price_modifier.modified_price(unit_price, 4) == 190


def test_combo_price_modifier_bad_input(combo_price_modifier: ComboDealPriceModifier):
    """Checks the ComboPriceModifier raises errors on bad input"""
    with pytest.raises(ValueError):
        combo_price_modifier.modified_price("by all known laws of aviation", 1)
    with pytest.raises(ValueError):
        combo_price_modifier.modified_price(5, "the bee should not be able to fly")
    with pytest.raises(ValueError):
        combo_price_modifier.modified_price(5, 5.5)

    with pytest.raises(ValueError):
        ComboDealPriceModifier("the bee, of course", 5)
    with pytest.raises(ValueError):
        ComboDealPriceModifier(5, "flies anyway")
    with pytest.raises(ValueError):
        ComboDealPriceModifier(5, -5)
    with pytest.raises(ValueError):
        ComboDealPriceModifier(5, 5.5)


def test_pricing_info_json_parsing(pricing_info: PricingInfo, input_as_json: str):
    """Checks that PricingInfo can parse a correct JSON input"""
    assert pricing_info.calculate_total_cost(input_as_json) == 284


@pytest.mark.parametrize(
    "expected_cost,a_combo_price_mod,a_unit_price_mod,a_quantity_mod,d_unit_price_mod",
    [
        (284, 0, 0, 0, 0),
        (294, 10, 0, 0, 0),
        (280, 0, 0, 0, -2),
        pytest.param(200, 0, 0, 0, 0, marks=pytest.mark.xfail),  # expect failure
    ],
)
def test_pricing_info_calculation(
    pricing_info: PricingInfo,
    input_as_object: List[dict],
    expected_cost,
    a_combo_price_mod,
    a_unit_price_mod,
    a_quantity_mod,
    d_unit_price_mod,
):
    """Checks that PricingInfo performs the calculations correctly"""
    pricings_a: ProductPricing = pricing_info.product_pricings["A"]
    pricings_a.unit_price += a_unit_price_mod
    pricings_d: ProductPricing = pricing_info.product_pricings["D"]
    pricings_d.unit_price += d_unit_price_mod

    a_basket_item = next((item for item in input_as_object if item["code"] == "A"))
    a_basket_item["quantity"] += a_quantity_mod

    modifier_a = pricings_a.price_modifier
    if isinstance(modifier_a, ComboDealPriceModifier):
        modifier_a.combo_price = modifier_a.combo_price + a_combo_price_mod

        assert pricing_info.calculate_total_cost(input_as_object) == expected_cost
    else:
        pytest.fail("A_modifier should be ComboDealPriceModifier")


def test_pricing_info_bad_input(pricing_info: PricingInfo, input_as_object: List[dict]):
    """Checks that PricingInfo raises errors on bad input"""
    with pytest.raises(ValueError):
        pricing_info.calculate_total_cost("not json")
    with pytest.raises(ValueError):
        pricing_info.calculate_total_cost(  # not a list of basket items
            [
                5,
            ]
        )

    with pytest.raises(ValueError):  # Non existent product
        pricing_info.calculate_total_cost([{"code": "E", "quantity": 1}])

    for bad_input in [
        [{"code": "A"}],  # no quantity
        [{"quantity": 5}],  # no code
        [{"code": 5, "quantity": 5}],  # nonstring code
        [{"code": "A", "quantity": 5.5}],
        [{"code": "A", "quantity": -1}],
    ]:
        with pytest.raises(ValueError):
            pricing_info.calculate_total_cost(bad_input)
