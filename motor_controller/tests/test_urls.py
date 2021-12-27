# -*- coding: utf-8 -*-
"""Tests for urls.py."""

# Standard Library
from unittest import TestCase

# Django
from django.urls import reverse


class TestURLs(TestCase):
    def test_urls(self):
        assert (
            reverse("move_stepper_motor_ajax_view", args=[1])
            == "motor-controller/stepper-motor-move/1"
        )
