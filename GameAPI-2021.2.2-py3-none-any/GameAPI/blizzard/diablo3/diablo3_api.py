"""
Copyright (C) 2021 https://github.com/binaryhabitat.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from GameAPI.blizzard.base_api import BaseAPI


class Diablo3API(BaseAPI):

    def __init__(self, client_id: str, client_secret: str, region: str):
        super().__init__(client_id, client_secret, region)
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_region = region

    # D3 APIs
    def season_index(self) -> dict:
        """
        Returns an index of available seasons.
        """
        resource = "/data/d3/season/"

        return self.request(resource)

    def season(self, season_id: int) -> dict:
        """
        Returns a leaderboard list for the specified season.

        :param season_id: The season for the leaderboard list
        """
        resource = f"/data/d3/season/{season_id}"

        return self.request(resource)

    def season_leaderboard(self, season_id: int, leaderboard: str) -> dict:
        """
        Returns a the specified leaderboard for the specified season.

        :param season_id: The season for the leaderboard.
        :param leaderboard: The leaderboard to retrieve (eg. achievement-points)
        """
        resource = f"/data/d3/season/{season_id}/leaderboard/{leaderboard}"

        return self.request(resource)

    def era_index(self) -> dict:
        """
        Returns an index of available eras.
        """
        resource = "/data/d3/era/"

        return self.request(resource)

    def era(self, era_id: int) -> dict:
        """
        Returns a leaderboard list for the specified era.

        :param era_id: The era for the leaderboard list
        """
        resource = f"/data/d3/era/{era_id}"

        return self.request(resource)

    def era_leaderboard(self, era_id: int, leaderboard: str) -> dict:
        """
        Returns a the specified leaderboard for the specified era.

        :param era_id: The era for the leaderboard.
        :param leaderboard: The leaderboard to retrieve (eg. rift-barbarian)
        """
        resource = f"/data/d3/era/{era_id}/leaderboard/{leaderboard}"

        return self.request(resource)
