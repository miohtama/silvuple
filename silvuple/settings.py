"""

    Define add-on settings.

"""

from zope import schema
from five import grok
from Products.CMFCore.interfaces import ISiteRoot

from plone.z3cform import layout
from plone.directives import form
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper

class ISettings(form.Schema):
    """ Define settings data structure """

    adminLanguage = schema.TextLine(title=u"Admin language", description=u"Type two letter language code and admins always use this language")

    form.widget(enabled_overrides=CheckBoxFieldWidget)
    content_types = schema.List(title=u"Enabled content types",
                               description=u"On which content types Facebook Like-button should appear",
                               required=False, default=["Document"],
                               value_type=schema.Choice(source="mfabrik.like.content_types"),
                               )


class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    schema = ISettings
    label = u"Silvuple settings"

class SettingsView(grok.CodeView):
    """

    """
    grok.name("silvuple-settings")
    grok.context(ISiteRoot)
    def render(self):
        view_factor = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
        view = view_factor(self.context, self.request)
        return view()

    