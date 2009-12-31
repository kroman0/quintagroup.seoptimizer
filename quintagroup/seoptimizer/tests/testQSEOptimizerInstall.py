#
# Test product's installation
#
import string
from base import getToolByName, FunctionalTestCase, TestCase, newSecurityManager
from config import *


class TestBeforeInstall(FunctionalTestCase):

    def afterSetUp(self):
        self.basic_auth = 'mgr:mgrpw'
        self.portal_path = '/%s' % self.portal.absolute_url(1)

    def testAccessPortalRootAnonymous(self):
        response = self.publish(self.portal_path)
        self.assertEqual(response.getStatus(), 200)

    def testAccessPortalRootAuthenticated(self):
        response = self.publish(self.portal_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)


class TestInstallation(TestCase):

    def afterSetUp(self):
        self.properties = getToolByName(self.portal, 'portal_properties')
        self.qi = self.portal.portal_quickinstaller
        self.qi.installProduct(PROJECT_NAME)

    def testAddingPropertySheet(self):
        """ Test adding property sheet to portal_properties tool """
        self.failUnless(hasattr(self.properties.aq_base, PROPERTY_SHEET))

    def testAddingPropertyFields(self):
        """ Test adding property field to portal_properties.maps_properties sheet """
        map_sheet = self.properties[PROPERTY_SHEET]
        for key, value in PROPS.items():
            self.failUnless(map_sheet.hasProperty(key) and list(map_sheet.getProperty(key)) == value)

    def test_configlet_install(self):
        configTool = getToolByName(self.portal, 'portal_controlpanel', None)
        self.assert_(PROJECT_NAME in [a.getId() for a in configTool.listActions()], 'Configlet not found')

    def test_actions_install(self):
        portal_types = getToolByName(self.portal, 'portal_types')
        for ptype in portal_types.objectValues():
            try:
                #for Plone-2.5 and higher
                acts = filter(lambda x: x.id == 'seo_properties', ptype.listActions())
                action = acts and acts[0] or None
            except AttributeError:
                action = ptype.getActionById('seo_properties', default=None )

            if ptype.getId() in qSEO_TYPES:
                self.assert_(action, 'Action for %s not found' % ptype.getId())
            else:
                self.assert_(not action, 'Action found for %s' % ptype.getId())

    def test_skins_install(self):
        skinstool=getToolByName(self.portal, 'portal_skins')

        for skin in skinstool.getSkinSelections():
            path = skinstool.getSkinPath(skin)
            path = map( string.strip, string.split( path,',' ) )
            self.assert_(PROJECT_NAME in path, 'qSEOptimizer layer not found in %s' %skin)

    def test_versionedskin_install(self):
        skinstool=getToolByName(self.portal, 'portal_skins')
        mtool = getToolByName(self.portal, 'portal_migration')
        plone_version = mtool.getFileSystemVersion()
        if plone_version < "3":
            for skin in skinstool.getSkinSelections():
                path = skinstool.getSkinPath(skin)
                path = map( string.strip, string.split( path,',' ) )
                self.assert_(PROJECT_NAME+'/%s' % plone_version in path, 'qSEOptimizer versioned layer not found in %s' %skin)

    def test_actions_uninstall(self):
        self.qi.uninstallProducts([PROJECT_NAME])
        self.assertNotEqual(self.qi.isProductInstalled(PROJECT_NAME), True,'qSEOptimizer is already installed')
        portal_types = getToolByName(self.portal, 'portal_types')
        for ptype in portal_types.objectValues():
            try:
                #for Plone-2.5 and higher
                acts = filter(lambda x: x.id == 'seo_properties', ptype.listActions())
                action = acts and acts[0] or None
            except AttributeError:
                action = ptype.getActionById('seo_properties', default=None )

            self.assert_(not action, 'Action for %s found after uninstallation' % ptype.getId())

    def test_skins_uninstall(self):
        self.qi.uninstallProducts([PROJECT_NAME])
        self.assertNotEqual(self.qi.isProductInstalled(PROJECT_NAME), True,'qSEOptimizer is already installed')
        skinstool=getToolByName(self.portal, 'portal_skins')

        for skin in skinstool.getSkinSelections():
            path = skinstool.getSkinPath(skin)
            path = map( string.strip, string.split( path,',' ) )
            self.assert_(not PROJECT_NAME in path, 'qSEOptimizer layer found in %s after uninstallation' %skin)

    def test_versionedskin_uninstall(self):
        self.qi.uninstallProducts([PROJECT_NAME])
        self.assertNotEqual(self.qi.isProductInstalled(PROJECT_NAME), True,'qSEOptimizer is already installed')
        skinstool=getToolByName(self.portal, 'portal_skins')
        mtool = getToolByName(self.portal, 'portal_migration')
        plone_version = mtool.getFileSystemVersion()

        for skin in skinstool.getSkinSelections():
            path = skinstool.getSkinPath(skin)
            path = map( string.strip, string.split( path,',' ) )
            self.assert_(not PROJECT_NAME+'/%s' % plone_version in path, 'qSEOptimizer versioned layer found in %s after uninstallation' %skin)

    def test_configlet_uninstall(self):
        self.qi.uninstallProducts([PROJECT_NAME])
        self.assertNotEqual(self.qi.isProductInstalled(PROJECT_NAME), True,'qSEOptimizer is already installed')

        configTool = getToolByName(self.portal, 'portal_controlpanel', None)
        self.assert_(not PROJECT_NAME in [a.getId() for a in configTool.listActions()], 'Configlet found after uninstallation')

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestBeforeInstall))
    suite.addTest(makeSuite(TestInstallation))
    return suite
