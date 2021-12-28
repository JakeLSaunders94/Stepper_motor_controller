# -*- coding: utf-8 -*-
"""Globally used constants for all apps."""

AVAILABLE_RPI_GPIO_PINS = [
    (2, "GPIO 2 - Pin 3"),
    (3, "GPIO 3 - Pin 5"),
    (4, "GPIO 4 - Pin 7"),
    (14, "GPIO 14 - Pin 8"),
    (15, "GPIO 15 - Pin 10"),
    (17, "GPIO 17 - Pin 11"),
    (18, "GPIO 18 - Pin 12"),
    (27, "GPIO 27 - Pin 13"),
    (22, "GPIO 22 - Pin 15"),
    (23, "GPIO 23 - Pin 16"),
    (24, "GPIO 24 - Pin 18"),
    (10, "GPIO 10 - Pin 19"),
    (9, "GPIO 9 - Pin 21"),
    (25, "GPIO 25 - Pin 22"),
    (11, "GPIO 11 - Pin 23"),
    (8, "GPIO 8 - Pin 24"),
    (7, "GPIO 7 - Pin 26"),
    (0, "GPIO 0 - Pin 27"),
    (1, "GPIO 1 - Pin 28"),
    (5, "GPIO 5 - Pin 29"),
    (6, "GPIO 6 - Pin 31"),
    (12, "GPIO 12 - Pin 32"),
    (13, "GPIO 13 - Pin 33"),
    (19, "GPIO 19 - Pin 35"),
    (16, "GPIO 16 - Pin 36"),
    (26, "GPIO 26 - Pin 37"),
    (20, "GPIO 20 - Pin 38"),
    (21, "GPIO 21 - Pin 40"),
]

# These are all the models that use GPIO pins.
# Used to check each pin is only used once.
GPIO_PIN_USING_MODELS = [
    "motor_controller.StepperMotor",
    "switch_controller.PushSwitch",
]
