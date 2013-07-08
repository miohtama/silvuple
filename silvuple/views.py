"""

    Plone views overrides.

    For more information see

    * http://collective-docs.readthedocs.org/en/latest/views/browserviews.html

"""


# Disable unused imports pylint warning as they are here
# here for example purposes
# W0611: 12,0: Unused import Interface
# R0201: 75,4:MultiLinguageContentListingHelper.getSettings: Method could be a function

# XXX: getContentByCanonical() is ugly code and the following must be cleaned up

# R0914:191,4:MultiLinguageContentListingHelper.getContentByCanonical: Too many local variables (17/15)
# R0912:191,4:MultiLinguageContentListingHelper.getContentByCanonical: Too many branches (20/12)

# pylint: disable=W0611, R0201, R0914, R0912

import json
from logging import getLogger

# Python 2.6 compatible ordered dict
# NOTE: API is not 1:1, but for normal dict access of
# set member, iterate keys and values this is enough
try:
    from collections import OrderedDict
except ImportError:
    from odict import odict as OrderedDict

# grok CodeView is now View
try:
    from five.grok import CodeView as View
except ImportError:
    from five.grok import View

# Zope imports
from zope.component import getMultiAdapter, ComponentLookupError, getUtility
from five import grok
from Products.CMFCore.interfaces import ISiteRoot
from zope.interface import Interface
from Acquisition import aq_inner, aq_parent

from plone.uuid.interfaces import IUUID
from Products.LinguaPlone.interfaces import ITranslatable
from plone.registry.interfaces import IRegistry
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.layout.navigation.interfaces import INavigationRoot


# Local imports
from interfaces import IAddonSpecific
from settings import ISettings

grok.templatedir("templates")
grok.layer(IAddonSpecific)

# The generated HTML snippet going to <head>
SETTINGS_TEMPLATE = u"""
<script type="text/javascript">
var %(name)s = %(json)s;
</script>
"""

logger = getLogger("silvuple")


def map_language_id(lang):
    """
    Handle neutral (empty) to "neutral" language id transformation
    """
    if not lang:
        return "neutral"

    return lang


