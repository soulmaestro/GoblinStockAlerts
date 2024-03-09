"""
The main entrypoint to GoblinStockAlerts, all usages, direct and third party should go through this function.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
import os
from argparse import ArgumentParser, Namespace
from typing import Optional, Callable

from GameAPI.blizzard import BlizzardAPI

from . import logo
from .addon import reset_addon_data_file, install_addon
from .callbacks import send_to_logger_and_addon
from .configuration import load_yaml_configuration_file, validate_configuration, convert_configuration_to_shopping_data
from .errors import GSAException, GSAConfigurationError
from .helpers import mask_string
from .logging import configure_logger_formats
from .scheduler import schedule

logger = logging.getLogger("GSA")


def start(*,
          args: Namespace,
          deal_callback: Optional[Callable] = None
          ) -> None:
    """
    This is the main entry point function to GoblinStockAlerts.

    :param args: A namespace object containing the relevant args for use with GoblinStockAlerts, check __main__ block.
    :param deal_callback: (OPTIONAL) A function pointer to the function to be called when deals are identified.
    """

    configure_logger_formats(debug=args.debug, extreme=args.extreme)

    logger.info("GSA is starting.")

    configuration = load_yaml_configuration_file(configuration_file=args.config)

    validate_configuration(configuration=configuration)

    region = configuration['configuration']['region'].upper()

    addon_path = None
    if configuration['configuration']['addon']:
        # If addon is enabled, install the addon (overwrite) and reset datafile to empty.
        addon_path = configuration['configuration'].get('addon_folder_path')
        install_addon(addon_directory=addon_path)
        reset_addon_data_file(addon_directory=addon_path)

    # An API returned from this function is confirmed to work, WoW Token has been tested.
    api = setup_and_test_api(region=region, client_id=args.bnet_id, client_secret=args.bnet_secret)

    if len(configuration) < 2:
        raise GSAConfigurationError("No realms were selected for scanning...")

    configuration = convert_configuration_to_shopping_data(configuration=configuration)

    if all((args.extreme, args.background)):
        raise GSAConfigurationError("You can't have both --background and --extreme selected.")

    schedule(api=api,
             extreme=args.extreme,
             background=args.background,
             configuration=configuration,
             region=region,
             addon_path=addon_path,
             deal_callback=send_to_logger_and_addon if not deal_callback else deal_callback,
             no_shutdown=args.no_shutdown)


def setup_and_test_api(*,
                       region: str,
                       client_id: Optional[str] = None,
                       client_secret: Optional[str] = None) -> BlizzardAPI:
    """
    Initialize a BlizzardAPI object and verify it works by requesting the regions WoW Token value.

    :param region: The region being queried (eg. US, EU).
    :param client_id: The user's client_id as provided by Blizzard.
    :param client_secret: The user's client_secret as provided by Blizzard.
    """

    client_id = client_id or os.getenv('BNET_ID')
    client_secret = client_secret or os.getenv('BNET_SECRET')

    if not all((client_id, client_secret)):
        raise GSAConfigurationError("One or more of BNET_ID, BNET_SECRET environment variables were not found.")

    logger.info(f"Setting up BlizzardAPI for the {region} region.")
    logger.info(f"Client ID: {mask_string(input_string=client_id)}.")
    logger.info(f"Client Secret: {mask_string(input_string=client_secret)}.")

    logger.debug(f"Testing API by obtaining WoW Token value.")
    api = BlizzardAPI(client_id=client_id, client_secret=client_secret, region=region.upper())

    return api


if __name__ == "__main__":
    print(logo)

    parser = ArgumentParser()
    parser.add_argument("-c", "--config",
                        type=str,
                        help="Location of your configuration .yml file.",
                        required=True)
    parser.add_argument('-d', "--debug",
                        help="Enable debug logging. This is noisy and verbose.",
                        action='store_true')
    parser.add_argument('-x', "--extreme",
                        help="Massively increase processing speed at the cost of about 1 GB of RAM. Has some bugs.",
                        action='store_true')
    parser.add_argument('-b', "--background",
                        help="Reduce workers if GoblinStockAlerts is running in the background.",
                        action='store_true')
    parser.add_argument("--bnet_id",
                        type=str,
                        help="Your Battle.net API Client ID. Please use environment variables.")
    parser.add_argument("--bnet_secret",
                        type=str,
                        help="Your Battle.net API Client Secret. Please use environment variables.")
    parser.add_argument('-ns', "--no_shutdown",
                        help="If supplied do not shutdown workers between updates, if used in conjunction with"
                             "extreme mode, this could use a lot of RAM.",
                        action='store_true')

    try:
        start(args=parser.parse_args())

    except GSAException as ex:
        logger.error(f"Exception: {repr(ex)}.")

    except Exception as ex:
        logger.critical(f"Exception: {repr(ex)}.")
        raise ex

    finally:
        logger.info("GoblinStockAlerts has finished.")
