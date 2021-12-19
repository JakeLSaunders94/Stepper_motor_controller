# -*- coding: utf-8 -*-
"""Models for motor control."""

# Standard Library
import logging

# Django
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

# 3rd-party
from RpiMotorLib.RpiMotorLib import A4988Nema

# Local
from .constants import AVAILABLE_RPI_GPIO_PINS
from .constants import GPIO_PIN_USING_MODELS
from .constants import STEPPER_DRIVER_TYPES
from .exceptions import CommandError
from .exceptions import ConfigurationError
from .exceptions import ImplementationError


class Motor(models.Model):
    """A Generic class for all motors, subclassed by concrete motor type classes."""

    name = models.CharField(max_length=200, verbose_name="Human Name")
    description = models.TextField(null=True, blank=True)

    @property
    def gpio_pin_fields(self):
        """
        Return the fields of this model that contain GPIO info.

        This project is only designed to work with one RPi at a time, so pins can only
        be used once.
        Allows for checking of used GPIO pins across all motors.
        """
        raise NotImplementedError("This needs to be set by the concrete subclass.")

    def clean(self):
        """Generic model clean functions for all Motor objects."""  # noqa: D401
        super(Motor, self).clean()

        # Check for already assigned GPIO pins in this instance.
        for gpio_field in self.gpio_pin_fields:
            for other_field in self.gpio_pin_fields:
                if gpio_field == other_field:
                    continue
                if not getattr(self, gpio_field):
                    continue
                if getattr(self, gpio_field) == getattr(self, other_field):
                    raise ValidationError(
                        {
                            gpio_field: f"This GPIO pin is used in this motor for "
                                        f"{other_field}, GPIO pins must be unique.",
                        },
                    )

        # Check for already assigned GPIO pins across all applicable models.
        this_instance_pins_used = [getattr(self, x) for x in self.gpio_pin_fields]
        this_instance_pins_used = [x for x in this_instance_pins_used if x]
        for pin_field in self.gpio_pin_fields:

            for modelstr in GPIO_PIN_USING_MODELS:
                try:
                    app, model = modelstr.split(".")
                except (IndexError, ValueError):
                    raise ImplementationError(
                        f"The format for defining models is '<app_name>.<model_name>'"
                        f", you defined {modelstr}.",
                    )

                model_to_search = apps.get_model(app_label=app, model_name=model)
                filters = Q()
                for spec_field in model_to_search().gpio_pin_fields:
                    for value in this_instance_pins_used:
                        filters.add(Q(**{spec_field: value}), Q.OR)

                filtered_results = model_to_search.objects.filter(filters)
                if filtered_results.count() > 0:
                    raise ValidationError(
                        {
                            pin_field: f"This GPIO pin is already in use on "
                                       f"{filtered_results[0].name}, please select "
                                       f"another.",
                        },
                    )


