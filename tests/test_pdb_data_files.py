import datetime
from unittest import TestCase
from molecupy.pdbfile import PdbFile, PdbRecord
from molecupy.pdbdatafile import *

class PdbDataFileTest(TestCase):

    def setUp(self):
        self.empty = PdbDataFile(PdbFile(""))



class PdbdataFilePropertiesTests(PdbDataFileTest):

    def test_has_pdb_file(self):
        self.assertIsInstance(self.empty.pdb_file, PdbFile)


    def test_repr(self):
        self.assertRegex(
         str(self.empty),
         r"<PdbDataFile \(([^\s]{4})\)>"
        )



class DateFromStringTests(TestCase):

    def test_can_get_date_from_string(self):
        self.assertEqual(
         date_from_string("01-JAN-00"),
         datetime.datetime(2000, 1, 1).date()
        )
        self.assertEqual(
         date_from_string("28-SEP-99"),
         datetime.datetime(1999, 9, 28).date()
        )



class RecordMergingTests(TestCase):

    def setUp(self):
        self.records = [PdbRecord(l, 1) for l in [
         "0123456789",
         "abcdefghij",
         "0123456789"
        ]]

        self.punc_records = [PdbRecord(l, 1) for l in [
         "0123, 456789",
         "abcd  efghij",
         "0123; 456789"
        ]]


    def test_can_merge_records(self):
        self.assertEqual(
         merge_records(self.records, 5),
         "56789 fghij 56789"
        )
        self.assertEqual(
         merge_records(self.records, 8),
         "89 ij 89"
        )


    def test_can_vary_join(self):
        self.assertEqual(
         merge_records(self.records, 5, join=""),
         "56789fghij56789"
        )
        self.assertEqual(
         merge_records(self.records, 8, join="."),
         "89.ij.89"
        )


    def test_can_condense(self):
        self.assertEqual(
         merge_records(self.punc_records, 2),
         "23,456789 cd efghij 23;456789"
        )


    def test_can_ignore_consensors(self):
        self.assertEqual(
         merge_records(self.punc_records, 2, dont_condense=","),
         "23, 456789 cd efghij 23;456789"
        )
        self.assertEqual(
         merge_records(self.punc_records, 2, dont_condense=";"),
         "23,456789 cd efghij 23; 456789"
        )
        self.assertEqual(
         merge_records(self.punc_records, 2, dont_condense=";,"),
         "23, 456789 cd efghij 23; 456789"
        )
        self.assertEqual(
         merge_records(self.punc_records, 2, dont_condense=";, "),
         "23, 456789 cd  efghij 23; 456789"
        )


class RecordsToDictTests(TestCase):

    def test_can_make_dicts(self):
        records = [PdbRecord(l, 1) for l in [
         "COMPND    MOL_ID: A;",
         "COMPND   2 MOLECULE: MOLNAME;",
         "COMPND   3 CHAIN_: CHAINS;",
         "COMPND   4 MOL_ID: B;",
         "COMPND   5 MOLECULE: MOLNAME2;",
         "COMPND   6 CHAIN_: CHAINS2;"
        ]]
        self.assertEqual(
         records_to_token_value_dicts(records),
         [
          {"MOL_ID": "A", "MOLECULE": "MOLNAME", "CHAIN_": "CHAINS"},
          {"MOL_ID": "B", "MOLECULE": "MOLNAME2", "CHAIN_": "CHAINS2"}
         ]
        )


    def test_can_detect_numeric_fields(self):
        records = [PdbRecord(l, 1) for l in [
         "COMPND    MOL_ID: 1;",
         "COMPND   2 MOLECULE: MOLNAME;",
         "COMPND   3 CHAIN_: CHAINS;"
        ]]
        self.assertEqual(
         records_to_token_value_dicts(records),
         [
          {"MOL_ID": 1, "MOLECULE": "MOLNAME", "CHAIN_": "CHAINS"}
         ]
        )


    def test_can_detect_boolean_fields(self):
        records = [PdbRecord(l, 1) for l in [
         "COMPND    MOL_ID: 1;",
         "COMPND   2 MOLECULE: YES;",
         "COMPND   3 CHAIN_: NO;"
        ]]
        self.assertEqual(
         records_to_token_value_dicts(records),
         [
          {"MOL_ID": 1, "MOLECULE": True, "CHAIN_": False}
         ]
        )


    def test_can_split_chains_and_synonyms(self):
        records = [PdbRecord(l, 1) for l in [
         "COMPND    MOL_ID: 1;",
         "COMPND   2 CHAIN: A,B;",
         "COMPND   2 SYNONYM: BEEP, BOOP;"
        ]]
        self.assertEqual(
         records_to_token_value_dicts(records),
         [
          {"MOL_ID": 1, "CHAIN": ["A", "B"], "SYNONYM": ["BEEP", "BOOP"]}
         ]
        )



class HeaderRecordTests(PdbDataFileTest):

    def test_header_processing(self):
        data_file = PdbDataFile(PdbFile(
         "HEADER    LYASE                                   06-MAY-02   1LOL"
        ))
        self.assertEqual(data_file.classification, "LYASE")
        self.assertEqual(
         data_file.deposition_date,
         datetime.datetime(2002, 5, 6).date()
        )
        self.assertEqual(data_file.pdb_code, "1LOL")


    def test_missing_header_processing(self):
        self.assertEqual(self.empty.classification, None)
        self.assertEqual(self.empty.deposition_date, None)
        self.assertEqual(self.empty.pdb_code, None)



class ObslteRecordTests(PdbDataFileTest):

    def test_obslte_processing(self):
        data_file = PdbDataFile(PdbFile(
         "OBSLTE     30-SEP-93 1LOL      1SAM"
        ))
        self.assertTrue(data_file.is_obsolete)
        self.assertEqual(
         data_file.obsolete_date,
         datetime.datetime(1993, 9, 30).date()
        )
        self.assertEqual(
         data_file.replacement_code,
         "1SAM"
        )


    def test_missing_obslte_processing(self):
        self.assertFalse(self.empty.is_obsolete)
        self.assertEqual(self.empty.obsolete_date, None)
        self.assertEqual(self.empty.replacement_code, None)



class TitleRecordTests(PdbDataFileTest):

    def test_title_processing(self):
        data_file = PdbDataFile(PdbFile(
         "TITLE     CRYSTAL STRUCTURE OF OROTIDINE MONOPHOSPHATE DECARBOXYLASE\n"
         "TITLE    2 COMPLEX WITH XMP"
        ))
        self.assertEqual(
         data_file.title,
         "CRYSTAL STRUCTURE OF OROTIDINE MONOPHOSPHATE DECARBOXYLASE COMPLEX WITH XMP"
        )


    def test_missing_title_processing(self):
        self.assertEqual(self.empty.title, None)



