"""

    Declare a Python package silvuple

    See 

    * http://wiki.python.org/moin/Distutils/Tutorial

    * http://packages.python.org/distribute/setuptools.html#developer-s-

    * http://plone.org/products/plone/roadmap/247

"""

from setuptools import setup
import os

setup(name = "silvuple",
    version = "1.0",
    description = "Translation manager for Plone / LinguaPlone websites",
    long_description=open("README.rst").read() + "\n" +
                     open(os.path.join("docs", "HISTORY.txt")).read(),
    author = "Mikko Ohtamaa",
    author_email = "mikko@opensourcehacker.com",
    url = "http://opensourcehacker.com",
    install_requires = ["five.grok", "plone.app.dexterity", "plone.app.registry", "odict"],
    packages = ['silvuple'],
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
    ],     
    license="GPL2",
    include_package_data = True,
    entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,        
) 