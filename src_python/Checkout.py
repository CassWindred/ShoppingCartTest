from abc import ABC, abstractmethod
from dataclasses import dataclass
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
        self.name = name


BasketItem = NamedTuple("BasketItem", [("product", Product), ("count", int)])

# Task Comment: Similarly, having a whole abstract class interface for Price Modifiers is overkill when the only deal type is "{amount} for {price}""
# .. But using a common interface in future allows for easy drop in alternative deal types such as "{percent}% Off"


class AbstractPriceModifier(ABC):

    @abstractmethod
    def modified_price(self, unit_price: float, quantity: int) -> float:
        pass


class ComboDealPriceModifier(AbstractPriceModifier):
    combo_price: int
    per_amount: int

    def __init__(self, combo_price, per_amount) -> None:
        self.combo_price = combo_price
        self.per_amount = per_amount

        super().__init__()


@dataclass
class ProductPricing:
    product: Product
    unit_price: float
    price_modifier: Optional[AbstractPriceModifier]


class PricingInfo:

    product_pricings: dict[str, ProductPricing]  # Product IDs to Pricing

    def __init__(self, product_pricings: dict[str, ProductPricing]) -> None:
        self.product_pricings = product_pricings

    def calculate_item_cost(self, item: BasketItem) -> float:
        try:
            pricing = self.product_pricings[item.product.id]
        except KeyError as e:
            raise ValueError(
                f"Product {item.product.id} in basket does not have pricing data in PricingInfo")

        if pricing.price_modifier is not None:
            item_price = pricing.price_modifier.modified_price(
                pricing.unit_price, item.count)
        else:
            item_price = item.count * pricing.unit_price

    def calculate_total_cost(self, basket: List[BasketItem]) -> float:
        total_cost = 0

        for item in basket:
            total_cost += self.calculate_item_cost(item)

        return total_cost
