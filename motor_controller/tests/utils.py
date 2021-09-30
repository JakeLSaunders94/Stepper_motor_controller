# -*- coding: utf-8 -*-
"""Utilities to help with testing."""
# 3rd-party
import factory
from factory.django import DjangoModelFactory

# Project
from motor_controller.constants import AVAILABLE_RPI_GPIO_PINS
from motor_controller.constants import STEPPER_DRIVER_TYPES
from motor_controller.models import StepperMotor


class StepperMotorFactory(DjangoModelFactory):
    """Factory for StepperMotor model."""

    name = factory.Sequence(lambda n: f"Stepper Motor {n}")
    description = factory.Sequence(lambda n: f"Factory generated stepper Motor {n}")
    driver_type = STEPPER_DRIVER_TYPES[0][0]
    direction_GPIO_pin = AVAILABLE_RPI_GPIO_PINS[0][0]
    step_GPIO_pin = AVAILABLE_RPI_GPIO_PINS[1][0]

    class Meta:  # noqa: D106
        model = StepperMotor
