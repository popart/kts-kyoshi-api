from fugashi import Tagger

tagger = Tagger('-Owakati')
text = "麩菓子は、麩を主材料とした日本の菓子。"
tagger.parse(text)
# => '麩 菓子 は 、 麩 を 主材 料 と し た 日本 の 菓子 。'
for word in tagger(text):
    print(word, word.feature.lemma, word.pos, sep='\t')
    # basically need to check if any kanji in word
    # remove parts that are not kanji
    # and add kata2hira(kanji)
    # "feature" is the Unidic feature data as a named tuple
