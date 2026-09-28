from setuptools import setup

package_name = 'drill_sim'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lostkid0617',
    maintainer_email='you@example.com',
    description='Minimal drill simulator',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': [
        'drill_sim = drill_sim.drill_sim_node:main',
    ],},
)
