"""
Copyright (C) 2021 https://github.com/binaryhabitat.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from datetime import datetime, timedelta
from typing import Optional


def datetime_in_n_seconds(seconds: int = 0) -> datetime:
    """
    Return the datetime object for n seconds in the future.

    :param seconds: How many seconds to add on.
    """
    return datetime.utcnow() + timedelta(seconds=seconds)


class OAuthToken:

    def __init__(self, token: Optional[str] = None, expiry: datetime = datetime.utcnow() - timedelta(1)):
        self.token = token
        self.expiry = expiry

    def token_valid(self) -> bool:
        """
        Return whether or not there is at least 60 seconds of token lifespan left.
        """
        return datetime_in_n_seconds(seconds=60) < self.expiry
