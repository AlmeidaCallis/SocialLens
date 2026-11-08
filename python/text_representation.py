import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def represent(texts, window=2):
 texts=[str(t) for t in texts if str(t).strip()]; corpus=texts or ["sample text"]
 vocab=sorted(set(w for t in corpus for w in re.findall(r"\b\w+\b",t.lower())))[:18]
 onehot={w:[1 if w==v else 0 for v in vocab] for w in vocab}
 try:
  vec=TfidfVectorizer(max_features=40,ngram_range=(1,2)); mat=vec.fit_transform(corpus); names=vec.get_feature_names_out().tolist()
  tfidf=[{"text":corpus[i],"values":[round(float(x),4) for x in mat.toarray()[i]]} for i in range(min(len(corpus),10))]
 except ValueError: names=[]; tfidf=[]
 pairs=[]
 for text in corpus:
  words=re.findall(r"\b\w+\b",text.lower())
  for i,target in enumerate(words):
   context=[words[j] for j in range(max(0,i-window),min(len(words),i+window+1)) if j!=i]
   if context: pairs.append({"target":target,"context":context})
 # Train actual Gensim Word2Vec models only when the text has enough tokens; keep the small-corpus warning explicit.
 embedding={"method":"context-target pairs; Gensim models attempted when corpus is large enough","dimensions":min(8,max(2,len(vocab))),"cbow_example":{"context_words":pairs[0]["context"],"target_word":pairs[0]["target"]} if pairs else None,"skipgram_example":{"target_word":pairs[0]["target"],"context_words":pairs[0]["context"]} if pairs else None,"trained":False,"warning":"Small corpora produce unstable embeddings; treat results as a demonstration only."}
 token_sents=[re.findall(r"\b\w+\b",t.lower()) for t in corpus]; token_sents=[s for s in token_sents if s]
 if len(token_sents)>=5 and len(set(w for s in token_sents for w in s))>=5:
  try:
   from gensim.models import Word2Vec
   models={}
   for name,sg in [('cbow',0),('skipgram',1)]:
    model=Word2Vec(sentences=token_sents,vector_size=8,window=max(1,int(window)),min_count=1,workers=1,sg=sg,epochs=30,seed=7)
    models[name]={w:[round(float(v),4) for v in model.wv[w]] for w in list(model.wv.index_to_key)[:8]}
   embedding.update({"trained":True,"models":models,"method":"Gensim Word2Vec trained on supplied corpus (CBOW sg=0; Skip-Gram sg=1)","warning":"These tiny demo embeddings are trained but not semantically reliable."})
  except Exception as exc:
   embedding["warning"]="Gensim training unavailable: "+str(exc)+". Context-target pairs are still shown."
 else:
  embedding["warning"]="Dataset too small for a meaningful embedding. Add at least five non-empty sentences with a vocabulary of five or more unique tokens."
 return {"vocabulary":vocab,"one_hot":onehot,"tfidf_features":names,"tfidf_rows":tfidf,"context_target_pairs":pairs[:60],"window_size":window,"embedding_demo":embedding,"sparse_tfidf":True,"one_hot_dimension":len(vocab)}
