import re
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Small synthetic teaching corpus: the model is a baseline, not a benchmark.
DATA = [
('I love this product amazing quality excellent wonderful', 'positive'), ('Absolutely fantastic and wonderful', 'positive'),
('Great service very happy thank you', 'positive'), ('This is the best purchase I have made', 'positive'),
('Beautiful design and excellent work', 'positive'), ('Thanks I really enjoyed it', 'positive'),
('Works perfectly highly recommend', 'positive'), ('So good and lovely brilliant', 'positive'),
('I hate this terrible quality awful', 'negative'), ('Very disappointed and horrible', 'negative'),
('Worst service ever bad experience', 'negative'), ('Not good I dislike it', 'negative'),
('Poor quality and waste of money', 'negative'), ('Broken frustrating useless and horrible', 'negative'),
('I regret buying this and would not recommend', 'negative'), ('This is a scam and a terrible experience', 'negative'),
('What is the price?', 'neutral'), ('Where can I buy this?', 'neutral'),
('Please share the details', 'neutral'), ('When will this be available?', 'neutral'),
('Is this open today?', 'neutral'), ('I have a question about the size', 'neutral'),
('The package arrived on Monday', 'neutral'), ('This product comes in blue', 'neutral'),
('Follow me for a free iPhone giveaway click the link', 'neutral'),
('Earn daily profit guaranteed check my page now', 'neutral'),
]
_model = Pipeline([('tfidf', TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
                   ('classifier', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))])
_model.fit([x[0] for x in DATA], [x[1] for x in DATA])
POSITIVE = {'love','loved','amazing','excellent','fantastic','wonderful','great','happy','best','beautiful','perfect','perfectly','recommend','enjoyed','brilliant','awesome','delightful','helpful','thanks','thank','good','lovely'}
NEGATIVE = {'hate','terrible','awful','worst','disappointed','bad','poor','broken','frustrating','useless','horrible','regret','scam','fraud','annoying','late','waste','fake','dislike','angry','sad','unhappy'}
NEGATORS = {'not','no','never','neither','hardly','isnt','wasnt','dont','didnt','cant','wont'}

def predict(text):
    text = str(text or '').strip()
    if not text:
        return {'sentiment':'neutral','confidence':None,'probabilities':{},'method':'empty input','explanation':'No text was provided.'}
    words = re.findall(r"[a-z']+", text.lower())
    pos = neg = 0
    for i, word in enumerate(words):
        negated = any(w in NEGATORS for w in words[max(0, i-3):i])
        if word in POSITIVE:
            if negated: neg += 1
            else: pos += 1
        if word in NEGATIVE:
            if negated: pos += 1
            else: neg += 1
    model_probs = _model.predict_proba([text])[0]
    classes = list(_model.named_steps['classifier'].classes_)
    probs = {str(c): float(p) for c, p in zip(classes, model_probs)}
    # Blend baseline model with a transparent sentiment-lexicon signal.
    if pos or neg:
        lex = {'positive': 0.15 + 0.7 * pos/(pos+neg), 'negative': 0.15 + 0.7 * neg/(pos+neg), 'neutral': 0.0}
        total = lex['positive'] + lex['negative']
        lex = {k:v/total for k,v in lex.items()}
        probs = {k: 0.45*probs.get(k,0) + 0.55*lex[k] for k in ('positive','negative','neutral')}
        total = sum(probs.values()); probs = {k:v/total for k,v in probs.items()}
    # Neutralize clearly factual/question-only text when no polarity terms occur.
    if pos == 0 and neg == 0 and (text.endswith('?') or re.search(r'\b(when|where|what|which|how|price|details|available|open)\b', text.lower())):
        probs = {k: v*0.55 for k,v in probs.items()}; probs['neutral'] += 0.45
        total=sum(probs.values()); probs={k:v/total for k,v in probs.items()}
    sentiment = max(probs, key=probs.get)
    confidence = round(probs[sentiment], 4)
    return {'sentiment':sentiment,'confidence':confidence,'probabilities':{k:round(v,4) for k,v in probs.items()},
            'method':'TF-IDF + Logistic Regression blended with an explainable sentiment lexicon',
            'explanation':'Probabilities are estimates, not guarantees. This teaching model is not benchmark-validated and may misread sarcasm, slang, context, emojis or multilingual text.',
            'limitations':'For high accuracy, evaluate and retrain on a larger representative, labelled dataset.'}

def metrics():
    return {'dataset':'small synthetic teaching corpus','samples':len(DATA),'note':'These figures are not a reliable benchmark of real-world accuracy.'}
