#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@author: David Siroky (siroky@dasir.cz)
@license: see LICENSE.txt
"""

import os
import types
import sys
import io

#########################################################################
#########################################################################

def err(txt):
    sys.stderr.write(txt + "\n")
    sys.exit(1)

#########################################################################
#########################################################################

if sys.version_info < (2, 6):
    err("this python is too old, see README.txt, section Prerequisities")

try:
    import yaml
except ImportError:
    err("missing YAML library, see README.txt, section Prerequisities")

try:
    from lxml import etree
    from lxml.builder import ElementMaker
except ImportError:
    err("missing lxml library, see README.txt, section Prerequisities")

#########################################################################
#########################################################################

class Cfg(object):
    PT_TO_CM = 1.0 / 72.0 * 2.54
    SPREAD = 1.0 # horizontal spread ratio

    DATA_LINE_WIDTH = 0.02 # cm
    DATA_COLOR = "#000000"
    LABEL_FONT_SIZE = 9 # pt
    ARROW_LENGTH = 0.2 # cm
    ARROW_WIDTH = 0.15 # cm

    MARK_COLOR = "#000000"
    MARK_SIZE = 0.1 # cm

    LABEL_CONNECTOR_COLOR = "#d0d0d0"
    LABEL_CONNECTOR_WIDTH = 0.01 # cm

    PROCESS_SPACING = 2.0 # cm
    PROCESS_LINE_HOFFSET = 0.2 # cm
    PROCESS_LINE_WIDTH = 0.02 # cm
    PROCESS_COLOR = "#787878"
    PROCESS_FONT_SIZE = 11 # pt

    FONT_FAMILY = "sans"

    MAXIMUM_ORIENTATION = 20

    SEND_FORMAT = "s(%s)"
    RECV_FORMAT = "r(%s)"

c = Cfg()

E = ElementMaker(namespace="http://www.lysator.liu.se/~alla/dia/",
                 nsmap={"dia" : "http://www.lysator.liu.se/~alla/dia/"})

#########################################################################
#########################################################################

def _attribute(attr_name, attr_value):
    if isinstance(attr_value, etree._Element):
        return attr_value
    elif isinstance(attr_value, DiaAttribute):
        return attr_value.elements()
    else:
        if isinstance(attr_value, str):
            attr_type = "string"
        elif isinstance(attr_value, float):
            attr_type = "real"
            attr_value = str(attr_value)
        elif isinstance(attr_value, bool):
            attr_type = "boolean"
            attr_value = "true" if attr_value else "false"
        elif isinstance(attr_value, int):
            attr_type = "int"
            attr_value = str(attr_value)
        else:
            raise ValueError("unknown attr type %s" % (repr(attr_value)))

        if attr_type == "string":
            return getattr(E, attr_type)(attr_value)
        else:
            return getattr(E, attr_type)(val=attr_value)

def attributes(attrs):
    elements = []
    for attr_name, attr_value in attrs:
        if isinstance(attr_value, (list, tuple)):
            children = [_attribute(attr_name, value) for value in attr_value]
        else:
            children = [_attribute(attr_name, attr_value)]
        elements.append(E.attribute(*children, name=attr_name))

    return elements

#########################################################################

def text_box_size(txt, font_size):
    """
    @return: approximate width and height
    """
    width = len(txt) * font_size * 0.6 * c.PT_TO_CM
    height = font_size * c.PT_TO_CM
    return width, height

#########################################################################
#########################################################################

class DiaAttribute(object):
    def __init__(self, val):
        self.val = val

    def elements(self):
        return getattr(E, self.TYPE)(val=self.val)

##################################################

class ColorAttribute(DiaAttribute):
    TYPE = "color"

##################################################

class PointAttribute(DiaAttribute):
    TYPE = "point"

#########################################################################
#########################################################################

class DiaObject(object):
    pass

##################################################

class LineObject(DiaObject):
    def __init__(self, x1, y1, x2, y2, width, color):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.width = width
        self.color = color

    def more(self):
        return []

    def tree(self, _id):
        attrs = attributes([
            ("obj_pos", PointAttribute("%f,%f" % (self.x1, self.y1))),
            ("conn_endpoints", (
                PointAttribute("%f,%f" % (self.x1, self.y1)),
                PointAttribute("%f,%f" % (self.x2, self.y2))
              )),
            ("numcp", 1),
            ("line_width", self.width),
            ("line_color", ColorAttribute(self.color))
          ]) + self.more()
        return E.object(*attrs, type="Standard - Line", version="0", id=_id)

##################################################

class ArrowObject(LineObject):
    def more(self):
        return attributes([
            ("end_arrow", E.enum(val="1")),
            ("end_arrow_length", c.ARROW_LENGTH),
            ("end_arrow_width", c.ARROW_WIDTH)
          ])

##################################################

class TextObject(DiaObject):
    def __init__(self, text, x, y, color, size):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.size = size
    
    def tree(self, _id):
        attrs = attributes([
            ("obj_pos", PointAttribute("%f,%f" % (self.x, self.y))),
            ("text", E.composite(
                *attributes([
                  ("string", "#" + self.text + "#"),
                  ("font", E.font(family=c.FONT_FAMILY, style="0")),
                  ("height", self.size * c.PT_TO_CM),
                  ("pos", PointAttribute("%f,%f" % (self.x, self.y))),
                  ("color", ColorAttribute(self.color))
                ]), type="text"))
          ])
        return E.object(*attrs, type="Standard - Text", version="1", id=_id)

##################################################

class PointObject(DiaObject):
    def __init__(self, x, y, diameter, color):
        self.x = x
        self.y = y
        self.diameter = diameter
        self.color = color

    def tree(self, _id):
        attrs = attributes([
            ("obj_pos", PointAttribute("%f,%f" % (self.x, self.y))),
            ("elem_corner", PointAttribute("%f,%f" % (self.x, self.y))),
            ("elem_width", self.diameter),
            ("elem_height", self.diameter),
            ("border_width", 0.0),
            ("inner_color", ColorAttribute(self.color)),
            ("border_color", ColorAttribute(self.color))
          ])
        return E.object(*attrs, type="Standard - Ellipse", version="0", id=_id)

#########################################################################
#########################################################################

class DiaConvertor(object):
    def __init__(self, input_data=None):
        self.input_data = input_data
        self.dia_document = None
        self.id_counter = 0
        self.time_start = None
        self.time_end = None
        self.process_pos = {}
        self.labels_per_line = {}
        self.line_hofs = 0.0

    #####################################################
        
    def convert(self):
        if self.input_data is None:
            self.input_data = yaml.load(sys.stdin)
        else:
            self.input_data = yaml.load(io.BytesIO(self.input_data))
        self.load_config()

        times = [packet["src"]["ts"] for packet in self.input_data["traffic"]]
        times += [packet["dst"]["ts"] for packet in self.input_data["traffic"]]
        if "marks" in self.input_data:
            times += [mark["ts"] for mark in self.input_data["marks"]]
        times.sort()
        self.time_start = times[0]
        self.time_end = times[-1] * c.SPREAD

        self.gen_dia_document()
        xml = etree.tostring(self.dia_document, pretty_print=True, 
                              xml_declaration=True, encoding="UTF-8")

        sys.stdout.write(xml.decode("utf-8"))

    #####################################################

    def load_config(self):
        if "config" not in self.input_data:
            return

        for key, value in list(self.input_data["config"].items()):
            if not hasattr(c, key):
                raise ValueError("unknown config key '%s'" % key)
            setattr(c, key, value)

    #####################################################

    def gen_dia_document(self):
        diagram_data = attributes([
            ("background", ColorAttribute("#ffffff")),
            ("pagebreak", ColorAttribute("#ffffff")),
            ("paper", E.composite(*attributes([
                    ("name", "#A4#"),
                    ("tmargin", 1.0),
                    ("bmargin", 1.0),
                    ("lmargin", 1.0),
                    ("rmargin", 1.0),
                    ("is_portrait", True),
                    ("scaling", 1.0),
                    ("fitto", False)
                  ]), type="paper")),
            ("grid", E.composite(*(attributes([
                    ("width_x", 1.0),
                    ("width_y", 1.0),
                    ("visible_x", 1),
                    ("visible_y", 1),
                  ]) + [E.composite(type="color")]), type="grid")),
            ("color", ColorAttribute("#ffffff")),
            ("guides", E.composite(
                    E.attribute(name="hguides"),
                    E.attribute(name="vguides"),
                    type="guides"))
          ])

        processes = self.draw_processes()
        traffic = self.draw_traffic()
        marks = self.draw_marks()
        labels_connectors, labels = self.draw_traffic_labels()

        layer = processes + labels_connectors + traffic + marks + labels

        self.dia_document = E.diagram(
            E.diagramdata(*diagram_data),
            E.layer(*layer, name="Background", visible="true", active="true")
          )

    #####################################################

    def convert_objects(self, objects):
        return [obj.tree(self.get_id()) for obj in objects]

    #####################################################

    def draw_processes(self):
        dia_processes = []
        
        # calculate timeline hoffset
        for process in self.input_data["processes"]:
            txt_width, txt_height = text_box_size(process, c.PROCESS_FONT_SIZE)
            self.line_hofs = max(self.line_hofs, txt_width + c.PROCESS_LINE_HOFFSET)

        for i, process in enumerate(self.input_data["processes"]):
            process = str(process)
            y = i * c.PROCESS_SPACING
            self.process_pos[process] = y

            txt_width, txt_height = text_box_size(process, c.PROCESS_FONT_SIZE)
            dia_processes.append(TextObject(process + ":", 
                                            0.0, 
                                            y - txt_height / 2.0, 
                                            c.PROCESS_COLOR,
                                            c.PROCESS_FONT_SIZE))
            length = self.time_end - self.time_start
            dia_processes.append(LineObject(self.line_hofs, 
                                            y, 
                                            self.line_hofs + length, 
                                            y,
                                            c.PROCESS_LINE_WIDTH, c.PROCESS_COLOR))

        return self.convert_objects(dia_processes)

    #####################################################

    def stack_labels(self, labels):
        labels.sort(key=(lambda x: x[1]))
        for i in range(1, len(labels)):
            label = labels[i]
            while abs(label[4]) < c.MAXIMUM_ORIENTATION:
                # go backwards and find overlapping label 
                # with the same orientation/level
                for j in range(i - 1, -1, -1):
                    prev_label = labels[j]
                    if prev_label[4] != label[4]:
                        # not on the same level
                        continue
                    width, height = text_box_size(prev_label[0], c.LABEL_FONT_SIZE)
                    prev_end = prev_label[1] + width
                    if label[1] < prev_end:
                        # overlapping found, proceed to next level
                        break
                else:
                    # not found, label is free to stay on its level
                    break # break the "while"

                # try next level
                if label[4] < 0:
                    label[4] -= 1
                else:
                    label[4] += 1
            
    #####################################################

    def draw_traffic(self):
        dia_traffic_arrows = []
        for packet in self.input_data["traffic"]:
            src_process, src_time = str(packet["src"]["p"]), packet["src"]["ts"]
            dst_process, dst_time = str(packet["dst"]["p"]), packet["dst"]["ts"]
            src_time *= c.SPREAD
            dst_time *= c.SPREAD
            data = str(packet["data"])
            color = packet.get("color", c.DATA_COLOR)
            x1 = self.line_hofs + src_time - self.time_start
            y1 = self.process_pos[src_process]
            x2 = self.line_hofs + dst_time - self.time_start
            y2 = self.process_pos[dst_process]

            dia_traffic_arrows.append(ArrowObject(x1, y1, x2, y2,
                                         c.DATA_LINE_WIDTH, color))

            # put the text on the right side of the process line
            if y1 < y2:
                orientation1 = -1
                orientation2 = 0
            else:
                orientation1 = 0
                orientation2 = -1
            key = "%s%i" % (src_process, orientation1)
            labels = self.labels_per_line.setdefault(key, [])
            labels.append([c.SEND_FORMAT % data, x1, y1, color, orientation1])
            key = "%s%i" % (dst_process, orientation2)
            labels = self.labels_per_line.setdefault(key, [])
            labels.append([c.RECV_FORMAT % data, x2, y2, color, orientation2])

        return self.convert_objects(dia_traffic_arrows)

    #####################################################

    def draw_marks(self):
        if "marks" not in self.input_data:
            return []

        dia_marks = []
        for mark in self.input_data["marks"]:
            x = self.line_hofs + mark["ts"] * c.SPREAD - self.time_start
            y = self.process_pos[mark["p"]]
            color = mark.get("color", c.MARK_COLOR)
            dia_marks.append(PointObject(x - c.MARK_SIZE / 2.0, 
                                        y - c.MARK_SIZE / 2.0,
                                        c.MARK_SIZE, color))
            orientation = -1
            key = "%s%i" % (mark["p"], orientation)
            labels = self.labels_per_line.setdefault(key, [])
            labels.append([str(mark["text"]), x, y, color, orientation])

        return self.convert_objects(dia_marks)

    #####################################################

    def draw_traffic_labels(self):
        dia_traffic_labels = []
        dia_connectors = []

        for labels in list(self.labels_per_line.values()):
            self.stack_labels(labels)
            for data, x, y, color, orientation in labels:
                height = c.LABEL_FONT_SIZE * c.PT_TO_CM
                ly = y + orientation * height
                lcy = ly + height / 2.0
                dia_connectors.append(LineObject(x, y, x, lcy,
                                            c.LABEL_CONNECTOR_WIDTH,
                                            c.LABEL_CONNECTOR_COLOR))
                dia_traffic_labels.append(TextObject(data, x, ly, color,
                                                      c.LABEL_FONT_SIZE))

        return (self.convert_objects(dia_connectors),
               self.convert_objects(dia_traffic_labels))

    #####################################################

    def get_id(self):
        self.id_counter += 1
        return str(self.id_counter)

#########################################################################
#########################################################################

if __name__ == "__main__":
    DiaConvertor().convert()