class StepperMotor(Motor):
    """Stepper motor object, with control API functionality built-in."""

    def __init__(self, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)
        self._direction_of_rotation = True
        self._steptype = "Full"
        self._step_delay = 0.01
        self._verbose = False  # not sure what this is yet.
        self._init_delay = 0.001
        if self.driver_type:
            self.controller_class = self.get_controller_class()
        else:
            self.controller_class = None
        self._controller = None  # Don't init this unless we're going to use it.

    driver_type = models.CharField(
        verbose_name="Motor Driver type",
        choices=[(x[0], x[0]) for x in STEPPER_DRIVER_TYPES],
        max_length=250,
    )
    direction_GPIO_pin = models.IntegerField(
        choices=AVAILABLE_RPI_GPIO_PINS,
        blank=True,
        null=True,
    )
    step_GPIO_pin = models.IntegerField(
        choices=AVAILABLE_RPI_GPIO_PINS,
        blank=True,
        null=True,
    )
    MS1_GPIO_pin = models.IntegerField(
        choices=AVAILABLE_RPI_GPIO_PINS,
        blank=True,
        null=True,
    )
    MS2_GPIO_pin = models.IntegerField(
        choices=AVAILABLE_RPI_GPIO_PINS,
        blank=True,
        null=True,
    )
    MS3_GPIO_pin = models.IntegerField(
        choices=AVAILABLE_RPI_GPIO_PINS,
        blank=True,
        null=True,
    )
    steps_per_revolution = models.IntegerField(default=200)
    mm_per_revolution = models.FloatField(null=True, blank=True)

    @property
    def gpio_pin_fields(self):
        """All fields housing GPIO pin config in this model."""
        return [
            "direction_GPIO_pin",
            "step_GPIO_pin",
            "MS1_GPIO_pin",
            "MS2_GPIO_pin",
            "MS3_GPIO_pin",
        ]

    def clean(self):
        """Custom model validation for steppers."""  # noqa: D401
        super().clean()

        # Validate that the correct fields are full for driver type
        if self.driver_type == "A4988":
            for field in ["direction_GPIO_pin", "step_GPIO_pin"]:
                if not getattr(self, field):
                    raise ValidationError(
                        {field: "This field is required for this driver type."},
                    )
            if self.MS1_GPIO_pin or self.MS2_GPIO_pin or self.MS3_GPIO_pin:
                if not self.MS1_GPIO_pin or not self.MS2_GPIO_pin or not self.MS3_GPIO_pin:
                    raise ValidationError(
                        {
                            "MS1_GPIO_pin": "All three of these must be set or none.",
                            "MS2_GPIO_pin": "All three of these must be set or none.",
                            "MS3_GPIO_pin": "All three of these must be set or none.",
                        },
                    )

    def get_controller_class(self):
        """Get the controller class for this motor."""
        if not self.driver_type:
            raise ConfigurationError(
                "This class does not have a driver set yet. Save the model first.",
            )

        for driver in STEPPER_DRIVER_TYPES:
            if self.driver_type == driver[0]:
                try:
                    return driver[1]
                except IndexError:
                    raise ImplementationError("Driver class not set for driver.")

    def _init_controller_class(self):
        """Initialize an instance of this motors controller class."""
        if not self.controller_class:
            self.controller_class = self.get_controller_class()

        if self.controller_class == A4988Nema:
            if self.MS1_GPIO_pin and self.MS2_GPIO_pin and self.MS3_GPIO_pin:
                mode_pins = (self.MS1_GPIO_pin, self.MS2_GPIO_pin, self.MS3_GPIO_pin)
            else:
                mode_pins = (-1, -1, -1)

            self._controller = A4988Nema(
                direction_pin=self.direction_GPIO_pin,
                mode_pins=mode_pins,
                step_pin=self.step_GPIO_pin,
            )

    @property
    def steps_per_rev(self):
        """
        Return the current number of steps required to do a full rev.

        Take into account the current steptype.
        """
        multipliers = [["Full", 1], ["Half", 2], ["1/4", 4], ["1/8", 8], ["1/16", 16]]
        for opts in multipliers:
            if self.steptype == opts[0]:
                return self.steps_per_revolution * opts[1]

    # Getters for modal settings
    @property
    def direction_of_rotation(self):
        """
        Current direction of rotation for the motor.

        Options are "clockwise" and "anti-clockwise".
        """
        if self._direction_of_rotation:
            return "clockwise"
        return "anti-clockwise"

    @property
    def steptype(self):
        """
        Size of steps, compared to the motors full step size.

        Options are "Full", "Half", "1/4", "1/8", "1/16":
        """
        return self._steptype

    @property
    def step_delay(self):
        """
        Delay between steps in seconds.

        Requires a float.
        """
        return self._step_delay

    @property
    def init_delay(self):
        """
        Delay after GPIO init before first move command.

        Requires a float.
        """
        return self._init_delay

    # Setters for modal settings
    @direction_of_rotation.setter
    def direction_of_rotation(self, direction):
        """Setter for direction of rotation."""
        if direction == "clockwise":
            self._direction_of_rotation = True
            return
        if direction == "anti-clockwise":
            self._direction_of_rotation = False
            return
        raise ValueError(
            "That is not a valid option, please choose 'clockwise' or 'anti-clockwise'.",
        )

    @steptype.setter
    def steptype(self, steptype):
        """Setter for size of steps."""
        if not self.MS1_GPIO_pin or not self.MS2_GPIO_pin or not self.MS3_GPIO_pin:
            raise ValueError(
                "MSX pins are not configured for this motor, "
                "therefore only full steps are allowed.",
            )
        valid_steptypes = ["Full", "Half", "1/4", "1/8", "1/16"]

        if steptype not in valid_steptypes:
            raise ValueError(
                f"That is not a valid step type. Options are {valid_steptypes}",
            )
        self._steptype = steptype

    @step_delay.setter
    def step_delay(self, delay):
        """Step delay setter."""
        if not isinstance(delay, int) and not isinstance(delay, float):
            raise ValueError("Step delay must be a numeric value in seconds.")
        self._step_delay = float(delay)

    @init_delay.setter
    def init_delay(self, delay):
        """Init delay setter."""
        if not isinstance(delay, int) and not isinstance(delay, float):
            raise ValueError("Step delay must be a numeric value in seconds.")
        self._init_delay = float(delay)

    # Movement commands
    def move_steps(self, steps: int, log=True):
        """Move a given number of steps in the set direction."""
        if not isinstance(steps, int):
            raise CommandError(f"{steps} is not a valid number of steps.")

        if not self._controller:
            self._init_controller_class()

        log_info = (
            f"Moving stepper {self.name} {steps} x {self.steptype} steps "
            f"in the {self.direction_of_rotation} direction."
        )

        self._controller.motor_go(
            self._direction_of_rotation,
            self._steptype,
            steps,
            self._step_delay,
            self._verbose,
            self._init_delay,
        )
        if log:
            logging.info(log_info)
            logging.info(
                self._direction_of_rotation,
                self._steptype,
                steps,
                self._step_delay,
                self._verbose,
                self._init_delay,
            )

        return log_info

    def move_rotations(self, rotations: [float, int]):
        """Move a given number of rotations or points of a rotation."""
        if not isinstance(rotations, int) and not isinstance(rotations, float):
            raise CommandError(f"{rotations} is not a valid number of rotations.")

        # Needs to be a float, but will cause minor inaccuracies.
        # Like, reeeeaaallllly minor.
        steps = round(rotations * self.steps_per_rev)

        log_info = (
            f"Moving stepper {self.name} {rotations} x rotations ({steps} steps) "
            f"in the {self.direction_of_rotation} direction."
        )

        self.move_steps(steps, log=False)

        logging.info(log_info)
        return log_info

    def move_mm(self, mm: [float, int]):
        """Move the motor a given number or fraction of a mm."""
        if not isinstance(mm, int) and not isinstance(mm, float):
            raise CommandError(f"{mm} is not a valid millimeter measurement.")
        if not self.mm_per_revolution:
            raise ConfigurationError("You have not designated a mm/rev for this motor.")

        rotations = mm / self.mm_per_revolution
        steps = round(rotations * self.steps_per_revolution)

        log_info = (
            f"Moving stepper {self.name} {mm}mm ({steps} steps) "
            f"in the {self.direction_of_rotation} direction."
        )

        self.move_steps(steps, log=False)

        logging.info(log_info)
        return log_info

    def save(self, **kwargs):
        """Call clean on save, even from backend."""
        self.clean()
        super(StepperMotor, self).save(**kwargs)

    def __str__(self):
        """String rep for model."""
        return f"{self.name} - {self.description}"
