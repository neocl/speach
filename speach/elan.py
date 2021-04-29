# -*- coding: utf-8 -*-

"""
ELAN module - manipulating ELAN transcript files (\*.eaf, \*.pfsx)
"""

# This code is a part of speach library: https://github.com/neocl/speach/
# :copyright: (c) 2018 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.


import logging
from collections import OrderedDict
from collections import defaultdict as dd
from typing import List, Tuple
import xml.etree.ElementTree as etree

from chirptext import DataObject
from chirptext import chio

from .__version__ import __issue__
from .vtt import sec2ts, ts2sec


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


class TimeSlot():
    def __init__(self, ID, value=None, xml_node=None, *args, **kwargs):
        """ An ELAN timestamp (with ID)
        """
        self.ID = ID
        self.value = value
        self.__xml_node = xml_node

    @property
    def ts(self):
        return sec2ts(self.sec) if self.value is not None else None

    @property
    def sec(self):
        """ Get TimeSlot value in seconds instead of milliseconds """
        return self.value / 1000 if self.value is not None else None

    def __lt__(self, other):
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return False
        return self.value < other.value if isinstance(other, TimeSlot) else self.value < other

    def __eq__(self, other):
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return False
        return self.value == other.value if isinstance(other, TimeSlot) else self.value == other

    def __gt__(self, other):
        if other is None or (isinstance(other, TimeSlot) and other.value is None):
            return True
        return self.value > other.value if isinstance(other, TimeSlot) else self.value > other

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __add__(self, other):
        return self.value + other.value if isinstance(other, TimeSlot) else self.value + other

    def __sub__(self, other):
        return self.value - other.value if isinstance(other, TimeSlot) else self.value - other

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f"TimeSlot(value={repr(self.value)})"

    def __str__(self):
        val = self.ts
        return val if val else self.ID

    @staticmethod
    def from_node(node):
        slotID = node.get('TIME_SLOT_ID')
        value = node.get('TIME_VALUE')
        if value is not None:
            return TimeSlot(slotID, int(node.get('TIME_VALUE')), xml_node=node)
        else:
            return TimeSlot(slotID, xml_node=node)

    @staticmethod
    def from_ts(ts, ID=None):
        value = ts2sec(ts) * 1000
        return TimeSlot(ID=ID, value=value)


