PROJECT_NAME = 'quintagroup.seoptimizer'

SUPPORT_BLAYER = True
try:
    from plone import browserlayer
except ImportError:
    SUPPORT_BLAYER = False
