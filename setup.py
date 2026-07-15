from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="supplycore",
    version="0.1.0",
    description="Hospital medical supply chain management — custom Frappe/ERPNext v15 app",
    author="SupplyCore Project",
    author_email="info@miyano.com.vn",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
