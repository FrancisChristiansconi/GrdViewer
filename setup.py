from setuptools import setup

setup(name='patternviewer',
      version='DEV-GV-300',
      description='executable grd and pat file manager with GUI',
      url='',
      author='C. Francesconi',
      author_email='christian.francesconi@ses.com',
      license='None',
      install_requires=[
          'basemap==1.2.0',
          'pyproj==1.9.5.1',
          'matplotlib==3.0.0',
      ],
      packages=['patternviewer'],
      zip_safe=False)
