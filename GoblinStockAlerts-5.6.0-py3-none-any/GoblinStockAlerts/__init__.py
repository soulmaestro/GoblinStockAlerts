"""
Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

from .__version__ import __version__

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

background_warning = """\n 
                ***** 
                GSA is running in background mode, this is a slow but least resource consuming mode.
                
                This also uses the least amount of API requests.
                ***** 
                """

extreme_warning = """\n 
                ***** 
                EXTREME MODE USES SERIOUS AMOUNTS OF RAM (APPROX 2GB+).. 

                25 Python workers are created. When GSA starts and during xx:05 and xx:08 every hour GSA will 
                need 1.5GB-ish of RAM. They are shut down when not being used.

                If this is unavailable, strange things can happen. You have been warned! 
                
                There may be additional bugs in this mode... Feel free to report them.
                ***** 
                """

quota_warning = """\n
***
Slamming on the API brakes. 

A realm encountered a 429. GSA will try to recover by waiting for a bit... This is a Blizzard limitation.

GSA is now stopping all API queries for 20 seconds. 

GSA has an absolute maximum of 60 requests per second. Blizzard API limits are 100 requests per second. 

Have you shared your client credentials with anyone? Are you running other applications with your client credentials?

You'll have to restart GSA later, this is not an issue support can help with."
***
"""