class MultiLinguageContentListingHelper(View):
    """
    Builds JSON multilingual content out of Plone.
    """

    grok.context(Interface)
    grok.name("multi-lingual-content-listing-helper")

    def getSettings(self):
        """
        Get silvuple Site Setup settings
        """
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

        return settings

    def getLanguages(self):
        """
        Return list of active langauges as ordered dictionary, the preferred first language as the first.

        Example output::

             {
                u'fi': {u'id' : u'fi', u'flag': u'/++resource++country-flags/fi.gif', u'name': u'Finnish', u'native': u'Suomi'},
                u'de': {u'id' : u'de', u'flag': u'/++resource++country-flags/de.gif', u'name': u'German', u'native': u'Deutsch'},
                u'en': {u'id' : u'en', u'flag': u'/++resource++country-flags/gb.gif', u'name': u'English', u'native': u'English'},
                u'ru': {u'id' : u'ru', u'flag': u'/++resource++country-flags/ru.gif', u'name': u'Russian', u'native': u'\u0420\u0443\u0441\u0441\u043a\u0438\u0439'}
              }
        """
        context = aq_inner(self.context)
        result = OrderedDict()

        portal = getMultiAdapter((context, self.request), name='plone_portal_state').portal()
        portal_languages = portal.portal_languages

        # Get barebone language listing from portal_languages tool
        langs = portal_languages.getAvailableLanguages()

        preferred = portal_languages.getPreferredLanguage()

        # Preferred first
        for lang, data in langs.items():
            if lang == preferred:
                result[lang] = data

        # Then other languages
        for lang, data in langs.items():
            if lang != preferred:
                result[lang] = data

        # Add special entry for "neutral" non-real language
        result["neutral"] = dict(id="", name="Neutral", native="Neutral")

        # For the convenience, export language ISO code also inside data,
        # so it easier to iterate data in the templates
        for lang, data in result.items():
            data["id"] = lang

        return result

    def shouldTranslate(self, brain):
        """
        Filtering function to check whether content types should appear in the translation list or not
        """

        settings = self.getSettings()

        if not settings:
            return False

        # XXX: Hard-coded Products.Carousel filtering
        if "Carousel" in brain["Title"]:
            return False

        return brain["portal_type"] in settings.contentTypes

    def sortContentListing(self, result):
        """
        Sort result listing items by canonical path.

        :param result: Listing of entry dicts as described by getContentByCanonical()
        """

        def get_canonical(entry):
            """
            Get canonical language in the entry dict
            """
            canonical = None

            # First snatch canonical  item for this content
            for lang in entry:

                if lang.get("canonical", False):
                    canonical = lang

            return canonical

        def compare(a, b):
            """
            """
            can_a = get_canonical(a)
            can_b = get_canonical(b)

            if can_a and can_b:
                return cmp(can_a["path"], can_b["path"])
            else:
                return 0

        result.sort(compare)

    def getContentByCanonical(self):
        """
        Gets a list of entries where content is arranged by its canonical language version.

        Each entry is a dictionary like:

            [
                ...
                [
                    { language : "en", available : true, title : "Foobar", canonical : True, url : "http://" },
                    { language : "fi", available : true, title : "Barbar", canonical : False, ... },
                    { language : "ru", available : false }
                ]
            ]

        Not available languages won't get any entries.
        """
        settings = self.getSettings()
        context = aq_inner(self.context)
        tools = getMultiAdapter((context, self.request), name="plone_tools")

        portal_catalog = tools.catalog()

        all_content = []

        if ITranslatable.providedBy(context):
            for lang, item in context.getTranslations(review_state=False).items():
                all_content += portal_catalog(Language="all",
                                              path='/'.join(item.getPhysicalPath()),
                                              portal_type=settings.contentTypes)
        else:
            all_content = portal_catalog(Language="all",
                                         path='/'.join(context.getPhysicalPath()),
                                         portal_type=settings.contentTypes)

        # List of UUID -> entry data mappings
        result = OrderedDict()

        # Create a dictionary entry populated with default languages,
        # so that languages come always in the same order
        # E.g. {en:{"available":False}}

        langs = self.getLanguages()

        def get_base_entry():
            """ Item row for all languages, everything set off by default """
            base_entry = OrderedDict()
            for lang in langs:
                base_entry[lang] = dict(available=False, language=lang, canTranslate=False)
            return base_entry

        def get_or_create_handle(translatable):
            """
            Get or create entry in the result listing.

            This is a dict of language -> data pairs
            """
            canonical = translatable.getCanonical()
            uuid = IUUID(canonical, None)

            if not uuid:
                raise RuntimeError("Object missing UUID: %s" % context)

            # Get the existing canonical entry
            # for the listing, or create a new empty
            # populated entry otherwise
            if uuid in result:
                return result[uuid]
            else:
                entry = get_base_entry()
                result[uuid] = entry
                return entry

        def can_translate(context, language):
            """ Check if required parent translations are in place so that we can translate this item

            :return: True if the item can be translated

            """

            assert context is not None

            parent = aq_parent(context)

            if ISiteRoot.providedBy(parent):
                return True

            # Parent is a language base folder at plone site root
            if INavigationRoot.providedBy(parent):
                return True

            if ITranslatable.providedBy(parent):
                translatable = ITranslatable(parent)
            else:
                from logging import getLogger
                log = getLogger('silvuple.views.can_translate')
                if parent:
                    log.info('Parent is not translatable: %s' % parent.absolute_url())
                else:
                    log.error('Cannot translate language: %s, no parent for %s' % (language, context.absolute_url()))

                return False

            translation = translatable.getTranslation(language)

            return translation is not None

        for brain in all_content:

            if not self.shouldTranslate(brain):
                continue

            try:
                context = brain.getObject()
            except Exception as e:
                logger.error("Could not load brain %s" % brain.getURL())
                logger.exception(e)
                continue

            if ITranslatable.providedBy(context):
                translatable = ITranslatable(context)
            else:
                from logging import getLogger
                log = getLogger('silvuple.views.can_translate')
                log.info('Content is not translatable: %s' % context.absolute_url())
                continue

            try:
                entry = get_or_create_handle(translatable)
            except RuntimeError:
                from logging import getLogger
                log = getLogger('silvuple.views.getContentByCanonical')
                log.info('Item has no UUID: %s' & translatable.absolute_url())
                continue

            # Data exported to JSON + context object needed for post-processing
            data = dict(
                canonical=translatable.isCanonical(),
                title=context.title_or_id(),
                url=context.absolute_url(),
                lang=map_language_id(context.Language()),
                available=True,
                path=context.absolute_url_path(),
                context=context
                )

            entry[map_language_id(context.Language())] = data

        # Fill in items which can be translated
        for entry in result.values():

            canonical = None

            # First snatch canonical  item for this content
            for lang in entry.values():

                if lang.get("canonical", False):
                    canonical = lang["context"]

                # Do not leak out to JSON serialization
                lang["context"] = None

            if not canonical:
                logger.warn("No canonical content for %s" % entry)
                continue

            # Then populate untranslated languages
            for lang in entry.values():
                if not lang["available"]:

                    lang_code = lang["language"]

                    lang["canTranslate"] = can_translate(canonical, lang_code)

                    if canonical:
                        # Point to LinguaPlone Translate into... form
                        lang["url"] = "%s/@@translate?newlanguage=%s" % (canonical.absolute_url(), lang_code)
                    else:
                        lang["url"] = "#"

        # Convert pre content entries to lists, so that we can guarantee
        # the order of langauges when passing thru JSON
        result = [entry.values() for entry in result.values()]

        self.sortContentListing(result)

        return result

    def render(self):
        """
        Use helper methods above instead
        """
        return ""


class JSONContentListing(View):
    """
    Called from main.js to populate the content listing view.
    """

    grok.context(Interface)
    grok.name("translator-master-json")

    def update(self):
        context = aq_inner(self.context)
        self.helper = MultiLinguageContentListingHelper(context, self.request)

    def render(self):
        listing = self.helper.getContentByCanonical()
        return json.dumps(listing)


class TranslatorMaster(View):
    """
    Translate content to multiple languages on a single view.
    """

    grok.context(Interface)
    grok.name("translator-master")
    grok.require("cmf.ModifyPortalContent")

    def update(self):
        context = aq_inner(self.context)
        self.helper = MultiLinguageContentListingHelper(context, self.request)

        if not self.helper.getSettings():
            messages = IStatusMessage(self.request)
            messages.addStatusMessage(u"Silvuple not configured in Site Setup", type="error")

    def getJavascriptContextVars(self):
        """
        @return: Python dictionary of settings
        """

        # Create youroptions Javascript object and populate in these variables
        context = aq_inner(self.context)
        return {
            # Javascript AJAX will call this view to populate the listing
            "jsonContentLister": "%s/%s" % (context.absolute_url(), getattr(JSONContentListing, "grokcore.component.directive.name"))
        }

    def getSetupJavascript(self):
        """
        Set some global helpers

        Generate Javascript code to set ``windows.silvupleOptions`` object from ``getJavascriptContextVars()``
        method output.
        """
        settings = self.getJavascriptContextVars()
        json_snippet = json.dumps(settings)

        # Use Python string template facility to produce the code
        html = SETTINGS_TEMPLATE % {"name": "silvupleOptions", "json": json_snippet}

        return html
