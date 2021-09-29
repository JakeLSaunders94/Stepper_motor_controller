from unittest.mock import patch
from django.test import TestCase
from motor_controller.exceptions import ImplementationError
from motor_controller.models import Motor


class TestMotor(TestCase):
    """Tests for the Motor model parent class."""

    def test_gpio_pin_fields_raises_notimplementederror_when_not_subclassed(self):
        with self.assertRaises(NotImplementedError) as e:
            motor = Motor()
            get = motor.gpio_pin_fields
        assert str(e.exception) == "This needs to be set by the concrete subclass."

    # Note that checking for GPIO pin usage cannot be completed in this base model
    # as there are no GPIO pin fields implemented.
    # TODO - Tests for GPIO pin usage in concrete subclass.



