from setuptools import setup

package_name = 'drill_bringup'

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
    description='Bringup for drill_sim',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={},
)
