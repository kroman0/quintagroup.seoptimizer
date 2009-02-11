from setuptools import setup, find_packages

version = '2.0.0'

desc = file('./docs/README.txt').read()

setup(name='quintagroup.seoptimizer',
      version=version,
      description="Quintagroup Search Engine Optimization Tool",
      long_description=desc,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Myroslav Opyr, Volodymyr Romaniuk, Mykola Kharechko, Vitaliy Podoba, Volodymyr Cherepanyak, Taras Melnychuk, Vitaliy Stepanov',
      author_email='support@quintagroup.com',
      url='http://svn.quintagroup.com/products/quintagroup.seoptimizer/trunk/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['quintagroup'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
