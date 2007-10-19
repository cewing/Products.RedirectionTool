from zope.interface import implements
from zope.component import getUtility

from AccessControl import getSecurityManager
from Products.RedirectionTool.permissions import ModifyAliases

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.interfaces import ISiteRoot
from plone.app.redirector.interfaces import IRedirectionStorage

from plone.memoize.instance import memoize

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('RedirectionTool')


class RedirectsView(BrowserView):
    template = ViewPageTemplateFile('manage-redirects.pt')

    def redirects(self):
        storage = getUtility(IRedirectionStorage)
        portal = getUtility(ISiteRoot)
        context_path = "/".join(self.context.getPhysicalPath())
        portal_path = "/".join(portal.getPhysicalPath())
        redirects = storage.redirects(context_path)
        for redirect in redirects:
            path = "/%s" % redirect.lstrip(portal_path)
            yield {
                'redirect': redirect,
                'path': path,
            }

    def __call__(self):
        storage = getUtility(IRedirectionStorage)
        portal = getUtility(ISiteRoot)
        request = self.request
        form = request.form
        status = IStatusMessage(self.request)
        errors = {}

        if 'form.button.Add' in form:
            redirection = form.get('redirection')
            if redirection is None or redirection == '':
                msg = _(u"You have to enter an alias.")
                errors['redirection'] = msg
                status.addStatusMessage(msg, type='error')
            elif '://' in redirection:
                msg = _(u"An alias is a path from the portal root and doesn't include http:// or alike.")
                errors['redirection'] = msg
                status.addStatusMessage(msg, type='error')
            else:
                if redirection[0] != '/':
                    path = "/".join(self.context.getPhysicalPath()[:-1])
                    redirection = "%s/%s" % (path, redirection)
                else:
                    path = "/".join(portal.getPhysicalPath())
                    redirection = "%s%s" % (path, redirection)
                source = redirection.split('/')
                while len(source):
                    obj = portal.unrestrictedTraverse(source, None)
                    if obj is None:
                        source = source[:-1]
                    else:
                        if not getSecurityManager().checkPermission(ModifyAliases, obj):
                            obj = None
                        break
                if obj is None:
                    msg = _(u"You don't have the permission to set an alias from the location you provided.")
                    errors['redirection'] = msg
                    status.addStatusMessage(msg, type='error')
                else:
                    # XXX check if there is an existing alias
                    # XXX check whether there is an object
                    del form['redirection']
                    storage.add(redirection, "/".join(self.context.getPhysicalPath()))
                    status.addStatusMessage(_(u"Alias added."), type='info')
        elif 'form.button.Remove' in form:
            redirects = form.get('redirects', ())
            for redirect in redirects:
                storage.remove(redirect)
            if len(redirects) > 1:
                status.addStatusMessage(_(u"Aliases removed."), type='info')
            else:
                status.addStatusMessage(_(u"Alias removed."), type='info')

        return self.template(errors=errors)

    @memoize
    def view_url(self):
        return self.context.absolute_url() + '/@@manage-aliases'


class RedirectsControlPanel(BrowserView):
    template = ViewPageTemplateFile('redirects-controlpanel.pt')

    def redirects(self):
        storage = getUtility(IRedirectionStorage)
        portal = getUtility(ISiteRoot)
        context_path = "/".join(self.context.getPhysicalPath())
        portal_path = "/".join(portal.getPhysicalPath())
        for redirect in storage:
            path = "/%s" % redirect.lstrip(portal_path)
            yield {
                'redirect': redirect,
                'path': path,
                'redirect-to': storage.get(redirect),
            }

    def __call__(self):
        storage = getUtility(IRedirectionStorage)
        portal = getUtility(ISiteRoot)
        request = self.request
        form = request.form
        status = IStatusMessage(self.request)
        errors = {}

        if 'form.button.Remove' in form:
            redirects = form.get('redirects', ())
            for redirect in redirects:
                storage.remove(redirect)
            if len(redirects) > 1:
                status.addStatusMessage(_(u"Aliases removed."), type='info')
            else:
                status.addStatusMessage(_(u"Alias removed."), type='info')

        return self.template(errors=errors)

    @memoize
    def view_url(self):
        return self.context.absolute_url() + '/@@aliases-controlpanel'
