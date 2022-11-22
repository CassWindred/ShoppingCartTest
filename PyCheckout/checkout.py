from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import Dict, List, Optional, Union

# Task Comment: Having an entire class for just the product name is overkill in this context.
# .. But is built as a class so as to make it easier to extend, as it would likely need to be in a
# .. production context.
# .. Other information this could encapsulate in production could be weight, a description,
# .. and so on.
# .. The price is not encapsulated in this class as it is not inherent to the product and can
# .. change between PriceInfo datasets.


class Product:
    """Encapsulates a single product."""

    name: str

    @property
    def id(self) -> str:
        # Task Comment: This is fine for this dataset, but would likely need to be changed
        # .. if product names can overlap
        return self.name

    def __init__(self, name) -> None:
        assert isinstance(name, str)

        self.name = name


# Task Comment: Similarly, having a whole abstract class interface for Price Modifiers is overkill when the only deal type is "{amount} for {price}""
# .. But using a common interface in future allows for easy drop in alternative deal types such as "{percent}% Off"
# .. If there was more than one Price Modifier type, it would likely be better to move them into a seperate file
# .. However in this case the two classes are small enough to not be worth the minor complexity introduced thusly


class AbstractPriceModifier(ABC):
    """A base class for Price Modifiers."""

    @abstractmethod
    def modified_price(self, unit_price: float, quantity: int) -> float:
        """Calculates the price of a quantity of items with modifier applied

        Args:
            unit_price (float): The base, individual price of an item
            quantity (int): The quantity of the item in the basket

        Returns:
            float: The modified price
        """
        pass


