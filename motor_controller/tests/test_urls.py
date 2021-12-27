# -*- coding: utf-8 -*-
"""Tests for urls.py."""

# Standard Library
from unittest import TestCase

# Django
from django.urls import reverse

from motor_controller.views import move_stepper_motor_ajax_view, stepper_motor_modal_ajax_view, \
    stepper_motor_basic_control_view


class TestURLs(TestCase):
    def test_urls(self):
        assert (
            reverse(move_stepper_motor_ajax_view, args=[1])
            == "motor-controller/stepper-motor-move/1"
        )
        assert (
                reverse(stepper_motor_modal_ajax_view, args=[1])
                == "motor-controller/stepper-motor-modal/1"
        )
        assert (
                reverse(stepper_motor_basic_control_view, args=[1])
                == "motor-controller/stepper-motor-control"
        )
