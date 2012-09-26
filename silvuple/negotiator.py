"""

    Override user interface language setting

"""

# W0703:105,11:_patched_translate: Catching too general exception Exception
# pylint: disable=W0703

import logging

from AccessControl import getSecurityManager
from zope.component import getUtility, ComponentLookupError
from Products.CMFCore import permissions
from Products.CMFCore.interfaces import IContentish, IFolderish
from plone.registry.interfaces import IRegistry

from interfaces import IAddonSpecific
from settings import ISettings

logger = logging.getLogger("silvuple")


def find_context(request):
    """Find the context from the request

    http://stackoverflow.com/questions/10489544/getting-published-content-item-out-of-requestpublished-in-plone
    """
    published = request.get('PUBLISHED', None)
    context = getattr(published, '__parent__', None)
    if context is None:
        context = request.PARENTS[0]
    return context


def get_editor_language(request):
    """
    Get editor language override if Silvuple is installed.
    """

    cached = getattr(request, "_cached_admin_language", None)
    if cached:
        return cached

    if not IAddonSpecific.providedBy(request):
        # Add on is not active
        return None

    context = find_context(request)

    # Filter out CSS and other non-sense
    # IFolderish check includes site root
    if not (IContentish.providedBy(context) or IFolderish.providedBy(context)):
        # Early terminate
        return None

    # Check if we are the editor
    if not getSecurityManager().checkPermission(permissions.ModifyPortalContent, context):
        # Anon visitor, normal language ->
        return None

    try:

        # Will raise an exception if plone.app.registry is not quick installed
        registry = getUtility(IRegistry)

        # Will raise exception if your product add-on installer has not been run
        settings = registry.forInterface(ISettings)
    except (KeyError, ComponentLookupError):
        # Registry schema and actual values do not match
        # Quick installer has not been run or need to rerun
        # to update registry.xml values to database
        return None

    # Read language from settings
    language = settings.adminLanguage

    if language:
        # Fake new language for all authenticated users
        request._cached_admin_language = language
        return language

    return None


def is_editor_language_domain(domain):
    """
    Filter to check which gettext domains will get forced to be in english always.
    """
    return domain.startswith("plone") or domain.startswith("collective") or domain == "linguaplone"


_unpatched_translate = None


def _patched_translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None):
    """ TranslatioDomain.translate() patched for editor language support

    :param context: HTTPRequest object
    """

    # Override translation language?
    try:
        if is_editor_language_domain(self.domain):
            language = get_editor_language(context)
            if language:
                target_language = language
    except Exception as e:
        # Some defensive programming here
        logger.error("Admin language force patch failed")
        logger.exception(e)

    #print "_patched_translate: %s: %s, %s" % (msgid, self.domain, target_language)

    return _unpatched_translate(self, msgid, mapping, context, target_language, default)

from zope.i18n.translationdomain import TranslationDomain
_unpatched_translate = TranslationDomain.translate
TranslationDomain.translate = _patched_translate