class SplitRecordTests(PdbDataFileTest):

    def test_split_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SPLIT      1VOQ 1VOR 1VOS 1VOU 1VOV 1VOW 1VOX 1VOY 1VP0 1VOZ 1VOY 1VP0 1VOZ 1VOZ\n"
         "SPLIT      1VOQ 1VOR 1VOS 1VOU 1VOV 1VOW 1VOX 1VOY 1VP0 1VOZ"
        ))
        self.assertEqual(
         data_file.split_codes,
         [
          "1VOQ", "1VOR", "1VOS", "1VOU", "1VOV", "1VOW",
          "1VOX", "1VOY", "1VP0", "1VOZ", "1VOY", "1VP0",
          "1VOZ", "1VOZ", "1VOQ", "1VOR", "1VOS", "1VOU",
          "1VOV", "1VOW", "1VOX", "1VOY", "1VP0", "1VOZ"
         ]
        )


    def test_missing_split_processing(self):
        self.assertEqual(self.empty.split_codes, [])



class CaveatRecordTests(PdbDataFileTest):

    def test_caveat_processing(self):
        data_file = PdbDataFile(PdbFile(
         "CAVEAT     1SAM    THE CRYSTAL TRANSFORMATION IS IN ERROR BUT IS\n"
         "CAVEAT   2 1SAM    UNCORRECTABLE AT THIS TIME"
        ))
        self.assertEqual(
         data_file.caveat,
         "THE CRYSTAL TRANSFORMATION IS IN ERROR BUT IS UNCORRECTABLE AT THIS TIME"
        )


    def test_missing_caveat_processing(self):
        self.assertEqual(self.empty.caveat, None)



class SourceRecordTests(PdbDataFileTest):

    def test_compnd_processing(self):
        data_file = PdbDataFile(PdbFile(
         "COMPND    MOL_ID: 1;\n"
         "COMPND   2 MOLECULE: OROTIDINE 5'-MONOPHOSPHATE DECARBOXYLASE;\n"
         "COMPND   3 CHAIN: A, B;\n"
         "COMPND   4 SYNONYM: OMP DECARBOXYLASE, OMPDCASE, OMPDECASE;\n"
         "COMPND   5 EC: 4.1.1.23;\n"
         "COMPND   6 ENGINEERED: YES;\n"
         "COMPND   7 MOL_ID: 2;\n"
         "COMPND   8 MOLECULE: OROTIDINE 5'-MONOPHOSPHATE DECARBOXYLASE\n"
         "COMPND   9 PLUS;"
        ))
        self.assertEqual(
         data_file.compounds,
         [
          {
           "MOL_ID": 1,
           "MOLECULE": "OROTIDINE 5'-MONOPHOSPHATE DECARBOXYLASE",
           "CHAIN": ["A", "B"],
           "SYNONYM": [
            "OMP DECARBOXYLASE",
            "OMPDCASE",
            "OMPDECASE"
           ],
           "EC": "4.1.1.23",
           "ENGINEERED": True
          }, {
           "MOL_ID": 2,
           "MOLECULE": "OROTIDINE 5'-MONOPHOSPHATE DECARBOXYLASE PLUS"
          }
         ]
        )


    def test_missing_compnd_processing(self):
        self.assertEqual(self.empty.compounds, [])



class SourceRecordTests(PdbDataFileTest):

    def test_source_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SOURCE    MOL_ID: 1;\n"
         "SOURCE   2 ORGANISM_SCIENTIFIC: METHANOTHERMOBACTER\n"
         "SOURCE   3 THERMAUTOTROPHICUS STR. DELTA H;\n"
         "SOURCE   4 ORGANISM_TAXID: 187420;\n"
         "SOURCE   5 STRAIN: DELTA H;\n"
         "SOURCE   6 EXPRESSION_SYSTEM: ESCHERICHIA COLI;\n"
         "SOURCE   7 EXPRESSION_SYSTEM_TAXID: 562;\n"
         "SOURCE   8 EXPRESSION_SYSTEM_PLASMID: PET15B\n"
        ))
        self.assertEqual(
         data_file.sources,
         [
          {
           "MOL_ID": 1,
           "ORGANISM_SCIENTIFIC": "METHANOTHERMOBACTER THERMAUTOTROPHICUS STR. DELTA H",
           "ORGANISM_TAXID": 187420,
           "STRAIN": "DELTA H",
           "EXPRESSION_SYSTEM": "ESCHERICHIA COLI",
           "EXPRESSION_SYSTEM_TAXID": 562,
           "EXPRESSION_SYSTEM_PLASMID": "PET15B"
          }
         ]
        )


    def test_missing_source_processing(self):
        self.assertEqual(self.empty.sources, [])



class KeywdsRecordTests(PdbDataFileTest):

    def test_keywds_processing(self):
        data_file = PdbDataFile(PdbFile(
         "KEYWDS    TIM BARREL, LYASE"
        ))
        self.assertEqual(
         data_file.keywords,
         ["TIM BARREL", "LYASE"]
        )


    def test_missing_keywds_processing(self):
        self.assertEqual(self.empty.keywords, [])



class ExpdtaRecordTests(PdbDataFileTest):

    def test_expdta_processing(self):
        data_file = PdbDataFile(PdbFile(
         "EXPDTA    NEUTRON DIFFRACTION; X-RAY DIFFRACTION"
        ))
        self.assertEqual(
         data_file.experimental_techniques,
         ["NEUTRON DIFFRACTION", "X-RAY DIFFRACTION"]
        )


    def test_missing_expdta_processing(self):
        self.assertEqual(self.empty.experimental_techniques, [])



class NummdlRecordTests(PdbDataFileTest):

    def test_nummdl_processing(self):
        data_file = PdbDataFile(PdbFile(
         "NUMMDL    2"
        ))
        self.assertEqual(data_file.model_count, 2)


    def test_missing_nummdl_processing(self):
        self.assertEqual(self.empty.model_count, 1)



class MdltypRecordTests(PdbDataFileTest):

    def test_mdltyp_processing(self):
        data_file = PdbDataFile(PdbFile(
         "MDLTYP    CA ATOMS ONLY, CHAIN A, B, C, D, E, F, G, H, I, J, K ; P ATOMS ONLY,\n"
         "MDLTYP   2 CHAIN X, Y, Z"
        ))
        self.assertEqual(
         data_file.model_annotations,
         [
          "CA ATOMS ONLY, CHAIN A, B, C, D, E, F, G, H, I, J, K",
          "P ATOMS ONLY, CHAIN X, Y, Z"
         ]
        )


    def test_missing_mdltyp_processing(self):
        self.assertEqual(self.empty.model_annotations, [])



class AuthorRecordTests(PdbDataFileTest):

    def test_mdltyp_processing(self):
        data_file = PdbDataFile(PdbFile(
         "AUTHOR    M.B.BERRY,B.MEADOR,T.BILDERBACK,P.LIANG,M.GLASER,\n"
         "AUTHOR   2 G.N.PHILLIPS JR.,T.L.ST. STEVENS"
        ))
        self.assertEqual(
         data_file.authors,
         [
          "M.B.BERRY", "B.MEADOR", "T.BILDERBACK", "P.LIANG", "M.GLASER",
          "G.N.PHILLIPS JR.", "T.L.ST. STEVENS"
         ]
        )


    def test_missing_mdltyp_processing(self):
        self.assertEqual(self.empty.authors, [])



