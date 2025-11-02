import sys
import os

from importlib.metadata import version as get_version

sys.path.insert(0, os.path.abspath('..'))


project = u'Attest'
copyright = u'2010-2011, Dag Odenhall'
release = get_version('attest')
version = release.split('dev', 1)[0]


extensions =\
    ['sphinx.ext.autodoc',
     'sphinx.ext.intersphinx',
     'sphinx.ext.viewcode',
     'sphinx.ext.doctest',
    ]

intersphinx_mapping =\
    {'http://docs.python.org/dev/': None,
    }


master_doc = 'index'
add_module_names = False
modindex_common_prefix = ['attest.']


if 'dev' in release:  # RTD
    html_theme = 'default'
else:
    html_theme = 'attest'
    html_theme_path = ['_themes']

html_static_path = ['_static']
html_use_opensearch = 'http://packages.python.org/Attest'
html_sidebars =\
    {'**':
        ['globaltoc.html',
         'searchbox.html',
        ],
    }


try:
    import sphinxcontrib.spelling
except ImportError:
    pass
else:
    extensions.append('sphinxcontrib.spelling')
    spelling_lang = 'en_UK'
    spelling_word_list_filename = os.path.abspath('non-typos.txt')
