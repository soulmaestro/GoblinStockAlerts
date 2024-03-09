"""
One function responsible for downloading and filtering Auction House data, workers will use this function only.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
from datetime import datetime, timedelta
from traceback import format_exc
from typing import List, Tuple, Dict, Optional

from GameAPI.blizzard import BlizzardAPI
from GameAPI.blizzard.errors import BlizzardAPIException, BlizzardAPIQuotaException, BlizzardAPIUnmodifiedData

from .deals import find_deals
from .pets import PET_CAGE_ID
from .state import STATE_ERROR, STATE_ERROR_QUOTA, STATE_NEW_DATA, STATE_SCHEDULED

logger = logging.getLogger("GSA")


def download_auction_house_and_find_deals(*,
                                          api: BlizzardAPI,
                                          connected_realm_id: int,
                                          shopping_list: Dict,
                                          modified_timestamp: datetime,
                                          ) -> Tuple[int, str, Dict, Optional[int], Optional[datetime], Optional[str]]:
    """
    Down an auction houses data and return items that are either in items_to_get or pets_to_get to reduce IPC between
    processes.

    :param api: An initialized BlizzardAPI object.
    :param connected_realm_id: The realm to query.
    :param shopping_list: TODO: Fill in.
    :param modified_timestamp: The timestamp to be transmitted to Blizzard for the If-Modified-Since header.
    """

    auctions = []
    auctions_with_deals = {
        "items": [],
        "pets": []
    }

    # This should be overwritten by the API query.
    last_modified_blizzard = None
    data_hash_blizzard = None
    desync = None

    error = ""

    try:
        # It seems Blizzard doesn't respect their old last modified times, add a little bit of time to it to account
        # for Blizzard servers being desynced.
        response = api.wow.auctions(connected_realm_id, modified_since=modified_timestamp + timedelta(minutes=10))
        auctions = response.get('auctions', [])
        last_modified_blizzard = response['GameAPI_Last_Modified']
        data_hash_blizzard = response['GameAPI_Data_SHA256']
        desync = response['GameAPI_Local_Server_Desync']
        status = STATE_NEW_DATA

    except BlizzardAPIQuotaException:
        status = STATE_ERROR_QUOTA

    except BlizzardAPIUnmodifiedData:
        status = STATE_SCHEDULED

    except BlizzardAPIException as ex:
        # This could indicate a networking issue but is "harmless", so display to user without a traceback.
        # Connection Resets are fairly normal, and scare users so we'll swallow them.
        error = f"{repr(ex)}" if "ConnectionResetError" not in repr(ex) else ""
        status = STATE_ERROR

    except Exception as ex:
        # This shouldn't happen, it's most likely a bug if it does. Supply traceback so it can be fixed.
        error = f"{ex} {format_exc()}"
        status = STATE_ERROR

    if status == STATE_NEW_DATA:

        try:
            # A single pass over auctions to smash them together, this means efficient indexing can be used
            auctions = index_auctions_into_items_pets(auctions=auctions)

            # Only returned items that are deals
            auctions_with_deals = find_deals(realm_config=shopping_list, auctions=auctions)

        except Exception as ex:
            # This shouldn't happen, it's most likely a bug if it does. Supply traceback so it can be fixed.
            error = f"{ex} {format_exc()}"
            status = STATE_ERROR

    return status, error, auctions_with_deals, desync, last_modified_blizzard, data_hash_blizzard


def index_auctions_into_items_pets(*, auctions: List) -> Dict:
    index = {
        "items": {},
        "pets": {}
    }

    for auction in auctions:
        item_id = auction['item']['id']
        if item_id == PET_CAGE_ID:
            pet_species_id = auction['item']['pet_species_id']

            if pet_species_id in index['pets']:
                index['pets'][pet_species_id].append(auction)
            else:
                index['pets'][pet_species_id] = [auction]

        else:
            if item_id in index['items']:
                index['items'][item_id].append(auction)
            else:
                index['items'][item_id] = [auction]

    return index
