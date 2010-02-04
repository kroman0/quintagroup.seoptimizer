from sets import Set
from DateTime import DateTime 
from Acquisition import aq_inner
from zope.component import queryAdapter
from plone.app.controlpanel.form import ControlPanelView

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as pmf

from quintagroup.seoptimizer import SeoptimizerMessageFactory as _

SEPERATOR = '|'
HAS_CANONICAL_PATH = True
SEO_PREFIX = 'seo_'
PROP_PREFIX = 'qSEO_'
SUFFIX = '_override'
PROP_CUSTOM_PREFIX = 'qSEO_custom_'

try:
    from quintagroup.canonicalpath.interfaces import ICanonicalPath
except ImportError:
    HAS_CANONICAL_PATH = False

class SEOContext( BrowserView ):
    """ This class contains methods that allows to edit html header meta tags.
    """
    def getSEOProperty( self, property_name, accessor='' ):
        """ Get value from seo property by property name.
        """
        context = aq_inner(self.context)

        if context.hasProperty(property_name):
            return context.getProperty(property_name)

        if accessor:
            method = getattr(context, accessor, None)
            if not callable(method):
                return None

            # Catch AttributeErrors raised by some AT applications
            try:
                value = method()
            except AttributeError:
                value = None

            return value

    def seo_title( self ):
        """ Generate SEO Title from SEO properties.
        """
        return self.getSEOProperty( 'qSEO_title', accessor='Title' )

    def seo_robots( self ):
        """ Generate SEO Robots from SEO properties.
        """
        robots = self.getSEOProperty( 'qSEO_robots' )
        return robots and robots or 'ALL'

    def seo_description( self ):
        """ Generate Description from SEO properties.
        """

        return self.getSEOProperty( 'qSEO_description', accessor = 'Description')

    def seo_distribution( self ):
        """ Generate Distribution from SEO properties.
        """
        dist = self.getSEOProperty( 'qSEO_distribution' )

        return dist and dist or 'Global'

    def seo_customMetaTags( self ):
        """        Returned seo custom metatags from default_custom_metatags property in seo_properties
        (global seo custom metatags) with update from seo custom metatags properties in context (local seo custom metatags).
        """
        tags = self.seo_globalCustomMetaTags()
        loc = self.seo_localCustomMetaTags()
        names = [i['meta_name'] for i in tags]
        add_tags = []
        for i in loc:
            if i['meta_name'] in names:
                for t in tags:
                    if t['meta_name'] == i['meta_name']:
                        t['meta_content'] = i['meta_content']
            else:
                add_tags.append(i)
        tags.extend(add_tags)
        return tags

    def seo_globalWithoutLocalCustomMetaTags( self ):
        """        Returned seo custom metatags from default_custom_metatags property in seo_properties
        (global seo custom metatags) without seo custom metatags from properties in context (local seo custom metatags).
        """
        glob = self.seo_globalCustomMetaTags()
        loc = self.seo_localCustomMetaTags()
        names = [i['meta_name'] for i in loc]
        tags = []
        for i in glob:
            if i['meta_name'] not in names:
                tags.append(i)
        return tags

    def seo_localCustomMetaTags( self ):
        """ Returned seo custom metatags from properties in context (local seo custom metatags).
        """
        result = []
        property_prefix = 'qSEO_custom_'
        context = aq_inner(self.context)
        for property, value in context.propertyItems():
            if property.startswith(property_prefix) and property[len(property_prefix):]:
                result.append({'meta_name'    : property[len(property_prefix):],
                               'meta_content' : value})
        return result

    def seo_globalCustomMetaTags( self ):
        """ Returned seo custom metatags from default_custom_metatags property in seo_properties.
        """
        result = []
        context = aq_inner(self.context)
        site_properties = getToolByName(context, 'portal_properties')
        if hasattr(site_properties, 'seo_properties'):
            custom_meta_tags = getattr(site_properties.seo_properties, 'default_custom_metatags', [])
            for tag in custom_meta_tags:
                name_value = tag.split(SEPERATOR)
                if name_value[0]:
                    result.append({'meta_name'    : name_value[0],
                                   'meta_content' : len(name_value) == 2 and name_value[1] or ''})
        return result

    def seo_nonEmptylocalMetaTags( self ):
        """
        """
        return bool(self.seo_localCustomMetaTags())

    def seo_html_comment( self ):
        """ Generate HTML Comments from SEO properties.
        """
        html_comment = self.getSEOProperty( 'qSEO_html_comment' )
        return html_comment and html_comment or '' 

    def meta_keywords( self ):
        """ Generate Meta Keywords from SEO properties (global and local) with Subject,
            depending on the options in configlet.
        """
        prop_name = 'qSEO_keywords'
        accessor = 'Subject'
        context = aq_inner(self.context)
        keywords = Set([])
        pprops = getToolByName(context, 'portal_properties')
        sheet = getattr(pprops, 'seo_properties', None)
        method = getattr(context, accessor, None)
        if not callable(method):
            return None

        # Catch AttributeErrors raised by some AT applications
        try:
            subject = Set(method())
        except AttributeError:
            subject = keywords

        if sheet:
          settings_use_keywords_sg = sheet.getProperty('settings_use_keywords_sg')
          settings_use_keywords_lg = sheet.getProperty('settings_use_keywords_lg')
          global_keywords = Set(sheet.getProperty('additional_keywords', None))
          local_keywords = Set(context.getProperty(prop_name, None))
          # Subject overrides global seo keywords and global overrides local seo keywords
          if [settings_use_keywords_sg, settings_use_keywords_lg] == [1, 1]:
              keywords = subject
          # Subject overrides global seo keywords and merge global and local seo keywords
          elif [settings_use_keywords_sg, settings_use_keywords_lg] == [1, 2]:
              keywords = subject | local_keywords
          # Global seo keywords overrides Subject and global overrides local seo keywords
          elif [settings_use_keywords_sg, settings_use_keywords_lg] == [2, 1]:
              keywords = global_keywords
          # Global seo keywords overrides Subject and merge global and local seo keywords
          elif [settings_use_keywords_sg, settings_use_keywords_lg] == [2, 2]:
              keywords = global_keywords | local_keywords
          # Merge Subject and global seo keywords and global overrides local seo keywords
          elif [settings_use_keywords_sg, settings_use_keywords_lg] == [3, 1]:
              keywords = subject | global_keywords
          # Merge Subject and global seo keywords and merge global and local seo keywords
          elif [settings_use_keywords_sg, settings_use_keywords_lg] == [3, 2]:
              keywords = subject | global_keywords | local_keywords
          else:
              keywords = subject
        else:
            keywords = subject

        return tuple(keywords)

    def seo_keywords( self ):
        """ Generate SEO Keywords from SEO properties (global merde local).
        """
        prop_name = 'qSEO_keywords'
        context = aq_inner(self.context)
        keywords = Set([])
        pprops = getToolByName(context, 'portal_properties')
        sheet = getattr(pprops, 'seo_properties', None)

        if sheet:
            settings_use_keywords_sg = sheet.getProperty('settings_use_keywords_sg')
            settings_use_keywords_lg = sheet.getProperty('settings_use_keywords_lg')
            global_keywords = Set(sheet.getProperty('additional_keywords', None))
            local_keywords = Set(context.getProperty(prop_name, None))
            keywords = global_keywords | local_keywords
        else:
            keywords = ''
        return tuple(keywords)

    def seo_canonical( self ):
        """ Generate canonical URL from SEO properties.
        """
        canonical = self.getSEOProperty( 'qSEO_canonical' )

        if not canonical and HAS_CANONICAL_PATH:
            canpath = queryAdapter(self.context, ICanonicalPath)
            if canpath:
                purl = getToolByName(self.context, 'portal_url')()
                cpath = canpath.canonical_path()
                canonical = purl + cpath

        return canonical and canonical or self.context.absolute_url()


