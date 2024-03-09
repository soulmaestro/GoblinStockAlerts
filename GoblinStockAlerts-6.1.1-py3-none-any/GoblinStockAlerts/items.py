"""
All item related functions and resources.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
import os
from functools import lru_cache
from typing import Dict, Tuple, Optional

from ruamel.yaml.scalarfloat import ScalarFloat
from scipy.interpolate import interp1d

from . import project_discord
from .errors import GSAConfigurationError
from .local_data import load_db, z
from .pets import PET_CAGE_ID

logger = logging.getLogger("GSA")


def check_item_validity(*,
                        item: Dict
                        ) -> None:
    """
    Verify all the expected components of a item shopping item are present.

    :param item: The item dictionary object.
    """

    if 'budget' not in item:
        raise GSAConfigurationError(f"Missing a budget.")

    if not isinstance(item['budget'], (int, float, ScalarFloat)):
        raise GSAConfigurationError(f"Budget is not valid (int/float).")

    if 'id' not in item:
        raise GSAConfigurationError(f"Missing an id.")

    if not isinstance(item['id'], int):
        raise GSAConfigurationError(f"Item ID is not a valid integer (no decimals).")

    if item['id'] == PET_CAGE_ID:
        raise GSAConfigurationError(f"Pet Cage ({PET_CAGE_ID}) is a forbidden item id. Please use 'pets:' section.")

    if 'suffix' in item and not isinstance(item['suffix'], str):
        raise GSAConfigurationError("Suffix must be provided in string form, eg. 'of the Aurora'.")

    if 'rare' in item and not isinstance(item['rare'], bool):
        raise GSAConfigurationError("Rare must be provided as a boolean, eg. True or False.")

    if 'ilvl' in item and not isinstance(item['ilvl'], (int, list)):
        raise GSAConfigurationError("An item level was provided, but it was not an integer (whole number) or list.")


def iii(a) -> Tuple[int, Optional[str]]:
    """
    If you steal this function, please give credit to Seriallos (Raidbots) and BinaryHabitat (GoblinStockAlerts),
    thank you. If you don't... well you should feel bad honestly.
    """
    i_ = 0
    s_ = ""
    try:
        dbi = get_item_from_db(item_id=a[z[1]][z[3]])
        logger.debug(f"Item ID: {a[z[1]][z[3]]} not found in the database. Report this error on Discord: "
                     f"{project_discord} - Thanks.")
    except KeyError:
        return i_, s_
    try:
        i_ = dbi[z[0]]
    except KeyError:
        return i_, s_
    for m in a[z[1]].get(z[7], []):
        if m[z[4]] == 9 and len(a[z[1]].get(z[6], [])) > 0:
            plv = m[z[9]]
            for bid in a[z[1]][z[6]]:
                try:
                    dbb = get_bonus_from_db(bonus_id=bid)
                except KeyError:
                    continue
                if z[8] not in dbb:
                    continue
                dbc = get_curve_from_db(curve_id=dbb[z[8]])
                # noinspection PyBroadException
                try:
                    # noinspection PyArgumentList
                    nl = int(round((interp1d([x[z[10]] for x in dbc[z[5]]],
                                             [x[z[11]] for x in dbc[z[5]]])(plv)).min()))
                except Exception:
                    nl = dbc[z[5]][-1][z[11]]
                logger.debug(f"{i_}->{nl}.")
                i_ = nl if nl > 0 else i_

    mtil = 0
    for bbbb in a[z[1]].get(z[6], []):
        try:
            dbb = get_bonus_from_db(bonus_id=bbbb)
        except KeyError:
            continue
        if z[2] in dbb:
            mtil += dbb[z[2]]
        if z[12] in dbb:
            s_ = dbb[z[12]]

    if mtil != 0:
        logger.debug(f"{i_}->{i_ + mtil}.")
        i_ += mtil
    else:
        logger.debug(f"F {a[z[1]]['id']}=={i_}.")

    return i_, s_


@lru_cache
def get_item_from_db(*,
                     item_id: int
                     ) -> Dict:
    """
    A cached method to get item metadata from the db

    :param item_id: The item id to lookup.
    """

    items = load_db(db="items.json")

    return items[str(item_id)]


@lru_cache
def get_curve_from_db(*,
                      curve_id: int
                      ) -> Dict:
    """
    A cached method to get curve metadata from the db

    :param curve_id: The curve id to lookup.
    """

    curves = load_db(db=os.path.join('raidbots_static', 'item-curves.json'))

    return curves[str(curve_id)]


@lru_cache
def get_bonus_from_db(*,
                      bonus_id: int
                      ) -> Dict:
    """
    A cached method to get bonus metadata from the db

    :param bonus_id: The bonus id to lookup.
    """

    bonuses = load_db(db=os.path.join('raidbots_static', 'bonuses.json'))

    return bonuses[str(bonus_id)]