class RevdatRecordTests(PdbDataFileTest):

    def test_revdat_processing(self):
        data_file = PdbDataFile(PdbFile(
         "REVDAT   4 1 24-FEB-09 1LOL    1       VERSN  COMPND EXPDTA CAVEAT\n"
         "REVDAT   4 2                   1       SOURCE JRNL\n"
         "REVDAT   3   01-APR-03 1LOL    1       JRNL\n"
         "REVDAT   2   14-AUG-02 1LOL    1       DBREF\n"
         "REVDAT   1   07-AUG-02 1LOL    0"
        ))
        self.assertEqual(
         data_file.revisions,
         [
          {
           "number": 1, "date": datetime.datetime(2002, 8, 7).date(),
           "type": 0, "records": []
          }, {
           "number": 2, "date": datetime.datetime(2002, 8, 14).date(),
           "type": 1, "records": ["DBREF"]
          }, {
           "number": 3, "date": datetime.datetime(2003, 4, 1).date(),
           "type": 1, "records": ["JRNL"]
          }, {
           "number": 4, "date": datetime.datetime(2009, 2, 24).date(),
           "type": 1, "records": ["VERSN", "COMPND", "EXPDTA", "CAVEAT", "SOURCE", "JRNL"]
          }
         ]
        )


    def test_missing_revdat_processing(self):
        self.assertEqual(self.empty.revisions, [])



class SprsdeRecordTests(PdbDataFileTest):

    def test_sprsde_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SPRSDE     27-FEB-95 1GDJ      1LH4 2LH4"
        ))
        self.assertEqual(
         data_file.supercedes,
         ["1LH4", "2LH4"]
        )
        self.assertEqual(
         data_file.supercede_date,
         datetime.datetime(1995, 2, 27).date()
        )


    def test_missing_sprsde_processing(self):
        self.assertEqual(self.empty.supercedes, [])
        self.assertEqual(self.empty.supercede_date, None)



class JrnlRecordTests(PdbDataFileTest):

    def test_jrnl_authors_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        AUTH   N.WU,E.F.PAI"
        ))
        self.assertEqual(
         data_file.journal["authors"],
         ["N.WU", "E.F.PAI"]
        )


    def test_empty_jrnl_authors_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["authors"], [])


    def test_jrnl_title_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        TITL   CRYSTAL STRUCTURES OF INHIBITOR COMPLEXES REVEAL\n"
         "JRNL        TITL 2 AN ALTERNATE BINDING MODE IN\n"
         "JRNL        TITL 3 OROTIDINE-5'-MONOPHOSPHATE DECARBOXYLASE."
        ))
        self.assertEqual(
         data_file.journal["title"],
         "CRYSTAL STRUCTURES OF INHIBITOR COMPLEXES REVEAL AN ALTERNA"
         "TE BINDING MODE IN OROTIDINE-5'-MONOPHOSPHATE DECARBOXYLASE."
        )


    def test_empty_jrnl_title_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["title"], None)


    def test_jrnl_editors_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        EDIT   J.REN,C.NICHOLS,L.BIRD,P.CHAMBERLAIN,K.WEAVER,\n"
         "JRNL        EDIT 2 S.SHORT,D.I.STUART,D.K.STAMMERS"
        ))
        self.assertEqual(
         data_file.journal["editors"],
         [
          "J.REN", "C.NICHOLS", "L.BIRD", "P.CHAMBERLAIN", "K.WEAVER",
          "S.SHORT", "D.I.STUART", "D.K.STAMMERS"
         ]
        )


    def test_empty_jrnl_editors_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["editors"], [])


    def test_jrnl_reference_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        REF    J.BIOL.CHEM.                  V. 277 28080 2002"
        ))
        self.assertEqual(
         data_file.journal["reference"],
         {"published": True, "publication": "J.BIOL.CHEM.", "volume": 277, "page": 28080, "year": 2002}
        )

    def test_jrnl_unpublished_reference_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL        REF    TO BE PUBLISHED"))
        self.assertEqual(
         data_file.journal["reference"],
         {"published": False, "publication": None, "volume": None, "page": None, "year": None}
        )


    def test_empty_jrnl_reference_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["reference"], None)


    def test_jrnl_publisher_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        PUBL   AMERICAN ASSOCIATION FOR THE ADVANCEMENT OF SCIENCE\n"
         "JRNL        PUBL 2 WASHINGTON, D.C."
        ))
        self.assertEqual(
         data_file.journal["publisher"],
         "AMERICAN ASSOCIATION FOR THE ADVANCEMENT OF SCIENCE WASHINGTON, D.C."
        )


    def test_empty_jrnl_publisher_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["publisher"], None)


    def test_jrnl_referencenumber__processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        REFN                   ISSN 0021-9258"
        ))
        self.assertEqual(
         data_file.journal["reference_number"],
         {"type": "ISSN", "value": "0021-9258"}
        )


    def test_empty_jrnl_reference_number_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["reference_number"], None)


    def test_jrnl_pubmed_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        PMID   12011084"
        ))
        self.assertEqual(
         data_file.journal["pubmed"],
         "12011084"
        )


    def test_empty_jrnl_pubmed_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["pubmed"], None)


    def test_jrnl_doi_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        DOI    10.1074/JBC.M202362200"
        ))
        self.assertEqual(
         data_file.journal["doi"],
         "10.1074/JBC.M202362200"
        )


    def test_empty_jrnl_doi_processing(self):
        data_file = PdbDataFile(PdbFile("JRNL"))
        self.assertEqual(data_file.journal["doi"], None)


    def test_full_jrnl_processing(self):
        data_file = PdbDataFile(PdbFile(
         "JRNL        AUTH   N.WU,E.F.PAI\n"
         "JRNL        TITL   CRYSTAL STRUCTURES OF INHIBITOR COMPLEXES REVEAL\n"
         "JRNL        TITL 2 AN ALTERNATE BINDING MODE IN\n"
         "JRNL        TITL 3 OROTIDINE-5'-MONOPHOSPHATE DECARBOXYLASE.\n"
         "JRNL        EDIT   J.REN,C.NICHOLS,L.BIRD,P.CHAMBERLAIN,K.WEAVER,\n"
         "JRNL        EDIT 2 S.SHORT,D.I.STUART,D.K.STAMMERS\n"
         "JRNL        REF    J.BIOL.CHEM.                  V. 277 28080 2002\n"
         "JRNL        PUBL   AMERICAN ASSOCIATION FOR THE ADVANCEMENT OF SCIENCE\n"
         "JRNL        PUBL 2 WASHINGTON, D.C.\n"
         "JRNL        REFN                   ISSN 0021-9258\n"
         "JRNL        PMID   12011084\n"
         "JRNL        DOI    10.1074/JBC.M202362200"
        ))
        self.assertEqual(
         data_file.journal,
         {
          "authors": ["N.WU", "E.F.PAI"],
          "title": "CRYSTAL STRUCTURES OF INHIBITOR COMPLEXES REVEAL AN ALTERNA"
          "TE BINDING MODE IN OROTIDINE-5'-MONOPHOSPHATE DECARBOXYLASE.",
          "editors": [
           "J.REN", "C.NICHOLS", "L.BIRD", "P.CHAMBERLAIN", "K.WEAVER",
           "S.SHORT", "D.I.STUART", "D.K.STAMMERS"
          ],
          "reference": {"published": True, "publication": "J.BIOL.CHEM.", "volume": 277, "page": 28080, "year": 2002},
          "publisher": "AMERICAN ASSOCIATION FOR THE ADVANCEMENT OF SCIENCE WASHINGTON, D.C.",
          "reference_number": {"type": "ISSN", "value": "0021-9258"},
          "pubmed": "12011084",
          "doi": "10.1074/JBC.M202362200"
         }
        )


    def test_empty_jrnl_processing(self):
        self.assertEqual(self.empty.journal, None)


