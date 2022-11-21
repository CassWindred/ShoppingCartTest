from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from typing import List, NamedTuple, Optional

# Task Comment: Having an entire class for just the product name is overkill in this context.
# .. But is built as a class so as to make it easier to extend, as it would likely need to be in a production context.
# .. Other information this could encapsulate in production could be weight, a description, and so on.
# .. The price is not encapsulated in this class as it is not inherent to the product and can change between PriceInfo datasets.


class Product:

    name: str

    @property
    def id(self):
        #  Task Comment: This is fine for this dataset, but would likely need to be changed if product names can overlap
        return self.name

    def __init__(self, name) -> None:
        assert isinstance(name, str)
        self.name = name


BasketItem = NamedTuple("BasketItem", [("code", str), ("quantity", int)])

# Task Comment: Similarly, having a whole abstract class interface for Price Modifiers is overkill when the only deal type is "{amount} for {price}""
# .. But using a common interface in future allows for easy drop in alternative deal types such as "{percent}% Off"
# .. If there was more than one Price Modifier type, it would likely be better to move them into a seperate file
# .. However in this case the two classes are small enough to not be worth the minor complexity introduced thusly


class AbstractPriceModifier(ABC):
    @abstractmethod
    def modified_price(self, unit_price: float, quantity: int) -> float:
        pass


class ComboDealPriceModifier(AbstractPriceModifier):
    combo_price: float
    per_amount: int

    def __init__(self, combo_price, per_amount) -> None:
        float(combo_price)  # Check that combo_price can be cast to float
        assert isinstance(per_amount, int) and per_amount > 0

        self.combo_price = combo_price
        self.per_amount = per_amount

        super().__init__()

    def modified_price(self, unitprice: float, quantity: int) -> float:
        float(unitprice)
        assert isinstance(quantity, int) and quantity >= 0

        deal_price = (quantity // self.per_amount) * self.combo_price
        remaining_price = (quantity % self.per_amount) * unitprice
        return deal_price + remaining_price


@dataclass
class ProductPricing:
    product: Product
    unit_price: float
    price_modifier: Optional[AbstractPriceModifier] = None

    def __post_init__(self):
        assert isinstance(self.product, Product), "product must be of type Product"
        float(self.unit_price)
        assert isinstance(
            self.price_modifier, Optional[AbstractPriceModifier]
        ), "price_modifier must be of type AbstractTypeModifier or None"


class PricingInfo:

    product_pricings: dict[str, ProductPricing]  # Product IDs to Pricing

    def __init__(
        self, product_pricings: dict[str, ProductPricing] | List[ProductPricing]
    ) -> None:
        assert isinstance(product_pricings, dict) or isinstance(
            product_pricings, list
        ), "product_pricing must be a ProductID:ProductPricing dictionary"

        if isinstance(product_pricings, dict):
            assert all(
                isinstance(key, str) for key in product_pricings.keys
            ), "Pricing Keys must all be Product id's (str)"

            assert all(
                isinstance(val, ProductPricing) for val in product_pricings.values
            ), "Pricing Values must all be ProductPricing's"

            self.product_pricings = product_pricings

        elif isinstance(product_pricings, List):
            assert all(isinstance(val, ProductPricing) for val in product_pricings)

            self.product_pricings = {
                pricing.product.id: pricing for pricing in product_pricings
            }

        else:
            raise ValueError("Invalid Input Type for product_pricing")

    def calculate_item_cost(self, item: BasketItem) -> float:
        try:
            pricing = self.product_pricings[item.product.id]
        except KeyError as e:
            raise ValueError(
                f"Product {item.product.id} in basket does not have pricing data in PricingInfo"
            )

        if pricing.price_modifier is not None:
            item_price = pricing.price_modifier.modified_price(
                pricing.unit_price, item.count
            )
        else:
            item_price = item.count * pricing.unit_price

        return item_price

    def dict_to_basket_item(item: dict):
        assert (
            "code" in item and "quantity" in item
        ), "Invalid Basket Format, items must include 'code' and 'quantity"
        assert isinstance(
            item["code"], str
        ), "Invalid Basket Format, 'code' value must be a string"
        assert isinstance(
            item["quantity"], int
        ), "Invalid Basket Format, 'quantity' value must be int"
        return BasketItem(item["code"], item["quantity"])

    def calculate_total_cost(
        self, basket: List[BasketItem] | List[dict] | str
    ) -> float:
        if isinstance(basket, str):
            try:
                basket = json.loads(basket)
            except json.JSONDecodeError as e:
                print("Invalid Basket JSON")
                raise e

        if isinstance(basket, List):
            if all(isinstance(item, BasketItem) for item in basket):
                pass
            elif all(isinstance(item, dict) for item in basket):
                basket = [self.dict_to_basket_item(item) for item in basket]
            else:
                raise ValueError(
                    "Invalid Basket Format, all elements of basket must be either a dict or a BasketItem"
                )
        else:
            raise ValueError("Invalid Basket Format, basket must be a list")

        total_cost = 0

        for item in basket:
            total_cost += self.calculate_item_cost(item)

        return total_cost
