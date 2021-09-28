# django-stepper-motor
A reusable library for adding and controlling stepper motors through Django. Designed to be used as a re-usable Django
app with the following:
 - A4988 Stepper Controllers
 - Raspberry Pi
 - NEMA-X Motors (The ones you can pull off old 3D printers, usually 11s or 17s).

This package makes registering and controlling as many stepper motors as you can attach to the Pi's GPIO pins trivial. 
You can register and configure motors and assign them to GPIO pins. Once this is complete you can just get() a motor 
directly from the DB and perform actions with it.