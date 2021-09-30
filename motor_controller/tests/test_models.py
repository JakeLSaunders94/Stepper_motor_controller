# -*- coding: utf-8 -*-
"""Tests for models.py."""

# Standard Library
from unittest.mock import patch

# Django
from django.core.exceptions import ValidationError
from django.test import TestCase

# Project
from motor_controller.constants import AVAILABLE_RPI_GPIO_PINS
from motor_controller.constants import STEPPER_DRIVER_TYPES
from motor_controller.exceptions import ConfigurationError
from motor_controller.exceptions import ImplementationError
from motor_controller.models import Motor
from motor_controller.models import StepperMotor
from motor_controller.tests.utils import StepperMotorFactory


class TestMotor(TestCase):
    """Tests for the Motor model parent class."""

    def test_gpio_pin_fields_raises_notimplementederror_when_not_subclassed(self):
        """Property should raise an error if not implemented in concrete subclass."""
        with self.assertRaises(NotImplementedError) as e:
            motor = Motor()
            motor.gpio_pin_fields
        assert str(e.exception) == "This needs to be set by the concrete subclass."

    # Note that checking for GPIO pin usage cannot be completed in this base model
    # as there are no GPIO pin fields implemented.
    # TODO - Tests for GPIO pin usage in concrete subclass.


