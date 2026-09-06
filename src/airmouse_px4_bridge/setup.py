from setuptools import find_packages, setup

package_name = 'airmouse_px4_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='vikingcodex',
    maintainer_email='rajeevtiwariunder100@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'px4_odom_bridge = airmouse_px4_bridge.px4_odom_bridge:main',
        ],
    },
)
