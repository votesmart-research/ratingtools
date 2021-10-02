
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setuptools

requires = []

with open('requirements.txt') as f:
    requires = f.read().splitlines()


EGG = '#egg='

install_requires = ['pandas', 'tqdm']
dependency_links = []

for line in requires:
    package_name = line
    if line.startswith('git+'):
        if EGG not in line:
            raise Exception('Invalid dependency format')
        package_name = line[line.find(EGG) + len(EGG):]
        dependency_links.append(line)

    install_requires.append(package_name)

config = {
    'description': "Vote Smart tool for SIG Ratings",
    'author': "Johanan Tai",
    'author_email': "jtai.dvlp@gmail.com",
    'version': '0.0.1',
    'install_requires': install_requires,
    'dependency_links': dependency_links,
    'packages': ['ratingtools'],
    'name': 'ratingtools'
}

setup(**config)
