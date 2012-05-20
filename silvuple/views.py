"""

    Plone views overrides.

    For more information see

    * http://collective-docs.readthedocs.org/en/latest/views/browserviews.html

"""


# Disable unused imports pylint warning as they are here 
# here for example purposes
# W0611: 12,0: Unused import Interface

# pylint: disable=W0611

import json

# Python 2.6 compatible ordered dict
# NOTE: API is not 1:1, but for normal dict access of
# set member, iterate keys and values this is enough
try:
    from collections import OrderedDict
except ImportError:    
    from odict import odict as OrderedDict

# Zope imports
from zope.interface import Interface
from zope.component import getMultiAdapter, ComponentLookupError, getUtility
from five import grok
from Products.CMFCore.interfaces import ISiteRoot


from plone.app.layout.globals.interfaces import ITools, IPortalState
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

def map_language_id(lang):
    """
    Handle neutral (empty) to "neutral" language id transformation
    """
    if not lang:
        return "neutral"

    return lang

class MultiLinguageContentListingHelper(grok.CodeView):
    """
    Builds JSON multilingual content out of Plone. 
    """

    grok.context(ISiteRoot)
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
        result = OrderedDict()

        portal_languages = self.context.portal_languages
        
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

        return brain["portal_type"] in settings.contentTypes

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

        tools = getMultiAdapter((self.context, self.request), name="plone_tools")

        portal_catalog = tools.catalog()

        all_content = portal_catalog(Language = "all")

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
                base_entry[lang]= dict(available=False, language=lang, canTranslate=False)
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
            """ Check if required parent translations are in place



            :return: True if the item can be translated
            """
            parent = context.aq_parent

            if ISiteRoot.providedBy(parent):
                return True

            # Parent is a language base folder at plone site root
            if INavigationRoot.providedBy(parent):
                return True

            if ITranslatable.providedBy(parent):
                translatable = ITranslatable(parent)
            else:
                raise RuntimeError("Not translatable parent: %s" % parent)

            translation = translatable.getTranslation(language)

            return translation is not None

        for brain in all_content:           
            
            if not self.shouldTranslate(brain):
                continue

            context = brain.getObject()          

            if ITranslatable.providedBy(context):
                translatable = ITranslatable(context)
            else:
                raise RuntimeError("Not translatable content: %s" % context)

            entry = get_or_create_handle(translatable)

            data = dict(
                canonical = translatable.isCanonical(),
                title = context.Title(),
                url = context.absolute_url(),
                lang = map_language_id(context.Language()),
                available = True,
                path = context.absolute_url_path(),
                context = context                
                )
            
            entry[map_language_id(context.Language())] = data

        # Fill in items which can be translated
        for entry in result.values():

            canonical = None

            for lang in entry.values():
            
                if lang.get("canonical", False):
                    canonical = lang["context"]

                # Do not leak out to JSON serialization
                lang["context"] = None

            for lang in entry.values():
                if not lang["available"]:
                    lang["canTranslate"] = can_translate(canonical, lang)

        # Convert pre content entries to lists, so that we can guarantee
        # the order of langauges when passing thru JSON
        for entry in result.values():
            yield list(entry.values())

    def render(self):
        """
        Use helper methods above instead
        """
        return ""


class JSONContentListing(grok.CodeView):
    """
    Called from main.js to populate the content listing view.
    """

    grok.context(ISiteRoot)
    grok.name("translator-master-json")

    def update(self):
        self.helper = MultiLinguageContentListingHelper(self.context, self.request)

    def render(self):
        listing = self.helper.getContentByCanonical()
        # Ungeneratorify
        listing = list(listing)
        return json.dumps(listing)


class TranslatorMaster(grok.View):
    """ 
    Translate content to multiple languages on a single view.
    """

    grok.context(ISiteRoot)
    grok.name("translator-master")
    grok.require("cmf.ModifyPortalContent")

    def update(self):
        self.helper = MultiLinguageContentListingHelper(self.context, self.request)

        if not self.helper.getSettings():
            messages = IStatusMessage(self.request)
            messages.addStatusMessage(u"Silvuple not configured in Site Setup", type="error")


    def getJavascriptContextVars(self):
        """
        @return: Python dictionary of settings
        """

        state = getMultiAdapter((self.context, self.request), name="plone_portal_state")


        # Create youroptions Javascript object and populate in these variables
        return {
            # Javascript AJAX will call this view to populate the listing
            "jsonContentLister" : "%s/%s" % (state.portal_url(), getattr(JSONContentListing, "grokcore.component.directive.name"))
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
        html = SETTINGS_TEMPLATE % { "name" : "silvupleOptions", "json" : json_snippet }

        return html        
