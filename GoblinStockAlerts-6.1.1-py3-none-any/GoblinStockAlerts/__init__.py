"""
Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""
from typing import Dict

from .__version__ import __version__
from .errors import GSAConfigurationError

project_github = "https://github.com/binaryhabitat/GoblinStockAlerts"
project_discord = "https://discord.gg/UeX7RekyUq"
project_pypi = "https://pypi.org/project/GoblinStockAlerts"

logo = f"""
 .d8888b.   .d8888b.         d8888
d88P  Y88b d88P  Y88b       d88888
888    888 Y88b.           d88P888
888         "Y888b.       d88P 888
888  88888     "Y88b.    d88P  888
888    888       "888   d88P   888
Y88b  d88P Y88b  d88P  d8888888888
 "Y8888P88  "Y8888P"  d88P     888
 
Goblin Stock Alerts (Version: {__version__}).

Discord: {project_discord}
GitHub: {project_github}
PyPI: {project_pypi}
"""

extreme_warning = """\n 
                ***** 
                WORKERS USING MULTIPROCESSING USES SERIOUS AMOUNTS OF RAM (APPROX 2GB+).. 

                Python workers are created as processes. GSA will need approx 40 MB per worker during realm update 
                periods.

                If this is unavailable, strange things can happen. You have been warned! 
                
                There may be additional bugs in this mode... Feel free to report them.
                ***** 
                """

quota_warning = """\n
***
Slamming on the API brakes. 

A realm encountered a 429. GSA will try to recover by waiting for a bit... This is a Blizzard limitation.

GSA is now stopping all API queries for 15 seconds. 

Have you shared your client credentials with anyone? Are you running other applications with your client credentials?

If you see this repeatedly, you'll have to restart GSA later, THIS IS BLIZZARD'S END."
***
"""


class GSA:
    initialized = False
    settings = {}
    shopping = {}

    def __init__(self):
        raise GSAConfigurationError("Do not instantiate this class.")

    @classmethod
    def configure(cls, configuration: Dict) -> None:
        if not cls.initialized:
            cls.settings = configuration.get('configuration') or {}
            cls.shopping = configuration.get('realms') or {}
            cls.initialized = True
        else:
            raise GSAConfigurationError("You cannot configure GSA more than once.")
