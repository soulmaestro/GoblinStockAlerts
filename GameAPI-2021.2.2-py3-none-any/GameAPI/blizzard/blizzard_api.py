"""
Copyright (C) 2021 https://github.com/binaryhabitat.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from GameAPI.blizzard.battlenet import BattleNetAPI
from GameAPI.blizzard.diablo3 import Diablo3API
from GameAPI.blizzard.hearthstone import HearthstoneAPI
from GameAPI.blizzard.warcraft import WarcraftAPI


class BlizzardAPI:

    def __init__(self, client_id: str, client_secret: str, region: str):
        self.battlenet = BattleNetAPI(client_id, client_secret, region)
        self.diablo3 = Diablo3API(client_id, client_secret, region)
        self.hearthstone = HearthstoneAPI(client_id, client_secret, region)
        self.wow = WarcraftAPI(client_id, client_secret, region)
        self.wow_vanilla = WarcraftAPI(client_id, client_secret, region, classic="Vanilla")
        self.wow_tbc = WarcraftAPI(client_id, client_secret, region, classic="TBC")