class RemarkRecordTests(PdbDataFileTest):

    def test_remark_processing(self):
        data_file = PdbDataFile(PdbFile(
         "REMARK   2\n"
         "REMARK 999\n"
         "REMARK   2 RESOLUTION.    1.90 ANGSTROMS.\n"
         "REMARK 999  SEQUENCE\n"
         "REMARK 999 AUTHOR STATES THAT ALTHOUGH RESIDUES 1 AND 1001 ARE MET\n"
         "REMARK 999 AND RESIDUES 101 AND 1101 ARE ARG ACCORDING TO THE\n"
         "REMARK 999 SWISSPROT ENTRY, RESIDUES 1 AND 1001 WERE LEU AND RESIDUES\n"
         "REMARK 999 101 AND 1101 WERE PRO IN THE ORIGINAL CONSTRUCT CLONED\n"
         "REMARK 999 OF MT GENOMIC DNA."
        ))
        self.assertEqual(
         data_file.remarks,
         [
          {
           "number": 2,
           "content": "RESOLUTION.    1.90 ANGSTROMS."
          }, {
           "number": 999,
           "content": "SEQUENCE\n"
           "AUTHOR STATES THAT ALTHOUGH RESIDUES 1 AND 1001 ARE MET\n"
           "AND RESIDUES 101 AND 1101 ARE ARG ACCORDING TO THE\n"
           "SWISSPROT ENTRY, RESIDUES 1 AND 1001 WERE LEU AND RESIDUES\n"
           "101 AND 1101 WERE PRO IN THE ORIGINAL CONSTRUCT CLONED\n"
           "OF MT GENOMIC DNA."
          }
         ]
        )


    def test_missing_remark_processing(self):
        self.assertEqual(self.empty.remarks, [])



class DbrefRecordTests(PdbDataFileTest):

    def test_dbref_processing(self):
        data_file = PdbDataFile(PdbFile(
         "DBREF  1LOL A    1   229  UNP    O26232   PYRF_METTH       1    228\n"
         "DBREF  1LOL B 1001  1229  UNP    O26232   PYRF_METTH       1    228"
        ))
        self.assertEqual(
         data_file.dbreferences,
         [
          {
           "chain_id": "A",
           "sequence_begin": 1,
           "insert_begin": None,
           "sequence_end": 229,
           "insert_end": None,
           "database": "UNP",
           "accession": "O26232",
           "db_id": "PYRF_METTH",
           "db_sequence_begin": 1,
           "db_insert_begin": None,
           "db_sequence_end": 228,
           "db_insert_end": None
          }, {
           "chain_id": "B",
           "sequence_begin": 1001,
           "insert_begin": None,
           "sequence_end": 1229,
           "insert_end": None,
           "database": "UNP",
           "accession": "O26232",
           "db_id": "PYRF_METTH",
           "db_sequence_begin": 1,
           "db_insert_begin": None,
           "db_sequence_end": 228,
           "db_insert_end": None
          }
         ]
        )


    def test_long_dbref_processing(self):
        data_file = PdbDataFile(PdbFile(
         "DBREF1 1LOL C   61   322  GB                   AE017221\n"
         "DBREF2 1LOL C     46197919                      1534489     1537377"
        ))
        self.assertEqual(
         data_file.dbreferences,
         [
          {
           "chain_id": "C",
           "sequence_begin": 61,
           "insert_begin": None,
           "sequence_end": 322,
           "insert_end": None,
           "database": "GB",
           "accession": "46197919",
           "db_id": "AE017221",
           "db_sequence_begin": 1534489,
           "db_insert_begin": None,
           "db_sequence_end": 1537377,
           "db_insert_end": None
          }
         ]
        )


    def test_mixed_dbref_processing(self):
        data_file = PdbDataFile(PdbFile(
         "DBREF  1LOL A    1   229  UNP    O26232   PYRF_METTH       1    228\n"
         "DBREF  1LOL B 1001  1229  UNP    O26232   PYRF_METTH       1    228\n"
         "DBREF1 1LOL C   61   322  GB                   AE017221\n"
         "DBREF2 1LOL C     46197919                      1534489     1537377"
        ))
        self.assertEqual(
         data_file.dbreferences,
         [
          {
           "chain_id": "A",
           "sequence_begin": 1,
           "insert_begin": None,
           "sequence_end": 229,
           "insert_end": None,
           "database": "UNP",
           "accession": "O26232",
           "db_id": "PYRF_METTH",
           "db_sequence_begin": 1,
           "db_insert_begin": None,
           "db_sequence_end": 228,
           "db_insert_end": None
          }, {
           "chain_id": "B",
           "sequence_begin": 1001,
           "insert_begin": None,
           "sequence_end": 1229,
           "insert_end": None,
           "database": "UNP",
           "accession": "O26232",
           "db_id": "PYRF_METTH",
           "db_sequence_begin": 1,
           "db_insert_begin": None,
           "db_sequence_end": 228,
           "db_insert_end": None
          }, {
           "chain_id": "C",
           "sequence_begin": 61,
           "insert_begin": None,
           "sequence_end": 322,
           "insert_end": None,
           "database": "GB",
           "accession": "46197919",
           "db_id": "AE017221",
           "db_sequence_begin": 1534489,
           "db_insert_begin": None,
           "db_sequence_end": 1537377,
           "db_insert_end": None
          }
         ]
        )
    def test_missing_dbref_processing(self):
        self.assertEqual(self.empty.dbreferences, [])



