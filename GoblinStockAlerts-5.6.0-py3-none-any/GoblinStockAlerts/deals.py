"""
All code related to filtering and finding deals against the configuration set by the user / third party.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
from collections import defaultdict
from typing import Dict

from .helpers import auction_price_get
from .items import iii

logger = logging.getLogger("GSA")


def find_deals(*,
               realm_config: Dict,
               auctions: Dict,
               ) -> Dict:
    """
    Check the filtered auction list against deal criteria. If deals are found call deals_callback.

    :param realm_config: The configuration that has the shopping lists.
    :param auctions: The filtered auctions.
    """
    deals = {
        'items': defaultdict(list),
        'pets': defaultdict(list)
    }

    # Items
    for item in realm_config.get('items', []):

        for auction in auctions.get('items', {}).get(item, []):
            
            item_data = realm_config['items'][item]

            if item_data['budget'] > 0:
                if auction_price_get(auction=auction) > item_data['budget']:
                    continue

            if 'ilvl' in item_data and item_data['ilvl'] != 0:
                ilvl, _ = iii(auction)
                if item_data['ilvl'] != ilvl:
                    continue

            deals['items'][item].append(auction)

    # Pets
    for pet in realm_config.get('pets', []):

        for auction in auctions.get('pets', {}).get(pet, []):
            
            pet_data = realm_config['pets'][pet]

            if pet_data['budget'] > 0:
                if auction_price_get(auction=auction) > pet_data['budget']:
                    continue

            if 'quality' in pet_data:
                if auction['item']['pet_quality_id'] not in pet_data['quality']:
                    continue

            if 'breed' in pet_data:
                if auction['item']['pet_breed_id'] not in pet_data['breed']:
                    continue

            if 'level' in pet_data:
                if auction['item']['pet_level'] != pet_data['level']:
                    continue

            deals['pets'][pet].append(auction)

    return deals
