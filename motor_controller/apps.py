# -*- coding: utf-8 -*-
"""Appconfig."""

# Django
from django.apps import AppConfig


class NemaStepperControllerConfig(AppConfig):  # noqa: D101
    default_auto_field = "django.db.models.BigAutoField"
    name = "motor_controller"
