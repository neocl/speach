# -*- coding: utf-8 -*-

"""
ELAN module - manipulating ELAN transcript files (\*.eaf, \*.pfsx)
"""

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import uuid
from datetime import datetime
from io import StringIO
import logging
from collections import OrderedDict
from collections import defaultdict as dd
from typing import List, Tuple

try:
    import defusedxml.ElementTree as best_parser
    import xml.etree.ElementTree as etree
    SAFE_MODE = True
    XML_PARSER = 'default'
except ModuleNotFoundError:
    SAFE_MODE = False
    try:
        # prioritise lxml if it is available
        from lxml import etree
        best_parser = etree
        XML_PARSER = 'lxml'
    except ImportError:
        import xml.etree.ElementTree as etree
        best_parser = etree
        XML_PARSER = 'default'
from xml.dom.minidom import parseString as minidom_parseString

import warnings

from chirptext import DataObject
from chirptext import chio

from .__version__ import __issue__
from .vtt import sec2ts, ts2sec
from .media import cut
from .data import ELAN_BLANK_FILE


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def ts2msec(ts):
    """ Convert ELAN timestamp string to milliseconds """
    return ts2sec(ts) * 1000


def msec2ts(value):
    """ Convert milliseconds to ELAN timestamp string """
    return sec2ts(value / 1000)


def _parse_xml(source):
    """ [Internal] Parse an XML stream """
    if XML_PARSER == 'lxml':
        return best_parser.parse(source).getroot()
    else:
        return best_parser.fromstring(source.read())


def _xml_tostring(root, encoding='utf-8',
                  default_namespace=None,
                  method="xml",
                  pretty_print=False,
                  short_empty_elements=True, *args, **kwargs):
    """ [Internal] Generate XML content as bytes """
    if XML_PARSER == 'lxml':
        # short_empty_elements is not supported
        return etree.tostring(root, encoding=encoding,
                              pretty_print=pretty_print,
                              *args, **kwargs)
    else:
        # does not support pretty_print
        _content = etree.tostring(root,
                                  encoding=encoding, method=method,
                                  short_empty_elements=short_empty_elements,
                                  *args, **kwargs)
        if pretty_print:
            dom = minidom_parseString(_content.decode(encoding))
            _content = dom.toprettyxml(encoding=encoding)
        return _content


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

class Language(DataObject):
    """ Language information """

    def __init__(self, xml_node=None, **kwargs):
        super().__init__(**kwargs)
        self.__xml_node = xml_node
        if xml_node is not None:
            self.__ID = xml_node.get('LANG_ID', default="")
            self.__lang_def = xml_node.get('LANG_DEF', default="")
            self.__label = xml_node.get('LANG_LABEL', default="")

    @property
    def ID(self):
        return self.__ID

    @property
    def lang_def(self):
        """ URL of the language """
        return self.__lang_def

    @property
    def label(self):
        """ Label of the language """
        return self.__label

    def __repr__(self):
        return f"{self.lang_def}#{self.label}"

    def __str__(self):
        return self.label

    @classmethod
    def from_xml(cls, xml_node, **kwargs):
        return Language(xml_node=xml_node, **kwargs)


class License(DataObject):
    """ License information """

    def __init__(self, xml_node=None, **kwargs):
        super().__init__(**kwargs)
        self.__xml_node = xml_node
        if xml_node is not None:
            self.__url = xml_node.get('LICENSE_URL', default="")

    @property
    def url(self):
        return self.__url

    def __repr__(self):
        if not self.url:
            return "License()"
        else:
            return f"License(url={repr(self.url)})"

    def __str__(self):
        return self.url

    @classmethod
    def from_xml(cls, xml_node, **kwargs):
        return License(xml_node=xml_node, **kwargs)


class ExternalRef(DataObject):
    """ An external resource (normally an external controlled vocabulary)

    <EXTERNAL_REF EXT_REF_ID="er1" TYPE="ecv" VALUE="file:/home/tuananh/Documents/ELAN/fables_cv.ecv"/>
    """

    def __init__(self, xml_node=None, **kwargs):
        super().__init__(**kwargs)
        self.__xml_node = xml_node
        if xml_node is not None:
            self.__ref_id = xml_node.get('EXT_REF_ID')
            self.__type = xml_node.get('TYPE')
            self.__value = xml_node.get('VALUE')

    @property
    def ref_id(self):
        """ Reference ID of this external resource """
        return self.__ref_id

    @property
    def type(self):
        """ Type of external resource 
        
        - ecv: External controlled vocabulary
        """
        return self.__type

    @property
    def value(self):
        """ URL to external resource """
        return self.__value

    def __repr__(self):
        return f"{self.type}/{self.ref_id}/{self.value}"

    def __str__(self):
        return self.value

    @classmethod
    def from_xml(cls, xml_node, **kwargs):
        return ExternalRef(xml_node=xml_node, **kwargs)


class TimeSlot:

    def __init__(self, xml_node=None, ID=None, value=None, *args, **kwargs):
        """ An ELAN timestamp
        """
        self.__xml_node = xml_node
        self.__ID = xml_node.get('TIME_SLOT_ID') if xml_node is not None else ID
        _v = xml_node.get('TIME_VALUE') if xml_node is not None else value
        self.__value = int(_v) if _v else None

    @property
    def ID(self):
        return self.__ID

    @property
    def value(self):
        """ TimeSlot value (in milliseconds) """
        return self.__value

    @value.setter
    def value(self, value):
        # TODO: update DOM to be able to save
        if isinstance(value, float):
            value = round(value)
        self.__value = value

    @property
    def ts(self) -> str:
        """ Return timestamp of this annotation in vtt format (00:01:02.345)

        :return: An empty string will be returned if TimeSlot value is None
        """
        return sec2ts(self.sec) if self.value is not None else ''

    @property
    def sec(self):
        """ Get TimeSlot value in seconds """
        return self.value / 1000 if self.value is not None else None

    def __lt__(self, other):
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return False
        elif self.value is None:
            return True
        return self.value < other.value if isinstance(other, TimeSlot) else self.value < other

    def __eq__(self, other):
        if other is None:
            return False
        elif isinstance(other, TimeSlot):
            return other.value == self.value
        return self.value == other.value if isinstance(other, TimeSlot) else self.value == other

    def __gt__(self, other):
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return True
        elif self.value is None:
            return False
        return self.value > other.value if isinstance(other, TimeSlot) else self.value > other

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __add__(self, other):
        sv = self.value if self.value is not None else 0
        if other is None:
            ov = 0
        elif isinstance(other, TimeSlot):
            ov = other.value if other.value is not None else 0
        else:
            ov = other
        return sv + ov

    def __sub__(self, other):
        sv = self.value if self.value is not None else 0
        if other is None:
            ov = 0
        elif isinstance(other, TimeSlot):
            ov = other.value if other.value is not None else 0
        else:
            ov = other
        return sv - ov

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f"TimeSlot(value={repr(self.value)})"

    def __str__(self):
        val = self.ts
        return val if val else self.ID

    @staticmethod
    def from_ts(ts, ID=None):
        value = ts2sec(ts) * 1000
        return TimeSlot(ID=ID, value=value)


