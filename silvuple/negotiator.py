"""

    Override user interface language setting

"""
from AccessControl import getSecurityManager
from zope.component import adapter
from ZPublisher.interfaces import IPubAfterTraversal
from zope.component import getUtility, ComponentLookupError
from Products.CMFCore import permissions

from plone.registry.interfaces import IRegistry

from interfaces import IAddonSpecific
from settings import ISettings

@adapter(IPubAfterTraversal)
def admin_language_negotiator(event):

    # Keep the current request language (negotiated on portal_languages)
    # untouched

    request = event.request

    context = event.object

    if not IAddonSpecific.provideBy(request):
        # Add on is not active
        return

    # Check if we are the editor
    if not getSecurityManager().checkPermission(permissions .ModifyPortalContent, context):
        return

    try:

        # Will raise an exception if plone.app.registry is not quick installed
        registry = getUtility(IRegistry)

        # Will raise exception if your product add-on installer has not been run
        settings = registry.forInterface(ISettings)
    except (KeyError, ComponentLookupError):
        # Registry schema and actual values do not match
        # Quick installer has not been run or need to rerun
        # to update registry.xml values to database
        return

    import pdb ; pdb.set_trace()

    # Read language from settings
    language = settings.adminLanguage

    if language:
        # Fake new language for all authenticated users
        event.request['LANGUAGE'] = language

