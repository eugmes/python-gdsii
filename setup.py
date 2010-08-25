from distutils.core import setup

setup(
    name = 'python-gdsii',
    version = '0.0',
    description = 'GDSII manipulation libaray',
    author = 'Eugeniy Meshcheryakov',
    author_email = 'eugen@debian.org',
    url = 'http://www.gitorious.org/python-gdsii',
    packages = ['gdsii'],
    scripts = ['scripts/gds2txt'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    license = 'LGPL-3+'
)