class Annotation(DataObject):
    """ An ELAN abstract annotation (for both alignable and non-alignable annotations)
    """

    def __init__(self, ID, value, cve_ref=None, xml_node=None, **kwargs):
        super().__init__(**kwargs)
        self.__ID = ID
        self.__value = value
        self.__cve_ref = cve_ref
        self.__xml_node = xml_node

    @property
    def ID(self):
        return self.__ID

    @property
    def value(self) -> str:
        """ Annotated text value.

        It is possible to change value of an annotation

        >>> ann.value
        'Old value'
        >>> ann.value = "New value"
        >>> ann.value
        'New value'
        """
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value
        if self.__xml_node is not None:
            self.__xml_node.find("ANNOTATION_VALUE").text = str(value) if value else ''

    @property
    def cve_ref(self):
        return self.__cve_ref

    @property
    def text(self):
        """ An alias to ELANAnnotation.value """
        return self.value

    @text.setter
    def text(self, value):
        self.value = value

    def __repr__(self):
        return f"Annotation(ID={repr(self.ID)},value={repr(self.value)})"

    def __str__(self):
        return str(self.value)


class TimeAnnotation(Annotation):
    """ An ELAN time-alignable annotation
    """

    def __init__(self, ID, from_ts, to_ts, value, xml_node=None, **kwargs):
        super().__init__(ID, value, xml_node=xml_node, **kwargs)
        self.__from_ts = from_ts
        self.__to_ts = to_ts

    @property
    def from_ts(self) -> TimeSlot:
        """ Start timestamp of this annotation
        """
        return self.__from_ts

    @property
    def to_ts(self) -> TimeSlot:
        """ End timestamp of this annotation
        """
        return self.__to_ts

    @property
    def duration(self) -> float:
        """ Duration of this annotation (in seconds) """
        return (self.to_ts.sec or 0) - (self.from_ts.sec or 0)

    def overlap(self, other):
        """ Calculate overlap score between two time annotations
        Score = 0 means adjacent, score > 0 means overlapped, score < 0 means no overlap (the distance between the two)
        """
        return min(self.to_ts, other.to_ts) - max(self.from_ts, other.from_ts)

    def __repr__(self):
        return '[{} -- {}] {}'.format(self.from_ts, self.to_ts, self.value)

    def __str__(self):
        return str(self.value)


class RefAnnotation(Annotation):
    """ An ELAN ref annotation (not time alignable)
    """

    def __init__(self, ID, ref_id, previous, value, xml_node=None, **kwargs):
        super().__init__(ID, value, xml_node=xml_node, **kwargs)
        self.__ref = None
        self.__ref_id = ref_id  # ANNOTATION_REF
        self.previous = previous  # PREVIOUS_ANNOTATION

    @property
    def ref(self):
        return self.__ref

    @property
    def from_ts(self):
        return self.__ref.from_ts if self.__ref is not None else None

    @property
    def to_ts(self):
        return self.__ref.to_ts if self.__ref is not None else None

    def resolve(self, elan_doc):
        _ref_ann = elan_doc.annotation(self.__ref_id)
        if _ref_ann is None:
            raise ValueError(f"Missing annotation ID ({self.__ref_id}) -- Corrupted ELAN file")
        else:
            self.__ref = _ref_ann

    @property
    def ref_id(self):
        """ ID of the referenced annotation """
        return self.__ref_id


class LinguisticType(DataObject):
    """ Linguistic Tier Type
    """

    def __init__(self, xml_node=None):
        self.__xml_node = xml_node
        data = {k.lower(): v for k, v in xml_node.attrib.items()} if xml_node is not None else {}
        if "time_alignable" in data:
            data["time_alignable"] = data["time_alignable"] == "true"
        super().__init__(**data)
        self.vocab = None
        self.tiers = []

    @property
    def ID(self):
        return self.linguistic_type_id

    @property
    def stereotype(self):
        return self.constraints

    @stereotype.setter
    def stereotype(self, value):
        self.constraints = value

    def __repr__(self):
        return f"LinguisticType(ID={repr(self.ID)}, constraints={repr(self.constraints)})"

    def __str__(self):
        return self.ID


