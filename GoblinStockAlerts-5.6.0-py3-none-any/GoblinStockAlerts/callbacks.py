"""
All current and future callbacks (unless third party) should live here. Initially just UI/Addon.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.

TODO: THIS FILE IS PARTICULARLY "SPAGHETTI" AND NEEDS WORK.
"""

import logging
from collections import defaultdict
from typing import Dict, List

from tabulate import tabulate

from .addon import write_deals_to_data_file
from .helpers import auction_price_get, convert_copper_value_to_gold_string
from .items import iii
from .local_data import load_db
from .pets import get_pet_quality_from_db, get_pet_breed_from_db
from .realms import get_pretty_list_of_realms_on_connected_id

logger = logging.getLogger("GSA")


def send_to_logger_and_addon(*,
                             configuration: Dict,
                             connected_realm_id: int,
                             item_deals: Dict,
                             pet_deals: Dict,
                             addon_path: str
                             ) -> None:
    """
    A potential callback function.

    Send found deals to the UI (via logging) and the GSA addon if set to 'addon: True'.

    :param configuration: The configuration that has the shopping lists.
    :param connected_realm_id: The connected realm the auctions are from.
    :param item_deals: A list of confirmed deals that are items.
    :param pet_deals: A list of confirmed deals that are pets.
    :param addon_path: The path to the user's World of Warcraft addon folder.
    """
    tmp = []
    for _, v in item_deals.items():
        tmp.extend(v)
    item_deals = tmp

    tmp = []
    for _, v in pet_deals.items():
        tmp.extend(v)
    pet_deals = tmp

    if not any((item_deals, pet_deals)):
        return

    if addon_path:
        # Send deals to the addon database file
        send_to_addon(deals_items=item_deals, deals_pets=pet_deals, addon_path=addon_path,
                      connected_realm_id=connected_realm_id)

    # Present deals on the UI (Console Window)
    send_to_logger(configuration=configuration, deals_items=item_deals, deals_pets=pet_deals,
                   connected_realm_id=connected_realm_id)


def send_to_logger(*,
                   configuration: Dict,
                   connected_realm_id: int,
                   deals_pets: List,
                   deals_items: List
                   ) -> None:
    """
    Show specified deals on the UI via Python logging.

    :param configuration: The configuration that has the shopping lists.
    :param connected_realm_id: The connected realm the auctions are from.
    :param deals_pets: A list of confirmed deals that are items.
    :param deals_items: A list of confirmed deals that are pets.
    """

    items_formatted = {}
    for item in deals_items:
        c = configuration['realms'][connected_realm_id]['items'][item['item']['id']]

        if item['item']['id'] not in items_formatted:
            items_formatted[item['item']['id']] = {
                'name': c['nickname'],
                'quantity': item['quantity'],
                'minimum_price': auction_price_get(auction=item),
                'minimum_price_bid': 'buyout' not in item and 'unit_price' not in item,
                'maximum_price': auction_price_get(auction=item),
                'maximum_price_bid': 'buyout' not in item and 'unit_price' not in item,
                'budget': convert_copper_value_to_gold_string(copper_price=c['budget'])
            }

        else:
            if auction_price_get(auction=item) > items_formatted[item['item']['id']]['maximum_price']:
                items_formatted[item['item']['id']]['maximum_price'] = auction_price_get(auction=item)
                items_formatted[item['item']['id']][
                    'maximum_price_bid'] = 'buyout' not in item and 'unit_price' not in item

            if auction_price_get(auction=item) < items_formatted[item['item']['id']]['minimum_price']:
                items_formatted[item['item']['id']]['minimum_price'] = auction_price_get(auction=item)
                items_formatted[item['item']['id']][
                    'minimum_price_bid'] = 'buyout' not in item and 'unit_price' not in item

            items_formatted[item['item']['id']]['quantity'] += item['quantity']

    if items_formatted:
        for item in items_formatted:
            items_formatted[item]['minimum_price'] = \
                convert_copper_value_to_gold_string(copper_price=items_formatted[item]['minimum_price'])
            if items_formatted[item]['minimum_price_bid']:
                items_formatted[item][
                    'minimum_price'] = f"\u001b[31m{items_formatted[item]['minimum_price']} [BID ONLY]\033[0m"

            items_formatted[item]['maximum_price'] = \
                convert_copper_value_to_gold_string(copper_price=items_formatted[item]['maximum_price'])
            if items_formatted[item]['maximum_price_bid']:
                items_formatted[item][
                    'maximum_price'] = f"\u001b[31m{items_formatted[item]['maximum_price']} [BID ONLY]\033[0m"

            del items_formatted[item]['maximum_price_bid']
            del items_formatted[item]['minimum_price_bid']

    item_string = ""
    if items_formatted:
        item_string = "\n{}\n".format(tabulate([items_formatted[x].values() for x in items_formatted],
                                               ['Item Name', 'Quantity', 'Minimum', 'Maximum', 'Budget']))

    pets_formatted = []
    for pet in deals_pets:
        c = configuration['realms'][connected_realm_id]['pets'][pet['item']['pet_species_id']]
        p = {
            "name": c['nickname'],
            "level": pet['item']['pet_level'],
            "quality": get_pet_quality_from_db(pet_quality_id=pet['item']['pet_quality_id']),
            "breed": get_pet_breed_from_db(pet_breed_id=pet['item']['pet_breed_id']),
            "price": convert_copper_value_to_gold_string(copper_price=auction_price_get(auction=pet)),
            "budget": convert_copper_value_to_gold_string(copper_price=c['budget'])
        }

        if 'unit_price' not in pet and 'buyout' not in pet:
            p['price'] = f"\u001b[31m{p['price']} [BID ONLY]\033[0m"
        pets_formatted.append(p)

    pet_string = ""
    if len(pets_formatted) > 0:
        pets_formatted = sorted(pets_formatted, key=lambda k: k['level'], reverse=True)
        pet_string = "\n{}\n".format(tabulate([x.values() for x in pets_formatted],
                                              ['Pet Name', 'Level', 'Quality', 'Breed', 'Price', 'Budget']))

    if connected_realm_id in configuration['configuration'].get('connected_realm_nicknames', {}):
        realms = configuration['configuration']['connected_realm_nicknames'][connected_realm_id]
    else:
        realms = ', '.join(get_pretty_list_of_realms_on_connected_id(connected_realm_id=connected_realm_id,
                                                                     region=configuration['configuration']['region']))
    print(f"\u001b[1;32m{realms}\033[0m - DEALS FOUND!{item_string}{pet_string}")


