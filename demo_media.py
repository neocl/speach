from pathlib import Path
from speach import media
from speach import elan


ELAN_DIR = Path("~/Documents/ELAN")

# converting a wave file into an ogg file
media.convert(ELAN_DIR / "test.wav", ELAN_DIR / "test.ogg")

# cutting audio file by timestamps
media.cut(ELAN_DIR / "test.wav", ELAN_DIR / "test_before10.ogg", to_ts="00:00:10")
media.cut(ELAN_DIR / "test.wav", ELAN_DIR / "test_after15.ogg", from_ts="00:00:15")
media.cut(ELAN_DIR / "test.wav", ELAN_DIR / "test_10-15.ogg", from_ts="00:00:10", to_ts="00:00:15")

# Cutting ELAN transcription
eaf = elan.read_eaf(ELAN_DIR / "test.eaf")
for idx, ann in enumerate(eaf["Person1 (Utterance)"], start=1):
    eaf.cut(ann, ELAN_DIR / f"test_person1_{idx}.ogg")