class Tier(DataObject):
    """ Represents an ELAN annotation tier """

    NONE = "None"
    TIME_SUB = "Time_Subdivision"
    SYM_SUB = "Symbolic_Subdivision"
    INCL = "Included_In"
    SYM_ASSOC = "Symbolic_Association"

    def __init__(self, doc=None, xml_node=None, **kwargs):
        """
        ELAN Tier Model which contains annotation objects
        """
        super().__init__(**kwargs)
        self.doc = doc
        self.children = []
        self.__annotations = []
        self.__xml_node = xml_node
        if xml_node is not None:
            self.__type_ref_id = xml_node.get('LINGUISTIC_TYPE_REF')
            self.__participant = xml_node.get('PARTICIPANT', '')
            self.__ID = xml_node.get('TIER_ID')
            self.__parent_ref = xml_node.get('PARENT_REF') if xml_node.get('PARENT_REF') else None  # ID of parent tier
            self.__default_locale = xml_node.get('DEFAULT_LOCALE')
            # add child annotations
            for elem in xml_node:
                self._add_annotation_xml(elem)

    @property
    def ID(self):
        return self.__ID

    @ID.setter
    def ID(self, value):
        if value == self.ID:
            return
        elif not value:
            raise ValueError("Tier ID cannot be empty")
        else:
            self.__ID = value
            if self.doc is not None:
                self.doc._reset_tier_map()
            if self.__xml_node is not None:
                self.__xml_node.set('TIER_ID', value)
                for child in self.children:
                    child.parent_ref = value

    @property
    def name(self):
        """ An alias to tier's ID """
        return self.ID

    @name.setter
    def name(self, value):
        self.ID = value

    @property
    def annotations(self):
        return self.__annotations

    @property
    def time_alignable(self):
        """ Check if this tier contains time alignable annotations """
        return self.linguistic_type and self.linguistic_type.time_alignable

    @property
    def participant(self):
        return self.__participant

    @participant.setter
    def participant(self, value):
        if self.__xml_node is not None:
            self.__xml_node.set('PARTICIPANT', value)
        else:
            logging.getLogger(__name__).warning(
                f"Could not update participant, DOM node is missing for tier {self.name}")
        self.__participant = value

    @property
    def parent(self):
        return self.doc[self.__parent_ref] if self.__parent_ref and self.doc is not None else None

    @property
    def parent_ref(self):
        """ ID of the parent tier. Return None if this is a root tier """
        return self.__parent_ref

    @parent_ref.setter
    def parent_ref(self, value):
        if self.__xml_node is not None:
            self.__xml_node.set('PARENT_REF', value)
        self.__parent_ref = value

    @property
    def type_ref_id(self):
        """ ID of the tier type ref """
        return self.__type_ref_id

    @property
    def type_ref(self) -> LinguisticType:
        """ Tier type object """
        return self.doc.get_linguistic_type(self.__type_ref_id)

    @property
    def linguistic_type(self) -> LinguisticType:
        """ Linguistic type object of this Tier (alias of type_ref """
        return self.type_ref

    @property
    def stereotype(self):
        return self.type_ref.constraints

    @property
    def vocab(self):
        if self.type_ref is not None and self.type_ref.vocab is not None:
            return self.type_ref.vocab
        else:
            return None

    @property
    def _type_ref_id(self):
        return self.__type_ref_id

    def __getitem__(self, key):
        return self.annotations[key]

    def __iter__(self):
        return iter(self.annotations)

    def get_child(self, ID):
        """ Get a child tier by ID, return None if nothing is found """
        for child in self.children:
            if child.ID == ID:
                return child
        return None

    def filter(self, from_ts=None, to_ts=None):
        """ Filter utterances by from_ts or to_ts or both
        If this tier is not a time-based tier everything will be returned
        """
        for ann in self.annotations:
            if from_ts is not None and ann.from_ts is not None and ann.from_ts < from_ts:
                continue
            elif to_ts is not None and ann.to_ts is not None and ann.from_ts > to_ts:
                continue
            else:
                yield ann

    def __len__(self):
        return len(self.annotations)

    def __repr__(self):
        return 'Tier(ID={})'.format(self.ID)

    def __str__(self):
        return f'Tier(ID={repr(self.ID)}),type={repr(self.linguistic_type)})'.format(self.ID, self.linguistic_type)

    def _validate_value(self, value):
        """ [Internal] """
        if self.vocab is not None:
            if not self.vocab.has_value(value):
                raise ValueError(f"{repr(value)} is not a valid value for tier {self.name}")
            else:
                return self.vocab.by_value(value)
        return None

    def new_annotation(self, value, from_ts=None, to_ts=None, ann_ref_id=None, values=None, timeslots=None, check_cv=True):
        """ Create new annotation(s) in this current tier
        ELAN provides 5 different tier stereotypes.

        To create a new standard annotation (in a tier with no constraints),
        a text value and a pair of from-to timestamp must be provided.

        >>> from speach import elan
        >>> eaf = elan.create()  # create a new ELAN transcript
        >>> # create a new utterance tier
        >>> tier = eaf.new_tier('Person1 (Utterance)')
        >>> # create a new annotation between 00:00:01.000 and 00:00:02.000
        >>> a1 = tier.new_annotation('Xin chào', 1000, 2000)

        Included-In tiers

        >>> eaf.new_linguistic_type('Phoneme', 'Included_In')
        >>> tp = eaf.new_tier('Person1 (Phoneme)', 'Phoneme', 'Person1 (Utterance)')
        >>> # string-based timestamps can also be used with the helper function elan.ts2msec()
        >>> tt.new_annotation('ch', elan.ts2msec("00:00:01.500"),
                              elan.ts2msec("00:00:01.600"),
                              ann_ref_id=a1.ID)
        
        Annotations in Symbolic-Associtation tiers:

        >>> eaf.new_linguistic_type('Translate', 'Symbolic_Association')
        >>> tt = eaf.new_tier('Person1 (Translate)', 'Translate', 'Person1 (Utterance)')
        >>> tt.new_annotation('Hello', ann_ref_id=a1.ID)

        Symbolic-Subdivision tiers:

        >>> eaf.new_linguistic_type('Tokens', 'Symbolic_Subdivision')
        >>> tto = eaf.new_tier('Person1 (Tokens)', 'Tokens', 'Person1 (Utterance)')
        >>> # extra annotations can be provided with the argument values
        >>> tto.new_annotation('Xin', values=['chào'], ann_ref_id=a1.ID)
        >>> # alternative method (set value to None and provide everything with values)
        >>> tto.new_annotation(None, values=['Xin', 'chào'], ann_ref_id=a1.ID)
        """
        if self.stereotype in (None, 'Included_In'):
            if from_ts is None:
                raise ValueError("From timestamp cannot be empty")
            if to_ts is None:
                raise ValueError("To timestamp cannot be empty")
        else:
            if from_ts is not None:
                raise ValueError(f"{self.linguistic_type} is not time-alignable (from_ts was provided)")
            if to_ts is not None:
                raise ValueError(f"{self.linguistic_type} is not time-alignable (to_ts was provided)")
        ann_ref = None
        if ann_ref_id:
            ann_ref = self.doc.annotation(ann_ref_id)
            if ann_ref is None:
                raise ValueError(f"Referent annotation ID {repr(ann_ref_id)} could not be found")
        if self.type_ref.constraints is not None and ann_ref is None:
            raise ValueError("Dependent tiers require a referent annotation to create new annotations")
        if not self.stereotype or self.stereotype == 'Included_In':
            if self.stereotype == 'Included_In':
                if ann_ref.from_ts > float(from_ts) or ann_ref.to_ts < float(to_ts):
                    raise ValueError("New annotation must be contained within the referent annotation")
            cve_ref = self._validate_value(value)
            ann_node = best_parser.XML(""" <ANNOTATION>
            <ALIGNABLE_ANNOTATION ANNOTATION_ID=""
            TIME_SLOT_REF1="" TIME_SLOT_REF2="">
            <ANNOTATION_VALUE></ANNOTATION_VALUE>
            </ALIGNABLE_ANNOTATION>
            </ANNOTATION>""")
            ann_info = ann_node.find("ALIGNABLE_ANNOTATION")
            if cve_ref is not None:
                ann_info.set('CVE_REF', cve_ref.ID)
            ann_info.set('TIME_SLOT_REF1', self.doc.new_timeslot(from_ts).ID)
            ann_info.set('TIME_SLOT_REF2', self.doc.new_timeslot(to_ts).ID)
            ann_info.find('ANNOTATION_VALUE').text = value
            ann_info.set('ANNOTATION_ID', self.doc.new_annotation_id())
            self.__xml_node.append(ann_node)
            ann_obj = self._add_annotation_xml(ann_node)
            self.doc._register_ann(ann_obj)
            return ann_obj
        elif self.stereotype in ('Time_Subdivision', 'Symbolic_Subdivision'):
            _values = [value] if value is not None else []
            if values:
                _values.extend(values)
            for v in _values:
                self._validate_value(v)
            if self.stereotype == 'Symbolic_Subdivision':
                last_id = None
                previous_ids = set()
                for ann in self:
                    if ann.ref.ID == ann_ref_id:
                        if ann.previous and ann.previous.ID not in previous_ids:
                            raise ValueError("Corrupted Time_Subdivision tier")
                        last_id = ann.ID
                        previous_ids.add(ann.ID)
                # create new nodes
                ann_objs = []
                for v in _values:
                    ann_node = best_parser.XML("""<ANNOTATION>
                    <REF_ANNOTATION ANNOTATION_ID="" ANNOTATION_REF="">
                    <ANNOTATION_VALUE></ANNOTATION_VALUE>
                    </REF_ANNOTATION>
                    </ANNOTATION>""")
                    ann_info = ann_node.find('REF_ANNOTATION')
                    cve_ref = self._validate_value(v)
                    if cve_ref is not None:
                        ann_info.set('CVE_REF', cve_ref.ID)
                    ann_info.set('ANNOTATION_REF', ann_ref.ID)
                    ann_info.find('ANNOTATION_VALUE').text = v
                    _nid = self.doc.new_annotation_id()
                    ann_info.set('ANNOTATION_ID', _nid)
                    if last_id is not None:
                        ann_info.set('PREVIOUS_ANNOTATION', last_id)
                    last_id = _nid
                    self.__xml_node.append(ann_node)
                    ann_obj = self._add_annotation_xml(ann_node)
                    ann_obj.resolve(self.doc)
                    self.doc._register_ann(ann_obj)
                    ann_objs.append(ann_obj)
                return ann_objs
            else:
                # Time_Subdivision
                if len(_values) > 1 and (not timeslots or len(timeslots) != len(_values) - 1):
                    raise ValueError("There is a mismatch between the number of annotation values and the number of provided timeslots")
                for t in timeslots:
                    if t is None or t <= ann_ref.from_ts or t >= ann_ref.to_ts:
                        raise ValueError("Child annotations must be within the time range of referent annotation")
                ts_objs = [ann_ref.from_ts.ID]
                if len(_values) > 1:
                    for t in sorted(timeslots):
                        ts_obj = self.doc.new_timeslot(t)
                        ts_objs.append(ts_obj.ID)
                ts_objs.append(ann_ref.to_ts.ID)
                ann_objs = []
                for idx, v in enumerate(_values):
                    ann_node = best_parser.XML("""<ANNOTATION>
                    <ALIGNABLE_ANNOTATION ANNOTATION_ID=""
                    TIME_SLOT_REF1="" TIME_SLOT_REF2="">
                    <ANNOTATION_VALUE></ANNOTATION_VALUE>
                    </ALIGNABLE_ANNOTATION>
                    </ANNOTATION>""")
                    ann_info = ann_node.find('ALIGNABLE_ANNOTATION')
                    cve_ref = self._validate_value(v)
                    if cve_ref is not None:
                        ann_info.set('CVE_REF', cve_ref.ID)
                    ann_info.find('ANNOTATION_VALUE').text = v
                    ann_info.set('TIME_SLOT_REF1', ts_objs[idx])
                    ann_info.set('TIME_SLOT_REF2', ts_objs[idx + 1])
                    ann_info.set('ANNOTATION_ID', self.doc.new_annotation_id())
                    self.__xml_node.append(ann_node)
                    ann_obj = self._add_annotation_xml(ann_node)
                    self.doc._register_ann(ann_obj)
                    ann_objs.append(ann_obj)
                return ann_objs
                # create new annotation    
        elif self.stereotype == 'Symbolic_Association':
            cve_ref = self._validate_value(value)
            ann_node = best_parser.XML("""        <ANNOTATION>
            <REF_ANNOTATION ANNOTATION_ID="" ANNOTATION_REF="">
            <ANNOTATION_VALUE></ANNOTATION_VALUE>
            </REF_ANNOTATION>
            </ANNOTATION>""")
            ann_info = ann_node.find("REF_ANNOTATION")
            ann_info.set('ANNOTATION_REF', ann_ref_id)
            if cve_ref is not None:
                ann_info.set('CVE_REF', cve_ref.ID)
            ann_info.find('ANNOTATION_VALUE').text = value
            ann_info.set('ANNOTATION_ID', self.doc.new_annotation_id())
            self.__xml_node.append(ann_node)
            ann_obj = self._add_annotation_xml(ann_node)
            self.doc._register_ann(ann_obj)
            return ann_obj
        else:
            raise NotImplementedError(f"Adding new annotation for {self.stereotype} tiers is yet to be implemented")

    def add_alignable_annotation_xml(self, alignable):
        ann_id = alignable.get('ANNOTATION_ID')
        from_ts_id = alignable.get('TIME_SLOT_REF1')
        cve_ref = alignable.get('CVE_REF')  # controlled vocab ref
        if from_ts_id not in self.doc.time_order:
            raise ValueError("Time slot ID not found ({})".format(from_ts_id))
        else:
            from_ts = self.doc.time_order[from_ts_id]
        to_ts_id = alignable.get('TIME_SLOT_REF2')
        if to_ts_id not in self.doc.time_order:
            raise ValueError("Time slot ID not found ({})".format(to_ts_id))
        else:
            to_ts = self.doc.time_order[to_ts_id]
        # [TODO] ensure that from_ts < to_ts
        value_node = alignable.find('ANNOTATION_VALUE')
        if value_node is None:
            raise ValueError("ALIGNABLE_ANNOTATION node must contain an ANNOTATION_VALUE node")
        else:
            value = value_node.text if value_node.text else ''
            anno = TimeAnnotation(ann_id, from_ts, to_ts, value, cve_ref=cve_ref, xml_node=alignable)
            self.annotations.append(anno)
            return anno

    def add_ref_annotation_xml(self, ref_node):
        ann_id = ref_node.get('ANNOTATION_ID')
        ref = ref_node.get('ANNOTATION_REF')
        previous = ref_node.get('PREVIOUS_ANNOTATION')
        cve_ref = ref_node.get('CVE_REF')  # controlled vocab ref
        value_node = ref_node.find('ANNOTATION_VALUE')
        if value_node is None:
            raise ValueError("REF_ANNOTATION node must contain an ANNOTATION_VALUE node")
        else:
            value = value_node.text if value_node.text else ''
            anno = RefAnnotation(ann_id, ref, previous, value, cve_ref=cve_ref, xml_node=ref_node)
            self.annotations.append(anno)
            return anno

    def _add_annotation_xml(self, annotation_node) -> Annotation:
        """ [Internal function] Create an annotation from a node

        General users should not use this function.
        """
        alignable = annotation_node.find('ALIGNABLE_ANNOTATION')
        if alignable is not None:
            return self.add_alignable_annotation_xml(alignable)
        else:
            ref_ann_node = annotation_node.find('REF_ANNOTATION')
            if ref_ann_node is not None:
                return self.add_ref_annotation_xml(ref_ann_node)
            else:
                raise ValueError("ANNOTATION node must not be empty")


