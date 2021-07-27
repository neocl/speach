# -*- coding: utf-8 -*-

"""
ELAN module - manipulating ELAN transcript files (\*.eaf, \*.pfsx)
"""

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
from io import StringIO
import logging
from collections import OrderedDict
from collections import defaultdict as dd
from typing import List, Tuple
import xml.etree.ElementTree as etree
import warnings

from chirptext import DataObject
from chirptext import chio

from .__version__ import __issue__
from .vtt import sec2ts, ts2sec
from .media import cut


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------

CSVRow = List[str]
CSVTable = List[CSVRow]


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
        data = {k.lower(): v for k, v in xml_node.attrib.items()} if xml_node is not None else {}
        if "time_alignable" in data:
            data["time_alignable"] = data["time_alignable"] == "true"
        super().__init__(**data)
        self.vocab = None
        self.tiers = []

    @property
    def ID(self):
        return self.linguistic_type_id

    def __repr__(self):
        return f"LinguisticType(ID={repr(self.ID)}, constraints={repr(self.constraints)}"

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
        self.__type_ref = None
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
    def linguistic_type(self) -> LinguisticType:
        """ Linguistic type object of this Tier """
        return self.__type_ref

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
    def type_ref(self):
        """ Tier type object """
        return self.__type_ref

    def _set_type_ref(self, type_ref_object):
        """ [Internal function] Update type_ref object of this Tier """
        self.__type_ref = type_ref_object

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

    @property
    def ID(self):
        return self.__ID

    @property
    def lang_ref(self):
        return self.__lang_ref

    @property
    def value(self):
        return self.__value

    @property
    def description(self):
        """ Description of this controlled vocabulary entry """
        return self.__description

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

    def _add_child(self, child):
        self.__entries.append(child)
        self.__entries_map[child.ID] = child

    def __getitem__(self, key):
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
        return self.lang_def

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
        self.path = None
        self.__xml_root = None
        self.__xml_header_node = None
        self.__xml_time_order_node = None

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

    def annotation(self, ID):
        """ Get annotation by ID """
        return self.__ann_map.get(ID, None)

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

    def get_vocab(self, vocab_id):
        """ Get controlled vocab list by ID """
        for vocab in self.__vocabs:
            if vocab.ID == vocab_id:
                return vocab
        return None

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

    def _update_info_xml(self, node):
        """ [Internal function] Update ELAN file metadata from an XML node

        General users should not use this function.
        """
        self.author = node.get('AUTHOR')
        self.date = node.get('DATE')
        self.fileformat = node.get('FORMAT')
        self.version = node.get('VERSION')

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

    def _add_linguistic_type_xml(self, elem):
        """ [Internal function] Parse a LinguisticType XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__linguistic_types.append(LinguisticType(elem))

    def _add_constraint_xml(self, elem):
        """ [Internal function] Parse a CONSTRAINT XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__constraints.append(Constraint(elem))

    def _add_vocab_xml(self, elem):
        """ [Internal function] Parse a CONTROLLED_VOCABULARY XML node and link it to current ELAN Doc

        General users should not use this function.
        """
        self.__vocabs.append(ControlledVocab(elem))

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

    def to_csv_rows(self) -> CSVTable:
        """ Convert this ELAN Doc into a CSV-friendly structure (i.e. list of list of strings)

        :return: A list of list of strings
        :rtype: CSVTable
        """
        rows = []
        for tier in self.tiers():
            for anno in tier.annotations:
                _from_ts = f"{anno.from_ts.sec:.3f}" if anno.from_ts else ''
                _to_ts = f"{anno.to_ts.sec:.3f}" if anno.to_ts else ''
                _duration = f"{anno.duration:.3f}" if anno.duration else ''
                rows.append((tier.ID, tier.participant, _from_ts, _to_ts, _duration, anno.value))
        return rows

    def to_xml_bin(self, encoding='utf-8', default_namespace=None, short_empty_elements=True, *args, **kwargs):
        """ Generate EAF content (bytes) in XML format

        :returns: EAF content
        :rtype: bytes
        """
        _content = etree.tostring(self.__xml_root, encoding=encoding, method="xml",
                                  short_empty_elements=short_empty_elements, *args, **kwargs)
        return _content

    def to_xml_str(self, encoding='utf-8', *args, **kwargs):
        """ Generate EAF content string in XML format """
        return self.to_xml_bin(encoding=encoding, *args, **kwargs).decode(encoding)

    def save(self, path, encoding='utf-8', xml_declaration=None,
             default_namespace=None, short_empty_elements=True, *args, **kwargs):
        """ Write ELAN Doc to an EAF file """
        _content = self.to_xml_bin(encoding=encoding,
                                   xml_declaration=xml_declaration,
                                   default_namespace=default_namespace,
                                   short_empty_elements=short_empty_elements)
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
    def parse_eaf_stream(cls, eaf_stream, *args, **kwargs):
        """ Parse an EAF input stream and return an elan.Doc object

        >>> with open('test/data/test.eaf').read() as eaf_stream:
        >>>    eaf = elan.parse_eaf_stream(eaf_stream)

        :param eaf_stream: EAF text input stream
        :rtype: speach.elan.Doc
        """
        _root = etree.fromstring(eaf_stream.read())
        _doc = Doc()
        _doc.__xml_root = _root
        _doc._update_info_xml(_root)
        for elem in _root:
            if elem.tag == 'HEADER':
                _doc._update_header_xml(elem)
            elif elem.tag == 'TIME_ORDER':
                _doc.__xml_time_order_node = elem
                for time_elem in elem:
                    _doc._add_timeslot_xml(time_elem)
            elif elem.tag == 'TIER':
                _doc._add_tier_xml(elem)
            elif elem.tag == 'LINGUISTIC_TYPE':
                _doc._add_linguistic_type_xml(elem)
            elif elem.tag == 'CONSTRAINT':
                _doc._add_constraint_xml(elem)
            elif elem.tag == 'CONTROLLED_VOCABULARY':
                _doc._add_vocab_xml(elem)
            elif elem.tag == 'LICENSE':
                _doc._add_license_xml(elem)
            elif elem.tag == "EXTERNAL_REF":
                _doc._add_external_ref(elem)
            elif elem.tag == 'LANGUAGE':
                _doc._add_language_xml(elem)
            else:
                logging.getLogger(__name__).warning(
                    f"Unknown element type -- {elem.tag}. Please consider to report an issue at {__issue__}")
        # linking parts together
        # linguistic_types -> vocabs
        for lingtype in _doc.linguistic_types:
            if lingtype.controlled_vocabulary_ref:
                lingtype.vocab = _doc.get_vocab(lingtype.controlled_vocabulary_ref)
        # resolves tiers' roots, parents, and type
        for tier in _doc:
            for ann in tier:
                _doc.__ann_map[ann.ID] = ann
            lingtype = _doc.get_linguistic_type(tier._type_ref_id)
            tier._set_type_ref(lingtype)
            lingtype.tiers.append(tier)  # type -> tiers
            if lingtype.vocab:
                lingtype.vocab.tiers.append(tier)  # vocab -> tiers
            if tier.parent_ref is not None:
                _doc[tier.parent_ref].children.append(tier)
        # resolve ref_ann
        for ann in _doc.__ann_map.values():
            if ann.ref_id:
                ann.resolve(_doc)
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


read_eaf = Doc.read_eaf
parse_eaf_stream = Doc.parse_eaf_stream
parse_string = Doc.parse_string


def open_eaf(*args, **kwargs):
    warnings.warn("elan.open_eaf() is deprecated and will be removed in near future. Use elan.read_eaf() instead.",
                  DeprecationWarning, stacklevel=2)
    Doc.read_eaf(*args, **kwargs)
