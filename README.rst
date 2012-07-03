What is this vizu?
==================
net_flow_vizu_dia.py converts a YAML formated network flow data into a dia
(http://projects.gnome.org/dia/) diagram file.

Prerequisites
=============
- python 2.6+
- python-lxml (http://pypi.python.org/pypi/lxml/)
- python-yaml (http://pyyaml.org/wiki/PyYAML)

Usage examples
==============
command line::

  $ ./net_flow_vizu_dia.py < data_example.yaml > f.dia
  $ data_generator | ./net_flow_vizu_dia.py > f.dia

  $ dia f.dia

Notes
=====
Items in sections "traffic" and "marks" doesn't need to be in order by
timestamps.

FAQ
===
Q:  net_flow_vizu_dia.py fails with an exception
    "yaml.scanner.(Parser|Scanner)Error".
A:  Input data is probably not in a correct YAML format
    (http://en.wikipedia.org/wiki/YAML).

Q:  net_flow_vizu_dia.py fails with any other exception.
A:  Your input data has a wrong structure (or net_flow_vizu has a bug :-)

Output example
==============
.. image:: http://www.smallbulb.net/uploads/2010/09/net_flow.png
