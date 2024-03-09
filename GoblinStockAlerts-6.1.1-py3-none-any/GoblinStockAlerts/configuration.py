"""
Deals with validating and modifying the configuration file, ready for use with GoblinStockAlerts.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging
import os
from collections import defaultdict
from typing import Dict

from mergedeep import merge
from ruamel.yaml import YAML, YAMLError

from .errors import GSAConfigurationError
from .helpers import convert_string_to_slug
from .items import check_item_validity
from .pets import check_pet_validity, get_pet_breed_id_from_db, get_pet_quality_id_from_db
from .realms import get_connected_realm_ids, get_realm_connected_id

logger = logging.getLogger("GSA")


def generate_configuration_shopping_data(*,
                                         configuration: Dict
                                         ) -> Dict:
    """
    Convert a GSA .yml configuration to a dictionary configuration with all the necessary metadata needed by
    GoblinStockAlerts.

    For example, if 'global' is specified, a shopping list for every realm will be created for the items under
    global.

    Secondly each realm will then be parsed and merged in (if already existing from global) the realm specific
    shopping list.

    :param configuration: The dictionary representation of the loaded .YML file.
    """

    shopping_data = {
        "configuration": configuration['configuration'],
        "realms": defaultdict(dict)
    }

    if 'global' in configuration:
        logger.info("Global shopping list identified. Adding items to all connected realms.")

        # Generate the shopping list for every possible realm as global was configured.
        for realm in get_connected_realm_ids(region=configuration['configuration']['region']):
            shopping_data['realms'][realm] = create_realm_shopping_list(connected_realm="global",
                                                                        conf=configuration['global'])

    for realm in configuration:

        # These aren't a valid realm, obviously.
        if realm.lower() in ('global', 'configuration'):
            continue

        # It's likely users won't provide the slug version of realm names.
        realm_slug = convert_string_to_slug(string=realm)

        # Users could specify any realm on a connected group, so let's get the realm id.
        realm_id = get_realm_connected_id(realm_name=realm_slug, region=configuration['configuration']['region'])

        # Recursively deep merge the realm specific shopping list into the configuration, this means realm specific
        # pricing trumps the global configuration.
        merge(shopping_data['realms'][realm_id],
              create_realm_shopping_list(connected_realm=realm_slug, conf=configuration[realm]))

    # Lets do some clean up.
    # If somehow a realm has ended up in the shopping list without items or pets actually in the shopping list.
    # No need to retrieve data that definitely will not have any deals.
    for realm in list(shopping_data['realms']):
        items = len(shopping_data['realms'][realm].get('items', {}))
        pets = len(shopping_data['realms'][realm].get('pets', {}))

        if all((items == 0, pets == 0)):
            del shopping_data['realms'][realm]
            logger.warning(f"Somehow {realm} ended up having a shopping list generated without any items or pets. "
                           f"Is your config weird?")

    return shopping_data


def create_realm_shopping_list(*,
                               connected_realm: str,
                               conf: Dict
                               ) -> Dict:
    """
    Takes a dictionary representation of the YML configuration object and translates it into a GSA shopping list.

    :param connected_realm: The connected realm being generated
    :param conf:  The configuration dict
    """

    # Bad configuration protection.
    if not any(('items' in conf, 'pets' in conf)):
        raise GSAConfigurationError(f"{connected_realm} was found in configuration, "
                                    "but neither 'items' or 'pets' found under it?")

    shopping_data = {
        'items': defaultdict(dict),
        'pets': defaultdict(dict)
    }

    item_config = conf.get('items', {})
    if item_config:
        for item in conf.get('items', {}):
            data = conf['items'][item]

            try:
                check_item_validity(item=data)
            except GSAConfigurationError as ex:
                raise GSAConfigurationError(f"Item '{item}' ({connected_realm}) - {ex}.")

            shopping_data['items'][data['id']] = {
                'id': data['id'],
                'ilvl': data.get('ilvl', 0),
                'nickname': f"\033[01;93m*{item}*\033[0m" if data.get('rare', False) else item,
                'budget': data['budget'] * 10000
            }

    pet_config = conf.get('pets', {})
    if pet_config:
        for pet in pet_config:
            data = conf['pets'][pet]

            try:
                check_pet_validity(pet=data)
            except GSAConfigurationError as ex:
                raise GSAConfigurationError(f"Pet '{pet}' ({connected_realm}) - {ex}.")

            shopping_data['pets'][data['species_id']] = {
                'species_id': data['species_id'],
                'nickname': f"\033[01;93m*{pet}*\033[0m" if data.get('rare', False) else pet,
                'budget': data['budget'] * 10000,
            }

            if level := data.get('level'):

                if level > 25 or level < 1:
                    raise GSAConfigurationError(f"{pet} cannot be level {level}.")

                shopping_data['pets'][data['species_id']]['level'] = level

            if quality := data.get('quality'):
                shopping_data['pets'][data['species_id']]['quality'] = get_pet_quality_id_from_db(pet_quality=quality)

            if breed := data.get('breed'):
                shopping_data['pets'][data['species_id']]['breed'] = get_pet_breed_id_from_db(pet_breed=breed)

    return shopping_data


def validate_configuration(*,
                           configuration: Dict
                           ) -> None:
    """
    Perform validity checks on a configuration, an exception is raised on non-validity.

    :param configuration: The configuration to be checked.
    """

    if not isinstance(configuration, dict):
        raise GSAConfigurationError("Configuration is not a valid dictionary.")

    if 'configuration' not in configuration:
        raise GSAConfigurationError("No configuration details are present, eg region?")

    if 'version' not in configuration.get('configuration', {}):
        raise GSAConfigurationError("No version configuration specified. It should be under a configuration: heading.")

    if 'region' not in configuration.get('configuration', {}):
        raise GSAConfigurationError("No region configuration specified. It should be under a configuration: heading.")

    logger.debug(f"Configuration version: {configuration['configuration']['version']}.")
    if configuration['configuration']['version'] != 4.0:
        raise GSAConfigurationError(f"Configuration version: {configuration['configuration']['version']} "
                                    f"is not compatible. If you are upgrading from version 3.0, please check Discord"
                                    f" for instructions to upgrade.")

    if configuration['configuration']['region'] not in 'US' 'EU':
        raise GSAConfigurationError("Invalid region specified. Please select US or EU (uppercase).")

    if 'addon' not in configuration.get('configuration', {}):
        raise GSAConfigurationError("No addon setting specified. Must be True/False.")

    # If addon is configured to True, check a lot of possible errors with addon_folder_path
    if configuration['configuration']['addon']:
        if 'addon_folder_path' not in configuration['configuration']:
            raise GSAConfigurationError("You set addon to True, but did not provide a path your addons folder.")

        path = configuration['configuration']['addon_folder_path']
        if not os.path.isdir(path):
            raise GSAConfigurationError(f"The addon_folder_path '{path}' is invalid.")

        if 'interface' not in path.lower():
            raise GSAConfigurationError(f"That addon path doesn't look correct {path}.")

        if 'GSA_X99_Sniper'.lower() in path.lower():
            raise GSAConfigurationError(f"You should be specifying your Interface\\Addons folder NOT the "
                                        f"GSA_X99_Sniper folder. You configured this path: {path}.")

    if 'connected_realm_nicknames' in configuration['configuration']:
        nicknames = configuration['configuration']['connected_realm_nicknames']
        if nicknames and not isinstance(nicknames, dict):
            raise GSAConfigurationError("The formatting of your connected_realm_nicknames is incorrect.")

        if not nicknames or not len(nicknames) > 0:
            raise GSAConfigurationError("connected_realm_nicknames was found in configuration, "
                                        "but no nicknames provided?")

        for nickname in nicknames:
            if not isinstance(nickname, int):
                raise GSAConfigurationError(f"'{nickname}' is not a valid connected realm id.")

            if not nicknames[nickname] or not isinstance(nicknames[nickname], str):
                raise GSAConfigurationError(f"You need to actually specify a valid nickname for realm '{nickname}' "
                                            f"(a string)")

    if any((not configuration['configuration']['bnet_id'],
            not configuration['configuration']['bnet_secret'])):
        raise GSAConfigurationError("You must provide a valid bnet_id and bnet_secret.")

    if not isinstance(configuration['configuration']['bnet_id'], str) or \
            not isinstance(configuration['configuration']['bnet_secret'], str):
        raise GSAConfigurationError("bnet_id/bnet_secret must be strings.")

    if not isinstance(configuration['configuration']['workers'], int) or configuration['configuration']['workers'] <= 0:
        raise GSAConfigurationError("Workers must be a whole number above 0.")


def load_yaml_configuration_file(*,
                                 configuration_file: str
                                 ) -> Dict[str, any]:
    """
    Load a .YML file from disk.

    :param configuration_file: The configuration file to load
    :return: A dictionary representation of the YML file
    """

    logger.debug(f"Loading configuration file: '{configuration_file}'.")

    if not os.path.isfile(configuration_file):
        raise GSAConfigurationError(f"Configuration file '{configuration_file}' was not found.")

    with open(configuration_file, 'r') as f:
        data = f.read()

        # Ugly, but helps users who mess it up.
        if '\t' in data:
            raise GSAConfigurationError("Your configuration contains TABs, replace them with spaces.")

        # Reset back to the beginning of the file.
        f.seek(0)

        try:
            config = YAML().load(f)

        except YAMLError as ex:
            raise GSAConfigurationError(f"YAML formatting error in {configuration_file}. {ex}.")

        except Exception as ex:
            raise GSAConfigurationError(f"Unable to load the file config {configuration_file}. {repr(ex)}.")

    return config
