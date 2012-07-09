"""

    Define add-on settings.

"""

from zope import schema
from five import grok
from Products.CMFCore.interfaces import ISiteRoot

from z3c.form.browser.checkbox import CheckBoxFieldWidget


from plone.z3cform import layout
from plone.directives import form
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper


class ISettings(form.Schema):
    """ Define settings data structure """

    adminLanguage = schema.TextLine(title=u"Editor language",
        description=u"Type two letter language code and admins always use this language",
        required=False)

    form.widget(contentTypes=CheckBoxFieldWidget)
    contentTypes = schema.List(title=u"Enabled content types",
                               description=u"Which content types appear on translation master page",
                               required=False,
                               value_type=schema.Choice(source="plone.app.vocabularies.ReallyUserFriendlyTypes"),
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