class SeqadvRecordTests(PdbDataFileTest):

    def test_seqadv_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SEQADV 1LOL GLU A  229  UNP  O26232              INSERTION\n"
         "SEQADV 1LOL GLU B 1229  UNP  O26232              INSERTION"
        ))
        self.assertEqual(
         data_file.sequence_differences,
         [
          {
           "residue_name": "GLU",
           "chain_id": "A",
           "residue_id": 229,
           "insert_code": None,
           "database": "UNP",
           "accession": "O26232",
           "db_residue_name": None,
           "db_residue_id": None,
           "conflict": "INSERTION"
          }, {
           "residue_name": "GLU",
           "chain_id": "B",
           "residue_id": 1229,
           "insert_code": None,
           "database": "UNP",
           "accession": "O26232",
           "db_residue_name": None,
           "db_residue_id": None,
           "conflict": "INSERTION"
          }
         ]
        )


    def test_missing_seqadv_processing(self):
        self.assertEqual(self.empty.sequence_differences, [])



class SeqresRecordTests(PdbDataFileTest):

    def test_seqres_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SEQRES   1 A    8  LEU ARG SER ARG ARG VAL ASP VAL MET ASP VAL MET ASN\n"
         "SEQRES   2 A    8  ARG LEU ILE\n"
         "SEQRES   1 B    8  LEU ARG SER ARG ARG VAL ASP VAL MET ASP VAL MET ASN\n"
         "SEQRES   2 B    8  ARG LEU ILE"
        ))
        self.assertEqual(
         data_file.residue_sequences,
         [
          {
           "chain_id": "A",
           "length": 8,
           "residues": [
            "LEU", "ARG", "SER", "ARG", "ARG", "VAL", "ASP", "VAL",
            "MET", "ASP", "VAL", "MET", "ASN", "ARG", "LEU", "ILE",
           ]
          }, {
           "chain_id": "B",
           "length": 8,
           "residues": [
            "LEU", "ARG", "SER", "ARG", "ARG", "VAL", "ASP", "VAL",
            "MET", "ASP", "VAL", "MET", "ASN", "ARG", "LEU", "ILE"
           ]
          }
         ]
        )


    def test_missing_seqres_processing(self):
        self.assertEqual(self.empty.residue_sequences, [])



class ModresRecordTests(PdbDataFileTest):

    def test_modres_processing(self):
        data_file = PdbDataFile(PdbFile(
         "MODRES 1LOL ASP A   10  ASP  GLYCOSYLATION SITE"
        ))
        self.assertEqual(
         data_file.modified_residues,
         [
          {
           "residue_name": "ASP",
           "chain_id": "A",
           "residue_id": 10,
           "insert_code": None,
           "standard_resisdue_name": 'ASP',
           "comment": "GLYCOSYLATION SITE"
          }
         ]
        )


    def test_missing_modres_processing(self):
        self.assertEqual(self.empty.modified_residues, [])



class HetRecordTests(PdbDataFileTest):

    def test_het_processing(self):
        data_file = PdbDataFile(PdbFile(
         "HET    BU2  A5001       6\n"
         "HET    BU2  B5002       6\n"
         "HET    XMP  A2001      24\n"
         "HET    XMP  B2002      24"
        ))
        self.assertEqual(
         data_file.hets,
         [
          {
           "het_name": "BU2",
           "chain_id": "A",
           "het_id": 5001,
           "insert_code": None,
           "atom_num": 6,
           "description": None
          }, {
           "het_name": "BU2",
           "chain_id": "B",
           "het_id": 5002,
           "insert_code": None,
           "atom_num": 6,
           "description": None
          }, {
           "het_name": "XMP",
           "chain_id": "A",
           "het_id": 2001,
           "insert_code": None,
           "atom_num": 24,
           "description": None
          }, {
           "het_name": "XMP",
           "chain_id": "B",
           "het_id": 2002,
           "insert_code": None,
           "atom_num": 24,
           "description": None
          }
         ]
        )


    def test_missing_het_processing(self):
        self.assertEqual(self.empty.hets, [])



class HetnamRecordTests(PdbDataFileTest):

    def test_hetnam_processing(self):
        data_file = PdbDataFile(PdbFile(
         "HETNAM     BU2 1,3-BUTANEDIOL\n"
         "HETNAM     XMP XANTHOSINE-5'-MONOPHOSPHATE"
        ))
        self.assertEqual(
         data_file.het_names,
         {
          "BU2": "1,3-BUTANEDIOL",
          "XMP": "XANTHOSINE-5'-MONOPHOSPHATE"
         }
        )


    def test_missing_hetnam_processing(self):
        self.assertEqual(self.empty.het_names, {})



class HetsynRecordTests(PdbDataFileTest):

    def test_hetsyn_processing(self):
        data_file = PdbDataFile(PdbFile(
         "HETSYN     BU2 BOOM BOOM BOMB; WYRDSTUFF\n"
         "HETSYN     XMP 5-MONOPHOSPHATE-9-BETA-D-RIBOFURANOSYL XANTHINE"
        ))
        self.assertEqual(
         data_file.het_synonyms,
         {
          "BU2": ["BOOM BOOM BOMB", "WYRDSTUFF"],
          "XMP": ["5-MONOPHOSPHATE-9-BETA-D-RIBOFURANOSYL XANTHINE"]
         }
        )


    def test_missing_hetsyn_processing(self):
        self.assertEqual(self.empty.het_synonyms, {})



class FormulRecordTests(PdbDataFileTest):

    def test_formul_processing(self):
        data_file = PdbDataFile(PdbFile(
         "FORMUL   3  BU2    2(C4 H10 O2)\n"
         "FORMUL   5  XMP    2(C10 H14 N4 O9 P 1+)\n"
         "FORMUL   7  HOH   *180(H2 O)"
        ))
        self.assertEqual(
         data_file.formulae,
         {
          "BU2": {"component_number": 3, "is_water": False, "formula": "2(C4 H10 O2)"},
          "XMP": {"component_number": 5, "is_water": False, "formula": "2(C10 H14 N4 O9 P 1+)"},
          "HOH": {"component_number": 7, "is_water": True, "formula": "180(H2 O)"}
         }
        )


    def test_missing_formul_processing(self):
        self.assertEqual(self.empty.formulae, {})



class HelixRecordTests(PdbDataFileTest):

    def test_helix_processing(self):
        data_file = PdbDataFile(PdbFile(
         "HELIX    1   1 VAL A   11  ASN A   13  5                                   3\n"
         "HELIX    2   2 ASN A   23  ARG A   35  1                                  13"
        ))
        self.assertEqual(
         data_file.helices,
         [
          {
           "helix_id": 1,
           "helix_name": "1",
           "start_residue_name": "VAL",
           "start_residue_chain_id": "A",
           "start_residue_id": 11,
           "start_residue_insert": None,
           "end_residue_name": "ASN",
           "end_residue_chain_id": "A",
           "end_residue_id": 13,
           "end_residue_insert": None,
           "helix_class": 5,
           "comment": None,
           "length": 3
          }, {
           "helix_id": 2,
           "helix_name": "2",
           "start_residue_name": "ASN",
           "start_residue_chain_id": "A",
           "start_residue_id": 23,
           "start_residue_insert": None,
           "end_residue_name": "ARG",
           "end_residue_chain_id": "A",
           "end_residue_id": 35,
           "end_residue_insert": None,
           "helix_class": 1,
           "comment": None,
           "length": 13
          }
         ]
        )


    def test_missing_helix_processing(self):
        self.assertEqual(self.empty.helices, [])



