"""
All realm related functions and resources.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
from functools import lru_cache
from typing import List

from .errors import GSAConfigurationError
from .helpers import convert_slug_to_string
from .local_data import load_db

logger = logging.getLogger("GSA")


@lru_cache
def load_connected_realms_db(*,
                             region: str
                             ) -> dict:
    """
    A cached method to return a dictionary containing realm metadata for the region specified.

    :param region: Which region realms should be returned for
    :return: A dictionary containing realms and their associated metadata
    """
    connected_realms = load_db(db="connected_realms.json")[region.upper()]

    # For consistency lets order each group alphabetically
    for connected_realm_group_id in connected_realms:
        connected_realms[connected_realm_group_id] = sorted(connected_realms[connected_realm_group_id])

    logger.debug(f"{len(connected_realms)} connected realm groups loaded.")

    return connected_realms


@lru_cache
def get_connected_realm_ids(*,
                            region: str
                            ) -> List:
    """
    Return a list of all connected realms in the region requested.

    :param region: The region being queried (eg. US, EU).
    """

    return [int(connected_realm_id) for connected_realm_id in load_connected_realms_db(region=region.upper())]


@lru_cache
def get_realm_connected_id(*,
                           realm_name: str,
                           region: str
                           ) -> int:
    """
    Get the connected realm id of a specified realm.

    :param realm_name: The slug format of the realm being requested.
    :param region: The region being queried (eg. US, EU).
    """

    connected_realms = load_connected_realms_db(region=region)

    for connected_realm_group in connected_realms:

        if realm_name in connected_realms[connected_realm_group]:
            connected_realm_id = connected_realm_group
            break

    else:
        raise GSAConfigurationError(f"Realm {realm_name} was not found in the region: {region}.")

    return int(connected_realm_id)


@lru_cache
def get_pretty_list_of_realms_on_connected_id(*,
                                              connected_realm_id=int,
                                              region: str
                                              ) -> List[str]:
    """
    Returns a non-slug list of strings for the realms connected the specified id.

    :param connected_realm_id: The connected realm id being requested.
    :param region: The region being queried (eg. US, EU).
    """

    connected_realms = load_connected_realms_db(region=region)

    group = connected_realms[str(connected_realm_id)]

    return [convert_slug_to_string(slug=realm) for realm in group]
