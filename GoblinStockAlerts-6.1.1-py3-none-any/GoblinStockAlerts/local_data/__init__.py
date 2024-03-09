"""
Common function for loading all static data.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import json
import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Dict

from ..errors import GSAException

logger = logging.getLogger("GSA")

z = ['item_level', 'item', 'level', 'id', 'type', 'points', 'bonus_lists',
     'modifiers', 'curveId', 'value', 'playerLevel', 'itemLevel', 'name']


@lru_cache
def load_db(*,
            db: str
            ) -> Dict:
    """
    Open a database file, check when it was last updated and return the JSON loaded representation.

    :param db: The database file to be opened.
    """

    # Working directory could be anywhere, so load relative to this files on-disk location.
    db_path = os.path.join(os.path.dirname(__file__), db)

    # We raise a GSAException rather than letting an OSError bubble up.
    if not os.path.isfile(db_path):
        raise GSAException(f"File {db_path} not found.")

    # We must allow utf-8 as some realm names have UTF-8 characters,
    # this could be useful if we ever do localizations.
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
        logger.debug(f"Loaded {db_path}.")

    # This is a soft requirement to push people to upgrade to reduce support queries.
    # 120 days feels very fair, which is three times per year.
    last_updated = datetime.fromtimestamp(data.get('last_updated', 0))
    if (datetime.utcnow() - last_updated).days > 365:
        logger.info(f"GSA database '{db}' is over 365 days old. It is highly likely it will be outdated.")

    return data.get('data', [])
