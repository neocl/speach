from speach import elan

# read an ELAN file
eaf = elan.read_eaf('./test_data/fables_01_03_aesop_64kb.eaf')

# accessing metadata
print("Accessing EAF Metadata")
print("-" * 60)
print(f"Author: {eaf.author} | Date: {eaf.date} | Format: {eaf.fileformat} | Version: {eaf.version}")
print(f"Media file: {eaf.media_file}")
print(f"Time units: {eaf.time_units}")
print(f"Media URL: {eaf.media_url} | MIME type: {eaf.mime_type}")
print(f"Media relative URL: {eaf.relative_media_url}")

# loop through all tiers in this eaf file
print("\nBasic ELAN demo: looping through all tiers and their annotations")
print("-" * 60)
for tier in eaf:
    print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
    # loop through all annotations in this tier
    for ann in tier:
        print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts} :: {ann.to_ts}] {ann.text}")

# loop through the root tiers only (i.e. ignored dependent tiers)
print("\n\nDemo nested ELAN file: loop through root tiers only")
print("-" * 60)
for tier in eaf.roots:
    print(f"[+]-- {tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
    for ann in tier:
        print(f" |- {ann.ID.rjust(4, ' ')}. [{ann.from_ts} -- {ann.to_ts}] {ann.text}")
    for child_tier in tier.children:
        print(f" |--[+]-- Child tier: {child_tier.ID} | Participant: {child_tier.participant} | Type: {child_tier.type_ref}")
        for child_ann in child_tier:
            # Dealing with ref annotation
            if child_ann.ref:
                print(f" .   |- {child_ann.ID.rjust(4, ' ')}. {child_ann.text} >> [#{child_ann.ref.ID}] `{child_ann.ref}`")
            else:
                print(f" .   |- {child_ann.ID.rjust(4, ' ')}. [{child_ann.from_ts} -- {child_ann.to_ts}] {child_ann.text}")
