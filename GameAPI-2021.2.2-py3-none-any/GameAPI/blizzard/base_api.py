"""
Copyright (C) 2021 https://github.com/binaryhabitat.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

import platform
import zlib
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional
from urllib import parse

import orjson
from urllib3 import PoolManager

from GameAPI.__version__ import __version__
from GameAPI.blizzard.errors import BlizzardAPIException, BlizzardAPIQuotaException, BlizzardAPIUnmodifiedData
from GameAPI.blizzard.helpers import OAuthToken, datetime_in_n_seconds

if TYPE_CHECKING:
    from urllib3.response import HTTPResponse


class BaseAPI:

    def __init__(self, client_id: str, client_secret: str, region: str):
        errors = []

        if not client_id:
            errors.append("Client ID must be set.")
        if not client_secret:
            errors.append("Client Secret must be set.")
        if not region or region.upper() not in ("US", "EU", "APAC"):
            errors.append("Region must be US, EU, or APAC.")

        if errors:
            raise BlizzardAPIException(" ".join(errors))

        self.client_id = client_id
        self.client_secret = client_secret
        self.api_region = region
        self.oauth_token = OAuthToken()
        self.client = PoolManager(
            maxsize=10,
            timeout=3,
            block=True,
            headers={
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": f"GameAPI/{__version__} Python/{platform.python_version()}"
            }
        )

    @staticmethod
    def _process_response(response: "HTTPResponse", request_time: Optional[timedelta] = None) -> dict:
        if response.status == 429:  # Too Many Requests
            raise BlizzardAPIQuotaException()
        elif response.status == 304:  # Not Modified
            raise BlizzardAPIUnmodifiedData()
        elif response.status != 200:  # Not OK
            raise BlizzardAPIException(f"Error. Status: {response.status}, URL: {response.geturl()}.")

        try:
            # Blindly load Blizzard's json data to verify it
            data = orjson.loads(response.data)
        except Exception as ex:
            raise BlizzardAPIException(f"Invalid JSON returned from Blizzard. Exception: {ex}, "
                                       f"URL: {response.geturl()}.")

        try:
            server_client_offset = response.headers["Date"]
            server_client_offset = datetime.strptime(server_client_offset, "%a, %d %b %Y %H:%M:%S GMT")
            server_client_offset = server_client_offset - datetime.utcnow()
            server_client_offset = server_client_offset - request_time
            server_client_offset = server_client_offset.total_seconds()
        except (KeyError, TypeError):
            server_client_offset = 0

        # TODO: Add test
        try:
            last_modified = response.headers["Last-Modified"]
            last_modified = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S GMT")
            last_modified = last_modified.timestamp()
        except (KeyError, TypeError):
            last_modified = None

        # noinspection PyBroadException
        try:
            checksum: Optional[int] = zlib.crc32(response.data)
        except Exception:
            checksum = None

        data["GameAPI"] = {"last_modified": last_modified,
                           "server_client_offset": server_client_offset,
                           "checksum": checksum}

        return data

    def _refresh_token(self) -> None:
        # TODO: Log

        # KR and TW OAuth requests have been merged in APAC
        # Source https://develop.battle.net/documentation/guides/using-oauth
        region = self.api_region if self.api_region.lower() in ("us", "eu") else "apac"

        url = f"https://{region}.battle.net/oauth/token?grant_type=client_credentials" \
              f"&client_id={self.client_id}" \
              f"&client_secret={self.client_secret}"

        response = self.client.request("POST", url)

        # Process the response
        data = self._process_response(response)

        try:
            # Update the cached token, with the newly received one
            self.oauth_token = OAuthToken(data["access_token"], datetime_in_n_seconds(data["expires_in"]))
        except KeyError as ex:
            raise BlizzardAPIException(f"Invalid JSON returned from Blizzard. Exception: {ex}, URL: {url}.")

    def request(self, resource: str, parameters: Optional[dict] = None, headers: Optional[dict] = None) -> dict:
        if not self.oauth_token.token_valid() or not self.oauth_token:
            self._refresh_token()

        # The Base URL for all API requests to Blizzard
        base_url = f"https://{self.api_region}.api.blizzard.com"

        # Add access_token to parameters
        parameters = parameters or {}
        parameters["access_token"] = self.oauth_token.token
        encoded_parameters = parse.urlencode(parameters)

        # Construct the final URL to be queried
        url = f"{base_url}{resource}?{encoded_parameters}"

        # Execute the GET request
        start = datetime.utcnow()
        response = self.client.request("GET", url, headers=headers or {})

        # Return the response after processing
        return self._process_response(response, datetime.utcnow() - start)
