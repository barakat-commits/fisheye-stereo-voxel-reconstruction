from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools
import pybind11

__version__ = '0.0.1'


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc', '/openmp', '/O2'],
        'unix': ['-O3', '-fopenmp', '-std=c++11'],
    }
    l_opts = {
        'msvc': ['/openmp'],
        'unix': ['-fopenmp'],
    }

    if sys.platform == 'darwin':
        darwin_opts = ['-stdlib=libc++', '-mmacosx-version-min=10.7', '-std=c++11']
        c_opts['unix'] += darwin_opts
        l_opts['unix'] += darwin_opts

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        link_opts = self.l_opts.get(ct, [])
        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
            opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts
        build_ext.build_extensions(self)


ext_modules = [
    Extension(
        'process_image_cpp',
        ['process_image.cpp'],
        include_dirs=[
            pybind11.get_include(),
            pybind11.get_include(user=True)
        ],
        language='c++'
    ),
]

setup(
    name='process_image_cpp',
    version=__version__,
    author='LLM Agent Framework',
    description='C++ extension for ray casting into voxel grids',
    long_description='',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.10.0', 'numpy>=1.21.0'],
    setup_requires=['pybind11>=2.10.0'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
)