class SheetRecordTests(PdbDataFileTest):

    def test_sheet_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SHEET    1   A 2 LEU A  15  MET A  19  0\n"
         "SHEET    2   A 2 THR A  40  GLY A  44  1  O  LYS A  42   N  LEU A  17"
        ))
        self.assertEqual(
         data_file.sheets,
         [
          {
           "sheet_id": "A",
           "strand_count": 2,
           "strands": [{
            "strand_id": 1,
            "start_residue_name": "LEU",
            "start_residue_chain_id": "A",
            "start_residue_id": 15,
            "start_residue_insert": None,
            "end_residue_name": "MET",
            "end_residue_chain_id": "A",
            "end_residue_id": 19,
            "end_residue_insert": None,
            "sense": 0,
            "current_atom": None,
            "current_residue_name": None,
            "current_chain_id": None,
            "current_residue_id": None,
            "current_insert": None,
            "previous_atom": None,
            "previous_residue_name": None,
            "previous_chain_id": None,
            "previous_residue_id": None,
            "previous_insert": None
           }, {
            "strand_id": 2,
            "start_residue_name": "THR",
            "start_residue_chain_id": "A",
            "start_residue_id": 40,
            "start_residue_insert": None,
            "end_residue_name": "GLY",
            "end_residue_chain_id": "A",
            "end_residue_id": 44,
            "end_residue_insert": None,
            "sense": 1,
            "current_atom": "O",
            "current_residue_name": "LYS",
            "current_chain_id": "A",
            "current_residue_id": 42,
            "current_insert": None,
            "previous_atom": "N",
            "previous_residue_name": "LEU",
            "previous_chain_id": "A",
            "previous_residue_id": 17,
            "previous_insert": None
           }]
          }
         ]
        )


    def test_missing_sheet_processing(self):
        self.assertEqual(self.empty.sheets, [])



class SsbondRecordTests(PdbDataFileTest):

    def test_ssbond_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SSBOND   1 CYS A  123    CYS A  155                          1555   1555  2.04"
        ))
        self.assertEqual(
         data_file.ss_bonds,
         [{
          "serial_num": 1,
          "residue_name_1": "CYS",
          "chain_id_1": "A",
          "residue_id_1": 123,
          "insert_code_1": None,
          "residue_name_2": "CYS",
          "chain_id_2": "A",
          "residue_id_2": 155,
          "insert_code_2": None,
          "symmetry_1": "1555",
          "symmetry_2": "1555",
          "length": 2.04
         }]
        )


    def test_missing_ssbond_processing(self):
        self.assertEqual(self.empty.ss_bonds, [])



class LinkRecordTests(PdbDataFileTest):

    def test_link_processing(self):
        data_file = PdbDataFile(PdbFile(
         "LINK         O   TYR A 146                 K     K A 501     1555   1555  2.75"
        ))
        self.maxDiff = None
        self.assertEqual(
         data_file.links,
         [
          {
           "atom_1": "O",
           "alt_loc_1": None,
           "residue_name_1": "TYR",
           "chain_id_1": "A",
           "residue_id_1": 146,
           "insert_code_1": None,
           "atom_2": "K",
           "alt_loc_2": None,
           "residue_name_2": "K",
           "chain_id_2": "A",
           "residue_id_2": 501,
           "insert_code_2": None,
           "symmetry_1": "1555",
           "symmetry_2": "1555",
           "length": 2.75
          }
         ]
        )


    def test_missing_link_processing(self):
        self.assertEqual(self.empty.links, [])



class CispepRecordTests(PdbDataFileTest):

    def test_cispep_processing(self):
        data_file = PdbDataFile(PdbFile(
         "CISPEP     ASP B 1188    PRO B 1189          0         0.35"
        ))
        self.assertEqual(
         data_file.cis_peptides,
         [
          {
           "serial_num": None,
           "residue_name_1": "ASP",
           "chain_id_1": "B",
           "residue_id_1": 1188,
           "insert_1": None,
           "residue_name_2": "PRO",
           "chain_id_2": "B",
           "residue_id_2": 1189,
           "insert_2": None,
           "model_number": 0,
           "angle": 0.35
          }
         ]
        )


    def test_missing_cispep_processing(self):
        self.assertEqual(self.empty.cis_peptides, [])



class SiteRecordTests(PdbDataFileTest):

    def test_site_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SITE     1 AC1  6 ASP A  70  LYS A  72  LEU A 123  VAL A 155\n"
         "SITE     2 AC1  6 XMP A2001  HOH A3015\n"
         "SITE     1 AC3  8 ALA A  18  ASP A  20  LYS A  42  ASP A  70\n"
         "SITE     2 AC3  8 MET A 126  SER A 127  SER A 158  PRO A 180"
        ))
        self.assertEqual(
         data_file.sites,
         [
          {
           "site_id": "AC1",
           "residue_count": 6,
           "residues": [
            {"residue_name": "ASP", "chain": "A", "residue_id": 70, "insert_code": None},
            {"residue_name": "LYS", "chain": "A", "residue_id": 72, "insert_code": None},
            {"residue_name": "LEU", "chain": "A", "residue_id": 123, "insert_code": None},
            {"residue_name": "VAL", "chain": "A", "residue_id": 155, "insert_code": None},
            {"residue_name": "XMP", "chain": "A", "residue_id": 2001, "insert_code": None},
            {"residue_name": "HOH", "chain": "A", "residue_id": 3015, "insert_code": None}
           ]
          }, {
           "site_id": "AC3",
           "residue_count": 8,
           "residues": [
            {"residue_name": "ALA", "chain": "A", "residue_id": 18, "insert_code": None},
            {"residue_name": "ASP", "chain": "A", "residue_id": 20, "insert_code": None},
            {"residue_name": "LYS", "chain": "A", "residue_id": 42, "insert_code": None},
            {"residue_name": "ASP", "chain": "A", "residue_id": 70, "insert_code": None},
            {"residue_name": "MET", "chain": "A", "residue_id": 126, "insert_code": None},
            {"residue_name": "SER", "chain": "A", "residue_id": 127, "insert_code": None},
            {"residue_name": "SER", "chain": "A", "residue_id": 158, "insert_code": None},
            {"residue_name": "PRO", "chain": "A", "residue_id": 180, "insert_code": None}
           ]
          }
         ]
        )


    def test_missing_site_processing(self):
        self.assertEqual(self.empty.sites, [])