class SEOControlPanel( ControlPanelView ):
    """ The class with methods configuration Search Engine Optimizer in configlet.
    """
    template = ViewPageTemplateFile('templates/seo_controlpanel.pt')

    @property
    def portal_properties( self ):
        """
        """
        context = aq_inner(self.context)
        return getToolByName(context, 'portal_properties')

    @property
    def portal_types( self ):
        """ Returned a list of portal types.
        """
        context = aq_inner(self.context)
        return getToolByName(context, 'portal_types')

    def hasSEOAction( self, type_info ):
        """
        """
        return filter(lambda x:x.id == 'seo_properties', type_info.listActions())

    def test( self, condition, first, second ):
        """
        """
        return condition and first or second 

    def getExposeDCMetaTags( self ):
        """ Get value from exposeDCMetaTags property in seo_properties.
        """
        sp = self.portal_properties.site_properties
        return sp.getProperty('exposeDCMetaTags')

    def getDefaultCustomMetatags( self ):
        """ Get values from default_custom_metatags property in seo_properties.
        """
        seo = self.portal_properties.seo_properties
        return seo.getProperty('default_custom_metatags')

    def getMetaTagsOrder( self ):
        """ Get values from metatags_order property in seo_properties.
        """
        seo = self.portal_properties.seo_properties
        return seo.getProperty('metatags_order')

    def getAdditionalKeywords( self ):
        """ Get values from additional_keywords property in seo_properties.
        """
        seo = self.portal_properties.seo_properties
        return seo.getProperty('additional_keywords')

    def getFilterKeywordsByContent( self ):
        """ Get values from filter_keywords_by_content property in seo_properties.
        """
        seo = self.portal_properties.seo_properties
        return seo.getProperty('filter_keywords_by_content')

    def createMultiColumnList( self ):
        """
        """
        context = aq_inner(self.context)
        allTypes = self.portal_types.listContentTypes()
        try:
            return context.createMultiColumnList(allTypes, sort_on='title_or_id')
        except AttributeError:
            return [slist]

    def __call__( self ):
        """ Perform the update and redirect if necessary, or render the page.
        """
        context = aq_inner(self.context)
        request = self.request

        content_types_seoprops_enabled = request.get( 'contentTypes', [] )
        exposeDCMetaTags = request.get( 'exposeDCMetaTags', None )
        additionalKeywords = request.get('additionalKeywords', [])
        default_custom_metatags = request.get('default_custom_metatags', [])
        metatags_order = request.get('metatags_order', [])
        filterKeywordsByContent = request.get('filterKeywordsByContent', None)
        settingsUseKeywordsSG = int(request.get('settingsUseKeywordsSG', 1))
        settingsUseKeywordsLG = int(request.get('settingsUseKeywordsLG', 1))

        site_props = getToolByName(self.portal_properties, 'site_properties')
        seo_props = getToolByName(self.portal_properties, 'seo_properties')

        form = self.request.form
        submitted = form.get('form.submitted', False)

        if submitted:
            site_props.manage_changeProperties(exposeDCMetaTags=exposeDCMetaTags)
            seo_props.manage_changeProperties(additional_keywords=additionalKeywords)
            seo_props.manage_changeProperties(default_custom_metatags=default_custom_metatags)
            seo_props.manage_changeProperties(metatags_order=metatags_order)
            seo_props.manage_changeProperties(content_types_seoprops_enabled=content_types_seoprops_enabled)
            seo_props.manage_changeProperties(filter_keywords_by_content=filterKeywordsByContent)
            seo_props.manage_changeProperties(settings_use_keywords_sg=settingsUseKeywordsSG)
            seo_props.manage_changeProperties(settings_use_keywords_lg=settingsUseKeywordsLG)

            for ptype in self.portal_types.objectValues():
                acts = filter(lambda x: x.id == 'seo_properties', ptype.listActions())
                action = acts and acts[0] or None
                if ptype.getId() in content_types_seoprops_enabled:
                    if action is None:
                        ptype.addAction('seo_properties',
                                        'SEO Properties',
                                        'string:${object_url}/@@seo-context-properties',
                                        "python:exists('portal/@@seo-context-properties')",
                                        'Modify portal content',
                                        'object',
                                        visible=1)
                else:
                    if action !=None:
                        actions = list(ptype.listActions())
                        ptype.deleteActions([actions.index(a) for a in actions if a.getId()=='seo_properties'])
            context.plone_utils.addPortalMessage(pmf(u'Changes saved.'))
            return request.response.redirect('%s/%s'%(self.context.absolute_url(), 'plone_control_panel'))
        else:
            return self.template(contentTypes=content_types_seoprops_enabled, exposeDCMetaTags=exposeDCMetaTags)

    def typeInfo( self, type_name ):
        """ Get info type by type name.
        """
        return self.portal_types.getTypeInfo( type_name )

    def select_settings_use_keywords_sg(self):
        context = aq_inner(self.context)
        site_properties = getToolByName(context, 'portal_properties')
        if hasattr(site_properties, 'seo_properties'):
            settings_use_keywords_sg = getattr(site_properties.seo_properties, 'settings_use_keywords_sg', 0)
        return settings_use_keywords_sg

    def select_settings_use_keywords_lg(self):
        context = aq_inner(self.context)
        site_properties = getToolByName(context, 'portal_properties')
        if hasattr(site_properties, 'seo_properties'):
            settings_use_keywords_lg = getattr(site_properties.seo_properties, 'settings_use_keywords_lg', 0)
        return settings_use_keywords_lg


