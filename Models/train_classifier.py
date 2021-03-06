# -*- coding: utf-8 -*-
"""
Created on Fri Dec 24 20:08:15 2021

@author:Manee44
"""

# import libraries
import pandas as pd
import sys
import nltk
nltk.download(['wordnet', 'punkt', 'stopwords'])
from sqlalchemy import create_engine
from nltk.tokenize import word_tokenize 
from nltk.corpus import stopwords 
from nltk.stem import WordNetLemmatizer
import re
import pickle
import pandas as pd 
from sqlalchemy import create_engine
from sklearn.pipeline import Pipeline 
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.model_selection import train_test_split,  GridSearchCV 
from sklearn.metrics import classification_report

# 
def load_data(db_path):
     """
     Function: 
     load data from database
     
     Args:
     db_path:DataBase Path
     
     Return:
       X: Messages Data Frame
       Y: Targeted Data Frame
     """
    engine = create_engine('sqlite:///'+db_path)
    df = pd.read_sql_table('Disater_Response',engine)
    X = df['message']
    Y = df.iloc[:, 4:]
    category_names = Y.columns
    return X,Y


def tokenize(text):
    """
     Function: 
     Clean and Split Text into Root Words
     
     Args:
     text: Message Text
     
     Return:
     lemm: List of Cleaned Root Words
     """
    text = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
    words = word_tokenize(text)
    stop = stopwords.words("english")
    words = [w for w in words if w not in stop]
    lemm = [WordNetLemmatizer().lemmatize(w) for w in words]
    return lemm

def buildmodel():
    """
     Function:
     build a model for classifing the disaster messages
     
     Return:
       cv(list of str): classification model
     """
    # Create a Pipeline
    pipeline_rfc = Pipeline([
        ('vect', CountVectorizer(tokenizer = tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf',  MultiOutputClassifier(RandomForestClassifier(n_estimators=100)))
    ])
    # Create Grid Search Parameters
    parameters =  {'features__text_pipeline__vect__ngram_range': ((1, 1), (1, 2)),
        'features__text_pipeline__vect__max_df': (0.5, 0.75, 1.0),
        'features__text_pipeline__vect__max_features': (None, 5000, 10000),
        'features__text_pipeline__tfidf__use_idf': (True, False),
        'clf__n_estimators': [50, 100, 200],
        'clf__min_samples_split': [2, 3, 4],
        'features__transformer_weights': (
            {'text_pipeline': 1, 'starting_verb': 0.5},
            {'text_pipeline': 0.5, 'starting_verb': 1},
            {'text_pipeline': 0.8, 'starting_verb': 1},
        )
              }
    cv = GridSearchCV(pipeline_rfc, param_grid=parameters)
    return cv


def evaluate_model(model, X_test, Y_test):
    """
    Function: Evaluate the model and print the f1 score, precision and recall for each output category of the dataset.
    Args:
    model: the classification model
    X_test: test messages
    Y_test: test target
    """
    y_pred = model.predict(X_test)
    class_report = classification_report(Y_test, y_pred)
    print(class_report)  
    

def save_model(model,model_path):
    """
    Function:
    Export Model to Pickle File
    
    Args:
    model: the classification model
    model_path (str): the path of pickle file
    """
    with open(model_path, 'wb') as file:
        pickle.dump(model, file)



def main():
    if len(sys.argv) == 3:
        db_path, model_path = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(db_path))
        X, Y = load_data(db_path)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Modeling On Process:')
        model = buildmodel()
        
        print('Training On Process:')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test)

        print('Saving model...\n    MODEL: {}'.format(model_path))
        save_model(model, model_path)

        print('Trained model saved!')

    else:
        print('Please make sure the provided filepath is in correct order.')


if __name__ == '__main__':
    main()
