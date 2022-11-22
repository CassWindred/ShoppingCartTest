"""A basic terminal interface for the Checkout classes provided by `Checkout_Python.Checkout`


The implementation given in `Checkout.py` is intended to be 
flexible, reusable and extendable for different pricing sets and such.

This file produces a setup as defined in the Task document, and provides a command-line interface for it.

If invoked without arguments, `TerminalCheckout` will use Interactive mode, allowing you to
copy paste JSON as a data source.

If provided with the command argument `--i` or `--input` followed by a filename,
then `TerminalCheckout will instead use the JSON found in the given filename.
"""

import json
import sys
from typing import List

from .checkout import (
    Product,
    PricingInfo,
    ProductPricing,
    ComboDealPriceModifier,
)

pricing_info = PricingInfo(
    [
        ProductPricing(
            Product("A"), unit_price=50, price_modifier=ComboDealPriceModifier(140, 3)
        ),
        ProductPricing(
            Product("B"), unit_price=35, price_modifier=ComboDealPriceModifier(60, 2)
        ),
        ProductPricing(Product("C"), unit_price=25),
        ProductPricing(Product("D"), unit_price=12),
    ]
)


def cause_stack(exception: BaseException) -> List[BaseException]:
    """A utility function returning an ordered list of Exceptions that caused the previous exception.

    Args:
        exception (BaseException): The first exception to find the cause of.

    Returns:
        List[BaseException]: An ordered list of exceptions caused by exceptions.
    """
    if exception.__cause__ is None:
        return [exception]
    else:
        return [exception] + cause_stack(exception.__cause__)


def format_causes(exception: BaseException) -> str:
    r"""A utility function returning a string formatted description of the exceptions that caused the given exception.

    Args:
        exception (BaseException): The first exception to find the cause of.

    Returns:
        str: A formatted string of exceptions seperated by `\n caused by \n`
    """
    return "\n - caused by -\n".join([str(cause) for cause in cause_stack(exception)])


def try_input(input_json: str):
    """Try to find the total cost of a given JSON string

    Args:
        input_json (str): JSON string input used as data source to calculate total cost
    """
    try:
        total_cost = pricing_info.calculate_total_cost(input_json)
        print("Total Cost of Order: ", total_cost)
    except json.JSONDecodeError as ex:
        print(
            f"""Input JSON failed to parse.
            JSON Error:
            ===
            {ex}
            ==="""
        )
    except (ValueError, AssertionError) as ex:
        print(
            f"""
Invalid Input:
===
{format_causes(ex)}
==="""
        )


def interactive_mode():
    """Enters interactive mode, allowing the user to input JSON strings directly into the terminal.
    """
    ITALIC_START = "\x1B[3m"
    ITALIC_END = "\x1B[0m"

    print(
        f"""Welcome to Terminal Checkout, the checkout application of the future!
    {ITALIC_START}Authors Note: In the future, there are only four products: A, B, C and D.
    Do not ask about Product E.{ITALIC_END}"""
    )

    while True:
        print("===")
        input_json = input("Please enter checkout data as valid JSON: ")
        try_input(input_json)


def use_input_file(filename: str):
    """Reads the input file and uses it's contents as the JSON data source to calculate total cost

    Args:
        filename (str): The name of the file to read input JSON from
    """
    with open(filename) as file:
        file_contents = file.read()
        print("Input File Contents:")
        print(file_contents)
        try_input(file_contents)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if args[0] == "-i" or args[0] == "--input":
            if len(args) == 1:
                print("--input argument requires filename")
            else:
                use_input_file(args[1])
        else:
            print(
                f"Unknown Argument: {args[0]}, -i or --input are the only valid first"
                " arguments"
            )

    else:
        print("No arguments detected, entering interactive mode...")
        interactive_mode()
