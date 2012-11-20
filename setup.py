import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-ios-push",
    version = "0.0.4",
    author = "Appsome",
    author_email = "N/A",
    description = ("A Django Application for contacting the Apple Push Service"
                                    " and maintaining a list of iOS devices."),
    license = "Apache License 2.0",
    keywords = "django ios push",
    url = "https://github.com/appsome/django-ios-push",
    packages=['iospush',],
    long_description="N/A",
)