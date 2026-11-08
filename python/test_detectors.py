from spam_detection import detect
from sentiment import predict

def test_obvious_scam_messages_flagged():
    samples = [
        "Earn daily profit guaranteed check my page now",
        "Click the link in my bio to win a free iPhone 15",
        "I made $2,000 in one day working from home message @crypto_master_fx",
        "DM me to recover your hacked instagram account fast",
        "Follow @example_store and use code SAVE50 for discounts",
    ]
    assert all(detect(text)["status"] == "potential_spam" for text in samples)

def test_legitimate_comments_not_automatically_spam():
    samples = ["I love your content and creativity", "What is the price?", "Beautiful photography"]
    assert all(detect(text)["status"] == "normal" for text in samples)

def test_sentiment_probabilities_are_present_and_normalized():
    result = predict("I love this product, amazing quality")
    assert result["sentiment"] == "positive"
    assert set(result["probabilities"]) == {"positive", "negative", "neutral"}
    assert abs(sum(result["probabilities"].values()) - 1) < 0.01
