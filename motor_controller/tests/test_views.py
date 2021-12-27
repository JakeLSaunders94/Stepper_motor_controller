# -*- coding: utf-8 -*-
"""Tests for views.py."""
# Standard Library
import json
from http.client import BAD_REQUEST
from http.client import NOT_IMPLEMENTED
from http.client import OK
from unittest.mock import patch

# Django
from django.test import RequestFactory
from django.test import TestCase

# Project
from motor_controller.exceptions import CommandError
from motor_controller.exceptions import ConfigurationError
from motor_controller.tests.utils import StepperMotorFactory
from motor_controller.views import move_stepper_motor_ajax_view


class TestMoveStepperMotorAJAXView(TestCase):
    """Tests for the move_stepper_motor_ajax_view."""

    def setUp(self) -> None:  # noqa: D102
        self.factory = RequestFactory()
        self.view = move_stepper_motor_ajax_view
        self.motor = StepperMotorFactory()

    def test_no_motor_found_gives_400_error(self):
        """If a motor cannot be found, return 400 and error message."""
        payload = {"motor_id": 2, "movement_type": "move_mm", "movement_amount": 123}
        request = self.factory.post("/", data=json.dumps(payload), content_type="application/json")

        response = self.view(request, motor_id=2)
        assert response.status_code == BAD_REQUEST
        assert json.loads(response.content) == {"error": "The specified motor does not exist."}

    def test_no_movement_type_gives_400_error(self):
        """If the specified movement type cannot be found, return 400 and error message."""
        payload = {"motor_id": self.motor.id, "movement_type": "move_feet", "movement_amount": 123}
        request = self.factory.post("/", data=json.dumps(payload), content_type="application/json")

        response = self.view(request, motor_id=self.motor.id)
        assert response.status_code == BAD_REQUEST
        assert json.loads(response.content) == {
            "error": "The specified movement type does not exist.",
        }

    @patch("motor_controller.models.StepperMotor.move_mm")
    def test_correct_payload_calls_correct_movement_function_and_returns_log_as_JSON(
        self, mock_move_mm,
    ):
        """The motors movement function should be called and the log returned as JSON."""
        mock_move_mm.return_value = "Called function successfully."

        payload = {"motor_id": self.motor.id, "movement_type": "move_mm", "movement_amount": 123}
        request = self.factory.post("/", data=json.dumps(payload), content_type="application/json")

        response = self.view(request, motor_id=self.motor.id)
        mock_move_mm.assert_called_once_with(123)
        assert response.status_code == OK
        assert json.loads(response.content) == {"log": "Called function successfully."}

    @patch("motor_controller.models.StepperMotor.move_mm")
    def test_command_error_and_configuration_error_return_error_as_json(self, mock_move_mm):
        """If a CommandError or ConfigurationError occur, send the error text back as JSON."""
        payload = {"motor_id": self.motor.id, "movement_type": "move_mm", "movement_amount": 123}
        for effect in [CommandError, ConfigurationError]:
            mock_move_mm.reset_mock()
            mock_move_mm.side_effect = effect("Error occurred!")
            request = self.factory.post(
                "/", data=json.dumps(payload), content_type="application/json",
            )
            response = self.view(request, motor_id=self.motor.id)
            mock_move_mm.assert_called_once_with(123)
            assert response.status_code == NOT_IMPLEMENTED
            assert json.loads(response.content) == {"error": "Error occurred!"}
