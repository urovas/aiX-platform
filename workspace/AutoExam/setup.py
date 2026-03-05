"""
AutoExam - 自动驾驶高危场景智能生成与测试系统
"""

from setuptools import setup, find_packages
import os

# 读取版本号
version_file = os.path.join(os.path.dirname(__file__), 'docs', 'VERSION')
with open(version_file, 'r') as f:
    version = f.read().strip()

# 读取README
readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
with open(readme_file, 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='autoexam',
    version=version,
    description='自动驾驶高危场景智能生成与测试系统',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='AutoExam Team',
    author_email='autoexam@example.com',
    url='https://github.com/yourusername/autoexam',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    include_package_data=True,
    package_data={
        'autoexam.ui': ['templates/*.html', 'static/**/*'],
    },
    install_requires=[
        'flask>=2.0.0',
        'numpy>=1.20.0',
        'matplotlib>=3.3.0',
        'scikit-learn>=0.24.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'pytest-xdist>=2.5.0',
        ],
        'carla': [
            'carla>=0.9.13',
        ],
    },
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'autoexam=autoexam.ui.app:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='autonomous-driving scenario-generation testing carla apollo',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/autoexam/issues',
        'Source': 'https://github.com/yourusername/autoexam',
        'Documentation': 'https://autoexam.readthedocs.io/',
    },
)
