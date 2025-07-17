from wordfreq import top_n_list
import random

german_words = top_n_list('de', 10000)

def get_random_german_word():
    return random.choice(german_words)

def get_common_search_terms():
    return [
        "yoga",
        "sprachen",
        "kochen",
        "fotografie",
        "programmieren",
        "malen",
        "musik",
        "fitness",
        "tanz",
        "geschichte",
        "literatur",
        "gesundheit",
        "wirtschaft",
        "politik",
        "wissenschaft",
    ]

def get_random_common_search_term():
    return random.choice(get_common_search_terms())
