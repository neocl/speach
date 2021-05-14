import os
from speach import media
from speach import elan
from chirptext import chio

# -----------------------------------------------------------------------------
# create a folder to store processed data
# -----------------------------------------------------------------------------
if not os.path.isdir("./test_data/processed"):
    os.mkdir("./test_data/processed")

# -----------------------------------------------------------------------------
# converting the source ogg file into m4a format
# -----------------------------------------------------------------------------
media.convert("./test_data/fables_01_03_aesop_64kb.ogg", "./test_data/processed/test.m4a")

# -----------------------------------------------------------------------------
# cutting audio file by timestamps
# -----------------------------------------------------------------------------
media.cut("./test_data/processed/test.m4a", "./test_data/processed/test_before_10.ogg", to_ts="00:00:10")
media.cut("./test_data/processed/test.m4a", "./test_data/processed/test_after_10.ogg", from_ts="00:00:15")
media.cut("./test_data/processed/test.m4a", "./test_data/processed/test_10-15.ogg", from_ts="00:00:10", to_ts="00:00:15")

# --------------------------------------------------------------------------------------------
# More complex use case
# Read an ELAN transcription file and:
#    1. Cut all utterances into separated ogg files
#    2. Write annotation text into separated text files
#    3. Write all utterances into a CSV file with annotation IDs and individual audio filenames
# --------------------------------------------------------------------------------------------
eaf = elan.read_eaf("./test_data/fables_01_03_aesop_64kb.eaf")
csv_rows = [["annID", "Text", "Filename"]]
for ann in eaf["Story"]:
    csv_rows.append([ann.ID, ann.text, f"test_{ann.ID}.ogg"])
    chio.write_file(f"./test_data/processed/test_{ann.ID}.txt", ann.text)
    eaf.cut(ann, f"./test_data/processed/test_{ann.ID}.ogg")
chio.write_csv("./test_data/processed/test_sentences.csv", csv_rows)
