from pathlib import Path
from speach import elan


transcript_folder = Path('./test/data/')
csv_data = []
for child_file in transcript_folder.iterdir():
    if child_file.suffix.endswith('.eaf'):
        print(child_file.name)
        c = 0
        eaf = elan.open_eaf(child_file)
        for tier in eaf.roots:
            if tier.type_ref == 'Utterance':
                print(f"  | {tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
                for ann in tier.annotations:
                    if 'BABYNAME' in ann.value:
                        c += 1
                        print(f"  | -- {tier.ID} --> {tier.participant}: {ann.value}")
        print(c)
        csv_data.append((child_file.name, c))

for fn, c in csv_data:
    print(f"{fn}\t{c}")