class ELANAnnotation(DataObject):
    """ An ELAN abstract annotation (for both alignable and non-alignable annotations)
    """

    def __init__(self, ID, value, cve_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.ID = ID
        self.value = value
        self.cve_ref = cve_ref

    @property
    def text(self):
        """ An alias to ELANAnnotation.value """
        return self.value

    def __repr__(self):
        return f"ELANAnnotation(ID={repr(self.ID)},value={repr(self.value)})"

    def __str__(self):
        return str(self.value)


class ELANTimeAnnotation(ELANAnnotation):
    """ An ELAN time-alignable annotation
    """
    def __init__(self, ID, from_ts, to_ts, value, xml_node=None, **kwargs):
        super().__init__(ID, value, **kwargs)
        self.from_ts = from_ts
        self.to_ts = to_ts
        self.__xml_node = xml_node

    @property
    def duration(self):
        return self.to_ts.sec - self.from_ts.sec

    def overlap(self, other):
        """ Calculate overlap score between two time annotations
        Score = 0 means adjacent, score > 0 means overlapped, score < 0 means no overlap (the distance between the two)
        """
        return min(self.to_ts, other.to_ts) - max(self.from_ts, other.from_ts)

    def __repr__(self):
        return '[{} -- {}] {}'.format(self.from_ts, self.to_ts, self.value)

    def __str__(self):
        return str(self.value)


class ELANRefAnnotation(ELANAnnotation):
    """ An ELAN ref annotation (not time alignable)
    """

    def __init__(self, ID, ref_id, previous, value, xml_node=None, **kwargs):
        super().__init__(ID, value, **kwargs)
        self.__ref = None
        self.__ref_id = ref_id  # ANNOTATION_REF
        self.previous = previous  # PREVIOUS_ANNOTATION
        self.__xml_node = xml_node

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


class ELANTier(DataObject):
    """ Represents an ELAN annotation tier """

    NONE = "None"
    TIME_SUB = "Time_Subdivision"
    SYM_SUB = "Symbolic_Subdivision"
    INCL = "Included_In"
    SYM_ASSOC = "Symbolic_Association"

    def __init__(self, type_ref_id, participant, ID, doc=None, default_locale=None, parent_ref=None, xml_node=None, **kwargs):
        """
        ELAN Tier Model which contains annotation objects
        """
        super().__init__(**kwargs)
        self.__type_ref = None
        self.__type_ref_id = type_ref_id
        self.participant = participant if participant else ''
        self.ID = ID
        self.default_locale = default_locale
        self.parent_ref = parent_ref
        self.parent = None
        self.doc = doc
        self.children = []
        self.__annotations = []
        self.__xml_node = xml_node

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
    def type_ref(self):
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
            anno = ELANTimeAnnotation(ann_id, from_ts, to_ts, value, cve_ref=cve_ref, xml_node=alignable)
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
            anno = ELANRefAnnotation(ann_id, ref, previous, value, cve_ref=cve_ref, xml_node=ref_node)
            self.annotations.append(anno)
            return anno

    def _add_annotation_xml(self, annotation_node) -> ELANAnnotation:
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


class ELANCVEntry(DataObject):

    """ A controlled vocabulary entry """

    def __init__(self, ID, lang_ref, value, description=None, **kwargs):
        super().__init__(**kwargs)
        self.ID = ID
        self.lang_ref = lang_ref
        self.value = value
        self.description = description

    def __repr__(self):
        return f'ELANCVEntry(ID={repr(self.ID)}, lang_ref={repr(self.lang_ref)}, value={repr(self.value)})'

    def __str__(self):
        return self.value


class ELANVocab(DataObject):
    """ ELAN Controlled Vocabulary """
    def __init__(self, ID, description, lang_ref, entries=None, **kwargs):
        super().__init__(**kwargs)
        self.ID = ID
        self.description = description
        self.lang_ref = lang_ref
        self.entries = list(entries) if entries else []
        self.entries_map = {e.ID: e for e in self.entries}
        self.tiers = []

    def __getitem__(self, key):
        return self.entries_map[key]

    def __iter__(self):
        return iter(self.entries)

    def __repr__(self):
        if self.description:
            return f'Vocab(ID={repr(self.ID)}, description={repr(self.description)})'
        else:
            return f'Vocab(ID={repr(self.ID)})'

    def __str__(self):
        return repr(self)

    @staticmethod
    def from_xml(node):
        CVID = node.get('CV_ID')
        description = ""
        lang_ref = ""
        entries = []
        for child in node:
            if child.tag == 'DESCRIPTION':
                description = child.text
                lang_ref = child.get('LANG_REF')
            elif child.tag == 'CV_ENTRY_ML':
                entryID = child.get('CVE_ID')
                entry_value_node = child.find('CVE_VALUE')
                entry_lang_ref = entry_value_node.get('LANG_REF')
                entry_value = entry_value_node.text
                entry_description = entry_value_node.get('DESCRIPTION')
                cv_entry = ELANCVEntry(entryID, entry_lang_ref, entry_value, description=entry_description)
                entries.append(cv_entry)
        return ELANVocab(CVID, description, lang_ref, entries=entries)


class ELANContraint(DataObject):
    """ ELAN Tier Constraints """

    def __init__(self, xml_node=None):
        super().__init__()
        if xml_node is not None:
            self.description = xml_node.get('DESCRIPTION')
            self.stereotype = xml_node.get('STEREOTYPE')


TierTuple = Tuple[ELANTier]
LinguisticTypeTuple= Tuple[LinguisticType]
ConstraintTuple = Tuple[ELANContraint]
VocabTuple = Tuple[ELANVocab]


class ELANDoc(DataObject):

    """ This class represents an ELAN file (\*.eaf)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.properties = OrderedDict()
        self.time_order = OrderedDict()
        self.__tiers_map = OrderedDict()  # internal - map tierIDs to tier objects
        self.__ann_map = dict()
        self.__linguistic_types = []
        self.__constraints = []
        self.__vocabs = []
        self.__roots = []
        self.__xml_root = None
        self.__xml_header_node = None
        self.__xml_time_order_node = None

    def annotation(self, ID):
        """ Get annotation by ID """
        return self.__ann_map.get(ID, None)

    @property
    def roots(self) -> TierTuple:
        """ All root-level tiers in this ELAN doc """
        return tuple(self.__roots)

    @property
    def vocabs(self) -> VocabTuple:
        """ A tuple of all existing controlled vocabulary objects in this ELAN file """
        return tuple(self.__vocabs)

    @property
    def constraints(self) -> ConstraintTuple:
        """ A tuple of all existing constraints in this ELAN file """
        return tuple(self.__constraints)

    @property
    def linguistic_types(self) -> LinguisticTypeTuple:
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
        return self.__tiers_map[tierID]

    def __iter__(self):
        """ Iterate through all tiers in this ELAN file """
        return iter(self.__tiers_map.values())

    def tiers(self) -> TierTuple:
        """ Collect all existing Tier in this ELAN file
        """
        return tuple(self.__tiers_map.values())

    def _update_info_xml(self, node):
        """ [Internal function] Update ELAN file metadata from an XML node

        General users should not use this function.
        """
        self.author = node.get('AUTHOR')
        self.date = node.get('DATE')
        self.fileformat = node.get('FORMAT')
        self.version = node.get('VERSION')

    def _update_header_xml(self, node):
        """ [Internal function] Read ELAN doc information from a HEADER XML node

        General users should not use this function.
        """
        self.__xml_header_node = node
        self.media_file = node.get('MEDIA_FILE')
        self.time_units = node.get('TIME_UNITS')
        # extract media information
        media_node = node.find('MEDIA_DESCRIPTOR')
        if media_node is not None:
            self.media_url = media_node.get('MEDIA_URL')
            self.mime_type = media_node.get('MIME_TYPE')
            self.relative_media_url = media_node.get('RELATIVE_MEDIA_URL')
        # extract properties
        for prop_node in node.findall('PROPERTY'):
            self.properties[prop_node.get('NAME')] = prop_node.text

    def _add_tier_xml(self, tier_node) -> ELANTier:
        """ [Internal function] Parse a TIER XML node, create an ELANTier object and link it to this ELANDoc

        General users should not use this function.
        """
        type_ref = tier_node.get('LINGUISTIC_TYPE_REF')
        participant = tier_node.get('PARTICIPANT')
        tier_id = tier_node.get('TIER_ID')
        parent_ref = tier_node.get('PARENT_REF')
        default_locale = tier_node.get('DEFAULT_LOCALE')
        tier = ELANTier(type_ref, participant, tier_id, doc=self, default_locale=default_locale, parent_ref=parent_ref, xml_node=tier_node)
        # add child annotations
        for elem in tier_node:
            tier._add_annotation_xml(elem)
        if tier_id in self.__tiers_map:
            raise ValueError("Duplicated tier ID ({})".format(tier_id))
        self.__tiers_map[tier_id] = tier
        if tier.parent_ref is None:
            self.__roots.append(tier)
        return tier

    def _add_timeslot_xml(self, timeslot_node):
        """ [Internal function] Parse a TimeSlot XML node and link it to current ELANDoc

        General users should not use this function.
        """
        timeslot = TimeSlot.from_node(timeslot_node)
        self.time_order[timeslot.ID] = timeslot

    def _add_linguistic_type_xml(self, elem):
        """ [Internal function] Parse a LinguisticType XML node and link it to current ELANDoc

        General users should not use this function.
        """
        self.__linguistic_types.append(LinguisticType(elem))

    def _add_constraint_xml(self, elem):
        """ [Internal function] Parse a CONSTRAINT XML node and link it to current ELANDoc

        General users should not use this function.
        """
        self.__constraints.append(ELANContraint(elem))

    def _add_vocab_xml(self, elem):
        """ [Internal function] Parse a CONTROLLED_VOCABULARY XML node and link it to current ELANDoc

        General users should not use this function.
        """
        self.__vocabs.append(ELANVocab.from_xml(elem))

    def to_csv_rows(self) -> CSVTable:
        """ Convert this ELANDoc into a CSV-friendly structure (i.e. list of list of strings)

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
        """ Generate EAF content in XML format

        :returns: EAF content
        :rtype: bytes
        """
        _content = etree.tostring(self.__xml_root, encoding=encoding, method="xml",
                                  short_empty_elements=short_empty_elements, *args, **kwargs)
        return _content

    def save(self, path, encoding='utf-8', xml_declaration=None,
             default_namespace=None, short_empty_elements=True, *args, **kwargs):
        """ Write ELANDoc to an EAF file """
        _content = self.to_xml_bin(encoding=encoding,
                                   xml_declaration=xml_declaration,
                                   default_namespace=default_namespace,
                                   short_empty_elements=short_empty_elements)
        chio.write_file(path, _content, encoding=encoding)

    @classmethod
    def open_eaf(cls, eaf_path, encoding='utf-8', *args, **kwargs):
        with chio.open(eaf_path, encoding=encoding, *args, **kwargs) as eaf_stream:
            return cls.parse_eaf_stream(eaf_stream)

    @classmethod
    def parse_eaf_stream(cls, eaf_stream):
        _root = etree.fromstring(eaf_stream.read())
        _doc = ELANDoc()
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
            elif elem.tag == 'LANGUAGE':
                logging.getLogger(__name__).info("LANGUAGE tag is not yet supported in this version")
            else:
                logging.getLogger(__name__).warning(f"Unknown element type -- {elem.tag}. Please consider to report an issue at {__issue__}")
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
                tier.parent = _doc[tier.parent_ref]
                _doc[tier.parent_ref].children.append(tier)
        # resolve ref_ann
        for ann in _doc.__ann_map.values():
            if ann.ref_id:
                ann.resolve(_doc)
        return _doc


open_eaf = ELANDoc.open_eaf
parse_eaf_stream = ELANDoc.parse_eaf_stream
