[app]
title = SnakeQuest Android
package.name = snakequest
package.domain = com.snakequest
source.dir = .
source.include_exts = py,png,jpg,mp3,wav,json,otf
version = 0.1

requirements = python3,kivy

orientation = landscape
fullscreen = 0

android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

presplash_color = #12082f

[buildozer]
log_level = 2
warn_on_root = 1