class CVEntry(DataObject):
    """ A controlled vocabulary entry """

    def __init__(self, xml_node=None, **kwargs):
        super().__init__(**kwargs)
        self.__xml_node = xml_node
        if xml_node is not None:
            self.__ID = xml_node.get('CVE_ID')
            self.__entry_value_node = xml_node.find('CVE_VALUE')
            self.__lang_ref = self.__entry_value_node.get('LANG_REF')
            self.__value = self.__entry_value_node.text
            self.__description = self.__entry_value_node.get('DESCRIPTION')
        else:
            self.__ID = ''
            self.__xml_node = None
            self.__entry_value_node = None
            self.__lang_ref = 'und'
            self.__value = ''
            self.__description = ''

    @property
    def _xml_node(self):
        return self.__xml_node

    @property
    def ID(self):
        return self.__ID

    @property
    def lang_ref(self):
        return self.__lang_ref

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if not value:
            raise ValueError("CV entry value cannot be blank")
        self.__value = value
        if self.__entry_value_node is not None:
            self.__entry_value_node.text = str(value) if value else ''

    @property
    def description(self):
        """ Description of this controlled vocabulary entry """
        return self.__description

    @description.setter
    def description(self, value):
        self.__description = value
        if self.__entry_value_node is not None:
            self.__entry_value_node.set('DESCRIPTION', str(value) if value else '')

    def __repr__(self):
        return f'CVEntry(ID={repr(self.ID)}, lang_ref={repr(self.lang_ref)}, value={repr(self.value)})'

    def __str__(self):
        return self.value


