# -*- coding: utf-8 -*-
"""Views."""

# Standard Library
import json

# Django
from django.http import JsonResponse
from django.shortcuts import render  # noqa: F401
from django.views.decorators.http import require_POST

# 3rd-party
from rest_framework import status

# Project
from motor_controller.exceptions import CommandError
from motor_controller.exceptions import ConfigurationError
from motor_controller.models import StepperMotor


@require_POST
def move_stepper_ajax_view(request, motor_id):
    """
    Async view to allow for movement of a given stepper.

    expected payload:
    {
        "motor_id": <int>
        "movement_type": [move_mm, move_steps, move_rotations],
        "movement_amount": <int>, possibly float,
    }
    """
    data = json.loads(request.body)

    try:
        motor = StepperMotor.objects.get(id=motor_id)
    except StepperMotor.DoesNotExist:
        return JsonResponse(
            {"error": "The specified motor does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        move_function = getattr(motor, data["movement_type"])
    except KeyError:
        return JsonResponse(
            {"error": "The specified motor does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        log = move_function(data["movement_amount"])
    except (CommandError, ConfigurationError) as e:
        return JsonResponse({"error": str(e.exception)}, status=status.HTTP_501_NOT_IMPLEMENTED)

    return JsonResponse({"log": log}, status=status.HTTP_200_OK)