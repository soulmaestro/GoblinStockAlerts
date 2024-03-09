"""
All errors and exceptions that are used by GoblinStockAlerts.

Source Code Copyright (C) 2021 BinaryHabitat. Released under GNU LESSER GENERAL PUBLIC LICENSE.
"""


class GSAException(Exception):
    pass


class GSAConfigurationError(GSAException):
    pass


class GSAOldDatabase(GSAException):
    pass


class GSAThreadError(GSAException):
    pass
