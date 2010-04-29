import logging
from zope.component import queryMultiAdapter

from quintagroup.canonicalpath.interfaces  import ICanonicalLink
from quintagroup.canonicalpath.adapters import PROPERTY_LINK

logger = logging.getLogger('quintagroup.seoptimizer')
FIX_PTYPES_DOMAIN = ['Document', 'File', 'News Item']
REMOVE_SEOPROPERTIES = ['additional_keywords', 'settings_use_keywords_sg',
                        'settings_use_keywords_lg', 'filter_keywords_by_content',
                       ]

def changeDomain(plone_tools):
    """ Fix i18n_domain bug for some portal_types,
        which present in earlier versions of the package.
    """
    types_tool = plone_tools.types()
    for ptype in [ptypes for ptypes in types_tool.objectValues()
                         if ptypes.id in FIX_PTYPES_DOMAIN]:
        if ptype.i18n_domain == 'quintagroup.seoptimizer':
            ptype.i18n_domain = 'plone'
            logger.log(logging.INFO, "I18n Domain of the type \'%s\' "
                       "changed to \'plone\'." % ptype.id)

def changeMetatagsOrderList(plone_tools):
    """ Change format metatags order list from "metaname accessor" to "metaname".
    """
    types_tool = plone_tools.types()
    setup_tool = plone_tools.url().getPortalObject().portal_setup
    seoprops_tool = plone_tools.properties().seo_properties
    if seoprops_tool.hasProperty('metatags_order'):
        mto = seoprops_tool.getProperty('metatags_order', [])
        mto_new = [line.split(' ')[0].strip() for line in mto]
        if not list(mto) == mto_new:
            logger.log(logging.INFO, "Changed format metatags order list in "
                       "configlet from \"metaname accessor\" to \"metaname\".")
            seoprops_tool.manage_changeProperties(metatags_order=mto_new)
    else:
        setup_tool.runImportStepFromProfile('profile-quintagroup.seoptimizer:default',
                                            'propertiestool')


def migrationActions(plone_tools):
    """ Migration actions from portal_types action to seoproperties tool
        (for seoaction in portal_actions).
    """
    types_tool = plone_tools.types()
    seoprops_tool = plone_tools.properties().seo_properties
    ctws = list(seoprops_tool.getProperty('content_types_with_seoproperties', []))
    flag = False
    for ptype in types_tool.objectValues():
        idxs = [idx_act[0] for idx_act in enumerate(ptype.listActions())
                           if idx_act[1].id == 'seo_properties']
        if idxs:
            if ptype.id not in ctws:
                ctws.append(ptype.id)
                flag = True
            ptype.deleteActions(idxs)
            logger.log(logging.INFO, "Moved \"SEO Properties\" action from %s "
                       "type in portal actions." % ptype.id)
    if flag:
        seoprops_tool.manage_changeProperties(content_types_with_seoproperties=ctws)

def removeNonUseSeoProperties(plone_tools):
    """ Revome properties used in earlier versions of the package
    """
    seoprops_tool = plone_tools.properties().seo_properties
    remove_properties = []
    for pr in REMOVE_SEOPROPERTIES:
      if seoprops_tool.hasProperty(pr):
          remove_properties.append(pr)
          logger.log(logging.INFO, "Removed %s property in seoproperties tool." % pr)
    if not remove_properties:
        seoprops_tool.manage_delProperties(remove_properties)

def removeSkin(plone_tools):
    """ Remove skin layers.
    """
    layer = 'quintagroup.seoptimizer'
    skins_tool = plone_tools.url().getPortalObject().portal_skins
    for skinName in skins_tool.getSkinSelections():
        skin_paths = skins_tool.getSkinPath(skinName).split(',') 
        paths = [l.strip() for l in skin_paths if not (l == layer or l.startswith(layer+'/'))]
        logger.log(logging.INFO, "Removed layers from %s skin." % skinName)
        skins_tool.addSkinSelection(skinName, ','.join(paths))

def migrateCanonical(plone_tools):
    """ Rename qSEO_canonical property into PROPERTY_LINK
        for all portal objects, which use SEO
    """
    types = plone_tools.types()
    portal = plone_tools.url().getPortalObject()
    allCTTypes = types.listContentTypes()
    obj_metatypes =  [m.content_meta_type for m in types.objectValues() \
                      if m.getId() in allCTTypes]
    portal.ZopeFindAndApply(
                            portal,
                            obj_metatypes=','.join(obj_metatypes),
                            apply_func=renameProperty
                            )

def renameProperty(obj, path):
    """ Rename qSEO_canonical property into PROPERTY_LINK
        for obj, which use SEO
    """
    if obj.hasProperty('qSEO_canonical'):
        value = obj.getProperty('qSEO_canonical')

        level, msg = logging.INFO, "For %(url)s object 'qSEO_canonical' "\
                     "property renamed to '%(name)s'."
        try:
            ICanonicalLink(obj).canonical_link = value
        except Exception, e:
            level, msg = logging.ERROR, "%s on renaming 'qSEO_canonical' " \
                         "property for %%(url)s object" % str(e)

        logger.log(level, msg % {'url':obj.absolute_url(), 'name':PROPERTY_LINK} )
        obj.manage_delProperties(['qSEO_canonical'])

def upgrade_2_to_3(setuptool):
    """ Upgrade quintagroup.seoptimizer from version 2.x.x to 3.0.0.
    """
    plone_tools = queryMultiAdapter((setuptool, setuptool.REQUEST), name="plone_tools")
    setuptool.runAllImportStepsFromProfile('profile-quintagroup.seoptimizer:upgrade_2_to_3')
    migrationActions(plone_tools)
    changeDomain(plone_tools)
    changeMetatagsOrderList(plone_tools)
    removeNonUseSeoProperties(plone_tools)
    removeSkin(plone_tools)
    migrateCanonical(plone_tools)