class ComboDealPriceModifier(AbstractPriceModifier):
    """A price modifier for combo-deals which define a given price for each set of items
    e.g. '3 for 140' or '2 for 60'."""

    combo_price: float
    per_amount: int

    def __init__(self, combo_price, per_amount) -> None:
        try:
            float(combo_price)  # Check that combo_price can be cast to float
        except ValueError as ex:
            raise ValueError("combo_price must be castable to float") from ex

        try:
            assert isinstance(per_amount, int) and per_amount > 0
        except AssertionError as ex:
            raise ValueError("per_amount must be an int > 0") from ex

        self.combo_price = combo_price
        self.per_amount = per_amount

        super().__init__()

    def modified_price(self, unit_price: float, quantity: int) -> float:
        try:
            float(unit_price)
        except ValueError as ex:
            raise ValueError("unit_price must be castable to float") from ex
        try:
            assert isinstance(quantity, int) and quantity >= 0
        except AssertionError as ex:
            raise ValueError("Quantity must be an int >= 0") from ex

        deal_price = (quantity // self.per_amount) * self.combo_price
        remaining_price = (quantity % self.per_amount) * unit_price
        return deal_price + remaining_price


@dataclass
class ProductPricing:
    """The pricing information for a single product, including an optional modifier."""

    product: Product
    unit_price: float
    price_modifier: Optional[AbstractPriceModifier] = None

    def __post_init__(self):
        assert isinstance(self.product, Product), "product must be of type Product"
        float(self.unit_price)
        assert isinstance(
            self.price_modifier, Optional[AbstractPriceModifier]
        ), "price_modifier must be of type AbstractTypeModifier or None"


@dataclass
class BasketItem:
    """A single item in a basket."""

    code: str
    quantity: int

    def __post_init__(self):
        try:
            assert (
                self.quantity >= 0
            ), f"Basket Item '{self.code}' has negative quantity '{self.quantity}'"
        except AssertionError as ex:
            raise ValueError("Invalid Basket Item") from ex


class PricingInfo:
    """A Pricing dataset, storing the prices and modifiers for each product."""

    product_pricings: dict[str, ProductPricing]  # Product IDs to Pricing

    def __init__(
        self, product_pricings: dict[str, ProductPricing] | List[ProductPricing]
    ) -> None:
        """Creates a `PricingInfo` instance.

        Args:
            product_pricings (dict[str, ProductPricing] | List[ProductPricing]):
                The pricings to include in the `PricingInfo`, provided as either a
                {ProductID: ProductPricing} `dict`, or just a `list` of `ProductPricing`s.

        Raises:
            ValueError: ProductPricings given are not valid.
        """
        assert isinstance(product_pricings, dict) or isinstance(
            product_pricings, list
        ), "product_pricing must be a ProductID:ProductPricing dictionary"

        if isinstance(product_pricings, dict):
            assert all(
                isinstance(key, str) for key in product_pricings
            ), "Pricing Keys must all be Product id's (str)"

            assert all(
                isinstance(val, ProductPricing) for val in product_pricings.values()
            ), "Pricing Values must all be ProductPricing's"

            self.product_pricings = product_pricings

        elif isinstance(product_pricings, List):
            assert all(isinstance(val, ProductPricing) for val in product_pricings)

            self.product_pricings = {
                pricing.product.id: pricing for pricing in product_pricings
            }

        else:
            raise ValueError("Invalid Input Type for product_pricing")

    def dict_to_basket_item(self, item: Dict[str, Union[str, int]]) -> BasketItem:
        """Converts a valid dictionary into a BasketItem

        Args:
            item (Dict[str, Union[str, int]]): A valid `dict` with the structure
            `{"code": (str), "quantity": (int > 0)}`

        Raises:
            ValueError: Invalid `dict` for conversion into BasketItem

        Returns:
            BasketItem: The `BasketItem` encapsulation of the dictionary
        """
        try:
            assert (
                "code" in item and "quantity" in item
            ), "Items must include 'code' and 'quantity"
            assert isinstance(
                item["code"], str
            ), f"'code' value must be a string, is {type(item['code'])}"
            assert isinstance(
                item["quantity"], int
            ), f"'quantity' value must be a int, is {type(item['code'])}"
        except AssertionError as ex:
            raise ValueError(f"Invalid format for basket item {item}") from ex

        return BasketItem(item["code"], item["quantity"])

    def calculate_item_cost(self, item: BasketItem) -> float:
        """Calculates the sum cost of a single `BasketItem`, including modifiers.`

        Args:
            item (BasketItem): The `BasketItem` to calculate the cost of.

        Raises:
            ValueError: Invalid `BasketItem`

        Returns:
            float: The sum cost of the `BasketItem`
        """
        try:
            pricing = self.product_pricings[item.code]
        except KeyError as ex:
            raise ValueError(
                f"Product {item.code} in basket does not have pricing data in"
                " PricingInfo"
            ) from ex

        if pricing.price_modifier is not None:
            item_price = pricing.price_modifier.modified_price(
                pricing.unit_price, item.quantity
            )
        else:
            item_price = item.quantity * pricing.unit_price

        return item_price

    def calculate_total_cost(
        self, basket: List[BasketItem] | List[dict] | str
    ) -> float:
        """Calculates the total cost of a given basket

        Args:
            basket (List[BasketItem] | List[dict] | str): The basket to calculate the total cost of.
                Can be provided as a `List` of `BasketItem`s or valid `dict`s, or as a JSON string
                that evaluates as such.

        Raises:
            ValueError: Invalid input basket.

        Returns:
            float: The total cost of the basket.
        """
        if isinstance(basket, str):
            try:
                basket = json.loads(basket)
            except json.JSONDecodeError as ex:
                raise ValueError("Invalid JSON") from ex

        if isinstance(basket, List):
            if all(isinstance(item, BasketItem) for item in basket):
                pass
            elif all(isinstance(item, dict) for item in basket):
                basket = [self.dict_to_basket_item(item) for item in basket]  # type: ignore
            else:
                raise ValueError(
                    "Invalid Basket Format, all elements of basket must be either a"
                    " dict or a BasketItem"
                )
        else:
            raise ValueError("Invalid Basket Format, basket must be a list")

        total_cost = 0

        for item in basket:
            total_cost += self.calculate_item_cost(item)  # type: ignore

        return total_cost
