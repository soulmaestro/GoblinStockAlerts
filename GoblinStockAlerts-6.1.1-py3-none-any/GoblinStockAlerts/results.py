"""
Responsible for monitoring the state dictionary for results, handle errors and process data.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.

TODO: THIS FILE IS PARTICULARLY "SPAGHETTI" AND NEEDS WORK.
"""

import logging
import sys
from datetime import datetime, timedelta
from time import sleep
from traceback import format_exc
from typing import Callable, Optional

from .addon import reset_addon_deals
from .realms import get_pretty_list_of_realms_on_connected_id
from .state import STATE_NEW_DATA, STATE_SCHEDULED, STATE_READY, STATE_FINISHED, STATE_ERROR, STATE_ERROR_QUOTA, \
    RealmState

logger = logging.getLogger("GSA")


def result_watcher(*,
                   rs: RealmState,
                   region: str,
                   deal_callback: Callable,
                   addon_path: Optional[str]
                   ) -> None:
    """
    Result watcher watches the state dictionary and checks if the response object is ready to be processed.

    If it is, the deal_callback will be called and the state dictionary updated.

    This function is also responsible for output to the UI regarding updates.

    :param rs: The state dictionary for all connected realms.
    :param region: The region being queried (eg. US, EU).
    :param deal_callback: The function that should be called when deals are identified.
    :param addon_path: (OPTIONAL) The path to the user's World of Warcraft addon folder.
    """

    timer = datetime.utcnow()
    updated = 0
    while True:
        try:
            for connected_realm in rs.states:

                if rs.states[connected_realm].status == STATE_SCHEDULED:

                    if rs.states[connected_realm].response and rs.states[connected_realm].response.done():
                        rs.states[connected_realm].status = STATE_FINISHED

                        # noinspection PyBroadException
                        try:
                            status, error, auctions, desync, last_modified, data_hash = \
                                rs.states[connected_realm].response.result()

                        except Exception:
                            # Extreme mode has caused some weird things here...
                            logger.critical("ResultWatcher: There was a critical error. Please restart GSA.")
                            return

                        if STATE_NEW_DATA and data_hash in rs.states[connected_realm].hashes:
                            logger.error(f"{connected_realm} returned old data! SHA256 '{data_hash}' has"
                                         f" been seen before despite having a last modified being shown by Blizzard "
                                         f"as {last_modified} (UTC)'. This realm has been queued again.")
                            rs.states[connected_realm].status = STATE_READY

                        # Did it update?
                        elif status == STATE_NEW_DATA:
                            logger.debug(f"{connected_realm} had new data.")

                            if updated == 0:
                                if addon_path:
                                    reset_addon_deals(addon_directory=addon_path)
                                timer = datetime.utcnow()
                                display_speed_message(connected_realm_id=connected_realm, region=region)

                            try:
                                deal_callback(connected_realm_id=connected_realm,
                                              item_deals=auctions['items'],
                                              pet_deals=auctions['pets'],
                                              addon_path=addon_path)

                            except Exception as ex:
                                logger.debug(f"{format_exc()}.")
                                logger.error(f"Deals callback encountered an exception: {ex}.")

                            updated += 1

                            if updated == len(rs.states):
                                display_speed_message(connected_realm_id=connected_realm, region=region, slowest=True)

                            # Only update last_modified if we actually found new data.
                            rs.states[connected_realm].hashes.append(data_hash)
                            rs.states[connected_realm].last_modified = last_modified
                            rs.states[connected_realm].status = STATE_NEW_DATA
                            if desync is not None:
                                logger.debug(f"{connected_realm} was served by a node with a desync of {desync}s")
                                rs.desync = desync

                        elif status == STATE_ERROR:
                            if len(error) > 0:
                                logger.error(f"Issue with realm {connected_realm} : {error} - "
                                             f"It will be rescanned momentarily.")
                            rs.states[connected_realm].status = STATE_READY

                        elif status == STATE_ERROR_QUOTA:
                            logger.debug(f"Blizzard returned a quota error on querying realm: {connected_realm}.")
                            rs.states[connected_realm].status = STATE_ERROR_QUOTA

                        else:
                            rs.states[connected_realm].status = STATE_READY

                        rs.states[connected_realm].last_checked = datetime.utcnow()
                        rs.states[connected_realm].response = None

            if updated == len(rs.states):
                updated = 0
                timer = datetime.utcnow()

                for connected_realm in rs.states:
                    rs.states[connected_realm].status = STATE_READY

            if updated > 0 and (datetime.utcnow() - timer).total_seconds() >= 30:
                logger.info(f"Progress: {updated}/{len(rs.states)}")
                timer = datetime.utcnow()

            if updated == 0 and (datetime.utcnow() - timer).total_seconds() >= 300:
                server_time = (datetime.utcnow() + timedelta(seconds=rs.desync)).strftime("%H:%M:%S")
                logger.info(f"Waiting until next snapshot, Blizzard servers (UTC) currently: {server_time})...")
                timer = datetime.utcnow()

            sleep(0.01)

        except Exception as ex:
            logger.critical(f"{ex} {format_exc()}")


def display_speed_message(*,
                          connected_realm_id: str,
                          region: str,
                          slowest: bool = False) -> None:
    """
    Displays a message to the user regarding the fastest/slowest realms.

    :param connected_realm_id: The connected realm that was responsible.
    :param region: The region the connected realm is in.
    :param slowest: FALSE if fastest connected realm. TRUE if slowest.
    """

    pretty = get_pretty_list_of_realms_on_connected_id(connected_realm_id=connected_realm_id,
                                                       region=region)

    if not slowest:
        message = f"New Blizzard Auction House data! Found on: {connected_realm_id} ({', '.join(pretty)})."

        if sys.platform.startswith("win"):
            from winotify import Notification
            t = Notification(app_id="GoblinStockAlerts",
                             title="New Blizzard Auction House data!",
                             msg=f"{', '.join(pretty)}")
            t.build().show()

    else:
        message = f"All realms scanned. Last realm: {connected_realm_id} ({', '.join(pretty)})."

    logger.info(message)
