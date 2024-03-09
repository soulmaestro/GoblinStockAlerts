"""
This deals with the state of realms, whether are scheduled or not, it is also used for error tracking last modified
times etc.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

STATE_ERROR_QUOTA = -2
STATE_ERROR = -1
STATE_READY = 0
STATE_SCHEDULED = 1
STATE_FINISHED = 2
STATE_NEW_DATA = 3

logger = logging.getLogger("GSA")


class State:
    def __init__(self, connected_realm_id: int):
        self.id = connected_realm_id
        self.status = STATE_READY
        self.last_modified = datetime.utcnow() - timedelta(days=1)
        self.last_checked = datetime.utcnow() - timedelta(days=1)
        self.response = None
        self.hashes = []


class RealmState:
    def __init__(self, connected_realm_ids: Dict):
        self._desync = []
        self.states = {}
        for connected_realm_id in connected_realm_ids:
            self.states[connected_realm_id] = State(connected_realm_id)

    @property
    def desync(self):
        try:
            desync = sum(self._desync) / len(self._desync)
        except ZeroDivisionError:
            desync = 0

        return desync

    @desync.setter
    def desync(self, value):
        # Only store the last 100 values.
        self._desync = self._desync[:99] + [value]
