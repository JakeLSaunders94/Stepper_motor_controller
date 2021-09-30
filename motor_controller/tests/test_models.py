# -*- coding: utf-8 -*-
"""Tests for models.py."""

# Django
from django.core.exceptions import ValidationError
from django.test import TestCase

# Project
from motor_controller.constants import AVAILABLE_RPI_GPIO_PINS
from motor_controller.constants import STEPPER_DRIVER_TYPES
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
            MS3_GPIO_pin=21
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
            }
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
