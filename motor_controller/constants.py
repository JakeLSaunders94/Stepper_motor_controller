# -*- coding: utf-8 -*-
"""Constants for motor controller."""

# 3rd-party
from RpiMotorLib.RpiMotorLib import A4988Nema

STEPPER_DRIVER_TYPES = [
    # [stepper_type_name, rpimsotorlib_driver_class]
    # Add to this as support comes online.
    ["A4988", A4988Nema],
]

AVAILABLE_RPI_GPIO_PINS = [
    (3, "GPIO 2 - Pin 3"),
    (5, "GPIO 3 - Pin 5"),
    (7, "GPIO 4 - Pin 7"),
    (8, "GPIO 14 - Pin 8"),
    (10, "GPIO 15 - Pin 10"),
    (11, "GPIO 17 - Pin 11"),
    (12, "GPIO 18 - Pin 12"),
    (13, "GPIO 27 - Pin 13"),
    (15, "GPIO 22 - Pin 15"),
    (16, "GPIO 23 - Pin 16"),
    (18, "GPIO 23 - Pin 18"),
    (19, "GPIO 10 - Pin 19"),
    (21, "GPIO 9 - Pin 21"),
    (22, "GPIO 25 - Pin 22"),
    (23, "GPIO 11 - Pin 23"),
    (24, "GPIO 8 - Pin 24"),
    (26, "GPIO 7 - Pin 26"),
    (27, "GPIO 0 - Pin 27"),
    (28, "GPIO 1 - Pin 28"),
    (29, "GPIO 5 - Pin 29"),
    (31, "GPIO 6 - Pin 31"),
    (32, "GPIO 12 - Pin 32"),
    (33, "GPIO 13 - Pin 33"),
    (35, "GPIO 19 - Pin 35"),
    (36, "GPIO 16 - Pin 36"),
    (37, "GPIO 26 - Pin 37"),
    (38, "GPIO 20 - Pin 38"),
    (40, "GPIO 21 - Pin 40"),
]

# These are all the models that use GPIO pins.
# Used to check each pin is only used once.
GPIO_PIN_USING_MODELS = ["motor_controller.StepperMotor"]
