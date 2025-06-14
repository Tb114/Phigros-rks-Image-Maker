import philib
import sys
sys.stdout = open('output.txt', 'w', encoding='utf-8')
user = philib.PhigrosGet("jg9hrrl12o3ugwkn7oawb580h","difficulty.tsv")
print(user.improving_suggestion(0.01))