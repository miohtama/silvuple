"""

    Plone 3 / short version of language negotiator admin override.

    Include using configure.zcml and ZPublisherBackports:

    <subscriber for="ZPublisherEventsBackport.interfaces.IPubAfterTraversal" handler=".negotiator.admin_language_negotiator" />

"""

from AccessControl import getSecurityManager
from Products.CMFCore import permissions
from Products.CMFCore.interfaces import IContentish, IFolderish

FORCED_LANGUAGE = "fi"


def find_context(request):
    """Find the context from the request

    http://stackoverflow.com/questions/10489544/getting-published-content-item-out-of-requestpublished-in-plone
    """
    published = request.get('PUBLISHED', None)
    context = getattr(published, '__parent__', None)
    if context is None:
        context = request.PARENTS[0]
    return context


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

    return FORCED_LANGUAGE