class CrystalRecordTests(PdbDataFileTest):

    def test_crystal_record_processing(self):
        data_file = PdbDataFile(PdbFile(
         "CRYST1   57.570   55.482   66.129  90.00  94.28  90.00 P 1 21 1      4"
        ))
        self.assertEqual(data_file.crystal_a, 57.57)
        self.assertEqual(data_file.crystal_b, 55.482)
        self.assertEqual(data_file.crystal_c, 66.129)
        self.assertEqual(data_file.crystal_alpha, 90.0)
        self.assertEqual(data_file.crystal_beta, 94.28)
        self.assertEqual(data_file.crystal_gamma, 90.0)
        self.assertEqual(data_file.crystal_s_group, "P 1 21 1")
        self.assertEqual(data_file.crystal_z, 4)


    def test_missing_crystal_processing(self):
        self.assertEqual(self.empty.crystal_a, None)
        self.assertEqual(self.empty.crystal_b, None)
        self.assertEqual(self.empty.crystal_c, None)
        self.assertEqual(self.empty.crystal_alpha, None)
        self.assertEqual(self.empty.crystal_beta, None)
        self.assertEqual(self.empty.crystal_gamma, None)
        self.assertEqual(self.empty.crystal_s_group, None)
        self.assertEqual(self.empty.crystal_z, None)



class OrigxRecordTests(PdbDataFileTest):

    def test_origx_record_processing(self):
        data_file = PdbDataFile(PdbFile(
         "ORIGX1      0.963457  0.136613  0.230424       16.61000\n"
         "ORIGX2     -0.158977  0.983924  0.081383       13.72000\n"
         "ORIGX3     -0.215598 -0.115048  0.969683       37.65000"
        ))
        self.assertEqual(data_file.crystal_o11, 0.963457)
        self.assertEqual(data_file.crystal_o12, 0.136613)
        self.assertEqual(data_file.crystal_o13, 0.230424)
        self.assertEqual(data_file.crystal_t1, 16.61)
        self.assertEqual(data_file.crystal_o21, -0.158977)
        self.assertEqual(data_file.crystal_o22, 0.983924)
        self.assertEqual(data_file.crystal_o23, 0.081383)
        self.assertEqual(data_file.crystal_t2, 13.72)
        self.assertEqual(data_file.crystal_o31, -0.215598)
        self.assertEqual(data_file.crystal_o32, -0.115048)
        self.assertEqual(data_file.crystal_o33, 0.969683)
        self.assertEqual(data_file.crystal_t3, 37.65)


    def test_missing_origx_processing(self):
        self.assertEqual(self.empty.crystal_o11, None)
        self.assertEqual(self.empty.crystal_o12, None)
        self.assertEqual(self.empty.crystal_o13, None)
        self.assertEqual(self.empty.crystal_t1, None)
        self.assertEqual(self.empty.crystal_o21, None)
        self.assertEqual(self.empty.crystal_o22, None)
        self.assertEqual(self.empty.crystal_o23, None)
        self.assertEqual(self.empty.crystal_t2, None)
        self.assertEqual(self.empty.crystal_o31, None)
        self.assertEqual(self.empty.crystal_o32, None)
        self.assertEqual(self.empty.crystal_o33, None)
        self.assertEqual(self.empty.crystal_t3, None)



class ScaleRecordTests(PdbDataFileTest):

    def test_scale_record_processing(self):
        data_file = PdbDataFile(PdbFile(
         "SCALE1      0.017370  0.000000  0.001301        0.00000\n"
         "SCALE2      0.000000  0.018024  0.000000        0.00000\n"
         "SCALE3      0.000000  0.000000  0.015164        0.00000"
        ))
        self.assertEqual(data_file.crystal_s11, 0.01737)
        self.assertEqual(data_file.crystal_s12, 0.0)
        self.assertEqual(data_file.crystal_s13, 0.001301)
        self.assertEqual(data_file.crystal_u1, 0.0)
        self.assertEqual(data_file.crystal_s21, 0.0)
        self.assertEqual(data_file.crystal_s22, 0.018024)
        self.assertEqual(data_file.crystal_s23, 0.0)
        self.assertEqual(data_file.crystal_u2, 0.0)
        self.assertEqual(data_file.crystal_s31, 0.0)
        self.assertEqual(data_file.crystal_s32, 0.0)
        self.assertEqual(data_file.crystal_s33, 0.015164)
        self.assertEqual(data_file.crystal_u3, 0.0)


    def test_missing_scale_processing(self):
        self.assertEqual(self.empty.crystal_s11, None)
        self.assertEqual(self.empty.crystal_s12, None)
        self.assertEqual(self.empty.crystal_s13, None)
        self.assertEqual(self.empty.crystal_u1, None)
        self.assertEqual(self.empty.crystal_s21, None)
        self.assertEqual(self.empty.crystal_s22, None)
        self.assertEqual(self.empty.crystal_s23, None)
        self.assertEqual(self.empty.crystal_u2, None)
        self.assertEqual(self.empty.crystal_s31, None)
        self.assertEqual(self.empty.crystal_s32, None)
        self.assertEqual(self.empty.crystal_s33, None)
        self.assertEqual(self.empty.crystal_u3, None)



class MtrixRecordTests(PdbDataFileTest):

    def test_mtrix_record_processing(self):
        data_file = PdbDataFile(PdbFile(
         "MTRIX1   1 -1.000000  0.000000  0.000000        0.00000    1\n"
         "MTRIX2   1  0.000000  1.000000  0.000000        0.00000    1\n"
         "MTRIX3   1  0.000000  0.000000 -1.000000        0.00000    1"
        ))
        self.assertEqual(data_file.crystal_serial_1, 1)
        self.assertEqual(data_file.crystal_m11, -1.0)
        self.assertEqual(data_file.crystal_m12, 0.0)
        self.assertEqual(data_file.crystal_m13, 0.0)
        self.assertEqual(data_file.crystal_v1, 0.0)
        self.assertEqual(data_file.crystal_i_given_1, True)
        self.assertEqual(data_file.crystal_serial_2, 1)
        self.assertEqual(data_file.crystal_m21, 0.0)
        self.assertEqual(data_file.crystal_m22, 1.0)
        self.assertEqual(data_file.crystal_m23, 0.0)
        self.assertEqual(data_file.crystal_v2, 0.0)
        self.assertEqual(data_file.crystal_i_given_3, True)
        self.assertEqual(data_file.crystal_serial_3, 1)
        self.assertEqual(data_file.crystal_m31, 0.0)
        self.assertEqual(data_file.crystal_m32, 0.0)
        self.assertEqual(data_file.crystal_m33, -1.0)
        self.assertEqual(data_file.crystal_v3, 0.0)
        self.assertEqual(data_file.crystal_i_given_3, True)


    def test_missing_mtrix_processing(self):
        self.assertEqual(self.empty.crystal_serial_1, None)
        self.assertEqual(self.empty.crystal_m11, None)
        self.assertEqual(self.empty.crystal_m12, None)
        self.assertEqual(self.empty.crystal_m13, None)
        self.assertEqual(self.empty.crystal_v1, None)
        self.assertEqual(self.empty.crystal_i_given_3, False)
        self.assertEqual(self.empty.crystal_serial_1, None)
        self.assertEqual(self.empty.crystal_m21, None)
        self.assertEqual(self.empty.crystal_m22, None)
        self.assertEqual(self.empty.crystal_m23, None)
        self.assertEqual(self.empty.crystal_v2, None)
        self.assertEqual(self.empty.crystal_i_given_3, False)
        self.assertEqual(self.empty.crystal_serial_1, None)
        self.assertEqual(self.empty.crystal_m31, None)
        self.assertEqual(self.empty.crystal_m32, None)
        self.assertEqual(self.empty.crystal_m33, None)
        self.assertEqual(self.empty.crystal_v3, None)
        self.assertEqual(self.empty.crystal_i_given_3, False)



