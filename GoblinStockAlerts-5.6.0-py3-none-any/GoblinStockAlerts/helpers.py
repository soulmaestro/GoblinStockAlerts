"""
Miscellaneous helpers that didn't have a better place to live.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
from functools import lru_cache

logger = logging.getLogger("GSA")


def mask_string(*,
                input_string: str
                ) -> str:
    """
    Hides the majority of a string with asterisks.

    If your sensitive string was "Password12345" it would return "Pas*******345".
    If your sensitive string was "Password" it would return "P******d".
    If your sensitive string was "Pass" it would return "****".

    :param input_string: The string to be masked
    """

    if len(input_string) > 10:
        return f"{input_string[:3]}{'*' * (len(input_string) - 6)}{input_string[-3:]}"

    if len(input_string) > 6:
        return f"{input_string[:1]}{'*' * (len(input_string) - 2)}{input_string[-1:]}"

    return '*' * len(input_string)


def convert_copper_value_to_gold_string(*,
                                        copper_price: int
                                        ) -> str:
    """
    Convert a large copper value to gold. All prices in World of Warcraft are represented as their
    copper value. Eg 10g = 10 * 100 (silver) * 100 (copper) so 100000. The function takes that copper
    price and returns a thousand comma seperated string with a "g" suffix.

    If the copper price is "0" we return "Unlimited".

    :param copper_price: copper price to be converted.
    """

    return "{:,.2f}g".format(copper_price / 10000) if copper_price != 0 else "Unlimited"


@lru_cache
def convert_string_to_slug(*,
                           string: str
                           ) -> str:
    """
    Convert a string to a slug format which includes removing spaces and apostrophes and converting to lowercase.

    :param string: The string to be converted to a slug.
    """

    # Convert to lowercase.
    slug = string.lower()

    # Remove spaces.
    slug = slug.replace(' ', '-')

    # Remove apostrophes.
    slug = slug.replace('\'', '')

    logger.debug(f"Slug: {slug} returned from input: {string}.")
    return slug


@lru_cache
def convert_slug_to_string(*,
                           slug: str
                           ) -> str:
    """
    Do the best west can to convert a slug back to a prettier string (we can't re-add apostrophes).

    :param slug: The slug to be converted.
    """
    # Add spaces back.
    string = slug.replace('-', ' ')

    # Add capital letter to each word.
    string = string.title()

    return string


def auction_price_get(*,
                      auction: dict
                      ) -> int:
    """
    The "price" of an auction can be in three different locations.
    Stackable units (eg. Linen Cloth) use 'unit_price'.
    Non-Stackable units (eg. A Mount) usually have a 'buyout' price, but if that's missing we query the current
    highest 'bid'.

    :param auction: The auction whose price needs to be queried.
    """

    # Commodities.
    if 'unit_price' in auction:
        return auction['unit_price']

    # Items (99% of the time).
    if 'buyout' in auction:
        return auction['buyout']

    # Items for strange people.
    return auction['bid']
