"""
Copyright (C) 2021 https://github.com/binaryhabitat.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from GameAPI.blizzard.base_api import BaseAPI


class BattleNetAPI(BaseAPI):

    def __init__(self, client_id: str, client_secret: str, region: str):
        super().__init__(client_id, client_secret, region)
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_region = region
