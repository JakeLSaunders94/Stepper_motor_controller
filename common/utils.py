# -*- coding: utf-8 -*-
"""Core code used across multiple apps."""
# Django
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models import Q

# Project
from common.constants import GPIO_PIN_USING_MODELS
from common.exceptions import ImplementationError


def check_for_GPIO_pin_use_in_this_instance(instance):
    """
    Validate that the selected GPIO pins have not been selected twice in this instance.

    Requires instance to be a model with the gpio_pin_fields attribute set.
    Raises ValidationErrors.
    Should be called before save, preferably in the clean method of a model.
    """
    # Check for already assigned GPIO pins in this instance.
    for gpio_field in instance.gpio_pin_fields:
        for other_field in instance.gpio_pin_fields:
            if gpio_field == other_field:
                continue
            if not getattr(instance, gpio_field):
                continue
            if getattr(instance, gpio_field) == getattr(instance, other_field):
                raise ValidationError(
                    {
                        gpio_field: f"This GPIO pin is used in this motor for "
                        f"{other_field}, GPIO pins must be unique.",
                    },
                )


def check_for_GPIO_pin_use_in_this_and_other_models(instance):
    """
    Validates that hte GPIO pins selected for this model are not used elsewhere.

    Requires instance to be a model with the gpio_pin_fields attribute set.
    Checks all models in constants.GPIO_PIN_USING_MODELS.
    Raises ValidationErrors.
    Should be called before save, preferably in the clean method of a model.
    """
    this_instance_pins_used = [getattr(instance, x) for x in instance.gpio_pin_fields]
    this_instance_pins_used = [x for x in this_instance_pins_used if x]

    for pin_field in instance.gpio_pin_fields:
        for modelstr in GPIO_PIN_USING_MODELS:
            try:
                app, model = modelstr.split(".")
            except (IndexError, ValueError):
                raise ImplementationError(
                    f"The format for defining models is '<app_name>.<model_name>'"
                    f", you defined {modelstr}.",
                )

            try:
                model_to_search = apps.get_model(app_label=app, model_name=model)
            except LookupError:
                # App is not installed in parent app.
                continue
            filters = Q()
            for spec_field in model_to_search().gpio_pin_fields:
                for value in this_instance_pins_used:
                    filters.add(Q(**{spec_field: value}), Q.OR)

            filtered_results = model_to_search.objects.filter(filters)
            if instance.pk:
                filtered_results = filtered_results.exclude(pk=instance.pk)
            if filtered_results.count() > 0:
                raise ValidationError(
                    {
                        pin_field: f"This GPIO pin is already in use on "
                        f"{filtered_results[0].name}, please select "
                        f"another.",
                    },
                )