class SEOContextPropertiesView( BrowserView ):
    """ This class contains methods that allows to manage seo properties.
    """
    template = ViewPageTemplateFile('templates/seo_context_properties.pt')

    def test( self, condition, first, second ):
        """
        """
        return condition and first or second 

    def getMainDomain(self, url):
        """ Get a main domain.
        """
        url = url.split('//')[-1]
        dompath = url.split(':')[0]
        dom = dompath.split('/')[0]
        return '.'.join(dom.split('.')[-2:])

    def validateSEOProperty(self, property, value):
        """ Validate a seo property.
        """
        purl = getToolByName(self.context, 'portal_url')()
        state = ''
        if property == PROP_PREFIX+'canonical':
            # validate seo canonical url property
            pdomain = self.getMainDomain(purl)
            if not pdomain == self.getMainDomain(value):
                state = _('canonical_msg', default=u'Canonical URL mast be in ${pdomain} domain.', mapping={'pdomain': pdomain})
        return state

    def setProperty(self, property, value, type='string'):
        """ Add a new property.

        Sets a new property with the given id, value and type or changes it.
        """
        context = aq_inner(self.context)
        state = self.validateSEOProperty(property, value)
        if not state:
            if context.hasProperty(property):
                context.manage_changeProperties({property: value})
            else:
                context.manage_addProperty(property, value, type)
        return state

    def manageSEOProps(self, **kw):
        """ Manage seo properties.
        """
        context = aq_inner(self.context)
        state = ''
        delete_list, seo_overrides_keys, seo_keys = [], [], []
        seo_items = dict([(k[len(SEO_PREFIX):],v) for k,v in kw.items() if k.startswith(SEO_PREFIX)])
        for key in seo_items.keys():
            if key.endswith(SUFFIX):
                seo_overrides_keys.append(key[:-len(SUFFIX)])
            else:
                seo_keys.append(key)
        for seo_key in seo_keys:
            if seo_key == 'custommetatags':
                self.manageSEOCustomMetaTagsProperties(**kw)
            else:
                if seo_key in seo_overrides_keys and seo_items.get(seo_key+SUFFIX):
                    seo_value = seo_items[seo_key]
                    t_value = 'string'
                    if type(seo_value)==type([]) or type(seo_value)==type(()): t_value = 'lines'
                    state = self.setProperty(PROP_PREFIX+seo_key, seo_value, type=t_value)
                    if state:
                        return state
                elif context.hasProperty(PROP_PREFIX+seo_key):
                    delete_list.append(PROP_PREFIX+seo_key)
        if delete_list:
            context.manage_delProperties(delete_list)
        return state

    def setSEOCustomMetaTags(self, custommetatags):
        """ Set seo custom metatags properties.
        """
        context = aq_inner(self.context)
        for tag in custommetatags:
            self.setProperty('%s%s' % (PROP_CUSTOM_PREFIX, tag['meta_name']), tag['meta_content'])

    def delAllSEOCustomMetaTagsProperties(self):
        """ Delete all seo custom metatags properties.
        """
        context = aq_inner(self.context)
        delete_list = []
        for property, value in context.propertyItems():
            if property.startswith(PROP_CUSTOM_PREFIX)  and not property == PROP_CUSTOM_PREFIX:
                delete_list.append(property)
        if delete_list:
            context.manage_delProperties(delete_list)

    def updateSEOCustomMetaTagsProperties(self, custommetatags):
        """ Update seo custom metatags properties.
        """
        context = aq_inner(self.context)
        site_properties = getToolByName(context, 'portal_properties')
        globalCustomMetaTags = []
        if hasattr(site_properties, 'seo_properties'):
            custom_meta_tags = getattr(site_properties.seo_properties, 'default_custom_metatags', [])
            for tag in custom_meta_tags:
                name_value = tag.split(SEPERATOR)
                if name_value[0]:
                    globalCustomMetaTags.append({'meta_name'    : name_value[0],
                                                 'meta_content' : len(name_value) == 1 and '' or name_value[1]})
        for tag in custommetatags:
            meta_name, meta_content = tag['meta_name'], tag['meta_content']
            if meta_name:
                if not [gmt for gmt in globalCustomMetaTags if (gmt['meta_name']==meta_name and gmt['meta_content']==meta_content)]:
                    self.setProperty('%s%s' % (PROP_CUSTOM_PREFIX, meta_name), meta_content)

    def manageSEOCustomMetaTagsProperties(self, **kw):
        """ Update seo custom metatags properties, if enabled checkbox override or delete properties.

        Change object properties by passing either a mapping object
        of name:value pairs {'foo':6} or passing name=value parameters.
        """
        context = aq_inner(self.context)
        self.delAllSEOCustomMetaTagsProperties()
        if kw.get('seo_custommetatags_override'):
            custommetatags = kw.get('seo_custommetatags', {})
            self.updateSEOCustomMetaTagsProperties(custommetatags)

    def __call__( self ):
        """ Perform the update seo properties and redirect if necessary, or render the page Call method.
        """
        context = aq_inner(self.context)
        request = self.request
        form = self.request.form
        submitted = form.get('form.submitted', False)
        if submitted:
            state = self.manageSEOProps(**form)
            if not state:
                state = _('seoproperties_saved', default=u'Content SEO properties have been saved.')
                context.plone_utils.addPortalMessage(state)
                kwargs = {'modification_date' : DateTime()} 
                context.plone_utils.contentEdit(context, **kwargs) 
                return request.response.redirect(self.context.absolute_url())
            context.plone_utils.addPortalMessage(state, 'error')
        return self.template()
