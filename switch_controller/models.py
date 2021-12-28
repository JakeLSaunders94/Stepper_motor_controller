# -*- coding: utf-8 -*-
"""Models for switch controller."""
# Django
from django.db import models

# Project
from constants import AVAILABLE_RPI_GPIO_PINS
from switch_controller.constants import PUSH_SWITCH_TYPES


class Switch(models.Model):
    """Generic parent class for switches."""

    name = models.CharField(max_length=200, help_text="An identifiable name.")

    class Meta:  # noqa: D106
        db_table = None


class PushSwitch(Switch):
    """Push switches."""

    switch_type = models.CharField(choices=PUSH_SWITCH_TYPES, max_length=200)
    input_GPIO_pin = models.IntegerField(choices=AVAILABLE_RPI_GPIO_PINS)

    @property
    def gpio_pin_fields(self):
        """All fields housing GPIO pin config in this model."""
        return [
            "input_GPIO_pin",
        ]
