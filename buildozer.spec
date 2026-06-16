[app]
title = QuizGen IA
package.name = quizgenia
package.domain = org.tsu.quizgen
source.include_exts = py,png,jpg,kv,json
version = 1.0.0

# Librerías necesarias para la ejecución en el celular
requirements = python3, kivy, mysql-connector-python, google-generativeai, requests, urllib3, charset-normalizer, idna

orientation = portrait
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
buildozer.use_ccache = 1