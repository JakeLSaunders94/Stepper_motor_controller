# django-stepper-motor
[![CircleCI](https://circleci.com/gh/JakeLSaunders94/Stepper_motor_controller/tree/master.svg?style=svg)](https://circleci.com/gh/JakeLSaunders94/Stepper_motor_controller/tree/master)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a href="https://github.com/psf/black/blob/main/LICENSE"><img alt="License: MIT" src="https://black.readthedocs.io/en/stable/_static/license.svg"></a>

A reusable library for adding and controlling stepper motors through Django. Designed to be used as a re-usable Django
app with the following:
 - A4988 Stepper Controllers
 - Raspberry Pi
 - NEMA-X Motors (The ones you can pull off old 3D printers, usually 11s or 17s).

This package makes registering and controlling as many stepper motors as you can attach to the Pi's GPIO pins trivial. 
You can register and configure motors and assign them to GPIO pins. Once this is complete you can just get() a motor 
directly from the DB and perform actions with it.