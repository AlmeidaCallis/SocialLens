from flask import Flask, request, jsonify
from flask_cors import CORS
from preprocessing import preprocess
from ngram_models import analyze as analyze_ngrams
from regex_extractor import extract
from linguistic_analysis import analyze as analyze_linguistic
from text_representation import represent
from sentiment import predict, metrics
from spam_detection import detect
app=Flask(__name__); CORS(app)
app.config['MAX_CONTENT_LENGTH']=5*1024*1024
@app.get('/health')
def health(): return jsonify({"status":"ok","service":"SocialLens NLP","experiments":["preprocess","ngrams","extract","linguistic","representations"]})
def body():
 data=request.get_json(silent=True) or {}; return data
@app.post('/preprocess')
def route_preprocess():
 d=body(); text=d.get('text','')
 if not isinstance(text,str) or not text.strip(): return jsonify({"error":"text must be a non-empty string"}),400
 return jsonify(preprocess(text))
@app.post('/ngrams')
def route_ngrams():
 d=body(); texts=d.get('texts') or ([d['text']] if d.get('text') else [])
 if not texts or not any(str(x).strip() for x in texts): return jsonify({"error":"Provide non-empty texts or text"}),400
 return jsonify(analyze_ngrams(texts,d.get('prefix',''),d.get('sentence','')))
@app.post('/extract')
def route_extract():
 d=body(); text=d.get('text','')
 if not isinstance(text,str) or not text.strip(): return jsonify({"error":"text must be a non-empty string"}),400
 return jsonify(extract(text))
@app.post('/linguistic')
def route_linguistic():
 d=body(); text=d.get('text','')
 if not isinstance(text,str) or not text.strip(): return jsonify({"error":"text must be a non-empty string"}),400
 return jsonify(analyze_linguistic(text,d.get('comparison','')))
@app.post('/representations')
def route_representations():
 d=body(); texts=d.get('texts') or ([d['text']] if d.get('text') else [])
 if not texts or not any(str(x).strip() for x in texts): return jsonify({"error":"Provide non-empty texts or text"}),400
 return jsonify(represent(texts,int(d.get('window',2))))
@app.post('/sentiment')
def route_sentiment():
 d=body(); text=d.get('text','')
 if not isinstance(text,str) or not text.strip(): return jsonify({"error":"text must be a non-empty string"}),400
 return jsonify(predict(text))
@app.post('/spam')
def route_spam():
 d=body(); text=d.get('text','')
 if not isinstance(text,str) or not text.strip(): return jsonify({"error":"text must be a non-empty string"}),400
 return jsonify(detect(text,bool(d.get('duplicate',False))))
@app.get('/metrics')
def route_metrics(): return jsonify(metrics())
@app.errorhandler(413)
def too_large(_): return jsonify({"error":"Request too large; limit is 5 MB"}),413
@app.errorhandler(500)
def server_error(_): return jsonify({"error":"NLP processing failed; check service setup and model resources"}),500
if __name__=='__main__': app.run(host='127.0.0.1',port=5001,debug=False)
