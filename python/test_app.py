import pytest
from app import app
@pytest.fixture
def client():
 app.config['TESTING']=True
 with app.test_client() as c: yield c
def test_health(client): assert client.get('/health').status_code==200
def test_preprocess(client):
 r=client.post('/preprocess',json={'text':'I do not like this!'});assert r.status_code==200;assert 'not' in r.json['stop_word_removed'] if 'stop_word_removed' in r.json else 'not' in r.json['stop_word_text']
def test_ngrams(client):
 r=client.post('/ngrams',json={'texts':['I love NLP','I love Python'],'prefix':'i love'});assert r.status_code==200;assert 'bigrams' in r.json
def test_extract(client):
 r=client.post('/extract',json={'text':'Email demo@example.com #test'});assert r.status_code==200;assert any(x['category']=='email' for x in r.json['matches'])
def test_linguistic(client):
 r=client.post('/linguistic',json={'text':'Rahul works at Google.'});assert r.status_code==200;assert 'tokens' in r.json
def test_representations(client):
 r=client.post('/representations',json={'texts':['great product','bad product']});assert r.status_code==200;assert 'one_hot' in r.json
def test_sentiment_spam(client):
 assert client.post('/sentiment',json={'text':'I love this amazing product'}).json['sentiment'] in ['positive','negative','neutral']
 assert client.post('/spam',json={'text':'BUY NOW click here https://example.com'}).json['status']=='potential_spam'
def test_empty_input(client): assert client.post('/extract',json={'text':' '}).status_code==400
