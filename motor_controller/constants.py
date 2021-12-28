# -*- coding: utf-8 -*-
"""Constants for motor controller."""

# 3rd-party
from RpiMotorLib.RpiMotorLib import A4988Nema

# Project
import constants as global_constants  # noqa: F401

STEPPER_DRIVER_TYPES = [
    # [stepper_type_name, rpimsotorlib_driver_class]
    # Add to this as support comes online.
    ["A4988", A4988Nema],
]
