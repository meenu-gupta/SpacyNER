from itertools import chain
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import numpy as np
import warnings
import pickle
import random
import tqdm
import json
import os
import re
warnings.filterwarnings("ignore")

def dataset(path):
    files = os.listdir(path)
    print(files)
    files = [(file, f"{file.replace('txt', 'ann')}") for file in files if '.txt' in file]
    df = pd.DataFrame()
    i = 1
    for iof in tqdm.tqdm(files):
        try:
            print(f'doc_num={i}, {iof[0]}')
            with open(os.path.join(path, iof[0]), "r", encoding = "utf-8", errors = "strict") as f:
                text = f.read()
            sent_df = pd.DataFrame(text.split('\n'), columns = ['text'])   #now split each line in a row and put it in a dataframe 
            sent_df['text'] = sent_df.text.str.strip().str.replace('\t', ' ') # remove extra space and convert tabs into spaces  
            sent_df = sent_df[sent_df.text != ''].reset_index(drop=True)  #to handle empty line in text file  
            sent_df['sent_num'] = sent_df.index + 1    #new column with name sent_num and its values start from 1  
            sent_df['text'] = sent_df['text'].str.split() #split each word
            sent_df['doc_num'] = i
            i += 1
            
            sent_df = sent_df.explode('text')

            idx_df=pd.DataFrame([(ele.start(), ele.end() - 1) for ele in re.finditer(r'\S+', text)], columns=['start', 'end'])
            sent_df = sent_df.merge(idx_df.astype({'start': int,'end': int}), right_index=True, left_index=True)
            sent_df  =sent_df.astype({"sent_num": int, "start": int, "end":int})
            ann_df =  pd.read_csv(os.path.join(path, iof[1]), sep='\t', names=['enity_num', 'ner', 'text'])
            ann_df[['ner', 'start', 'end']] = ann_df['ner'].str.split().apply(pd.Series)

            ann_df['len'] = ann_df['text'].str.split().apply(len)
            sent_df = sent_df.merge(ann_df.astype({'start': int}), on='start', how='left')
            df = df.append(sent_df.rename(columns={'text_x':'text'}))
            
            spacy_format = df.loc[df.ner.notnull()].groupby(
                ['doc_num','sent_num', 'ner']
            ).agg(
                {
                    'text': ' '.join, 
                    'start': 'unique', 
                    'end_x': 'unique', 
                    'ner': 'unique'
                }
            )

            DATA = []
            entity = list()
            sent = []
            for idx in spacy_format.index:
                entity_ele = dict()
                # sent = entity_ele['sentence']
                sent_ele = dict()
                # sent_ele['sentence'] = spacy_format.loc[idx, 'text']
                sent_ele['sentence'] = spacy_format.loc[idx,'text']
                entity_ele['entities'] = [(
                    spacy_format.loc[idx, 'start'][0], 
                    spacy_format.loc[idx, 'end_x'][0], 
                    spacy_format.loc[idx, 'ner'][0]
                )]
                entity.append(entity_ele)

                spacy_format= (sent_ele['sentence'], entity_ele)
                DATA.append(spacy_format)
        

        except Exception as ex:
            print(iof)
            print(ex)
            # raise ex

    return DATA

TRAIN_DATA = dataset("/home/softuvo/Garima/SpacyNER/data/train")
TEST_DATA = dataset("/home/softuvo/Garima/SpacyNER/data/test")
VALID_DATA= dataset("/home/softuvo/Garima/SpacyNER/data/valid")
print(type(TRAIN_DATA))
print(type(TEST_DATA))
print(type(VALID_DATA))   #should be a list

dir_path = "/home/softuvo/Garima/SpacyNER/data"

with open(os.path.join(dir_path, '') + "entity_train.pkl", "wb") as f:
    pickle.dump(TRAIN_DATA, f)
with open(os.path.join(dir_path, '') + "entity_test.pkl", "wb") as f:
    pickle.dump(TEST_DATA, f)

with open(os.path.join(dir_path, '') + "entity_valid.pkl", "wb") as f:
    pickle.dump(VALID_DATA, f)

model = r"/home/softuvo/Garima/SpacyNER/data/entity_train.pkl"
file_obj = open(model, 'rb')
file =  pickle.load(file_obj)