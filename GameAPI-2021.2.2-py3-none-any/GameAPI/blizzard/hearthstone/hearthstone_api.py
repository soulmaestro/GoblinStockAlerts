"""
Copyright (C) 2021 https://github.com/binaryhabitat.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from typing import Union

from GameAPI.blizzard.base_api import BaseAPI


class HearthstoneAPI(BaseAPI):

    def __init__(self, client_id: str, client_secret: str, region: str):
        super().__init__(client_id, client_secret, region)
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_region = region

    # Cards APIs
    def card_search(self, **params: dict) -> dict:
        """
        Returns an up-to-date list of all cards matching the search criteria. (eg. health, attack, manaCost)
        """
        resource = "/hearthstone/cards"

        return self.request(resource, params)

    def fetch_one_card(self, id_or_slug: Union[str, int]) -> dict:
        """
        Returns the card with an ID or slug that matches the one you specify.
        """
        resource = f"/hearthstone/cards/{id_or_slug}"

        return self.request(resource)

    # Card Backs APIs
    def card_back_search(self, **params: dict) -> dict:
        """
        Returns an up-to-date list of all card backs matching the search criteria. (eg. cardBackCategory)
        """
        resource = "/hearthstone/cardbacks"

        return self.request(resource, params)

    def fetch_one_card_back(self, id_or_slug: Union[str, int]) -> dict:
        """
        Returns a specific card back by using card back ID or slug.
        """
        resource = f"/hearthstone/cardbacks/{id_or_slug}"

        return self.request(resource)

    # Decks APIs
    def get_deck_by_code(self, **params: dict) -> dict:
        """
        Finds a deck by deck code.
        """
        resource = "/hearthstone/deck"

        return self.request(resource, params)

    def get_deck_by_card_list(self, **params: dict) -> dict:
        """
        Finds a deck by list of cards, including the hero.
        """
        resource = "/hearthstone/deck"

        return self.request(resource, params)

    # Metadata APIs
    def all_metadata(self) -> dict:
        """
        Returns the card with an ID or slug that matches the one you specify.
        """
        resource = "/hearthstone/metadata"

        return self.request(resource)

    def specific_metadata(self, metadata_type: str) -> dict:
        """
        Returns information about just one type of metadata.
        """
        resource = f"/hearthstone/metadata/{metadata_type}"

        return self.request(resource)
