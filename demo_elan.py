from speach import elan

# read an ELAN file
eaf = elan.open_eaf('./test/data/test.eaf')

# accessing metadata
print(f"Author: {eaf.author} | Date: {eaf.date} | Format: {eaf.fileformat} | Version: {eaf.version}")
print(f"Media file: {eaf.media_file}")
print(f"Time units: {eaf.time_units}")
print(f"Media URL: {eaf.media_url} | MIME type: {eaf.mime_type}")
print(f"Media relative URL: {eaf.relative_media_url}")

# accessing tiers & annotations
for tier in eaf.tiers():
    print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
    for ann in tier.annotations:
        print(f"{ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")


# test parsing EAF files with nested tiers
elan2 = elan.open_eaf('./data/test_nested.eaf')
# accessing nested tiers
for tier in eaf.roots:
    print(f"{tier.ID} | Participant: {tier.participant} | Type: {tier.type_ref}")
    print(f"  -- {ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")    
    for child_tier in tier.children:
        print(f"    | {child_tier.ID} | Participant: {child_tier.participant} | Type: {child_tier.type_ref}")
        for ann in child_tier.annotations:
            print(f"    |- {ann.ID.rjust(4, ' ')}. [{ann.from_ts.ts} -- {ann.to_ts.ts}] {ann.value}")
