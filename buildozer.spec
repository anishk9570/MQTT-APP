[app]

# (str) Title of your application
title = MQTT Application

# (str) Package name
package.name = mqttapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.fpi

# (source.dir) Source code where the main.py live
source.dir = .

# (list) Source includes patterns, let empty to include all the files
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source excludes patterns, let empty to not exclude anything
#source.exclude_exts = spec

# (list) List of directory to exclude from build
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 30

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android app theme, default is ok for Kivy-based app
# android.theme = "@android:style/Theme.NoTitleBar"

# (bool) Copy library jar from libs to armeabi-v7a directory to fix issue "private final class android.support.v7.internal.view.menu.OverflowMenuButton"
android.copy_libs = 1

# (bool) Enable AndroidX support, this will add androidx to your gradle dependencies
android.enable_androidx = True

# (list) Pattern to whitelist for the whole project
android.whitelist = lib-dynload/termios.so

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library jar from libs to armeabi-v7a directory to fix issue "private final class android.support.v7.internal.view.menu.OverflowMenuButton"
android.copy_libs = 1

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) Enable AndroidX support, default is True (required for API 31+)
android.enable_androidx = True

# (list) Android permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# (str) The requirements for your project
# the requirements must be separated by whitespace
p4a.requirements = python3,kivy,kivymd,paho-mqtt,openssl,requests

# (str) Supported orientations
android.orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the application (image or video), give the path of your presplash file
# without extension, it must be 1024x1024.
# android.presplash_filename = %(source.dir)s/data/presplash

# (list) Permissions
android.permissions = INTERNET

# (int) Target API (let default)
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
#android.sdk = 31

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android app theme, default is ok for Kivy-based app
android.theme = "@android:style/Theme.NoTitleBar"

# (bool) Copy library jar from libs to armeabi-v7a directory to fix issue
android.copy_libs = 1

# (list) Gradle dependencies
android.gradle_dependencies = 

# Java classes to add to the bootstrap Java source
#android.add_src = 

# (list) Pattern to whitelist for the whole project
#android.whitelist = lib-dynload/.*\.so

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) List of Java files to add to the gradle build (let empty to don't add)
#android.add_gradle_repositories = com.google.android.gms:play-services-gcm

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

#
# Python for android (p4a) specific
#

# (bool) Should use buildozer instead of p4a
# android.skip_update = False

# (str) android.logcat_filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library jar from libs to armeabi-v7a directory to fix issue "private final class android.support.v7.internal.view.menu.OverflowMenuButton"
android.copy_libs = 1

# (list) Pattern to whitelist for the whole project
#android.whitelist = lib-dynload/termios.so

# (bool) Enable AndroidX support, this will add androidx to your gradle dependencies
android.enable_androidx = True

#
# iOS specific
#

# (bool) Whether or not to sign the code
ios.codesign.allowed = False


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display advancement percentage in the console (off, on or debug)
display_advancement = on

# (list) dependencies to download before building
# Comma separated of package/version; dependency2 (eg. sdl2==2.0.9;pymodules==19.0)
# assuming the htmllib will be needed, resolved by buildozer
#android.add_src =

# (bool) Indicates whether the --requirements parameter was passed as is
requirements.source.all = 0

# (list) Garden requirements
#garden_requirements =

# (str) Supported OS
os.require = linux

# (str) The user to use with `buildozer android p4a_bootstrap_prepare`
#android.bootstrap_user = android

# (bool) Copy library jar from libs to armeabi-v7a directory to fix issue "private final class android.support.v7.internal.view.menu.OverflowMenuButton"
android.copy_libs = 1
