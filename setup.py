from setuptools import setup, Extension, Distribution
import setuptools.command.build_ext

import sys
import sysconfig
import os
import distutils.sysconfig

import itertools
from glob import iglob


def _get_turbodbc_libname():
    builder = setuptools.command.build_ext.build_ext(Distribution())
    full_name = builder.get_ext_filename('libturbodbc')
    without_lib = full_name.split('lib', 1)[-1]
    without_so = without_lib.rsplit('.so', 1)[0]
    return without_so


def _get_distutils_build_directory():
    """
    Returns the directory distutils uses to build its files.
    We need this directory since we build extensions which have to link
    other ones.
    """
    pattern = "lib.{platform}-{major}.{minor}"
    return os.path.join('build', pattern.format(platform=sysconfig.get_platform(),
                                                major=sys.version_info[0],
                                                minor=sys.version_info[1]))


def _get_source_files(directory):
    path = os.path.join('src', directory)
    iterable_sources = (iglob(os.path.join(root,'*.cpp')) for root, dirs, files in os.walk(path))
    source_files = itertools.chain.from_iterable(iterable_sources)
    return list(source_files)


def _remove_strict_prototype_option_from_distutils_config():
    strict_prototypes = '-Wstrict-prototypes'
    config = distutils.sysconfig.get_config_vars()
    for key, value in config.items():
        if strict_prototypes in str(value):
            config[key] = config[key].replace(strict_prototypes, '')

_remove_strict_prototype_option_from_distutils_config()


def _has_numpy_headers():
    try:
        import numpy
        return True
    except:
        return False


class _deferred_pybind11_include(object):
    def __str__(self):
        import pybind11
        return pybind11.get_include()


def get_extension_modules():
    """
    Extension module which is actually a plain C++ library without Python bindings
    """
    turbodbc_sources = _get_source_files('cpp_odbc') + _get_source_files('turbodbc')
    turbodbc_library = Extension('libturbodbc',
                                 sources=turbodbc_sources,
                                 include_dirs=['include/'],
                                 extra_compile_args=['--std=c++11'],
                                 libraries=['odbc'])
    turbodbc_lib = _get_turbodbc_libname()

    """
    An extension module which contains the main Python bindings for turbodbc
    """
    turbodbc_python = Extension('turbodbc_intern',
                                sources=_get_source_files('turbodbc_python'),
                                include_dirs=['include/',
                                              _deferred_pybind11_include()],
                                extra_compile_args=['--std=c++11'],
                                libraries=['odbc', turbodbc_lib],
                                extra_link_args=["-Wl,-rpath,$ORIGIN"],
                                library_dirs=[_get_distutils_build_directory()])

    """
    An extension module which contains Python bindings which require numpy support
    to work. Not included in the standard Python bindings so this can stay optional.
    """
    if _has_numpy_headers():
        import numpy
        turbodbc_numpy = Extension('turbodbc_numpy_support',
                                   sources=_get_source_files('turbodbc_numpy'),
                                   include_dirs=['include/',
                                                 _deferred_pybind11_include(),
                                                 numpy.get_include()],
                                   extra_compile_args=['--std=c++11'],
                                   libraries=['odbc', turbodbc_lib],
                                   extra_link_args=["-Wl,-rpath,$ORIGIN"],
                                   library_dirs=[_get_distutils_build_directory()])
        return [turbodbc_library, turbodbc_python, turbodbc_numpy]
    else:
        return [turbodbc_library, turbodbc_python]


setup(name = 'turbodbc',
      version = '1.0.0',
      description = 'turbodbc is a Python DB API 2.0 compatible ODBC driver',
      include_package_data = True,
      url = 'https://github.com/blue-yonder/turbodbc',
      author='Michael Koenig',
      author_email = 'michael.koenig@blue-yonder.com',
      packages = ['turbodbc'],
      classifiers = ['Development Status :: 4 - Beta',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Operating System :: POSIX :: Linux',
                     'Programming Language :: C++',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3.4',
                     'Programming Language :: Python :: 3.5',
                     'Programming Language :: Python :: 3.6',
                     'Programming Language :: Python :: Implementation :: CPython',
                     'Topic :: Database'],
      ext_modules = get_extension_modules(),
      install_requires=['pybind11>=2.0.0', 'six']
      )
