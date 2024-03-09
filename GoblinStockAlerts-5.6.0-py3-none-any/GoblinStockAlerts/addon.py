"""
All functions relating to GSA_X99_Sniper.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""
import logging
import os
import re
import shutil
from typing import Dict

from mergedeep import merge
from slpp import slpp as lua

from .__version__ import __version__

logger = logging.getLogger("GSA")

# We may one day need to support other operating systems, so let Python construct the path.
ADDON_DATA_PATH = os.path.join('GSA_X99_Sniper', 'GSA_X99_Data.lua')

# This is default data the database must have inside it to prevent LUA errors in the addon.
ADDON_DEFAULT_DATA = """GSAVersion="UNKNOWN"
GSAData={

}
"""


def write_deals_to_data_file(*,
                             addon_directory: str,
                             deals: Dict
                             ) -> None:
    """
    Convert the specified deals to LUA and write them to disk.

    :param addon_directory: The path to the user's World of Warcraft addon folder.
    :param deals: The deals to be converted to LUA and written to disk.
    """
    deals = deals['GSAData']

    data_file = os.path.join(addon_directory, ADDON_DATA_PATH)

    with open(data_file, "r") as f:
        # We replace the variable assignment, this is not valid for LUA object decoding to a dictionary.
        current_data = f.read()

    current_data = re.sub('.*\nGSAData=', '', current_data)
    current_data = lua.decode(current_data)

    # Only attempt to smash deals together if lua.decode successfully gave us a dictionary.
    if isinstance(current_data, dict):
        merge(deals, current_data)

    lua_data = lua.encode(deals)

    # Re-add the variable assignment.
    lua_data = f"""GSAVersion="{__version__}"\nGSAData={lua_data}"""

    with open(data_file, "w") as f:
        f.write(lua_data)


def reset_addon_data_file(*,
                          addon_directory: str
                          ) -> None:
    """
    Write a blank shopping list to the addon's data file.

    :param addon_directory: The path to the user's World of Warcraft addon folder.
    """

    data_file = os.path.join(addon_directory, ADDON_DATA_PATH)

    with open(data_file, "w") as f:
        f.write(ADDON_DEFAULT_DATA)

    logger.warning(f"Successfully reset addon database {data_file}.")


def install_addon(*,
                  addon_directory: str
                  ) -> None:
    """
    Installs the GSA_X99_Sniper Addon.

    :param addon_directory: The path to the user's World of Warcraft addon folder.
    """

    addon_files = os.path.join(os.path.dirname(__file__), 'local_data', 'addon')

    # We overwrite files and directories in the path.
    shutil.copytree(addon_files, addon_directory, dirs_exist_ok=True)

    logger.warning(f"Successfully installed/updated GSA_X99_Sniper to addon_directory {addon_directory}.")