class ModelRecordTests(PdbDataFileTest):

    def test_model_processing(self):
        data_file = PdbDataFile(PdbFile(
         "MODEL        1\n"
         "ATOM    107  N   GLY A  13      12.681  37.302 -25.211 1.000 15.56           N\n"
         "ENDMDL\n"
         "MODEL        2\n"
         "ATOM    107  N   GLY A  13      12.681  37.302 -25.211 1.000 15.56           N\n"
         "ENDMDL"
        ))
        self.assertEqual(
         data_file.models,
         [
          {
           "model_id": 1,
           "start_record": 1,
           "end_record": 3
          }, {
           "model_id": 2,
           "start_record": 4,
           "end_record": 6
          }
         ]
        )


    def test_missing_model_processing(self):
        self.assertEqual(
         self.empty.models,
         [
          {
           "model_id": 1,
           "start_record": 0,
           "end_record": 0
          }
         ]
        )



class AtomRecordTests(PdbDataFileTest):

    def test_atom_processing(self):
        data_file = PdbDataFile(PdbFile(
         "ATOM    107  N   GLY A  13      12.681  37.302 -25.211 1.000 15.56           N\n"
         "ATOM    108  CA  GLY A  13      11.982  37.996 -26.241 1.000 16.92           C"
        ))
        self.assertEqual(
         data_file.atoms,
         [
          {
           "atom_id": 107,
           "atom_name": "N",
           "alt_loc": None,
           "residue_name": "GLY",
           "chain_id": "A",
           "residue_id": 13,
           "insert_code": None,
           "x": 12.681,
           "y": 37.302,
           "z": -25.211,
           "occupancy": 1.0,
           "temperature_factor": 15.56,
           "element": "N",
           "charge": None,
           "model_id": 1
          }, {
           "atom_id": 108,
           "atom_name": "CA",
           "alt_loc": None,
           "residue_name": "GLY",
           "chain_id": "A",
           "residue_id": 13,
           "insert_code": None,
           "x": 11.982,
           "y": 37.996,
           "z": -26.241,
           "occupancy": 1.0,
           "temperature_factor": 16.92,
           "element": "C",
           "charge": None,
           "model_id": 1
          }
         ]
        )


    def test_missing_atom_processing(self):
        self.assertEqual(self.empty.atoms, [])



class AnisouRecordTests(PdbDataFileTest):

    def test_anisou_processing(self):
        data_file = PdbDataFile(PdbFile(
         "ANISOU  107  N   GLY A  13     2406   1892   1614    198    519   -328       N\n"
         "ANISOU  108  CA  GLY A  13     2748   2004   1679    -21    155   -419       C"
        ))
        self.assertEqual(
         data_file.anisou,
         [
          {
           "atom_id": 107,
           "atom_name": "N",
           "alt_loc": None,
           "residue_name": "GLY",
           "chain_id": "A",
           "residue_id": 13,
           "insert_code": None,
           "u11": 2406,
           "u22": 1892,
           "u33": 1614,
           "u12": 198,
           "u13": 519,
           "u23": -328,
           "element": "N",
           "charge": None,
           "model_id": 1
          }, {
           "atom_id": 108,
           "atom_name": "CA",
           "alt_loc": None,
           "residue_name": "GLY",
           "chain_id": "A",
           "residue_id": 13,
           "insert_code": None,
           "u11": 2748,
           "u22": 2004,
           "u33": 1679,
           "u12": -21,
           "u13": 155,
           "u23": -419,
           "element": "C",
           "charge": None,
           "model_id": 1
          }
         ]
        )


    def test_missing_anisou_processing(self):
        self.assertEqual(self.empty.anisou, [])



class TerRecordTests(PdbDataFileTest):

    def test_ter_processing(self):
        data_file = PdbDataFile(PdbFile(
         "TER     109      GLY A  13"
        ))
        self.assertEqual(
         data_file.termini,
         [
          {
           "atom_id": 109,
           "residue_name": "GLY",
           "chain_id": "A",
           "residue_id": 13,
           "insert_code": None,
           "model_id": 1
          }
         ]
        )


    def test_missing_ter_processing(self):
        self.assertEqual(self.empty.termini, [])



class HetatmRecordTests(PdbDataFileTest):

    def test_hetatm_processing(self):
        data_file = PdbDataFile(PdbFile(
         "HETATM 8237 MG    MG A1001      13.872  -2.555 -29.045  1.00 27.36          MG"
        ))
        self.assertEqual(
         data_file.heteroatoms,
         [
          {
           "atom_id": 8237,
           "atom_name": "MG",
           "alt_loc": None,
           "residue_name": "MG",
           "chain_id": "A",
           "residue_id": 1001,
           "insert_code": None,
           "x": 13.872,
           "y": -2.555,
           "z": -29.045,
           "occupancy": 1.0,
           "temperature_factor": 27.36,
           "element": "MG",
           "charge": None,
           "model_id": 1
          }
         ]
        )


    def test_missing_hetatm_processing(self):
        self.assertEqual(self.empty.heteroatoms, [])



class ConectRecordTests(PdbDataFileTest):

    def test_conect_processing(self):
        data_file = PdbDataFile(PdbFile(
         "CONECT 1179  746 1184 1195 1203\n"
         "CONECT 1179 1211 1222"
        ))
        self.assertEqual(
         data_file.connections,
         [
          {
           "atom_id": 1179,
           "bonded_atoms": [746, 1184, 1195, 1203, 1211, 1222]
          }
         ]
        )


    def test_missing_conect_processing(self):
        self.assertEqual(self.empty.connections, [])



class MiscRecordTests(PdbDataFileTest):

    def test_misc_processing(self):
        data_file = PdbDataFile(PdbFile(
         "MASTER       40    0    0    0    0    0    0    6 2930    2    0   29"
        ))
        self.assertEqual(
         data_file.master,
         {
          "remark_num": 40,
          "het_num": 0,
          "helix_num": 0,
          "sheet_num": 0,
          "site_num": 0,
          "crystal_num": 6,
          "coordinate_num": 2930,
          "ter_num": 2,
          "conect_num": 0,
          "seqres_num": 29
         }
        )


    def test_missing_misc_processing(self):
        self.assertEqual(self.empty.master, None)
