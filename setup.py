from setuptools import setup

setup(name="NetFlowVizu",
      version="0.6",
      description="Network flow visualizer.",
      long_description = open("README.rst").read(),
      keywords="network, host, flow, traffic, communication, visualization, dia",
      author="David Siroky",
      author_email="siroky@dasir.cz",
      url="http://www.smallbulb.net/netflowvizu",
      license="MIT License",
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: Education",
          "Intended Audience :: Science/Research",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python",
          "Topic :: System :: Networking",
          "Topic :: Scientific/Engineering :: Information Analysis",
          "Topic :: Scientific/Engineering :: Visualization"
        ],
      install_requires=["lxml", "pyyaml"],
      scripts=["net_flow_vizu_dia.py"]
    )
