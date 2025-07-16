from wordfreq import top_n_list
import random

german_words = top_n_list('de', 10000)

def get_random_german_word():
    return random.choice(german_words)