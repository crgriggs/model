import slate

with open('iv2.pdf') as f:
    doc = slate.PDF(f)
    print doc
