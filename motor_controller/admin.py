# -*- coding: utf-8 -*-
"""Admin."""

# Django
from django.contrib import admin  # noqa: F401

# Project
from motor_controller.models import StepperMotor

admin.site.register(StepperMotor)
