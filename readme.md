# django_raspberry_pi_hardware
[![CircleCI](https://circleci.com/gh/JakeLSaunders94/django_raspberry_pi_hardware/tree/master.svg?style=svg)](https://circleci.com/gh/JakeLSaunders94/Stepper_motor_controller/tree/master)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/psf/black/blob/main/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>
[![codecov](https://codecov.io/gh/JakeLSaunders94/django_raspberry_pi_hardware/branch/master/graph/badge.svg?token=6LHTN91968)](https://codecov.io/gh/JakeLSaunders94/Stepper_motor_controller)

A reusable django app for basic control of hardware attached to a Raspberry Pi. This 
will currently control:
 - NEMA-X motors (using A4988 Stepper Controllers)
 - PTM / PRB Switches

This package makes registering and controlling as many stepper motors as you can attach to the Pi's GPIO pins trivial. 
You can register and configure motors and assign them to GPIO pins. Once this is complete you can just get() a motor 
directly from the DB and perform actions with it.

**NOTE: This django app exposes unprotected API endpoints for direct control of your stepper motors.
DO NOT deploy this anywhere except your trusted local network without implementing auth!**
