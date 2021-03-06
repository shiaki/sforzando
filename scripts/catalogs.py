#!/usr/bin/python

'''
    Catalogs.
'''

# define catalogs to search.
vizier_cats = [
    'II/246/out',
    'VII/233/xsc',
    'II/349/ps1',
    'VII/237/pgc',
    'V/147/sdss12',
    'VII/259/6dfgs',
    'I/345/gaia2',
    # 'J/ApJS/199/26/table3',
    # 'VII/62A/mcg',
    # 'VII/155/rc3'
]
# 2MASS PSC/XSC, HyperLEDA, SDSS, 6dF, 2MRS, MCG, RC3

cat_names = {
    'II/246/out':           '2MASS-PSC',
    'VII/233/xsc':          '2MASS-XSC',
    'VII/237/pgc':          'HyperLEDA',
    'V/147/sdss12':         'SDSS',
    'VII/259/6dfgs':        '6dFGS',
    'II/349/ps1':           'PS1',
    'J/ApJS/199/26/table3': '2MRS',
    'VII/62A/mcg':          'MCG',
    'VII/155/rc3':          'RC3',
    'I/345/gaia2':          'Gaia2'
}

radec_cols = {
    'II/246/out':           (( 0,  1), ('deg',  'deg')),
    'VII/233/xsc':          (( 2,  3), ('deg',  'deg')),
    'VII/237/pgc':          (( 1,  2), ('hour', 'deg')),
    'V/147/sdss12':         (( 0,  1), ('deg',  'deg')),
    'II/349/ps1':           (( 0,  1), ('deg',  'deg')),
    'VII/259/6dfgs':        ((13, 14), ('hour', 'deg')),
    'J/ApJS/199/26/table3': (( 2,  3), ('deg',  'deg')),
    'VII/62A/mcg':          (( 8,  9), ('hour', 'deg')),
    'VII/155/rc3':          (( 0,  1), ('hour', 'deg')),
    'I/345/gaia2':          (( 0,  2), ('deg', 'deg')),
}

srcid_cols = {
    'II/246/out':           2,
    'VII/233/xsc':          0,
    'VII/237/pgc':          0,
    'V/147/sdss12':         5,
    'II/349/ps1':           2,
    'VII/259/6dfgs':        0,
    'J/ApJS/199/26/table3': 0,
    'VII/62A/mcg':          0,
    'VII/155/rc3':          2,
    'VII/155/rc3':          2,
    'I/345/gaia2':          4,
}