class TestStepperMotor(TestCase):
    """Tests for the StepperMotor class."""

    def setUp(self) -> None:  # noqa: D102
        self.basic_motor = StepperMotor(
            driver_type="A4988",
            name="Basic Motor",
            direction_GPIO_pin=24,
            step_GPIO_pin=26,
        )

    def test_init_params(self):
        """The class should be initialised with the correct params."""
        motor = StepperMotorFactory()
        assert motor._direction_of_rotation
        assert motor._steptype == "Full"
        assert motor._step_delay == 0.01
        assert not motor._verbose
        assert motor._init_delay == 0.001

    def test_init_assigns_controller_class_on_init_if_driver_type_is_set(self):
        """If the instance has a driver type, set the self.controller_class attr."""
        motor = StepperMotor(driver_type=STEPPER_DRIVER_TYPES[0][0])
        assert motor.controller_class == STEPPER_DRIVER_TYPES[0][1]

    def test_init_does_not_assign_controller_class_on_init_if_no_driver_type(self):
        """If the instance has a driver type, set the self.controller_class attr."""
        motor = StepperMotor()
        assert not motor.controller_class

    def test_correct_GPIO_pin_fields_set(self):
        """The correct GPIO pin fields should have been set for the model."""
        expected_fields = []
        for field in StepperMotor._meta.fields:
            if field.choices == AVAILABLE_RPI_GPIO_PINS:
                expected_fields.append(field.name)

        motor = StepperMotor()
        assert set(motor.gpio_pin_fields) == set(expected_fields)
        # TODO - Could we not just use this logic for the attr, or would it be circular?

    def test_clean_A4988_errors_if_direction_and_step_pin_not_set(self):
        """For A4988 drivers, the direction and step pin should be set."""
        motor = StepperMotor(driver_type="A4988", name="Tester", direction_GPIO_pin=5)
        with self.assertRaises(ValidationError) as e:
            motor.clean()
        assert str(e.exception) == str(
            {"step_GPIO_pin": ["This field is required for this driver type."]},
        )

        motor = StepperMotor(driver_type="A4988", name="Tester", step_GPIO_pin=5)
        with self.assertRaises(ValidationError) as e:
            motor.clean()
        assert str(e.exception) == str(
            {"direction_GPIO_pin": ["This field is required for this driver type."]},
        )

    def test_clean_A4988_errors_if_not_all_3_MSX_pins_set(self):
        """For A4988 drivers, all 3 MSX pins should be set or none."""
        motor = StepperMotor(
            driver_type="A4988",
            name="Tester",
            direction_GPIO_pin=5,
            step_GPIO_pin=7,
        )
        motor.clean()  # Should be fine

        motor = StepperMotor(
            driver_type="A4988",
            name="Tester",
            direction_GPIO_pin=5,
            step_GPIO_pin=7,
            MS1_GPIO_pin=16,
            MS2_GPIO_pin=18,
            MS3_GPIO_pin=21,
        )
        motor.clean()  # Should be fine

        motor = StepperMotor(
            driver_type="A4988",
            name="Tester",
            direction_GPIO_pin=5,
            step_GPIO_pin=7,
            MS1_GPIO_pin=13,
        )
        with self.assertRaises(ValidationError) as e:
            motor.clean()
        assert str(e.exception) == str(
            {
                "MS1_GPIO_pin": ["All three of these must be set or none."],
                "MS2_GPIO_pin": ["All three of these must be set or none."],
                "MS3_GPIO_pin": ["All three of these must be set or none."],
            },
        )

    def test_clean_faults_if_same_GPIO_pin_used_twice_in_same_instance(self):
        """Validationerror should be raised if the same GPIO pin used twice, same instance."""
        motor = StepperMotor(
            driver_type="A4988",
            name="Tester",
            direction_GPIO_pin=5,
            step_GPIO_pin=5,
        )
        with self.assertRaises(ValidationError) as e:
            motor.clean()

        # Assert parts to prevent flakeyness with ordering.
        exception_text = str(e.exception)
        assert "GPIO pins must be unique." in exception_text
        assert "step_GPIO_pin" in exception_text
        assert "direction_GPIO_pin" in exception_text

    def test_clean_faults_if_same_GPIO_pin_used_twice_in_different_instance(self):
        """Validationerror should be raised if the same GPIO pin used twice, different instance."""
        motor1 = StepperMotor.objects.create(
            driver_type="A4988",
            name="First Motor",
            direction_GPIO_pin=5,
            step_GPIO_pin=7,
        )
        motor2 = StepperMotor(
            driver_type="A4988",
            name="Second Motor",
            direction_GPIO_pin=5,
            step_GPIO_pin=7,
        )

        with self.assertRaises(ValidationError) as e:
            motor2.clean()
        assert (
            f"This GPIO pin is already in use on {motor1.name}, "
            f"please select another." in str(e.exception)
        )

    def test_get_controller_class_raises_ConfigurationError_if_no_driver_type(self):
        """Configuration Error should be raised if instance has no driver type."""
        motor1 = StepperMotor(
            name="First Motor",
            direction_GPIO_pin=5,
            step_GPIO_pin=7,
        )
        with self.assertRaises(ConfigurationError) as e:
            motor1.get_controller_class()
        assert (
            str(e.exception) == "This class does not have a driver set yet. Save the "
            "model first."
        )

    @patch("motor_controller.models.STEPPER_DRIVER_TYPES", [["A4988", "Tomatos"]])
    def test_get_controller_class_returns_correct_constant(self):
        """Function should return the second constant for given driver type."""
        motor = StepperMotor(
            driver_type="A4988",
            name="First Motor",
            direction_GPIO_pin=5,
            step_GPIO_pin=7,
        )
        assert motor.get_controller_class() == "Tomatos"

    @patch("motor_controller.models.STEPPER_DRIVER_TYPES", [["A4988"]])
    def test_get_controller_class_returns_raises_error_if_bad_list(self):
        """Function should raise an Implementation error if driver class not set."""
        with self.assertRaises(ImplementationError) as e:
            motor = StepperMotor(
                driver_type="A4988",
                name="First Motor",
                direction_GPIO_pin=5,
                step_GPIO_pin=7,
            )
            motor.get_controller_class()
        assert str(e.exception) == "Driver class not set for driver."

    @patch("motor_controller.models.StepperMotor.get_controller_class")
    def test_init_controller_class_gets_controller_class_if_needed(self, mock_get):
        """Function should get the controller class if not set."""
        self.basic_motor.controller_class = None
        mock_get.reset_mock()
        self.basic_motor._init_controller_class()
        mock_get.assert_called_once()
        assert self.basic_motor.controller_class

    @patch("motor_controller.constants.A4988Nema")
    @patch("motor_controller.models.A4988Nema")
    def test_A4988Nema_sets_controller_MSX_pins_set(self, mock_nema_models, mock_nema_constants):
        """Function should assign and init an A4988Nema class with MSX pin settings."""
        self.basic_motor.MS1_GPIO_pin = 1
        self.basic_motor.MS2_GPIO_pin = 2
        self.basic_motor.MS3_GPIO_pin = 3

        # Patch out the controller class, because of the multiple
        # imports from different places
        self.basic_motor.controller_class = mock_nema_models

        mock_nema_models.return_value = "Return"

        self.basic_motor._init_controller_class()
        mock_nema_models.assert_called_once_with(
            direction_pin=self.basic_motor.direction_GPIO_pin,
            mode_pins=(
                self.basic_motor.MS1_GPIO_pin,
                self.basic_motor.MS2_GPIO_pin,
                self.basic_motor.MS3_GPIO_pin,
            ),
            step_pin=self.basic_motor.step_GPIO_pin,
        )
        assert self.basic_motor._controller == "Return"

    @patch("motor_controller.constants.A4988Nema")
    @patch("motor_controller.models.A4988Nema")
    def test_A4988Nema_sets_controller_MSX_pins_not_set(
        self,
        mock_nema_models,
        mock_nema_constants,
    ):
        """Function should assign and init an A4988Nema class with default MSX pin settings."""

        # Patch out the controller class, because of the multiple
        # imports from different places
        self.basic_motor.controller_class = mock_nema_models

        mock_nema_models.return_value = "Return"

        self.basic_motor._init_controller_class()
        mock_nema_models.assert_called_once_with(
            direction_pin=self.basic_motor.direction_GPIO_pin,
            mode_pins=(-1, -1, -1),
            step_pin=self.basic_motor.step_GPIO_pin,
        )
        assert self.basic_motor._controller == "Return"
