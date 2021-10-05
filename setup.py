
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setuptools


EGG = '#egg='
install_requires = []

with open('requirements.txt') as f:
    for line in f.read().splitlines():

        if line.startswith('git+'):
            if EGG not in line:
                raise Exception('egg specification is required.')
            package_name = line[line.find(EGG) + len(EGG):]
            dependency_link = line[:line.find(EGG)]
            install_requires.append(f"{package_name} @ {dependency_link}")
        else:
            install_requires.append(line)

config = {
    'description': "Ratings-Candidate matching tool for Vote Smart SIGs",
    'author': "Johanan Tai",
    'author_email': "jtai.dvlp@gmail.com",
    'version': '0.0.1',
    'install_requires': install_requires,
    'packages': ['ratingtools', 'ratingtools.match', 'ratingtools.harvest'],
    'name': 'ratingtools'
}

setup(**config)
