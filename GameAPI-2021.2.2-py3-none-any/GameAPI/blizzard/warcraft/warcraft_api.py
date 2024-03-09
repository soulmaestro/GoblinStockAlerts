"""
Copyright (C) 2021 https://github.com/binaryhabitat.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

import re
from datetime import datetime
from typing import Optional, Union

from GameAPI.blizzard.base_api import BaseAPI
from GameAPI.blizzard.errors import BlizzardAPIException


class WarcraftAPI(BaseAPI):

    def __init__(self, client_id: str, client_secret: str, region: str, classic: str = ""):
        super().__init__(client_id, client_secret, region)
        self.classic = classic

    def _request_gateway(self, resource: str, parameters: dict, modified_since: Optional[datetime] = None) -> dict:
        """
        A gateway method that raises an exception if the API requested is not a
        valid request for the Warcraft Classic API.

        :param resource: The resource being requested (eg. /data/wow/connected-realm/index)
        :param parameters: The parameters for the request, (eg. the namespace 'static')
        :param modified_since: A datetime object for use in a If-Modified-Since HTTP header
        """
        namespace = f"{parameters.get('namespace', '')}-{self.api_region}"

        if self.classic == "Vanilla" and "classic1x-" not in namespace:
            raise BlizzardAPIException(f"{resource} ({namespace}) is not a valid Warcraft Classic (Vanilla) request.")
        elif self.classic == "TBC" and "classic-" not in namespace:
            raise BlizzardAPIException(f"{resource} ({namespace}) is not a valid Warcraft Classic (TBC) request.")

        parameters["namespace"] = namespace
        parameters["locale"] = "en_US"

        # For large requests (especially auction house data) implement If-Modified-Since.
        headers = {}
        if modified_since:
            if not isinstance(modified_since, datetime):
                raise TypeError(f"Supplied modified_since '{modified_since}' is not a valid datetime.")

            headers["If-Modified-Since"] = modified_since.strftime("%a, %d %b %Y %H:%M:%S GMT")

        return self.request(resource, parameters, headers)

    # Achievement APIs
    def achievement_categories_index(self) -> dict:
        """
        Returns an index of achievement categories.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/achievement-category/index"

        return self._request_gateway(resource, params)

    def achievement_category(self, achievement_category_id: int) -> dict:
        """
        Returns an achievement category by ID.

        :param achievement_category_id: The ID of the achievement category.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/achievement-category/{achievement_category_id}"

        return self._request_gateway(resource, params)

    def achievement_index(self) -> dict:
        """
        Returns an index of achievements.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/achievement/index"

        return self._request_gateway(resource, params)

    def achievement(self, achievement_id: int) -> dict:
        """
        Returns an achievement by ID.

        :param achievement_id: The ID of the achievement.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/achievement/{achievement_id}"

        return self._request_gateway(resource, params)

    def achievement_media(self, achievement_id: int) -> dict:
        """
        Returns media for an achievement by ID.

        :param achievement_id: The ID of the achievement.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/achievement/{achievement_id}"

        return self._request_gateway(resource, params)

    # Auction APIs
    def auctions(self, connected_realm_id: int, modified_since: Optional[datetime] = None) -> dict:
        """
        Returns all active auctions for a connected realm.

        Depending on the number of active auctions on the specified connected realm,
        the response from this endpoint may be rather large, sometimes exceeding 10 MB.

        :param connected_realm_id: The ID of the connected realm.
        :param modified_since: Only return data if its newer than the datetime specified
        """
        params = {"namespace": "dynamic"}

        resource = f"/data/wow/connected-realm/{connected_realm_id}/auctions"

        return self._request_gateway(resource, params, modified_since)

    def auction_index(self, connected_realm_id: int) -> dict:
        """
        Returns the auction index's for a connected realm.

        :param connected_realm_id: The ID of the connected realm.
        """
        params = {"namespace": "dynamic-classic"}

        if not self.classic == "TBC":
            raise BlizzardAPIException("This end point is only for Classic (TBC).")

        resource = f"/data/wow/connected-realm/{connected_realm_id}/auctions/index"

        return self._request_gateway(resource, params)

    def auction_house(
            self,
            connected_realm_id: int,
            auction_house: str,
            modified_since: Optional[datetime] = None
    ) -> dict:
        """
        Returns all active auctions for a connected realm at a specific auction house.

        Depending on the number of active auctions on the specified connected realm,
        the response from this endpoint may be rather large, sometimes exceeding 10 MB.

        :param auction_house: ALLIANCE, HORDE, or NEUTRAL.
        :param connected_realm_id: The ID of the connected realm.
        :param modified_since: Only return data if its newer than the datetime specified
        """
        params = {"namespace": "dynamic-classic"}

        if not self.classic == "TBC":
            raise BlizzardAPIException("This end point is only for Classic (TBC).")

        auction_house = auction_house.upper()

        if auction_house == "ALLIANCE":
            resource = f"/data/wow/connected-realm/{connected_realm_id}/auctions/2"
        elif auction_house == "HORDE":
            resource = f"/data/wow/connected-realm/{connected_realm_id}/auctions/6"
        elif auction_house in ("NEUTRAL", "BLACKWATER"):
            resource = f"/data/wow/connected-realm/{connected_realm_id}/auctions/7"
        else:
            raise BlizzardAPIException(f"'{auction_house}' is not a valid Auction House.")

        return self._request_gateway(resource, params, modified_since)

    # Azerite Essence APIs
    def azerite_essences_index(self) -> dict:
        """
        Returns an index of azerite essences.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/azerite-essence/index"

        return self._request_gateway(resource, params)

    def azerite_essence(self, azerite_essence_id: int) -> dict:
        """
        Returns an azerite essence by ID.

        :param azerite_essence_id: The ID of the Azerite Essence
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/azerite-essence/{azerite_essence_id}"

        return self._request_gateway(resource, params)

    def azerite_essence_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of azerite essences.
        """
        raise NotImplementedError()

    def azerite_essence_media(self, azerite_essence_id: int) -> dict:
        """
        Returns media for an azerite essence by ID.

        :param azerite_essence_id: The ID of the Azerite Essence
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/azerite-essence/{azerite_essence_id}"

        return self._request_gateway(resource, params)

    # Connected Realm APIs
    def connected_realm_index(self, add_id_to_realm: bool = True) -> dict:
        """
        Returns an index of connected realms.

        :param add_id_to_realm: Blizzard API returns data in the following format,
                                unless disabled, the data will be enriched to add an "id" field to the anonymous
                                dicts. If you don't want this behaviour for any reason, specify False.

                                "connected_realms": [{
                                "href": "https://us.api.blizzard.com/data/wow/connected-realm/4?namespace=dynamic-us"
                                },{
                                "href": "https://us.api.blizzard.com/data/wow/connected-realm/5?namespace=dynamic-us"
                                }]

                                Becomes

                                "connected_realms": [{
                                "href": "https://us.api.blizzard.com/data/wow/connected-realm/4?namespace=dynamic-us",
                                "id": 4
                                },{
                                "href": "https://us.api.blizzard.com/data/wow/connected-realm/5?namespace=dynamic-us",
                                "id": 5
                                }]
        """
        params = {"namespace": "dynamic"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/connected-realm/index"

        data = self._request_gateway(resource, params)

        if add_id_to_realm:
            for realm in data.get("connected_realms", {}):
                try:
                    # Group 1: https://{region}.api.warcraft.com/data/wow/connected-realm/
                    # Group 2: connected_realm_id
                    # Group 3: ?namespace=dynamic-{region}
                    match = re.search(r"(https\S*realm/)([0-9]*)(\?\S*)", realm.get("href", ""))
                    if match:
                        realm["id"] = int(match.group(2))
                except (IndexError, re.error):
                    pass

        return data

    def connected_realm(self, connected_realm_id: int) -> dict:
        """
        Returns a connected realm by ID.

        :param connected_realm_id: The ID of the connected realm.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/connected-realm/{connected_realm_id}"

        return self._request_gateway(resource, params)

    def connected_realm_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of connected realms
        """
        raise NotImplementedError()

    # Covenant APIs
    def covenant_index(self) -> dict:
        """
        Returns an index of covenants.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/covenant/index"

        return self._request_gateway(resource, params)

    def covenant(self, covenant_id: int) -> dict:
        """
        Returns a covenant by ID.

        :param covenant_id: The ID of the covenant.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/covenant/{covenant_id}"

        return self._request_gateway(resource, params)

    def covenant_media(self, covenant_id: int) -> dict:
        """
        Returns media for a covenant by ID.

        :param covenant_id: The ID of the covenant.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/covenant/{covenant_id}"

        return self._request_gateway(resource, params)

    def soulbind_index(self) -> dict:
        """
        Returns an index of soulbinds.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/covenant/soulbind/index"

        return self._request_gateway(resource, params)

    def soulbind(self, soulbind_id: int) -> dict:
        """
        Returns a soulbind by ID.

        :param soulbind_id: The ID of the soulbind.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/covenant/soulbind/{soulbind_id}"

        return self._request_gateway(resource, params)

    def conduit_index(self) -> dict:
        """
        Returns an index of conduits.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/covenant/conduit/index"

        return self._request_gateway(resource, params)

    def conduit(self, conduit_id: int) -> dict:
        """
        Returns a conduit by ID.

        :param conduit_id: The ID of the conduit.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/covenant/conduit/{conduit_id}"

        return self._request_gateway(resource, params)

    # Creature APIs
    def creature_families_index(self) -> dict:
        """
        Returns an index of creature families.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/creature-family/index"

        return self._request_gateway(resource, params)

    def creature_family(self, creature_family_id: int) -> dict:
        """
        Returns a creature family by ID.

        :param creature_family_id: The ID of the creature family.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/creature-family/{creature_family_id}"

        return self._request_gateway(resource, params)

    def creature_types_index(self) -> dict:
        """
        Returns an index of creature types.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/creature-type/index"

        return self._request_gateway(resource, params)

    def creature_type(self, creature_type_id: int) -> dict:
        """
        Returns a creature type by ID.

        :param creature_type_id: The ID of the creature type.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/creature-type/{creature_type_id}"

        return self._request_gateway(resource, params)

    def creature(self, creature_id: int) -> dict:
        """
        Returns a creature by ID.

        :param creature_id: The ID of the creature.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/creature/{creature_id}"

        return self._request_gateway(resource, params)

    def creature_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of creatures.
        """
        raise NotImplementedError()

    def creature_display_media(self, creature_display_id: int) -> dict:
        """
        Returns media for a creature display by ID.

        :param creature_display_id: The ID of the creature display.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/media/creature-display/{creature_display_id}"

        return self._request_gateway(resource, params)

    def creature_family_media(self, creature_family_id: int) -> dict:
        """
        Returns media for a creature family by ID.

        :param creature_family_id: The ID of the creature family.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/media/creature-family/{creature_family_id}"

        return self._request_gateway(resource, params)

    # Guild Crest APIs
    def guild_crest_components_index(self) -> dict:
        """
        Returns an index of guild crest media.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/guild-crest/index"

        return self._request_gateway(resource, params)

    def guild_crest_border_media(self, border_id: int) -> dict:
        """
        Returns media for a guild crest border by ID.

        :param border_id: The ID of the guild crest border.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/media/guild-crest/border/{border_id}"

        return self._request_gateway(resource, params)

    def guild_crest_emblem_media(self, emblem_id: int) -> dict:
        """
        Returns media for a guild crest emblem by ID.

        :param emblem_id: The ID of the guild crest emblem.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/media/guild-crest/emblem/{emblem_id}"

        return self._request_gateway(resource, params)

    # Item APIs
    def item_classes_index(self) -> dict:
        """
        Returns an index of item classes.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/item-class/index"

        return self._request_gateway(resource, params)

    def item_class(self, item_class_id: int) -> dict:
        """
        Returns an item class by ID.

        :param item_class_id: The ID of the item class.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/item-class/{item_class_id}"

        return self._request_gateway(resource, params)

    def item_sets_index(self) -> dict:
        """
        Returns an index of item sets.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/item-set/index"

        return self._request_gateway(resource, params)

    def item_set(self, item_set_id: int) -> dict:
        """
        Returns an item set by ID.

        :param item_set_id: The ID of the item set.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/item-set/{item_set_id}"

        return self._request_gateway(resource, params)

    def item_subclass(self, item_class_id: int, item_subclass_id: int) -> dict:
        """
        Returns an item subclass by ID.

        :param item_class_id: The ID of the item class.
        :param item_subclass_id: The ID of the item subclass.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/item-class/{item_class_id}/item-subclass/{item_subclass_id}"

        return self._request_gateway(resource, params)

    def item(self, item_id: int) -> dict:
        """
        Returns an item by ID.

        :param item_id: The ID of the item.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/item/{item_id}"

        return self._request_gateway(resource, params)

    def item_media(self, item_id: int) -> dict:
        """
        Returns media for an item by ID.

        :param item_id: The ID of the item.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/media/item/{item_id}"

        return self._request_gateway(resource, params)

    def item_search(self, **kwargs: dict) -> dict:
        """
        Performs a search of items.
        """
        params: dict = {"namespace": "static"}
        resource = "/data/wow/search/item"

        return self._request_gateway(resource, params | kwargs)

    # Journal APIs
    def journal_expansions_index(self) -> dict:
        """
        Returns an index of journal expansions.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/journal-expansion/index"

        return self._request_gateway(resource, params)

    def journal_expansion(self, journal_expansion_id: int) -> dict:
        """
        Returns a journal expansion by ID.

        :param journal_expansion_id: The ID of the journal expansion.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/journal-expansion/{journal_expansion_id}"

        return self._request_gateway(resource, params)

    def journal_encounters_index(self) -> dict:
        """
        Returns an index of journal encounters.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/journal-encounter/index"

        return self._request_gateway(resource, params)

    def journal_encounter(self, journal_encounter_id: int) -> dict:
        """
        Returns a journal encounter by ID.

        :param journal_encounter_id: The ID of the journal encounter.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/journal-encounter/{journal_encounter_id}"

        return self._request_gateway(resource, params)

    def journal_encounter_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of journal encounters.
        """
        raise NotImplementedError()

    def journal_instances_index(self) -> dict:
        """
        Returns an index of journal instances.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/journal-instance/index"

        return self._request_gateway(resource, params)

    def journal_instance(self, journal_instance_id: int) -> dict:
        """
        Returns a journal instance.

        :param journal_instance_id: The ID of the journal instance.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/journal-instance/{journal_instance_id}"

        return self._request_gateway(resource, params)

    def journal_instance_media(self, journal_instance_id: int) -> dict:
        """
        Returns media for a journal instance by ID.

        :param journal_instance_id: The ID of the journal instance.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/journal-instance/{journal_instance_id}"

        return self._request_gateway(resource, params)

    # Media Search APIs
    def media_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of all types of media documents.
        """
        raise NotImplementedError()

    # Modified Crafting APIs
    def modified_crafting_index(self) -> dict:
        """
        Returns the parent index for Modified Crafting.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/modified-crafting/index"

        return self._request_gateway(resource, params)

    def modified_crafting_category_index(self) -> dict:
        """
        Returns the index of Modified Crafting categories.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/modified-crafting/category/index"

        return self._request_gateway(resource, params)

    def modified_crafting_category(self, category_id: int) -> dict:
        """
        Returns a Modified Crafting category by ID.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/modified-crafting/category/{category_id}"

        return self._request_gateway(resource, params)

    def modified_crafting_reagent_slot_type_index(self) -> dict:
        """
        Returns the index of Modified Crafting reagent slot types.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/modified-crafting/reagent-slot-type/index"

        return self._request_gateway(resource, params)

    def modified_crafting_reagent_slot_type(self, slot_type_id: int) -> dict:
        """
        Returns a Modified Crafting reagent slot type by ID.

        :param slot_type_id: The ID of the Modified Crafting reagent slot type.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/modified-crafting/reagent-slot-type/{slot_type_id}"

        return self._request_gateway(resource, params)

    # Mount APIs
    def mounts_index(self) -> dict:
        """
        Returns an index of mounts.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/mount/index"

        return self._request_gateway(resource, params)

    def mount(self, mount_id: int) -> dict:
        """
        Returns a mount by ID.

        :param mount_id: The ID of the mount.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/mount/{mount_id}"

        return self._request_gateway(resource, params)

    def mount_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of mounts.
        """
        raise NotImplementedError()

    # Mythic Keystone Affix APIs
    def mythic_keystone_affixes_index(self) -> dict:
        """
        Returns an index of mythic keystone affixes.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/keystone-affix/index"

        return self._request_gateway(resource, params)

    def mythic_keystone_affix(self, keystone_affix_id: int) -> dict:
        """
        Returns a mythic keystone affix by ID.

        :param keystone_affix_id: The ID of the mythic keystone affix.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/keystone-affix/{keystone_affix_id}"

        return self._request_gateway(resource, params)

    def mythic_keystone_affix_media(self, keystone_affix_id: int) -> dict:
        """
        Returns media for a mythic keystone affix by ID.

        :param keystone_affix_id: The ID of the mythic keystone affix.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/keystone-affix/{keystone_affix_id}"

        return self._request_gateway(resource, params)

    # Mythic Keystone Dungeon API
    def mythic_keystone_dungeon_index(self) -> dict:
        """
        Returns an index of Mythic Keystone dungeons.
        """
        params = {"namespace": "dynamic"}
        resource = "/data/wow/mythic-keystone/dungeon/index"

        return self._request_gateway(resource, params)

    def mythic_keystone_dungeon(self, dungeon_id: int) -> dict:
        """
        Returns a Mythic Keystone dungeon by ID.

        :param dungeon_id: The ID of the dungeon.
        """
        params = {"namespace": "dynamic"}
        resource = f"/data/wow/mythic-keystone/dungeon/{dungeon_id}"

        return self._request_gateway(resource, params)

    def mythic_keystone_index(self) -> dict:
        """
        Returns an index of links to other documents related to Mythic Keystone dungeons.
        """
        params = {"namespace": "dynamic"}
        resource = "/data/wow/mythic-keystone/index"

        return self._request_gateway(resource, params)

    def mythic_keystone_period_index(self) -> dict:
        """
        Returns an index of Mythic Keystone periods.
        """
        params = {"namespace": "dynamic"}
        resource = "/data/wow/mythic-keystone/period/index"

        return self._request_gateway(resource, params)

    def mythic_keystone_period(self, period_id: int) -> dict:
        """
        Returns a Mythic Keystone period by ID.

        :param period_id: The ID of the Mythic Keystone season period.
        """
        params = {"namespace": "dynamic"}
        resource = f"/data/wow/mythic-keystone/period/{period_id}"

        return self._request_gateway(resource, params)

    def mythic_keystone_season_index(self) -> dict:
        """
        Returns an index of Mythic Keystone seasons.
        """
        params = {"namespace": "dynamic"}
        resource = "/data/wow/mythic-keystone/season/index"

        return self._request_gateway(resource, params)

    def mythic_keystone_season(self, season_id: int) -> dict:
        """
        Returns a Mythic Keystone season by ID.

        :param season_id: The ID of the Mythic Keystone season.
        """
        params = {"namespace": "dynamic"}
        resource = f"/data/wow/mythic-keystone/season/{season_id}"

        return self._request_gateway(resource, params)

    # Mythic Keystone Leaderboard API
    def mythic_keystone_leaderboard_index(self, connected_realm_id: int) -> dict:
        """
        Returns an index of Mythic Keystone Leaderboard dungeon instances for a connected realm.

        :param connected_realm_id: The ID of the connected realm.
        """
        params = {"namespace": "dynamic"}
        resource = f"/data/wow/connected-realm/{connected_realm_id}/mythic-leaderboard/index"

        return self._request_gateway(resource, params)

    def mythic_keystone_leaderboard(self, connected_realm_id: int, dungeon_id: int, period_id: int) -> dict:
        """
        Returns a weekly Mythic Keystone Leaderboard by period.

        :param connected_realm_id: The ID of the connected realm.
        :param dungeon_id: The ID of the dungeon.
        :param period_id: The unique identifier for the leaderboard period.
        """
        params = {"namespace": "dynamic"}
        resource = f"/data/wow/connected-realm/{connected_realm_id}/mythic-leaderboard/" \
                   f"{dungeon_id}/period/{period_id}"

        return self._request_gateway(resource, params)

    # Mythic Raid Leaderboard API
    def mythic_raid_leaderboard(self, raid: str, faction: str) -> dict:
        """
        Returns the leaderboard for a given raid and faction.

        :param raid: The raid for a leaderboard.
        :param faction: Player faction (`alliance` or `horde`).
        """
        params = {"namespace": "dynamic"}
        resource = f"/data/wow/leaderboard/hall-of-fame/{raid}/{faction}"

        return self._request_gateway(resource, params)

    # Pet API
    def pets_index(self) -> dict:
        """
        Returns an index of battle pets.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/pet/index"

        return self._request_gateway(resource, params)

    def pet(self, pet_id: int) -> dict:
        """
        Returns a battle pet by ID.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/pet/{pet_id}"

        return self._request_gateway(resource, params)

    def pet_media(self, pet_id: int) -> dict:
        """
        Returns media for a battle pet by ID.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/pet/{pet_id}"

        return self._request_gateway(resource, params)

    def pet_abilities_index(self) -> dict:
        """
        Returns an index of pet abilities.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/pet-ability/index"

        return self._request_gateway(resource, params)

    def pet_ability(self, pet_ability_id: int) -> dict:
        """
        Returns a pet ability by ID.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/pet-ability/{pet_ability_id}"

        return self._request_gateway(resource, params)

    def pet_ability_media(self, pet_ability_id: int) -> dict:
        """
        Returns media for a pet ability by ID.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/pet-ability/{pet_ability_id}"

        return self._request_gateway(resource, params)

    # Playable Class APIs
    def playable_classes_index(self) -> dict:
        """
        Returns an index of playable classes.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/playable-class/index"

        return self._request_gateway(resource, params)

    def playable_class(self, playable_class_id: int) -> dict:
        """
        Returns a playable class by ID.

        :param playable_class_id: The ID of the playable class.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/playable-class/{playable_class_id}"

        return self._request_gateway(resource, params)

    def playable_class_media(self, playable_class_id: int) -> dict:
        """
        Returns media for a playable class by ID.

        :param playable_class_id: The ID of the playable class.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/media/playable-class/{playable_class_id}"

        return self._request_gateway(resource, params)

    def pvp_talent_slots(self, playable_class_id: int) -> dict:
        """
        Returns the PvP talent slots for a playable class by ID.

        :param playable_class_id: The ID of the playable class.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/playable-class/{playable_class_id}/pvp-talent-slots"

        return self._request_gateway(resource, params)

    # Playable Race APIs
    def playable_races_index(self) -> dict:
        """
        Returns an index of playable races.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/playable-race/index"

        return self._request_gateway(resource, params)

    def playable_race(self, playable_race_id: int) -> dict:
        """
        Returns a playable race by ID.

        :param playable_race_id: The ID of the playable race.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/playable-race/{playable_race_id}"

        return self._request_gateway(resource, params)

    # Playable Specialization APIs
    def playable_specializations_index(self) -> dict:
        """
        Returns an index of playable specializations.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/playable-specialization/index"

        return self._request_gateway(resource, params)

    def playable_specialization(self, playable_specialization_id: int) -> dict:
        """
        Returns a playable specialization by ID.

        :param playable_specialization_id: The ID of the playable specialization.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/playable-specialization/{playable_specialization_id}"

        return self._request_gateway(resource, params)

    def playable_specialization_media(self, playable_specialization_id: int) -> dict:
        """
        Returns media for a playable specialization by ID.

        :param playable_specialization_id: The ID of the playable specialization.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/playable-specialization/{playable_specialization_id}"

        return self._request_gateway(resource, params)

    # Power Type APIs
    def power_types_index(self) -> dict:
        """
        Returns an index of power types.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/power-type/index"

        return self._request_gateway(resource, params)

    def power_type(self, power_type_id: int) -> dict:
        """
        Returns a power type by ID.

        :param power_type_id: The ID of the power type.
        """
        params = {"namespace": "static"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/power-type/{power_type_id}"

        return self._request_gateway(resource, params)

    # Profession APIs
    def professions_index(self) -> dict:
        """
        Returns an index of professions.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/profession/index"

        return self._request_gateway(resource, params)

    def profession(self, profession_id: int) -> dict:
        """
        Returns a profession by ID.

        :param profession_id: The ID of the profession.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/profession/{profession_id}"

        return self._request_gateway(resource, params)

    def profession_media(self, profession_id: int) -> dict:
        """
        Returns a profession by ID.

        :param profession_id: The ID of the profession.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/profession/{profession_id}"

        return self._request_gateway(resource, params)

    def profession_skill_tier(self, profession_id: int, skill_tier_id: int) -> dict:
        """
        Returns a skill tier for a profession by ID.

        :param profession_id: The ID of the profession.
        :param skill_tier_id: The ID of the skill tier.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/profession/{profession_id}/skill-tier/{skill_tier_id}"

        return self._request_gateway(resource, params)

    def recipe(self, recipe_id: int) -> dict:
        """
        Returns a recipe by ID.

        :param recipe_id: The ID of the recipe.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/recipe/{recipe_id}"

        return self._request_gateway(resource, params)

    def recipe_media(self, recipe_id: int) -> dict:
        """
        Returns media for a recipe by ID.

        :param recipe_id: The ID of the recipe.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/recipe/{recipe_id}"

        return self._request_gateway(resource, params)

    # PvP Season APIs
    def pvp_seasons_index(self) -> dict:
        """
        Returns an index of PvP seasons.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"

        resource = "/data/wow/pvp-season/index"

        return self._request_gateway(resource, params)

    def pvp_season(self, pvp_season_id: int) -> dict:
        """
        Returns a PvP season by ID.

        :param pvp_season_id: The ID of the PvP season.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"

        resource = f"/data/wow/pvp-season/{pvp_season_id}"

        return self._request_gateway(resource, params)

    def pvp_leaderboards_index(self, pvp_season_id: int) -> dict:
        """
        Returns an index of PvP leaderboards for a PvP season.

        :param pvp_season_id: The ID of the PvP season.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"

        resource = f"/data/wow/pvp-season/{pvp_season_id}/pvp-leaderboard/index"

        return self._request_gateway(resource, params)

    def pvp_leaderboard(self, pvp_season_id: int, pvp_bracket: str) -> dict:
        """
        Returns the PvP leaderboard of a specific PvP bracket for a PvP season.

        :param pvp_season_id: The ID of the PvP season.
        :param pvp_bracket: The PvP bracket type.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"

        resource = f"/data/wow/pvp-season/{pvp_season_id}/pvp-leaderboard/{pvp_bracket}"

        return self._request_gateway(resource, params)

    def pvp_rewards_index(self, pvp_season_id: int) -> dict:
        """
        Returns an index of PvP rewards for a PvP season.

        :param pvp_season_id: The ID of the PvP season.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"

        resource = f"/data/wow/pvp-season/{pvp_season_id}/pvp-reward/index"

        return self._request_gateway(resource, params)

    # PvP Tier APIs
    def pvp_tier_media(self, pvp_tier_id: int) -> dict:
        """
        Returns media for a PvP tier by ID.

        :param pvp_tier_id: The ID of the PvP tier.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/pvp-tier/{pvp_tier_id}"

        return self._request_gateway(resource, params)

    def pvp_tiers_index(self) -> dict:
        """
        Returns an index of PvP tiers.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/pvp-tier/index"

        return self._request_gateway(resource, params)

    def pvp_tier(self, pvp_tier_id: int) -> dict:
        """
        Returns a PvP tier by ID.

        :param pvp_tier_id: The ID of the PvP tier.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/pvp-tier/{pvp_tier_id}"

        return self._request_gateway(resource, params)

    # Quest APIs
    def quests_index(self) -> dict:
        """
        Returns the parent index for quests.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/quest/index"

        return self._request_gateway(resource, params)

    def quest(self, quest_id: int) -> dict:
        """
        Returns a quest by ID.

        :param quest_id: The ID of the quest.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/quest/{quest_id}"

        return self._request_gateway(resource, params)

    def quest_categories_index(self) -> dict:
        """
        Returns an index of quest categories (such as quests for a specific class, profession, or storyline).
        """
        params = {"namespace": "static"}
        resource = "/data/wow/quest/category/index"

        return self._request_gateway(resource, params)

    def quest_category(self, quest_category_id: int) -> dict:
        """
        Returns a quest category by ID.

        :param quest_category_id: The ID of the quest category.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/quest/category/{quest_category_id}"

        return self._request_gateway(resource, params)

    def quest_areas_index(self) -> dict:
        """
        Returns an index of quest areas.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/quest/area/index"

        return self._request_gateway(resource, params)

    def quest_area(self, quest_area_id: int) -> dict:
        """
        Returns a quest area by ID.

        :param quest_area_id: The ID of the quest area.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/quest/area/{quest_area_id}"

        return self._request_gateway(resource, params)

    def quest_types_index(self) -> dict:
        """
        Returns an index of quest types (such as PvP quests, raid quests, or account quests).
        """
        params = {"namespace": "static"}
        resource = "/data/wow/quest/type/index"

        return self._request_gateway(resource, params)

    def quest_type(self, quest_type_id: int) -> dict:
        """
        Returns a quest type by ID.

        :param quest_type_id: The ID of the quest type.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/quest/type/{quest_type_id}"

        return self._request_gateway(resource, params)

    # Realm APIs
    def realms_index(self) -> dict:
        """
        Returns an index of realms.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/realm/index"

        return self._request_gateway(resource, params)

    def realm(self, realm_id: Union[int, str], add_id_to_realm: bool = True) -> dict:
        """
        Returns a single realm by slug or ID.

        :param realm_id: The slug or ID of the realm.
        :param add_id_to_realm: TODO: Document.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/realm/{realm_id}"

        data = self._request_gateway(resource, params)

        if add_id_to_realm:
            try:
                # Group 1: https://{region}.api.warcraft.com/data/wow/connected-realm/
                # Group 2: connected_realm_id
                # Group 3: ?namespace=dynamic-{region}
                match = re.search(r"(https\S*realm/)([0-9]*)(\?\S*)", data["connected_realm"].get("href", ""))
                if match:
                    data["connected_realm"]["id"] = int(match.group(2))
            except (IndexError, re.error):
                pass

        return data

    def realm_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of realms.
        """
        raise NotImplementedError()

    # Region APIs
    def regions_index(self) -> dict:
        """
        Returns an index of regions.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = "/data/wow/region/index"

        return self._request_gateway(resource, params)

    def region(self, region_id: int) -> dict:
        """
        Returns a region by ID.

        :param region_id: The ID of the region.
        """
        params = {"namespace": "dynamic"}
        if self.classic == "Vanilla":
            params["namespace"] = f"{params['namespace']}-classic1x"
        elif self.classic == "TBC":
            params["namespace"] = f"{params['namespace']}-classic"
        resource = f"/data/wow/region/{region_id}"

        return self._request_gateway(resource, params)

    # Reputations APIs
    def reputation_factions_index(self) -> dict:
        """
        Returns an index of reputation factions.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/reputation-faction/index"

        return self._request_gateway(resource, params)

    def reputation_faction(self, reputation_faction_id: int) -> dict:
        """
        Returns a single reputation faction by ID.

        :param reputation_faction_id: The ID of the reputation faction.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/reputation-faction/{reputation_faction_id}"

        return self._request_gateway(resource, params)

    def reputation_tiers_index(self) -> dict:
        """
        Returns an index of reputation tiers.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/reputation-tiers/index"

        return self._request_gateway(resource, params)

    def reputation_tier(self, reputation_tier_id: int) -> dict:
        """
        Returns a single set of reputation tiers by ID.

        :param reputation_tier_id: The ID of the reputation faction.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/reputation-tiers/{reputation_tier_id}"

        return self._request_gateway(resource, params)

    # Spell API
    def spell(self, spell_id: int) -> dict:
        """
        Returns a spell by ID.

        :param spell_id: The ID of the spell.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/spell/{spell_id}"

        return self._request_gateway(resource, params)

    def spell_media(self, spell_id: int) -> dict:
        """
        Returns media for a spell by ID.

        :param spell_id: The ID of the spell.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/spell/{spell_id}"

        return self._request_gateway(resource, params)

    def spell_search(self, **kwargs: dict) -> None:
        """
        NOT IMPLEMENTED. Performs a search of spells.
        """
        raise NotImplementedError()

    # Talent APIs
    def talents_index(self) -> dict:
        """
        Returns an index of talents.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/talent/index"

        return self._request_gateway(resource, params)

    def talent(self, talent_id: int) -> dict:
        """
        Returns a talent by ID.

        :param talent_id: The ID of the talent.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/talent/{talent_id}"

        return self._request_gateway(resource, params)

    def pvp_talents_index(self) -> dict:
        """
        Returns an index of PvP talents.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/pvp-talent/index"

        return self._request_gateway(resource, params)

    def pvp_talent(self, pvp_talent_id: int) -> dict:
        """
        Returns a PvP talent by ID.

        :param pvp_talent_id: The ID of the PvP talent.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/pvp-talent/{pvp_talent_id}"

        return self._request_gateway(resource, params)

    # Tech Talent APIs
    def tech_talent_tree_index(self) -> dict:
        """
        Returns an index of tech talent trees.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/tech-talent-tree/index"

        return self._request_gateway(resource, params)

    def tech_talent_tree(self, tech_talent_tree_id: int) -> dict:
        """
        Returns a tech talent tree by ID.

        :param tech_talent_tree_id: The ID of the tech talent tree.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/tech-talent-tree/{tech_talent_tree_id}"

        return self._request_gateway(resource, params)

    def tech_talent_index(self) -> dict:
        """
        Returns an index of tech talents.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/tech-talent/index"

        return self._request_gateway(resource, params)

    def tech_talent(self, tech_talent_id: int) -> dict:
        """
        Returns a tech talent by ID.

        :param tech_talent_id: The ID of the tech talent.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/tech-talent/{tech_talent_id}"

        return self._request_gateway(resource, params)

    def tech_talent_media(self, tech_talent_id: int) -> dict:
        """
        Returns media for a tech talent by ID.

        :param tech_talent_id: The ID of the tech talent.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/media/tech-talent/{tech_talent_id}"

        return self._request_gateway(resource, params)

    # Title APIs
    def titles_index(self) -> dict:
        """
        Returns an index of titles.
        """
        params = {"namespace": "static"}
        resource = "/data/wow/title/index"

        return self._request_gateway(resource, params)

    def title(self, title_id: int) -> dict:
        """
        Returns a title by ID.

        :param title_id: The ID of the title.
        """
        params = {"namespace": "static"}
        resource = f"/data/wow/title/{title_id}"

        return self._request_gateway(resource, params)

    # Token APIs
    def token(self) -> dict:
        """
        Returns the WoW Token index.
        """
        params = {"namespace": "dynamic"}
        resource = "/data/wow/token/index"

        return self._request_gateway(resource, params)

    # Account Profile APIs
    def account_profile_summary(self) -> dict:
        """
        Returns a profile summary for an account.

        Because this endpoint provides data about the current logged-in user's World of Warcraft account,
        it requires an access token with the wow.profile scope
        """
        params = {"namespace": "profile"}
        resource = "/profile/user/wow"

        return self._request_gateway(resource, params)

    def protected_character_profile_summary(self, realm_id: int, character_id: int) -> dict:
        """
        Returns a protected profile summary for a character.

        Because this endpoint provides data about the current logged-in user's World of Warcraft account,
        it requires an access token with the wow.profile scope

        :param realm_id: The ID of the character's realm.
        :param character_id: The ID of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/user/wow/protected-character/{realm_id}-{character_id}"

        return self._request_gateway(resource, params)

    def account_collections_index(self) -> dict:
        """
        Returns an index of collection types for an account.

        Because this endpoint provides data about the current logged-in user's World of Warcraft account,
        it requires an access token with the wow.profile scope
        """
        params = {"namespace": "profile"}
        resource = "/profile/user/wow/collections"

        return self._request_gateway(resource, params)

    def account_mounts_collection_summary(self) -> dict:
        """
        Returns a summary of the mounts an account has obtained.

        Because this endpoint provides data about the current logged-in user's World of Warcraft account,
        it requires an access token with the wow.profile scope
        """
        params = {"namespace": "profile"}
        resource = "/profile/user/wow/collections/mounts"

        return self._request_gateway(resource, params)

    def account_pets_collection_summary(self) -> dict:
        """
        Returns a summary of the battle pets an account has obtained.

        Because this endpoint provides data about the current logged-in user's World of Warcraft account,
        it requires an access token with the wow.profile scope
        """
        params = {"namespace": "profile"}
        resource = "/profile/user/wow/collections/pets"

        return self._request_gateway(resource, params)

    # Character Achievements API
    def character_achievements_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of the achievements a character has completed.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """

        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/achievements"

        return self._request_gateway(resource, params)

    def character_achievement_statistics(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a character's statistics as they pertain to achievements.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/achievements/statistics"

        return self._request_gateway(resource, params)

    # Character Appearance API
    def character_appearance_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of a character's appearance settings.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/appearance"

        return self._request_gateway(resource, params)

    # Character Collections APIs
    def character_collections_index(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns an index of collection types for a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/collections"

        return self._request_gateway(resource, params)

    def character_mounts_collection_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of the mounts a character has obtained.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/collections/mounts"

        return self._request_gateway(resource, params)

    def character_pets_collection_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of the battle pets a character has obtained.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/collections/pets"

        return self._request_gateway(resource, params)

    # Character Encounters APIs
    def character_encounters_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of a character's encounters.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/encounters"

        return self._request_gateway(resource, params)

    def character_dungeons(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of a character's completed dungeons.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/encounters/dungeons"

        return self._request_gateway(resource, params)

    def character_raids(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of a character's completed raids.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/encounters/raids"

        return self._request_gateway(resource, params)

    # Character Encounters APIs
    def character_equipment_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of the items equipped by a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/equipment"

        return self._request_gateway(resource, params)

    # Character Hunter Pets APIs
    def character_hunter_pets_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        If the character is a hunter, returns a summary of the character's hunter pets.
        Otherwise, returns an HTTP 404 Not Found error.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/hunter-pets"

        return self._request_gateway(resource, params)

    # Character Media APIs
    def character_media_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of the media assets available for a character (such as an avatar render).

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/character-media"

        return self._request_gateway(resource, params)

    # Character Mythic Keystone Profile APIs
    def character_mythic_keystone_profile_index(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns the Mythic Keystone profile index for a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/mythic-keystone-profile"

        return self._request_gateway(resource, params)

    def character_mythic_keystone_season_details(self, realm_slug: str, character_name: str, season_id: int) -> dict:
        """
        Returns the Mythic Keystone season details for a character.

        Returns a 404 Not Found for characters that have not yet completed
        a Mythic Keystone dungeon for the specified season.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        :param season_id: The ID of the Mythic Keystone season.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/mythic-keystone-profile/season/{season_id}"

        return self._request_gateway(resource, params)

    # Character Professions APIs
    def character_professions_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of professions for a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/professions"

        return self._request_gateway(resource, params)

    # Character Profile APIs
    def character_profile_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a profile summary for a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}"

        return self._request_gateway(resource, params)

    def character_profile_status(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns the status and a unique ID for a character.

        A client should delete information about a character from their application if any of the following occur:
            - An HTTP 404 Not Found error is returned
            - The is_valid value is false
            - The returned character ID doesn't match the previously recorded value for the character

        The following example illustrates how to use this endpoint:
            - A client requests and stores information about a character,
              including its unique character ID and the timestamp of the request.
            - After 30 days, the client makes a request to the status endpoint to
              verify if the character information is still valid.
            - If character cannot be found, is not valid, or the characters IDs do not match,
              the client removes the information from their application.
            - If the character is valid and the character IDs match, the client retains the data for another 30 days.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/status"

        return self._request_gateway(resource, params)

    # Character PvP APIs
    def character_pvp_bracket_statistics(self, realm_slug: str, character_name: str, pvp_bracket: str) -> dict:
        """
        Returns a profile summary for a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        :param pvp_bracket: The PvP bracket type.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/pvp-bracket/{pvp_bracket}"

        return self._request_gateway(resource, params)

    def character_pvp_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a PvP summary for a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/pvp-summary"

        return self._request_gateway(resource, params)

    # Character Quest APIs
    def character_quests(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a character's active quests as well as a link to the character's completed quests.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/quests"

        return self._request_gateway(resource, params)

    def character_completed_quests(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a list of quests that a character has completed.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/quests/completed"

        return self._request_gateway(resource, params)

    # Character Reputations APIs
    def character_reputations_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of a character's reputations.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/reputations"

        return self._request_gateway(resource, params)

    # Character Soulbinds APIs
    def character_soulbinds(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a character's soulbinds.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/soulbinds"

        return self._request_gateway(resource, params)

    # Character Specializations APIs
    def character_specializations_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of a character's specializations.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/specializations"

        return self._request_gateway(resource, params)

    # Character Statistics APIs
    def character_statistics_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a statistics summary for a character.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/statistics"

        return self._request_gateway(resource, params)

    # Character Titles APIs
    def character_titles_summary(self, realm_slug: str, character_name: str) -> dict:
        """
        Returns a summary of titles a character has obtained.

        :param realm_slug: The slug of the realm.
        :param character_name: The lowercase name of the character.
        """
        params = {"namespace": "profile"}
        resource = f"/profile/wow/character/{realm_slug}/{character_name}/titles"

        return self._request_gateway(resource, params)

    # Guild APIs
    def guild(self, realm_slug: str, guild_slug: str) -> dict:
        """
        Returns a summary of titles a character has obtained.

        :param realm_slug: The slug of the realm.
        :param guild_slug: The slug of the guild.
        """
        params = {"namespace": "profile"}
        resource = f"/data/wow/guild/{realm_slug}/{guild_slug}"

        return self._request_gateway(resource, params)

    def guild_activity(self, realm_slug: str, guild_slug: str) -> dict:
        """
        Returns a single guild's activity by name and realm.

        :param realm_slug: The slug of the realm.
        :param guild_slug: The slug of the guild.
        """
        params = {"namespace": "profile"}
        resource = f"/data/wow/guild/{realm_slug}/{guild_slug}/activity"

        return self._request_gateway(resource, params)

    def guild_achievements(self, realm_slug: str, guild_slug: str) -> dict:
        """
        Returns a single guild's achievements by name and realm.

        :param realm_slug: The slug of the realm.
        :param guild_slug: The slug of the guild.
        """
        params = {"namespace": "profile"}
        resource = f"/data/wow/guild/{realm_slug}/{guild_slug}/achievements"

        return self._request_gateway(resource, params)

    def guild_roster(self, realm_slug: str, guild_slug: str) -> dict:
        """
        Returns a single guild's roster by its name and realm.

        :param realm_slug: The slug of the realm.
        :param guild_slug: The slug of the guild.
        """
        params = {"namespace": "profile"}
        resource = f"/data/wow/guild/{realm_slug}/{guild_slug}/roster"

        return self._request_gateway(resource, params)
