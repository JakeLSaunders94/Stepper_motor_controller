# -*- coding: utf-8 -*-
"""Common model classes."""

# Standard Library
from datetime import timedelta

# Django
from django.apps import apps
from django.db import models
from django.utils import timezone

# Conditional GPIO import for non Pi machine testing purposes
try:
    # 3rd-party
    import RPi.GPIO as GPIO
except ImportError:
    # 3rd-party
    import Mock.GPIO as GPIO

# Project
from common.exceptions import CommandError


class Lockout(models.Model):
    """
    A generic lockout model for keeping track of locks on PersistentDevices.

    Needs to be imported into the child apps models.py alongside PersistentDevice to work.
    """

    device_type = models.CharField(max_length=200)
    device_pk = models.BigIntegerField(max_length=200, verbose_name="Human Name")
    lockout_start = models.DateTimeField(default=timezone.now)
    lockout_end = models.DateTimeField()


class PersistentDevice(models.Model):
    """
    Persist hardware config to database and lock for use.

    Some of our hardware (e.g. motors) have the ability to receive commands as inputs. However,
    it's possible to pull them from the Db in any part of the app and start sending commands.
    This will cause a problem if you start sending two move commands to the same motor at the same
    time.

    To get around this, create a locking mech with an inbuilt timeout that checks that the device
    is in use.
    """

    def initialise(self, lockout_time=1000):
        """Check if the device has a lock and initialise."""
        if not self.pk:
            raise CommandError(
                "You cannot use a PersistentDevice without saving it to the DB first.",
            )

        lockout_model = apps.get_model(app_label=self._meta.app_label, model_name="Lockout")
        lockouts = lockout_model.objects.filter(
            device_type=self.__name__,
            lockout_end__gte=timezone.now(),
            manual_return=False,
            device_pk=self.pk,
        ).count()

        if lockouts > 0:
            raise CommandError(
                "Cannot initialise this PersistentDevice, another process has locked it out.",
            )

        lockout_model.objects.create(
            device_type=self.__name__,
            device_pk=self.pk,
            lockout_time=timezone.now(),
            lockout_end=timezone.now() + timedelta(seconds=lockout_time),
        )

    @property
    def gpio_pin_fields(self):
        """
        Return the fields of this model that contain GPIO info.

        This project is only designed to work with one RPi at a time, so pins can only
        be used once.
        Allows for checking of used GPIO pins across all motors.
        """
        raise NotImplementedError("This needs to be set by the concrete subclass.")

    def kill(self):
        """Remove the lockout and do a cleanup."""
        lockout_model = apps.get_model(app_label=self._meta.app_label, model_name="Lockout")
        lockout_model.objects.filter(
            device_type=self.__name__,
            lockout_end__gte=timezone.now(),
            manual_return=False,
            device_pk=self.pk,
        ).delete()

        GPIO.cleanup()
