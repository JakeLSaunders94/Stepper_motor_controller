# -*- coding: utf-8 -*-
"""Urls."""

# Django
from django.urls import path

# Local
from .views import move_stepper_move_ajax_view
from .views import stepper_motor_basic_control_view
from .views import stepper_motor_modal_ajax_view

urlpatterns = [
    path(
        "stepper-motor-move/<motor_id>",
        move_stepper_move_ajax_view,
        name="stepper_motor_move",
    ),
    path(
        "stepper-motor-modal/<motor_id>",
        stepper_motor_modal_ajax_view,
        name="stepper_motor_modal",
    ),
    path(
        "stepper-motor-control",
        stepper_motor_basic_control_view,
        name="stepper_motor_control",
    ),
]
