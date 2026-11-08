from collections import Counter
import math, re

def analyze(texts, prefix="", sentence=""):
    tokens = [re.findall(r"[\w']+", str(t).lower()) for t in texts if str(t).strip()]
    flat = [w for row in tokens for w in row]
    vocab = sorted(set(flat)); V = max(1, len(vocab))
    uni = Counter(flat); bi = Counter(zip(flat, flat[1:])); tri = Counter(zip(flat, flat[1:], flat[2:]))
    def rows(counter, n):
        out=[]
        for gram,count in counter.most_common(50):
            if n == 1: prob=count/max(1,len(flat))
            elif n == 2: prob=(count+1)/(uni[gram[0]]+V)
            else: prob=(count+1)/(bi[(gram[0],gram[1])]+V)
            out.append({"ngram":" ".join(gram) if isinstance(gram,tuple) else gram,"frequency":count,"probability":round(prob,6)})
        return out
    prefix_tokens=re.findall(r"[\w']+", prefix.lower())
    candidates=[]
    if len(prefix_tokens)>=2:
        key=tuple(prefix_tokens[-2:]); denom=bi[key]
        candidates=[{"word":w,"count":c,"probability":round((c+1)/(denom+V),6)} for (a,b,w),c in tri.items() if (a,b)==key]
    elif prefix_tokens:
        key=prefix_tokens[-1]; denom=uni[key]
        candidates=[{"word":w,"count":c,"probability":round((c+1)/(denom+V),6)} for (a,w),c in bi.items() if a==key]
    candidates=sorted(candidates,key=lambda x:x['probability'],reverse=True)[:8]
    sent_tokens=re.findall(r"[\w']+", sentence.lower()); logp=0.0
    for i,w in enumerate(sent_tokens):
        if i==0: p=(uni[w]+1)/(len(flat)+V)
        else: p=(bi[(sent_tokens[i-1],w)]+1)/(uni[sent_tokens[i-1]]+V)
        logp += math.log(max(p,1e-300))
    perplexity=math.exp(-logp/len(sent_tokens)) if sent_tokens else None
    return {"vocabulary_size":len(vocab),"unigrams":rows(uni,1),"bigrams":rows(bi,2),"trigrams":rows(tri,3),"predictions":candidates,"sentence_probability_log":round(logp,6) if sent_tokens else None,"perplexity":round(perplexity,6) if perplexity is not None else None,"training_token_count":len(flat),"smoothing":"Add-one/Laplace smoothing is used for conditional n-gram probabilities."}
