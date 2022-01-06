# -*- coding: utf-8 -*-
"""
Tests for switch models.

There is limited testing we can do here without direct GPIO outputs.
"""

# Standard Library
from unittest.mock import patch

# Django
from django.core.exceptions import ValidationError
from django.test import TestCase

# Project
import switch_controller.models
from common.constants import AVAILABLE_RPI_GPIO_PINS
from common.constants import RPI_GPIO_MODE
from common.exceptions import ImplementationError
from switch_controller.constants import PUSH_SWITCH_TYPES
from switch_controller.models import PushSwitch

# Local
from .utils import PushSwitchFactory


class TestPushSwitch(TestCase):
    """Tests for the PushSwitch model."""

    def setUp(self) -> None:  # noqa: D012
        self.switch = PushSwitchFactory()

    def test_push_switch_type_choices(self):
        """Should only be able to save the type as one of the choices."""
        with self.assertRaisesMessage(ValidationError, "Value 'Barry' is not a valid choice."):
            switch = PushSwitch(
                name="Switchy",
                switch_type="Barry",
                input_GPIO_pin=AVAILABLE_RPI_GPIO_PINS[0][0],
            )
            switch.full_clean()

    def test_gpio_pin_valid_choice(self):
        """Should only be able to save the GPIO pin as one of the correct pins."""
        with self.assertRaisesMessage(ValidationError, "Value 99999 is not a valid choice."):
            switch = PushSwitch(
                name="Switchy",
                switch_type=PUSH_SWITCH_TYPES[0][0],
                input_GPIO_pin=99999,
            )
            switch.full_clean()

    @patch("common.utils.GPIO_PIN_USING_MODELS", ["Something"])
    def test_clean_raises_ImplementationError_if_GPIO_PIN_USING_MODELS_incorrect(self):
        """Clean should error if the models to check are defined incorrectly."""
        with self.assertRaises(ImplementationError) as e:
            self.switch.clean()
        assert (
            str(e.exception) == "The format for defining models is '<app_name>.<model_name>', you "
            "defined Something."
        )

    def test_clean_faults_if_same_GPIO_pin_used_twice_in_different_instance(self):
        """ValidationError should be raised if the same GPIO pin used twice, different instance."""
        switch1 = PushSwitch.objects.create(
            name="First Switch",
            switch_type=PUSH_SWITCH_TYPES[0][0],
            input_GPIO_pin=5,
        )
        switch2 = PushSwitch(
            name="Second Switch",
            switch_type=PUSH_SWITCH_TYPES[0][0],
            input_GPIO_pin=5,
        )

        with self.assertRaises(ValidationError) as e:
            switch2.clean()
        assert (
            f"This GPIO pin is already in use on {switch1.name}, "
            f"please select another." in str(e.exception)
        )

    @patch("switch_controller.models.GPIO")
    def test_initialise_initialises_GPIO_pin(self, GPIO_mock):
        """We can't really test this, so just check with mocks."""
        self.switch.initialise()
        GPIO_mock.setmode.assert_called_once_with(RPI_GPIO_MODE)
        GPIO_mock.setup.assert_called_once_with(self.switch.input_GPIO_pin, GPIO_mock.IN)
        assert self.switch.initialised

    def test_is_made_initialises_if_not_already(self):
        """Is_made should initilaise the GPIO if it hasn't been done already."""
        assert not self.switch.initialised
        self.switch.is_made
        assert self.switch.initialised

    @patch("switch_controller.models.GPIO")
    def test_is_made_output(self, GPIO_mock):
        """Is_made should output based on the GPIO pin status. Again, mocking a lot here."""
        GPIO_mock.HIGH = 123
        GPIO_mock.input.return_value = 123
        assert self.switch.is_made

        GPIO_mock.input.return_value = 321
        assert not self.switch.is_made

    @patch("switch_controller.models.GPIO")
    def test_is_pressed_output(self, GPIO_mock):
        """Is_pressed should output based on is made and type."""
        GPIO_mock.HIGH = 123
        GPIO_mock.input.return_value = 123
        assert self.switch.is_pressed

        self.switch.switch_type = "PTB"
        assert not self.switch.is_pressed
