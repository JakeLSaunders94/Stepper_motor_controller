# -*- coding: utf-8 -*-
"""Models for switch controller."""
# Standard Library
from typing import Union

# Django
from django.db import models

# Project
from common.constants import AVAILABLE_RPI_GPIO_PINS
from common.constants import RPI_GPIO_MODE
from common.utils import check_for_GPIO_pin_use_in_this_and_other_models
from common.utils import check_for_GPIO_pin_use_in_this_instance
from switch_controller.constants import PUSH_SWITCH_TYPES

# Conditional GPIO import for non Pi machine testing purposes
try:
    # 3rd-party
    import RPi.GPIO as GPIO
except ImportError:
    # 3rd-party
    import Mock.GPIO as GPIO


class Switch(models.Model):
    """Generic parent class for switches."""

    name = models.CharField(max_length=200, help_text="An identifiable name.")

    class Meta:  # noqa: D106
        db_table = None


class PushSwitch(Switch):
    """Push switches."""

    switch_type = models.CharField(choices=PUSH_SWITCH_TYPES, max_length=200)
    input_GPIO_pin = models.IntegerField(choices=AVAILABLE_RPI_GPIO_PINS)

    def __init__(self, *args, **kwargs):  # noqa: D107
        self.initialised = False
        super().__init__(*args, **kwargs)

    @property
    def gpio_pin_fields(self):
        """All fields housing GPIO pin config in this model."""
        return [
            "input_GPIO_pin",
        ]

    def clean(self):  # noqa: D102
        check_for_GPIO_pin_use_in_this_instance(self)
        check_for_GPIO_pin_use_in_this_and_other_models(self)
        super(PushSwitch, self).clean()

    def initialise(self):
        """Get the GPIO ready to accept the switch input."""
        GPIO.setmode(RPI_GPIO_MODE)
        GPIO.setup(
            self.input_GPIO_pin,
            GPIO.IN,
        )
        self.initialised = True

    @property
    def is_made(self):
        """Detect if the switch is made (unbroken circuit)."""
        if not self.initialised:
            self.initialise()
        return GPIO.input(self.input_GPIO_pin) == GPIO.HIGH

    @property
    def is_pressed(self):
        """Detect if the switch is pressed."""
        if self.switch_type == "PTM":
            return self.is_made
        elif self.switch_type == "PTB":
            return not self.is_made

    def wait_for_edge(
        self,
        edge=Union[GPIO.RISING, GPIO.FALLING, GPIO.BOTH],
        bouncetime: int = 50,
        timeout: int = None,
    ):
        """
        Block further program execution until an edge is detected.

        Rising will detect the switch being made.
        Falling wil detect the switch being broken.
        Both will... detect both.

        Returns false if timed out, else True.
        """
        if not self.initialised:
            self.initialise()
        edge = GPIO.wait_for_edge(self.input_GPIO_pin, edge, bouncetime=bouncetime, timeout=timeout)
        if edge is None:
            return False
        else:
            return True

    def begin_edge_detection(
        self,
        edge=Union[GPIO.RISING, GPIO.FALLING, GPIO.BOTH],
        bouncetime: int = 50,
        callback=None,
    ):
        """
        Add threaded edge detection to the switch.

        Add edge detection using this function, then check for detected edges
        using check_for_detected_edges.
        """
        if not self.initialised:
            self.initialise()
        GPIO.add_event_detect(
            self.input_GPIO_pin,
            edge=edge,
            bouncetime=bouncetime,
            callback=callback,
        )

    @property
    def edge_detected(self):
        """Has there been an edge detected."""
        return GPIO.event_detected(self.input_GPIO_pin)

    def remove_edge_detection(self):
        """Remove all edge detection from the switch."""
        GPIO.remove_event_detect(self.input_GPIO_pin)

    def kill(self):
        """Kill the GPIO connection and associated stuff."""
        GPIO.cleanup()
