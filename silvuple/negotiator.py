"""

    Override user interface language setting

"""

from AccessControl import getSecurityManager
from ZPublisher.interfaces import IPubAfterTraversal
from zope.component import getUtility, ComponentLookupError
from Products.CMFCore import permissions
from Products.CMFCore.interfaces import IContentish, IFolderish
from five import grok
from plone.registry.interfaces import IRegistry

from interfaces import IAddonSpecific
from settings import ISettings

def find_context(request):
    """Find the context from the request

    http://stackoverflow.com/questions/10489544/getting-published-content-item-out-of-requestpublished-in-plone
    """
    published = request.get('PUBLISHED', None)
    context = getattr(published, '__parent__', None)
    if context is None:
        context = request.PARENTS[0]
    return context

@grok.subscribe(IPubAfterTraversal)
def admin_language_negotiator(event):
    """
    Event handler which pokes the language after traversing and authentication is done, but before rendering.

    Normally language negotiation happens in LanguageTool.setLanguageBindings() but this is before we have found request["PUBLISHED"]
    and we know if we are an editor or not.
    """

    request = event.request

    lang = get_editor_language(request)

    if lang:
        # Kill it with fire
        request["LANGUAGE"] = lang
        tool = request["LANGUAGE_TOOL"]
        tool.LANGUAGE = lang
        tool.LANGUAGE_LIST = [lang]
        tool.DEFAULT_LANGUAGE = lang

def get_editor_language(request):
    """
    Get editor language override if Silvuple is installed.
    """

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
        return language

    return None

