from quintagroup.canonicalpath.interfaces import ICanonicalLink
from base import *

class TestCanonicalURL(FunctionalTestCase):

    def afterSetUp(self):
        self.basic_auth = ':'.join((portal_owner,default_password))
        self.loginAsPortalOwner()
        # Preparation for functional testing
        self.portal.invokeFactory('Document', id='mydoc')
        self.mydoc = self.portal['mydoc']
        self.mydoc_path = "/%s" % self.mydoc.absolute_url(1)
        self.curl = re.compile('<link\srel\s*=\s*"canonical"\s+' \
            '[^>]*href\s*=\s*\"([^\"]*)\"[^>]*>', re.S|re.M)

    def test_CanonicalURL(self):
        html = self.publish(self.mydoc_path, self.basic_auth).getBody()
        foundcurls = self.curl.findall(html)
        mydoc_url = self.mydoc.absolute_url()

        self.assertTrue([1 for curl in foundcurls if curl==mydoc_url],
           "Wrong CANONICAL URL for document: %s, all must be: %s" % (
           foundcurls, mydoc_url))

    def test_updateCanonicalURL(self):
        mydoc_url_new = self.mydoc.absolute_url() + '.new'
        # Update canonical url property
        self.publish(self.mydoc_path + '/@@seo-context-properties?' \
           'seo_canonical_override=checked&seo_canonical=%s&' \
           'form.submitted=1' % mydoc_url_new, self.basic_auth)
        # Test updated canonical url
        html = self.publish(self.mydoc_path, self.basic_auth).getBody()
        foundcurls = self.curl.findall(html)

        qseo_url = ICanonicalLink(self.mydoc).canonical_link
        self.assertTrue(qseo_url == mydoc_url_new,
           "Not set 'qSEO_canonical' property")
        self.assertTrue([1 for curl in foundcurls if curl==mydoc_url_new],
           "Wrong CANONICAL URL for document: %s, all must be: %s" % (
           foundcurls, mydoc_url_new))

    def test_defaultCanonical(self):
        expect = self.mydoc.absolute_url()
        cpath = ICanonicalLink(self.mydoc).canonical_link
        self.assertTrue(cpath == expect,
            "Default canonical link adapter return: '%s', must be: '%s'" % (
             cpath, expect))

    def testCatalogUpdated(self):
        purl = getToolByName(self.portal, 'portal_url')
        catalog = getToolByName(self.portal, 'portal_catalog')
        catalog.addColumn('canonical_link')

        # get catalog data before update
        mydoc_catalog_canonical = catalog(id="mydoc")[0].canonical_link
        self.assertTrue(not mydoc_catalog_canonical)

        # Update canonical url property
        mydoc_url_new = self.mydoc.absolute_url() + '.new'
        self.publish(self.mydoc_path + '/@@seo-context-properties?' \
            'seo_canonical_override=checked&seo_canonical=%s' \
            '&form.submitted=1' % mydoc_url_new, self.basic_auth)

        newcpath = ICanonicalLink(self.mydoc).canonical_link
        mydoc_catalog_canonical = catalog(id="mydoc")[0].canonical_link
        self.assertTrue(newcpath == mydoc_catalog_canonical,
            "canonical path get by adapter: '%s' not equals to cataloged one: '%s'" % (
             newcpath, mydoc_catalog_canonical))

    def test_canonicalValidation(self):
        wrong_canonical = 'wrong   canonical'
        # Update canonical url property
        html = self.publish(self.mydoc_path + '/@@seo-context-properties?' \
               'seo_canonical_override=checked&seo_canonical=%s&' \
               'form.submitted=1' % wrong_canonical, self.basic_auth).getBody()
        self.assertTrue("wrong canonical url" in html,
                        "Canonical url not validated")

    def test_delCanonical(self):
        newcanonical = '/new_canonical'
        ICanonicalLink(self.mydoc).canonical_link = newcanonical

        assert ICanonicalLink(self.mydoc).canonical_link == newcanonical

        # remove canonical url customization
        self.publish(self.mydoc_path + '/@@seo-context-properties?' \
           'seo_canonical=%s&seo_canonical_override=&form.submitted=1' % newcanonical,
            self.basic_auth)

        mydoc_canonical = ICanonicalLink(self.mydoc).canonical_link
        self.assertTrue(mydoc_canonical == self.mydoc.absolute_url(),
            "Steel customized canonical url after remove customization")


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCanonicalURL))
    return suite
