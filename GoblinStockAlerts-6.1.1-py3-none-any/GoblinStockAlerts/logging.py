"""
Set 'pretty' (subjective) logging up.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""

import logging.config

import coloredlogs

from .__version__ import __version__

logger = logging.getLogger("GSA")


def setup_logger(*,
                 debug: bool = False,
                 ) -> None:
    """
    Setup logger format and colors.

    :param debug: TRUE if the level of warnings should be at DEBUG, else INFO.
    """

    if debug:
        message_format = f"%(asctime)s %(name)s-{__version__} %(levelname)s %(message)s"
    else:
        message_format = f"%(asctime)s %(name)s-{__version__} %(message)s"

    field_styles = {
        "asctime": {"color": "green"},
        "levelname": {"color": "magenta"},
        "name": {"color": "green"}
    }

    level_styles = {
        "debug": {"color": "white"},
        "info": {},
        "warning": {"color": "yellow"},
        "error": {"color": "red"},
        "critical": {"color": "red", "bold": True},
    }

    coloredlogs.install(level=logging.DEBUG if debug else logging.INFO,
                        logger=logging.getLogger("GSA"), fmt=message_format,
                        level_styles=level_styles, field_styles=field_styles)