def send_to_addon(*,
                  connected_realm_id: int,
                  deals_pets: List,
                  deals_items: List,
                  addon_path: str
                  ) -> None:
    """
    Construct the dictionary that the addon requires and call the follow-on function to write it to disk.

    :param connected_realm_id: The connected realm the deals are on.
    :param deals_pets: The list of deals that are pets.
    :param deals_items The list of deals that are items.
    :param addon_path: The path to the user's World of Warcraft addon folder.
    :return:
    """

    deals = {
        "GSAData":
            {
                connected_realm_id: []
            }
    }

    for pet in deals_pets:
        deals["GSAData"][connected_realm_id].append(
            {
                "item_id": pet['item']['id'],
                "auction_id": pet['id'],
                "pet_id": pet['item']['pet_species_id'],
                "value": auction_price_get(auction=pet)
            }
        )

    # Smash commodities together first
    deals_items = smash_commodities_together(deals_items=deals_items)

    for item in deals_items:
        item_metadata = {
            "item_id": item['item']['id'],
            "auction_id": item['id'],
            "value": auction_price_get(auction=item),
            "quantity": item['quantity']
        }

        if 'unit_price' not in item:
            item_level, suffix = iii(item)

            if item_level > 0:
                item_metadata['item_level'] = item_level

            if suffix:
                suffix_db = load_db(db='item_metadata.json')
                item_metadata['item_suffix'] = suffix_db[suffix]

        deals["GSAData"][connected_realm_id].append(item_metadata)
    deals["GSAData"][connected_realm_id].reverse()

    write_deals_to_data_file(addon_directory=addon_path, deals=deals)


def smash_commodities_together(*,
                               deals_items: List
                               ) -> List:
    """
    Commodities use the most recent Auction House ID, even though behind the scenes there's separate auctions.

    So for every price point of every commodity smash it together under one id.

    :param deals_items: All the item deals, including non-commodities.
    """
    logger.debug(f"{len(deals_items)} item auctions in to the smasher.")

    # First let's remove all commodities from the deals
    deals_commodities = []
    out = []

    for item in deals_items:
        if 'unit_price' in item:
            deals_commodities.append(item)
        else:
            out.append(item)

    tmp = defaultdict(dict)  # Yea ignore this.

    # Now let the smashing commence.
    for commodity in deals_commodities:
        item_id = commodity['item']['id']
        item_price = commodity['unit_price']

        # If the item isn't there at all
        if item_id not in tmp:
            # Add a reference at the exact price
            tmp[item_id][item_price] = commodity

        else:
            # If the item is not there at the same price point
            if item_price not in tmp[item_id]:
                tmp[item_id][item_price] = commodity

            else:
                tmp[item_id][item_price]['quantity'] += commodity['quantity']

    for commodity in tmp:
        for price_point in sorted(list(tmp[commodity]), reverse=True):
            out.append(tmp[commodity][price_point])

    logger.debug(f"{len(out)} item auctions out of the smasher.")
    return out
