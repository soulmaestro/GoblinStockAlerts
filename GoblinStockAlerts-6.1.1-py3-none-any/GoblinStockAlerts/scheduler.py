"""
The overall scheduling mechanisms, should a realm be queued, actually do the queueing, spin up all the worker threads
et cetera.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime, timedelta
from typing import Callable, Optional, Union

from GameAPI.blizzard import BlizzardAPI

from . import extreme_warning, quota_warning, GSA
from .download import download_auction_house_and_find_deals
from .results import result_watcher
from .state import RealmState, STATE_READY, STATE_SCHEDULED, STATE_ERROR_QUOTA

logger = logging.getLogger("GSA")


def schedule(*,
             api: BlizzardAPI,
             region: str,
             deal_callback: Callable,
             addon_path: Optional[str]
             ) -> None:
    """
    Responsible for scheduling the query of the Auction House data.

    This function will spin up one thread to monitor for results, and n threads (depending on the extreme
    flag) to be used as workers for querying the Blizzard API.

    :param api: An initialized BlizzardAPI object.
    :param region: The region being queried (eg. US, EU).
    :param deal_callback: The function that should be called when deals are identified.
    :param addon_path: (OPTIONAL) The path to the user's World of Warcraft addon folder.
    """

    rs = RealmState(connected_realm_ids=GSA.shopping)

    watcher_threads = ThreadPoolExecutor(max_workers=1)
    watcher_threads.submit(result_watcher,
                           rs=rs,
                           region=region,
                           deal_callback=deal_callback,
                           addon_path=addon_path)

    worker_pool = None

    while True:
        realms = list(GSA.shopping)
        random.shuffle(realms)

        for realm in realms:

            if should_connected_realm_be_queued(state=rs, connected_realm=realm):
                if worker_pool is None:
                    worker_pool = setup_workers(api=api, rs=rs)

                try:
                    rs.states[realm].response = worker_pool.submit(download_auction_house_and_find_deals,
                                                                   shopping=GSA.shopping,
                                                                   api=api,
                                                                   connected_realm_id=realm,
                                                                   modified_timestamp=rs.states[realm].last_modified)
                except Exception as ex:
                    logger.error(f"{ex}")
                    logger.critical("Scheduler: There was a critical error. Please restart GSA.")
                    watcher_threads.shutdown(wait=True, cancel_futures=True)
                    return

                else:  # No exception
                    rs.states[realm].status = STATE_SCHEDULED

        if GSA.settings['workers_shutdown']:
            if worker_pool is not None and should_executor_be_shutdown(realm_states=rs):
                logger.info("Workers shutting down...")
                worker_pool.shutdown(wait=True, cancel_futures=True)
                worker_pool = None
                logger.info("Workers shut down.")

        time.sleep(0.25)


def setup_workers(*,
                  rs: RealmState,
                  api: BlizzardAPI
                  ) -> Union[ProcessPoolExecutor, ThreadPoolExecutor]:
    """
    Creates a worker pool for use in scheduling.

    :param rs: The state dictionary for all connected realms.
    :param api: An initialized BlizzardAPI object.
    """

    logger.info("Workers starting up...")
    if GSA.settings['workers_use_multiprocessing']:
        worker_pool = ProcessPoolExecutor(max_workers=GSA.settings['workers'])
        logger.warning(extreme_warning)
    else:
        worker_pool = ThreadPoolExecutor(max_workers=GSA.settings['workers'])

    # Lets confirm API is still working...
    while not test_api(api=api, rs=rs):
        time.sleep(3)

    return worker_pool


def test_api(*,
             api: BlizzardAPI,
             rs: RealmState,
             ) -> bool:
    """
    Test if the API is working.

    :param api: An initialized BlizzardAPI object.
    :param rs: The state dictionary for all connected realms.
    """

    try:
        for _ in range(3):
            result = api.wow.token()
            desync = result.get('GameAPI_Local_Server_Desync', 0)
            logger.debug(f"Token served by node with a desync of {desync}")
            rs.desync = desync
        logger.info(f"API has been checked and is working. (Local PC/Blizzard CDN average desync is {rs.desync}s)")
    except Exception as ex:
        logger.error(f"It's time to task the workers, but the API is failing? {ex}. If this is the first run of GSA"
                     f" please check your Client ID/Secret.")
        return False

    return True


def should_connected_realm_be_queued(*,
                                     state: RealmState,
                                     connected_realm: int
                                     ) -> bool:
    """
    Decides whether or not a connected realm is ready to be queried.

    :param state: The state dictionary.
    :param connected_realm: The ID of the read being checked.
    """

    realm_state = state.states[connected_realm]

    # STATE_ERROR_QUOTA: The last query excepted because Blizzard returned a 429 - we'll stop all scheduling.
    if realm_state.status == STATE_ERROR_QUOTA:
        # Slam on the brakes. Stop all realms being queried for twenty seconds.
        logger.critical(quota_warning)
        while (datetime.utcnow() - realm_state.last_checked).total_seconds() < 15:
            time.sleep(0.5)

        # Lets go and clear up the other ERROR_QUOTAS
        for cr in state.states:
            if state.states[cr].status == STATE_ERROR_QUOTA:
                state.states[cr].status = STATE_READY
        logger.info("Scheduling continuing...")

    # We will not schedule a realm if it's in any of the following states.
    # STATE_ERROR: The query function excepted for x reason.
    # STATE_FINISHED: The query function has been detected as finished by the results scanner.
    # STATE_NEW_DATA: The query function returned successfully and there was new data.
    # STATE_SCHEDULED: The scheduler has tasked this realm to be queried.
    if realm_state.status != STATE_READY:
        return False

    # We will only query a realm if it's due in the next eight seconds
    server_time = datetime.utcnow() + timedelta(seconds=state.desync)
    if (server_time - realm_state.last_modified).total_seconds() < (60 * 60) - 9:
        return False

    # STATE_READY
    return True


def should_executor_be_shutdown(*,
                                realm_states: RealmState
                                ) -> bool:
    """
    Self-explanatory through comments.

    :param realm_states: The state dictionary with all realm metadata
    """
    for cr in realm_states.states:
        # If any realm isn't idling, don't shut down the workers.
        if realm_states.states[cr].status != STATE_READY:
            return False

        # If any realm is freshly updated, keep workers online - safety net.
        if (datetime.utcnow() - realm_states.states[cr].last_checked).total_seconds() < 90:
            return False

    return True
