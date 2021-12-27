# -*- coding: utf-8 -*-
"""Views."""

# Standard Library
import json

# Django
from django.http import JsonResponse
from django.shortcuts import render  # noqa: F401
from django.urls import reverse
from django.views.decorators.http import require_POST

# 3rd-party
from rest_framework import status

# Project
from motor_controller.exceptions import CommandError
from motor_controller.exceptions import ConfigurationError
from motor_controller.exceptions import ImplementationError
from motor_controller.models import StepperMotor


@require_POST
def move_stepper_motor_ajax_view(request, motor_id):
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
            {"error": "The specified movement type does not exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        log = move_function(data["movement_amount"])
    except (CommandError, ConfigurationError) as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)

    return JsonResponse({"log": log}, status=status.HTTP_200_OK)


@require_POST
def stepper_motor_modal_ajax_view(request, motor_id):
    """
    Change the modal properties of a stepper motor.

    This expects a property (which we will use for setattr) and a value.
    """
    data = json.loads(request.body)

    try:
        attr = data["property"]
        value = data["value"]
    except KeyError:
        response = {"error": "You did not provide a property or value key."}
        return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)

    try:
        motor = StepperMotor.objects.get(id=motor_id)
    except StepperMotor.DoesNotExist:
        response = {"error": "This stepper motor does not exist."}
        return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)

    if attr[:1] == "_":
        response = {"error": "You cannot set protected attributes with this API."}
        return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)

    try:
        setattr(motor, attr, value)
    except AttributeError:
        response = {"error": "Could not set this attribute, does not exist."}
        return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)
    except (CommandError, ImplementationError) as e:
        response = {"error": f"Could not set this attribute, error {e}."}
        return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)

    response = {"log": f"Attribute set successfully, new value {getattr(motor, attr)}"}
    return JsonResponse(response, status=status.HTTP_200_OK)


def stepper_motor_basic_control_view(request):
    """
    A basic view to select steppers and move them around.

    This doesn't do much apart from basic GET as all commands are posted to move_stepper_ajax_view.
    """
    context = {
        "stepper_motors": StepperMotor.objects.all(),
        "post_url": reverse(move_stepper_motor_ajax_view, args={"motor_id": 1}),
        "movement_types": ["move_mm", "move_steps", "move_rotations"],
    }
    return render(request, "stepper_motor_basic_control_view.html", context)
