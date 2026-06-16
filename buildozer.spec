[app]
# (string) Title of your application
title = QuizGen IA

# (string) Package name
package.name = quizgenia

# (string) Package domain (needed for android packaging)
package.domain = org.camaron

# (string) Source code where the main.py lives (¡ESTA ES LA LÍNEA QUE FALTA!)
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (string) Application version
version = 0.1

# (list) Application requirements
# Aquí incluimos kivy y las librerías que usa tu main.py
requirements = python3,kivy,google-generativeai,mysql-connector-python

# (str) Supported orientations
orientation = portrait

# ==========================================================
# Android configuration
# ==========================================================

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET

# (int) Android API to use (33 es el estándar actual para Google Play)
android.api = 33

# (int) Minimum API required
android.minapi = 21