class ControlledVocab(DataObject):
    """ ELAN Controlled Vocabulary """

    def __init__(self, xml_node=None, **kwargs):
        super().__init__(**kwargs)
        self.__entries = []
        self.__entries_map = dict()
        self.__values_map = dict()  # values are also uniquq
        self.__tiers = []
        self.__xml_node = xml_node
        if xml_node is not None:
            self.__ID = xml_node.get('CV_ID')
            self.__entries = []
            for child in xml_node:
                if child.tag == 'DESCRIPTION':
                    self.__description_node = child
                    self.__description = child.text
                    self.__lang_ref = child.get('LANG_REF')
                elif child.tag == 'CV_ENTRY_ML':
                    cv_entry = CVEntry(child)
                    self._add_child(cv_entry)

    def _add_child(self, child, prev_entry=None, next_entry=None, **kwargs):
        if prev_entry is not None:
            self.__entries.insert(self.__entries.index(prev_entry) + 1, child)
        elif next_entry is not None:
            self.__entries.insert(self.__entries.index(next_entry), child)
        else:
            self.__entries.append(child)
        self.__entries_map[child.ID] = child
        self.__values_map[child.value] = child

    def new_entry(self, ID, value, description='', lang_ref=None, prev_entry=None, next_entry=None, **kwargs):
        if lang_ref is None:
            if self.__lang_ref:
                lang_ref = self.__lang_ref
            else:
                lang_ref = 'und'
        entry_node = etree.Element('CV_ENTRY_ML')
        if not value:
            raise ValueError("CV Entry value cannot be blank")
        if value in self.__values_map:
            raise ValueError("CV Entry {repr()} already exists.")
        if ID is not None and ID in self.__entries_map:
            raise ValueError("CV entry ID {repr(ID)} already exists.")
        if ID is None:
            ID = f'cveid_{uuid.uuid4()}'
        entry_node.set('CVE_ID', ID)
        node_value = etree.SubElement(entry_node, 'CVE_VALUE')
        if description:
            node_value.set('DESCRIPTION', description)
        node_value.set('LANG_REF', lang_ref)
        node_value.text = value
        # add entry node to vocab node
        idx = None
        if self.__xml_node is not None:
            if prev_entry is not None:
                idx = list(self.__xml_node).index(prev_entry._xml_node) + 1
            elif next_entry is not None:
                idx = list(self.__xml_node).index(next_entry._xml_node)
            # add child
            if idx is not None:
                self.__xml_node.insert(idx, entry_node)
            else:
                # append to the end of the list
                self.__xml_node.append(entry_node)
        cv_entry = CVEntry(entry_node)
        self._add_child(cv_entry, prev_entry=prev_entry, next_entry=next_entry)
        return cv_entry

    def remove(self, child):
        if self.__xml_node is not None  and child._xml_node is not None:
            self.__xml_node.remove(child._xml_node)
        if child in self.__entries:
            self.__entries.remove(child)
        if child.ID in self.__entries_map:
            self.__entries_map.pop(child.ID)
        if child.value in self.__values_map:
            self.__values_map.pop(child.value)

    def __contains__(self, item):
        return item in self.__entries_map

    def __getitem__(self, key):
        """ Get a CV entry object by its unique text value """
        return self.by_value(key)

    def has_id(self, key):
        return key in self.__entries_map

    def has_value(self, key):
        return key in self.__values_map

    def by_value(self, key):
        """ Get a CV entry object by its unique text value """
        return self.__values_map[key]

    def by_id(self, key):
        """ Get a CV entry object by its cveid (i.e. randomly generated UUID)
        """
        return self.__entries_map[key]

    def __iter__(self):
        return iter(self.__entries)

    def __repr__(self):
        if self.description:
            return f'Vocab(ID={repr(self.ID)}, description={repr(self.description)})'
        else:
            return f'Vocab(ID={repr(self.ID)})'

    def __str__(self):
        return repr(self)

    @property
    def ID(self):
        return self.__ID

    @property
    def description(self):
        return self.__description

    @property
    def lang_ref(self):
        return self.__lang_ref

    @property
    def tiers(self):
        return self.__tiers


class ExternalControlledVocabResource(ControlledVocab):

    def __init__(self, xml_node=None, path=None, **kwargs):
        super().__init__(xml_node=None, **kwargs)
        self.__xml_node = xml_node
        self.__path = path
        self.__languages = []
        # self.__vocabs = []
        if self.__xml_node is not None:
            for node in self.__xml_node:
                if node.tag == 'LANGUAGE':
                    self.__languages.append(Language.from_xml(node))
                elif node.tag == 'CONTROLLED_VOCABULARY':
                    self._add_child(ControlledVocab(node))
                else:
                    logging.getLogger(__name__).warning(f"Unknown tag name ({node.tag}) was found in current ECV stream")

    @property
    def vocabs(self) -> Tuple[ControlledVocab]:
        """ A tuple of all controlled vocabulary lists in this ECV stream """
        return tuple(self)

    @property
    def languages(self) -> Tuple[Language]:
        """ A tuple of all language in this ECV stream """
        return tuple(self.__languages)

    @property
    def author(self):
        return self.__xml_node.get('AUTHOR') if self.__xml_node is not None else None

    @author.setter
    def author(self, value):
        if self.__xml_node is not None:
            self.__xml_node.set('AUTHOR', value)
        else:
            raise Exception("Editing empty ExternalControlledVocabResource is yet to be implemented")

    @property
    def date(self):
        return self.__xml_node.get('DATE') if self.__xml_node is not None else None

    @date.setter
    def date(self, value):
        if self.__xml_node is not None:
            if isinstance(value, datetime):
                value = datetime.astimezone().isoformat()
            self.__xml_node.set('DATE', value)
        else:
            raise Exception("Editing empty ExternalControlledVocabResource is yet to be implemented")

    @property
    def version(self):
        return self.__xml_node.get('VERSION') if self.__xml_node is not None else None

    @property
    def schema_location(self):
        if self.__xml_node is not None:
            return self.__xml_node.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation')
        else:
            return None

    @classmethod
    def read_ecv(cls, ecv_path, encoding='utf-8', *args, **kwargs):
        """ Read an external controlled vocabulary file

        >>> from speach import elan
        >>> ecv = elan.read_ecv("my_controlled_vocab_file.ecv")

        :param ecv_path: Path to an existing ECV file
        :type ecv_path: str or Path-like object
        :param encoding: Encoding of the eaf stream, defaulted to UTF-8
        :type encoding: str
        :rtype: speach.elan.ExternalControlledVocabResource
        """
        ecv_path = str(ecv_path)
        if ecv_path.startswith("~"):
            ecv_path = os.path.expanduser(ecv_path)
        with chio.open(ecv_path, encoding=encoding, *args, **kwargs) as ecv_stream:
            _doc = cls.parse_stream(ecv_stream, path=ecv_path)
            return _doc

    @classmethod
    def parse_stream(cls, ecv_stream, *args, **kwargs):
        """ Parse an external controlled vocab input stream

        >>> with open('test/data/test.ecv').read() as ecv_stream:
        >>>    ecv = elan.parse_ecv_stream(ecv_stream)

        :param ecv_stream: ECV text input stream
        :rtype: speach.elan.ExternalControlledVocabResource
        """
        _root = _parse_xml(ecv_stream)
        ecv = ExternalControlledVocabResource(xml_node=_root, **kwargs)
        return ecv

    @classmethod
    def parse_string(cls, ecv_string, *args, **kwargs):
        """ Parse ECV content in a string

        >>> with open('test/data/test.ecv').read() as ecv_stream:
        >>>    ecv_content = ecv_stream.read()
        >>>    ecv = elan.parse_ecv_string(ecv_content)

        :param eaf_string: ECV content stored in a string
        :type eaf_string: str
        :rtype: speach.elan.ExternalControlledVocabResource
        """
        return cls.parse_ecv_stream(StringIO(ecv_string), *args, **kwargs)


class Constraint(DataObject):
    """ ELAN Tier Constraints """

    def __init__(self, xml_node=None):
        super().__init__()
        self.__xml_node = xml_node
        if xml_node is not None:
            self.__description = xml_node.get('DESCRIPTION')
            self.__stereotype = xml_node.get('STEREOTYPE')

    @property
    def description(self):
        return self.__description

    @property
    def stereotype(self):
        return self.__stereotype

    def __repr__(self):
        return f"(Constraint {repr(self.stereotype)})"

    def __str__(self):
        return self.stereotype


