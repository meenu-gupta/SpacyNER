import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example
from evaluate import calc_precision, calc_recall, calc_f1, evaluate
from itertools import chain
from data import file, TRAIN_DATA, TEST_DATA, VALID_DATA 
from pathlib import Path
import warnings
import random

warnings.filterwarnings("ignore")
updated_model_dir = '/home/softuvo/Garima/SpacyNER/updated_model'
valid_f1scores=[]
test_f1scores=[]
## Update existing spacy model and store into a folder
def update_model(model='en_core_web_md', output_dir=updated_model_dir, n_iter=100):
    """Load the model, set up the pipeline and train the entity recognizer."""
    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank("en")  # create blank Language class
        print("Created blank 'en' model")

    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")

        nlp.add_pipe(ner, last=True)
    # otherwise, get it so we can add labels
    else:
        ner = nlp.get_pipe("ner")

    # add labels
    for _, annotations in file:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):  # only train NER
        # reset and initialize the weights randomly – but only if we're
        # training a new model
        if model is None:
            nlp.begin_training()
        for itr in range(n_iter):
            random.shuffle(file)
            losses = {}
            batches = spacy.util.minibatch(file, size = compounding(16.0, 64.0, 1.5))
            for batch in batches:
                for text, annotations in batch:
                    doc = nlp.make_doc(str(text))
                    example = Example.from_dict(doc, annotations)
                    nlp.update([example],losses = losses, drop = 0.5)
            print("Losses", losses)
            scores = evaluate(nlp, VALID_DATA)
            valid_f1scores.append(scores["textcat_f"])
            
            print('=======================================')
            print('Interation = '+str(itr))
            print('Losses = '+str(losses))
            print('===============VALID DATA========================')
            print('F1-score = '+str(scores["textcat_f"]))
            print('Precision = '+str(scores["textcat_p"]))
            print('Recall = '+str(scores["textcat_r"]))
            
            scores = evaluate(nlp,TEST_DATA)
            test_f1scores.append(scores["textcat_f"])
            print('===============TEST DATA========================')
            print('F1-score = '+str(scores["textcat_f"]))
            print('Precision = '+str(scores["textcat_p"]))
            print('Recall = '+str(scores["textcat_r"]))
            print('=======================================')
    

    # test the trained model
    for text, _ in TEST_DATA:
        doc = nlp(text)
        print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
        print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])

    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)

    return valid_f1scores, test_f1scores, nlp

update_model()

    

# Finally train the model by calling above function        


