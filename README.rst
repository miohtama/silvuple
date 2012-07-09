Introduction
-----------------

Translation manager and helper for `Plone CMS <http://plone.org>`_ / LinguaPlone sites.

Features
------------

* **Force admin language**: Useful e.g. for when admin needs to work with languages they are not familiar with. Very useful
  for strange languages (from western point of view) like China, Japanese or Russian. You can set this language in
  the control panel.

* **Translations Manager**: A menu item for the admins in the user menu. This allows you to batch enter translated content
  and quickly get overview what contents still needs to be translated.

Notes
------

By default the forced admin language is handled by overriding language when doing look-ups for ``plone``
and ``collective.*`` gettext translation domains. The logic here is that these language strings
are used by the management interface.

The actual language is not switched in any point: changing the language itself would cause
site behavior differense in folder contents, search and other content listing views making
administrative tasks impossible.

Author
--------

`Mikko Ohtamaa <http://opensourcehacker.com>`_

Special thanks for Andreas Jung for providing support with the code.