class Locale(DataObject):
    """ Locale information """

    def __init__(self, xml_node=None, **kwargs):
        super().__init__()
        self.__xml_node = xml_node
        self.__country_code = kwargs.get("country_code")
        self.__language_code = kwargs.get("language_code")
        if xml_node is not None:
            self.__country_code = xml_node.get('COUNTRY_CODE')
            self.__language_code = xml_node.get('LANGUAGE_CODE', default="en")

    @property
    def country_code(self):
        return self.__country_code

    @property
    def language_code(self):
        return self.__language_code

    def __repr__(self):
        if self.__country_code:
            return f"Locale(country_code={repr(self.__country_code)}, language_code={repr(self.__language_code)})"
        else:
            return f"Locale(language_code={repr(self.__language_code)})"

    def __str__(self):
        return self.__language_code


class Doc(DataObject):
    """ This class represents an ELAN file (\*.eaf)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.properties = OrderedDict()
        self.time_order = OrderedDict()
        self.__tiers = []
        self.__tier_map = OrderedDict()  # internal - map tierIDs to tier objects
        self.__ann_map = dict()
        self.__linguistic_types = []
        self.__constraints = []
        self.__vocabs = []
        self.__licenses = []
        self.__external_refs = []
        self.__languages = []
        self.__locale = None
        self.path = None
        self.__xml_root = None
        self.__xml_header_node = None
        self.__xml_time_order_node = None
        self.__date = None
        self.__author = ""

    @property
    def author(self):
        return self.__author

    @author.setter
    def author(self, value):
        self.__author = value
        self.__xml_root.set('AUTHOR', value)

    @property
    def date(self):
        return self.__date

    @date.setter
    def date(self, value):
        if isinstance(value, datetime):
            value = value.astimezone().isoformat()
        self.__date = value
        self.__xml_root.set('DATE', value)

    def media_path(self):
        """ Try to determine the best path to source media file """
        mpath = self.relative_media_url
        if mpath and os.path.isfile(mpath):
            return mpath
        # try to join with eaf path if possible
        if self.path and mpath:
            mpath = os.path.join(os.path.dirname(self.path), mpath)
            if os.path.isfile(mpath):
                return mpath
        # otherwise use media_url
        mpath = self.media_url
        if mpath.startswith("file://"):
            mpath = mpath[7:]
        return mpath

    @property
    def locale(self):
        return self.__locale

    def annotation(self, ID):
        """ Get annotation by ID """
        return self.__ann_map.get(ID, None)

    def new_annotation_id(self):
        seed = len(self.__ann_map) + 1
        while True:
            ann_id = f"a{seed}"
            if ann_id in self.__ann_map:
                seed += 1
            else:
                return ann_id

    @property
    def tier_map(self):
        if self.__tier_map is None:
            self.__tier_map = OrderedDict((t.ID, t) for t in self.__tiers)
        return self.__tier_map

    @property
    def licenses(self) -> Tuple[License]:
        """ Get all licenses """
        return tuple(self.__licenses)

    @property
    def external_refs(self) -> Tuple[ExternalRef]:
        """ Get all external references """
        return tuple(self.__external_refs)

    @property
    def languages(self) -> Tuple[Language]:
        """ Get all languages """
        return tuple(self.__languages)

    @property
    def roots(self) -> Tuple[Tier]:
        """ All root-level tiers in this ELAN doc """
        return tuple(t for t in self if not t.parent_ref)

    @property
    def vocabs(self) -> Tuple[ControlledVocab]:
        """ A tuple of all existing controlled vocabulary objects in this ELAN file """
        return tuple(self.__vocabs)

    @property
    def constraints(self) -> Tuple[Constraint]:
        """ A tuple of all existing constraints in this ELAN file """
        return tuple(self.__constraints)

    @property
    def linguistic_types(self) -> Tuple[LinguisticType]:
        """ A tuple of all existing linguistic types in this ELAN file """
        return tuple(self.__linguistic_types)

    def get_linguistic_type(self, type_id):
        """ Get linguistic type by ID. Return None if can not be found """
        for lingtype in self.__linguistic_types:
            if lingtype.linguistic_type_id == type_id:
                return lingtype
        return None

    def _find_last_element_index(self, tag_name):
        """ [Internal] """
        last_idx = None
        for idx, elem in enumerate(self.__xml_root):
            if elem.tag == tag_name:
                last_idx = idx
        return last_idx

    def new_linguistic_type(self, type_id, constraints=None, vocab_id=None):
        if constraints not in (None, "Time_Subdivision", "Included_In",
                               "Symbolic_Subdivision", "Symbolic_Association"):
            raise ValueError(f"{constraints} is not a supported tier stereotype")
        lt = self.get_linguistic_type(type_id)
        if lt is not None:
            raise ValueError(f"ID of linguistic type must be unique. type_id {type_id} already exists.")
        else:
            idx = self._find_last_element_index('LINGUISTIC_TYPE') + 1
            new_lt = best_parser.XML('''<LINGUISTIC_TYPE GRAPHIC_REFERENCES="false"
        LINGUISTIC_TYPE_ID="" TIME_ALIGNABLE="true"/>''')
            new_lt.set("LINGUISTIC_TYPE_ID", type_id)
            if constraints is not None:
                new_lt.set("CONSTRAINTS", constraints)
            if constraints in ("Symbolic_Subdivision", "Symbolic_Association"):
                new_lt.set("TIME_ALIGNABLE", "false")
            if vocab_id is not None:
                new_lt.set("CONTROLLED_VOCABULARY_REF", vocab_id)
            self.__xml_root.insert(idx, new_lt)
            lt_obj = self._add_linguistic_type_xml(new_lt)
            if vocab_id:
                lt_obj.vocab = self.get_vocab(vocab_id)

    def get_vocab(self, vocab_id):
        """ Get controlled vocab list by ID """
        for vocab in self.__vocabs:
            if vocab.ID == vocab_id:
                return vocab
        return None

    def new_vocab(self, vocab_id, language=None):
        if not vocab_id:
            raise ValueError("Controlled vocabulary ID cannot be blank")
        elif self.get_vocab(vocab_id) is not None:
            raise ValueError(f"Controlled vocabulary ID must be unique. {vocab_id} already exists.")
        vc_node = best_parser.XML(""" <CONTROLLED_VOCABULARY CV_ID="">
        <DESCRIPTION LANG_REF="eng"/>
        </CONTROLLED_VOCABULARY> """)
        vc_node.set("CV_ID", vocab_id)
        if language is not None:
            vc_node.find('DESCRIPTION').set('LANG_REF', language)
        vc_obj = self._add_vocab_xml(vc_node)
        self.__xml_root.append(vc_node)
        return vc_obj

    def new_timeslot(self, value):
        """ Create a new timeslot object 

        :param value: Timeslot value (in milliseconds)
        :type value: int or str
        """
        ts_node = etree.Element("TIME_SLOT")
        seed = len(self.time_order) + 1
        while True:
            ts_id = f"ts{seed}"
            if ts_id in self.time_order:
                seed += 1
            else:
                ts_node.set('TIME_SLOT_ID', ts_id)
                break
        if isinstance(value, float):
            value = round(value)
        ts_node.set('TIME_VALUE', str(value))
        self.__xml_root.find('TIME_ORDER').append(ts_node)
        ts_obj = self._add_timeslot_xml(ts_node)
        return ts_obj

    def get_participant_map(self):
        """ Map participants to tiers
        Return a map from participant name to a list of corresponding tiers
        """
        par_map = dd(list)
        for t in self.tiers():
            par_map[t.participant].append(t)
        return par_map

    def __getitem__(self, tierID):
        """ Find a tier object using tierID """
        return self.tier_map[tierID]

    def __contains__(self, tierID):
        return tierID in self.tier_map

    def __iter__(self):
        """ Iterate through all tiers in this ELAN file """
        return iter(self.__tiers)

    def tiers(self) -> Tuple[Tier]:
        """ Collect all existing Tier in this ELAN file
        """
        return tuple(self.__tiers)

    def _reset_tier_map(self):
        """ [Internal] Update tier map

        This function will be updated in the future once a better mapping mechanism has been decided
        """
        self.__tier_map = None

    def new_tier(self, tier_id, type_id, parent_id=None, participant=None, annotator=None):
        if tier_id is None:
            raise ValueError("Tier ID cannot be blank")
        type_obj = self.get_linguistic_type(type_id)
        if type_obj is None:
            raise ValueError("Unknown linguistic type ID was provided")
        if parent_id is not None and parent_id not in self:
            raise ValueError(f"Tier {repr(parent_id)} could not be found")
        parent_tier = None if parent_id is None else self[parent_id]
        if type_obj.constraints is not None and parent_tier is None:
            raise ValueError(f"Tiers with type={type_obj.constraints} require a parent tier.")
        elif parent_tier is not None and not type_obj.constraints:
            raise ValueError("Tiers without constraints must be root level.")
        if self.__tiers:
            idx = self._find_last_element_index('TIER') + 1
        else:
            idx = self._find_last_element_index('TIME_ORDER') + 1
        tier_node = best_parser.XML(""" <TIER LINGUISTIC_TYPE_REF="" TIER_ID=""></TIER>""")
        tier_node.set('TIER_ID', tier_id)
        tier_node.set('LINGUISTIC_TYPE_REF', type_id)
        if parent_id:
            tier_node.set('PARENT_REF', parent_id)
        if participant:
            tier_node.set('PARTICIPANT', participant)
        if annotator:
            tier_node.set('ANNOTATOR', annotator)
        self.__xml_root.insert(idx, tier_node)
        tier_obj = self._add_tier_xml(tier_node)
        if parent_tier is not None:
            self[tier_obj.parent_ref].children.append(tier_obj)
        return tier_obj

    @property
    def _xml_media_node(self):
        if self.__xml_header_node is not None:
            return self.__xml_header_node.find('MEDIA_DESCRIPTOR')
        else:
            return None

    @property
    def media_file(self):
        return self.__xml_header_node.get('MEDIA_FILE', '')

    @media_file.setter
    def media_file(self, value):
        # TODO: what if __xml_header_node is None?
        self.__xml_header_node.set('MEDIA_FILE', value)

    @property
    def time_units(self):
        return self.__xml_header_node.get('TIME_UNITS')

    @time_units.setter
    def time_units(self, value):
        # TODO: what if __xml_header_node is None?
        self.__xml_header_node.set('TIME_UNITS', value)

    @property
    def media_url(self):
        return self._xml_media_node.get('MEDIA_URL')

    @media_url.setter
    def media_url(self, value):
        # TODO: what if __xml_header_node is None?
        self._xml_media_node.set('MEDIA_URL', value)

    @property
    def mime_type(self):
        return self._xml_media_node.get('MIME_TYPE')

    @mime_type.setter
    def mime_type(self, value):
        # TODO: what if __xml_header_node is None?
        self._xml_media_node.set('MIME_TYPE', value)

    @property
    def relative_media_url(self):
        return self._xml_media_node.get('RELATIVE_MEDIA_URL')

    @relative_media_url.setter
    def relative_media_url(self, value):
        # TODO: what if __xml_header_node is None?
        self._xml_media_node.set('RELATIVE_MEDIA_URL', value)

    def _update_header_xml(self, node):
        """ [Internal function] Read ELAN doc information from a HEADER XML node

        General users should not use this function.
        """
        self.__xml_header_node = node
        # extract extra properties
        for prop_node in node.findall('PROPERTY'):
            self.properties[prop_node.get('NAME')] = prop_node.text

    def _add_tier_xml(self, tier_node) -> Tier:
        """ [Internal function] Parse a TIER XML node, create an ELANTier object and link it to this ELAN Doc

        General users should not use this function.
        """
        tier = Tier(self, tier_node)
        if tier.ID in self:
            raise ValueError(f"Duplicated tier ID ({tier.ID})")
        self.__tiers.append(tier)
        self.tier_map[tier.ID] = tier
        return tier

    def _add_timeslot_xml(self, timeslot_node):
        """ [Internal function] Parse a TimeSlot XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        timeslot = TimeSlot(timeslot_node)
        self.time_order[timeslot.ID] = timeslot
        return timeslot

    def _add_linguistic_type_xml(self, elem):
        """ [Internal function] Parse a LinguisticType XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        lt = LinguisticType(elem)
        self.__linguistic_types.append(lt)
        return lt

    def _add_constraint_xml(self, elem):
        """ [Internal function] Parse a CONSTRAINT XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__constraints.append(Constraint(elem))

    def _add_vocab_xml(self, elem):
        """ [Internal function] Parse a CONTROLLED_VOCABULARY XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        cv = ControlledVocab(elem)
        self.__vocabs.append(cv)
        return cv

    def _add_license_xml(self, elem):
        """ [Internal function] Parse a LICENSE XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__licenses.append(License.from_xml(elem))

    def _add_external_ref(self, elem):
        """ [Internal function] Parse an EXTERNAL_REF XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__external_refs.append(ExternalRef.from_xml(elem))

    def _add_language_xml(self, elem):
        """ [Internal function] Parse a LANGUAGE XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__languages.append(Language.from_xml(elem))

    def _add_locale_xml(self, elem):
        """ [Internal function] Parse a LOCALE XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__locale = Locale(elem)

    def _register_ann(self, ann):
        """ [Internal] """
        self.__ann_map[ann.ID] = ann

    def to_csv_rows(self) -> List[List[str]]:
        """ Convert this ELAN Doc into a CSV-friendly structure (i.e. list of list of strings)

        :return: A list of list of strings
        :rtype: List[List[str]]
        """
        rows = []
        for tier in self.tiers():
            for anno in tier.annotations:
                _from_ts = f"{anno.from_ts.sec:.3f}" if anno.from_ts else ''
                _to_ts = f"{anno.to_ts.sec:.3f}" if anno.to_ts else ''
                _duration = f"{anno.duration:.3f}" if anno.duration else ''
                rows.append((tier.ID, tier.participant, _from_ts, _to_ts, _duration, anno.value))
        return rows

    def to_xml_bin(self, encoding='utf-8',
                   default_namespace=None,
                   short_empty_elements=True, *args, **kwargs):
        """ Generate EAF content (bytes) in XML format

        :returns: EAF content
        :rtype: bytes
        """
        _content = _xml_tostring(self.__xml_root,
                                 encoding=encoding,
                                 default_namespace=default_namespace,
                                 short_empty_elements=short_empty_elements,
                                 *args, **kwargs)
        return _content

    def to_xml_str(self, encoding='utf-8', *args, **kwargs):
        """ Generate EAF content string in XML format """
        return _xml_tostring(self.__xml_root,
                             *args, **kwargs).decode(encoding=encoding)

    def save(self, path, encoding='utf-8', xml_declaration=None,
             default_namespace=None, short_empty_elements=True, *args, **kwargs):
        """ Write ELAN Doc to an EAF file """
        _content = self.to_xml_str(encoding=encoding,
                                   xml_declaration=xml_declaration,
                                   default_namespace=default_namespace,
                                   short_empty_elements=short_empty_elements,
                                   *args, **kwargs)
        chio.write_file(path, _content, encoding=encoding)

    def cut(self, section, outfile, media_file=None):
        """ Cut the source media with timestamps defined in section object 

        For example, the following code cut all annotations in tier "Tier 1" into appopriate audio files

        >>> for idx, ann in enumerate(eaf["Tier 1"], start=1):
        >>>     eaf.cut(ann, f"tier1_ann{idx}.wav")

        :param section: Any object with ``from_ts`` and ``to_ts`` attributes which return TimeSlot objects
        :param outfile: Path to output media file, must not exist or a FileExistsError will be raised
        :param media_file: Use to specify source media file. This will override the value specified in source EAF file
        :raises: FileExistsError, ValueError
        """
        if section is None:
            raise ValueError("Annotation object cannot be empty")
        elif not section.from_ts or not section.to_ts:
            raise ValueError("Annotation object must be time-alignable")
        elif media_file is None:
            media_file = self.media_path()
        # verify that media_file exists
        if not os.path.isfile(media_file):
            raise FileNotFoundError(f"Source media file ({media_file}) could not be found")
        cut(media_file, outfile, from_ts=section.from_ts, to_ts=section.to_ts)

    def _parse_root(self):
        """ [Internal] Parse XML structure to build ELAN structure

        General users should not use this function.
        """
        # Update ELAN file metadata from an XML node
        self.__author = self.__xml_root.get('AUTHOR')
        self.__date = self.__xml_root.get('DATE')
        self.fileformat = self.__xml_root.get('FORMAT')
        self.version = self.__xml_root.get('VERSION')
        
        for elem in self.__xml_root:
            if elem.tag == 'HEADER':
                self._update_header_xml(elem)
            elif elem.tag == 'TIME_ORDER':
                self.__xml_time_order_node = elem
                for time_elem in elem:
                    self._add_timeslot_xml(time_elem)
            elif elem.tag == 'TIER':
                self._add_tier_xml(elem)
            elif elem.tag == 'LINGUISTIC_TYPE':
                self._add_linguistic_type_xml(elem)
            elif elem.tag == 'CONSTRAINT':
                self._add_constraint_xml(elem)
            elif elem.tag == 'CONTROLLED_VOCABULARY':
                self._add_vocab_xml(elem)
            elif elem.tag == 'LICENSE':
                self._add_license_xml(elem)
            elif elem.tag == "EXTERNAL_REF":
                self._add_external_ref(elem)
            elif elem.tag == 'LANGUAGE':
                self._add_language_xml(elem)
            elif elem.tag == 'LOCALE':
                self._add_locale_xml(elem)
            else:
                logging.getLogger(__name__).warning(
                    f"Unknown element type -- {elem.tag}. Please consider to report an issue at {__issue__}")

    def _resolve_structure(self):
        """ [Internal] Link different parts of the Doc structure together
        + Link linguistic types to controlled vocabularies
        + Create tier hierarchy
        + Link annotations and tiers and vocabularies

        General users should not use this function.
        """
        # linguistic_types -> vocabs
        for lingtype in self.linguistic_types:
            if lingtype.controlled_vocabulary_ref:
                lingtype.vocab = self.get_vocab(lingtype.controlled_vocabulary_ref)
        # resolves tiers' roots, parents, and type
        for tier in self:
            for ann in tier:
                self._register_ann(ann)
            lingtype = self.get_linguistic_type(tier._type_ref_id)
            lingtype.tiers.append(tier)  # type -> tiers
            if lingtype.vocab:
                lingtype.vocab.tiers.append(tier)  # vocab -> tiers
            if tier.parent_ref is not None:
                self[tier.parent_ref].children.append(tier)
        # resolve ref_ann
        for ann in self.__ann_map.values():
            if ann.ref_id:
                ann.resolve(self)


    @classmethod
    def parse_eaf_stream(cls, eaf_stream, *args, **kwargs):
        """ Parse an EAF input stream and return an elan.Doc object

        >>> with open('test/data/test.eaf').read() as eaf_stream:
        >>>    eaf = elan.parse_eaf_stream(eaf_stream)

        :param eaf_stream: EAF text input stream
        :rtype: speach.elan.Doc
        """
        _root = _parse_xml(eaf_stream)
        _doc = Doc()
        # store XML root node
        _doc.__xml_root = _root
        # construct raw ELAN structure
        _doc._parse_root()
        # linking parts together
        _doc._resolve_structure()
        return _doc

    @classmethod
    def parse_string(cls, eaf_string, *args, **kwargs):
        """ Parse EAF content in a string and return an elan.Doc object

        >>> with open('test/data/test.eaf').read() as eaf_stream:
        >>>    eaf_content = eaf_stream.read()
        >>>    eaf = elan.parse_string(eaf_content)

        :param eaf_string: EAF content stored in a string
        :type eaf_string: str
        :rtype: speach.elan.Doc
        """
        return cls.parse_eaf_stream(StringIO(eaf_string), *args, **kwargs)

    @classmethod
    def read_eaf(cls, eaf_path, encoding='utf-8', *args, **kwargs):
        """ Read an EAF file and return an elan.Doc object

        >>> from speach import elan
        >>> eaf = elan.read_eaf("myfile.eaf")

        :param eaf_path: Path to existing EAF file
        :type eaf_path: str or Path-like object
        :param encoding: Encoding of the eaf stream, defaulted to UTF-8
        :type encoding: str
        :rtype: speach.elan.Doc
        """
        eaf_path = str(eaf_path)
        if eaf_path.startswith("~"):
            eaf_path = os.path.expanduser(eaf_path)
        with chio.open(eaf_path, encoding=encoding, *args, **kwargs) as eaf_stream:
            _doc = cls.parse_eaf_stream(eaf_stream)
            _doc.path = eaf_path
            return _doc

    @classmethod
    def create(cls, media_file='audio.wav',
               media_url=None,
               relative_media_url=None,
               author="",
               *args, **kwargs):
        """ Create a new blank ELAN doc

        >>> from speach import elan
        >>> eaf = elan.create()

        :param encoding: Encoding of the eaf stream, defaulted to UTF-8
        :type encoding: str
        :rtype: speach.elan.Doc
        """
        eaf = cls.read_eaf(ELAN_BLANK_FILE, *args, **kwargs)
        if not media_url:
            media_url = media_file
        if not relative_media_url:
            relative_media_url = media_file
        if media_file:
            eaf.media_file = media_file
            eaf.media_url = media_url
            eaf.relative_media_url = relative_media_url
        eaf.date = datetime.now()
        if author:
            eaf.author = author
        return eaf


read_eaf = Doc.read_eaf
parse_eaf_stream = Doc.parse_eaf_stream
parse_string = Doc.parse_string
create = Doc.create
read_ecv = ExternalControlledVocabResource.read_ecv
parse_ecv_string = ExternalControlledVocabResource.parse_string
parse_ecv_stream = ExternalControlledVocabResource.parse_stream


def open_eaf(*args, **kwargs):
    warnings.warn("elan.open_eaf() is deprecated and will be removed in near future. Use elan.read_eaf() instead.",
                  DeprecationWarning, stacklevel=2)
    Doc.read_eaf(*args, **kwargs)
