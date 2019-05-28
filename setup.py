from setuptools import setup

setup(name='IoTMonitor',
      version='1.0',
      description='Home monitoring tool and framework',
      url='https://github.com/RemDec/IoTMonitor',
      author='Remy Decocq',
      author_email='remy.decocq@student.umons.ac.be',
      license='GNU',
      packages=['src', 'modules'],
      install_requires=['lxml'])