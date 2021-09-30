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
from motor_controller.exceptions import CommandError
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

    def test_steps_per_rev(self):
        """Test function calculates properly."""
        self.basic_motor.MS1_GPIO_pin = 1
        self.basic_motor.MS2_GPIO_pin = 2
        self.basic_motor.MS3_GPIO_pin = 3

        # [steptype, steps_per_rev, expected_steps]
        tests = [
            ["Full", 100, 100],
            ["Half", 200, 400],
            ["1/4", 10, 40],
            ["1/8", 20, 160],
            ["1/16", 23, 23 * 16],
        ]
        for test in tests:
            self.basic_motor.steptype = test[0]
            self.basic_motor.steps_per_revolution = test[1]
            assert self.basic_motor.steps_per_rev == test[2]

    def test_direction_of_rotation_getter(self):
        """Test the getter for direction of rotation."""
        self.basic_motor._direction_of_rotation = True
        assert self.basic_motor.direction_of_rotation == "clockwise"
        self.basic_motor._direction_of_rotation = False
        assert self.basic_motor.direction_of_rotation == "anti-clockwise"

    def test_steptype_getter(self):
        """Test for the steptype getter."""
        for options in ["Full", "Half", "1/4", "1/8", "1/16", "barry"]:
            self.basic_motor._steptype = options
            assert self.basic_motor.steptype == options

    def test_step_delay_getter(self):
        """Test the step_delay getter."""
        for options in [0.01, 0.1, 0.5, 1, 5, 105]:
            self.basic_motor._step_delay = options
            assert self.basic_motor.step_delay == options

    def test_init_delay_getter(self):
        """Test the step_delay getter."""
        for options in [0.01, 0.1, 0.5, 1, 5, 105]:
            self.basic_motor._init_delay = options
            assert self.basic_motor.init_delay == options

    def test_direction_of_rotation_setter(self):
        """Test the direction_of_rotation setter."""
        self.basic_motor.direction_of_rotation = "clockwise"
        assert self.basic_motor._direction_of_rotation
        self.basic_motor.direction_of_rotation = "anti-clockwise"
        assert not self.basic_motor._direction_of_rotation

        with self.assertRaises(ValueError) as e:
            self.basic_motor.direction_of_rotation = "Dis is wrong Yo!"
        assert (
            str(e.exception)
            == "That is not a valid option, please choose 'clockwise' or 'anti-clockwise'."
        )

    def test_steptype_setter_raises_value_error_if_GPIO_pins_not_set(self):
        """Test for the steptype setter."""
        with self.assertRaises(ValueError) as e:
            self.basic_motor.steptype = "Half"
        assert (
            str(e.exception) == "MSX pins are not configured for this motor, "
            "therefore only full steps are allowed."
        )

    def test_steptype_setter_raises_valuerror_if_steptype_not_in_list(self):
        """Function should raise a ValueError if the requested steptype is not in list."""
        self.basic_motor.MS1_GPIO_pin = 1
        self.basic_motor.MS2_GPIO_pin = 2
        self.basic_motor.MS3_GPIO_pin = 3

        with self.assertRaises(ValueError) as e:
            self.basic_motor.steptype = "Whatever"
        assert (
            str(e.exception) == "That is not a valid step type. Options are "
            "['Full', 'Half', '1/4', '1/8', '1/16']"
        )

    def test_steptype_setter_sets_steptype_correctly(self):
        """Test setting of steptype with setter."""
        self.basic_motor.MS1_GPIO_pin = 1
        self.basic_motor.MS2_GPIO_pin = 2
        self.basic_motor.MS3_GPIO_pin = 3

        for possible in ["Full", "Half", "1/4", "1/8", "1/16"]:
            self.basic_motor.steptype = possible
            assert self.basic_motor._steptype == possible

    def test_step_delay_setter_raises_ValueError_if_not_int_or_float(self):
        """Step delay values should be integers or floats only."""
        for items in ["bananas", AssertionError, self.basic_motor]:
            with self.assertRaises(ValueError) as e:
                self.basic_motor.step_delay = items
            assert str(e.exception) == "Step delay must be a numeric value in seconds."

    def test_step_delay_saves_value_always_as_a_float(self):
        """Setter should set value always as a float."""
        for items in [0, 1, 5.2, 123, 12.132435344]:
            self.basic_motor.step_delay = items
            assert self.basic_motor._step_delay == float(items)

    def test_init_delay_setter_raises_ValueError_if_not_int_or_float(self):
        """Init delay values should be integers or floats only."""
        for items in ["bananas", AssertionError, self.basic_motor]:
            with self.assertRaises(ValueError) as e:
                self.basic_motor.init_delay = items
            assert str(e.exception) == "Step delay must be a numeric value in seconds."

    def test_init_delay_saves_value_always_as_a_float(self):
        """Setter should set value always as a float."""
        for items in [0, 1, 5.2, 123, 12.132435344]:
            self.basic_motor.init_delay = items
            assert self.basic_motor._init_delay == float(items)

    @patch("motor_controller.models.A4988Nema")
    def test_move_steps_raises_CommandError_if_steps_is_not_int(self, mock_nema):
        """Move steps command should only take an integer value."""
        for items in ["bananas", AssertionError, self.basic_motor]:
            with self.assertRaises(CommandError) as e:
                self.basic_motor.move_steps(items)
            assert str(e.exception) == f"{items} is not a valid number of steps."

    @patch("motor_controller.models.StepperMotor._init_controller_class")
    @patch("motor_controller.models.A4988Nema")
    def test_move_steps_initalises_controller_if_not_initialised(self, mock_nema, mock_init):
        """Move steps command should init the controller class if not done already."""
        mock_init.return_value = "controller"
        self.basic_motor._controller = None
        with self.assertRaises(AttributeError):  # mocked nema
            self.basic_motor.move_steps(1)
        mock_init.assert_called_once()

    @patch("motor_controller.models.logging")
    @patch("motor_controller.models.A4988Nema")
    def test_move_steps_logs_move_if_requested(self, mock_nema, mock_logging):
        """Function should log the move made if requested or default."""
        self.basic_motor.controller_class = mock_nema
        self.basic_motor.move_steps(1)
        mock_logging.info.assert_called_once_with(
            f"Moving stepper {self.basic_motor.name} 1 x {self.basic_motor.steptype} "
            f"steps in the {self.basic_motor.direction_of_rotation} direction.",
        )

    @patch("motor_controller.models.A4988Nema")
    def test_move_steps_calls_motor_go_with_correct_params(self, mock_nema):
        """Function should call move_motor with correct params."""
        self.basic_motor._controller = mock_nema
        self.basic_motor.move_steps(1)
        mock_nema.motor_go.assert_called_once_with(
            self.basic_motor._direction_of_rotation,
            self.basic_motor._steptype,
            1,
            self.basic_motor._step_delay,
            self.basic_motor._verbose,
            self.basic_motor.init_delay,
        )

    @patch("motor_controller.models.A4988Nema")
    def test_move_rotations_raises_CommandError_if_rotations_is_not_int_or_float(self, mock_nema):
        """Move steps command should only take a numeric value."""
        for items in ["bananas", AssertionError, self.basic_motor]:
            with self.assertRaises(CommandError) as e:
                self.basic_motor.move_rotations(items)
            assert str(e.exception) == f"{items} is not a valid number of rotations."

    @patch("motor_controller.models.logging")
    @patch("motor_controller.models.A4988Nema")
    def test_move_rotations_logs_move_if_requested(self, mock_nema, mock_logging):
        """Function should log the move made."""
        self.basic_motor.controller_class = mock_nema
        self.basic_motor.move_rotations(1)
        mock_logging.info.assert_called_once_with(
            f"Moving stepper {self.basic_motor.name} 1 x rotations (200 steps) "
            f"in the {self.basic_motor.direction_of_rotation} direction.",
        )

    @patch("motor_controller.models.StepperMotor.move_steps")
    @patch("motor_controller.models.A4988Nema")
    def test_move_rotations_calls_move_steps_with_correct_steps(self, mock_nema, mock_steps):
        """Function should call move_steps with calced steps and logging off."""
        self.basic_motor.steps_per_revolution = 1
        self.basic_motor.controller_class = mock_nema
        self.basic_motor.move_rotations(1)
        mock_steps.assert_called_once_with(1, log=False)

    @patch("motor_controller.models.StepperMotor.move_steps")
    @patch("motor_controller.models.A4988Nema")
    def test_steps_per_rev_calculation_in_move_rotations(self, mock_nema, mock_steps):
        """Test that the function always calculates correct steps for rotation."""
        # [steps_per_revolution, rotations, steptype, expected_steps]
        self.basic_motor.controller_class = mock_nema
        self.basic_motor.MS1_GPIO_pin = 1
        self.basic_motor.MS2_GPIO_pin = 2
        self.basic_motor.MS3_GPIO_pin = 3

        tests = [
            [1, 1, "Full", 1],
            [1, 10, "Half", 20],
            [100, 1, "1/4", 400],
            [534, 0.5432, "Full", 290],
        ]
        for test in tests:
            self.basic_motor.steps_per_revolution = test[0]
            self.basic_motor.steptype = test[2]
            self.basic_motor.move_rotations(test[1])
            mock_steps.assert_called_once_with(test[3], log=False)
            mock_steps.reset_mock()

    def test_move_mm_raises_CommandError_if_mm_is_not_int_or_float(self):
        """Move mm command should only take a numeric value."""
        for items in ["bananas", AssertionError, self.basic_motor]:
            with self.assertRaises(CommandError) as e:
                self.basic_motor.move_mm(items)
            assert str(e.exception) == f"{items} is not a valid millimeter measurement."

    def test_move_mm_raises_ConfigurationError_if_mm_per_revolution_not_set(self):
        """The mm_per_revolution attribute must be set to use move_mm."""
        with self.assertRaises(ConfigurationError) as e:
            self.basic_motor.move_mm(2)
        assert str(e.exception) == "You have not designated a mm/rev for this motor."

    @patch("motor_controller.models.logging")
    @patch("motor_controller.models.A4988Nema")
    def test_move_rotations_logs_move(self, mock_nema, mock_logging):
        """Function should log the move made."""
        self.basic_motor.controller_class = mock_nema
        self.basic_motor.mm_per_revolution = 1
        self.basic_motor.move_mm(1)
        mock_logging.info.assert_called_once_with(
            f"Moving stepper {self.basic_motor.name} 1mm (200 steps) "
            f"in the {self.basic_motor.direction_of_rotation} direction.",
        )

    @patch("motor_controller.models.StepperMotor.move_steps")
    @patch("motor_controller.models.A4988Nema")
    def test_move_mm_calls_move_steps_with_correct_steps(self, mock_nema, mock_steps):
        """Function should call move_steps with calced steps and logging off."""
        self.basic_motor.steps_per_revolution = 2
        self.basic_motor.mm_per_revolution = 1
        self.basic_motor.controller_class = mock_nema
        self.basic_motor.move_mm(1)
        mock_steps.assert_called_once_with(2, log=False)

    @patch("motor_controller.models.StepperMotor.move_steps")
    @patch("motor_controller.models.A4988Nema")
    def test_steps_calculation_in_move_mm(self, mock_nema, mock_steps):
        """Test that the function always calculates correct steps for rotation."""
        # [steps_per_revolution, mm, steptype, mm_per_revolution, expected_steps]
        self.basic_motor.controller_class = mock_nema
        self.basic_motor.MS1_GPIO_pin = 1
        self.basic_motor.MS2_GPIO_pin = 2
        self.basic_motor.MS3_GPIO_pin = 3

        tests = [
            [1, 1, "Full", 1, 1],
            [1, 10, "Half", 1, 20],
            [100, 1, "1/4", 2, 400],
            [534, 0.5432, "Full", 1, 290],
        ]
        for test in tests:
            self.basic_motor.steps_per_revolution = test[0]
            self.basic_motor.steptype = test[2]
            self.basic_motor.mm_per_revolution = test[3]
            self.basic_motor.move_rotations(test[1])
            mock_steps.assert_called_once_with(test[4], log=False)
            mock_steps.reset_mock()

    @patch("motor_controller.models.StepperMotor.clean")
    def test_save_calls_clean_method(self, mock_clean):
        """Saving the model should call clean."""
        self.basic_motor.save()
        mock_clean.assert_called_once()
