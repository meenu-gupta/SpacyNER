import os
import spacy


updated_model_dir = '/home/softuvo/Garima/SpacyNER/updated_model'
# Use updated saved model
print("Loading updated model from:", updated_model_dir)
nlp = spacy.load(updated_model_dir)
doc= nlp("""'what movies star bruce willis', 'show me films with drew barrymore from the 1980s', 'what mo'""")

# for ent in doc.ents:
    # print(ent.text, ent.start_char, ent.end_char, ent.label_)

for token in doc:
    print(token, token.ent_type_)

        
        