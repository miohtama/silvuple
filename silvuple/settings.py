"""

    Define add-on settings.

"""

from zope import schema
from five import grok

# grok CodeView is now View
try:
    from five.grok import CodeView as View
except ImportError:
    from five.grok import View

from Products.CMFCore.interfaces import ISiteRoot

from z3c.form.browser.checkbox import CheckBoxFieldWidget


from plone.z3cform import layout
from plone.directives import form
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

from silvuple.i18n import silvupleMessageFactory as _


class ISettings(form.Schema):
    """ Define settings data structure """

    adminLanguage = schema.TextLine(title=_(u"Editor language"),
        description=_(u"Type two letter language code and admins always use this language"),
        required=False)

    form.widget(contentTypes=CheckBoxFieldWidget)
    contentTypes = schema.List(title=_(u"Enabled content types"),
                               description=_(u"Which content types appear on translation master page"),
                               required=False,
                               value_type=schema.Choice(source="plone.app.vocabularies.ReallyUserFriendlyTypes"),
                               )


class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    schema = ISettings
    label = _(u"Silvuple settings")


class SettingsView(View):
    """

    """
    grok.name("silvuple-settings")
    grok.context(ISiteRoot)
    grok.require("cmf.ManagePortal")

    def render(self):
        view_factor = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
        view = view_factor(self.context, self.request)
        return view()
