# -*- coding: utf-8 -*-
"""Utilities to help with testing."""
# 3rd-party
import factory
from factory.django import DjangoModelFactory

# Project
from common.constants import AVAILABLE_RPI_GPIO_PINS
from switch_controller.constants import PUSH_SWITCH_TYPES
from switch_controller.models import PushSwitch


class PushSwitchFactory(DjangoModelFactory):
    """Factory for PushSwitch model."""

    name = factory.Sequence(lambda n: f"Push Switch {n}")
    switch_type = PUSH_SWITCH_TYPES[0][0]
    input_GPIO_pin = AVAILABLE_RPI_GPIO_PINS[0][0]

    class Meta:  # noqa: D106
        model = PushSwitch
