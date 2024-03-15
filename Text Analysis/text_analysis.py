import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import os
import shutil
import re
import nltk
nltk.download('cmudict')
nltk.download('punkt')

import string

df = pd.read_excel("./Artifacts/Input.xlsx", "Sheet1")

# ---------------------------

error_404 = []
def get_article(df):
    
    if os.path.exists("./Artifacts/Articles"):
        shutil.rmtree("./Artifacts/Articles")
    
    os.makedirs("./Artifacts/Articles")

    
    for i in df.values:

        id = i[0]
        response = requests.get(i[1])
        
        if response.status_code == 404:
            error_404.append(i[0])
            continue
            
        soup = bs(response.text)

        print()
        print("Fethching Articles...")

        article_heading = soup.find("h1", "entry-title")
        if article_heading == None:
            article_heading = soup.find("h1", "tdb-title-text")

        # article_div = soup.find("div", "td-post-content tagdiv-type")
        article_div = soup.find_all("div", "td-post-content tagdiv-type")
        flag = 0
        
        if article_div == []:
            flag = 1
            # article_div = soup.find("div", "tdb-block-inner td-fix-index")
            article_div = soup.find_all("div", "tdb-block-inner td-fix-index")
        # print(i)
        
        heading = article_heading.get_text(strip = False)
        lb = "\n"*2
        if flag == 0:
            article_text = article_div[0].get_text(strip = False)
            # article_text = article_div[0].get_text(strip = True)
            article_text = re.sub(r'\n{2,}', '\n\n', article_text)
        else:
            article_text = article_div[14].get_text(strip = False)
            # article_text = article_div[14].get_text(strip = True)
            article_text = re.sub(r'\n{2,}', '\n\n', article_text)
        
        article_text = article_text.strip()
        last_line = article_text.rfind("\n")
        article_text = article_text[:last_line]
       
        article = heading + lb + article_text
        article = article.strip()

        with open("./Artifacts/Articles/{}.txt".format(id), "a", encoding="utf-8") as f:
            f.write(article)

get_article(df)

# ------------------

def list_stopwords(path):
    
    print()
    print("Cleaning for analysis...")

    h0, h1, h2 = [], [], []
    
    for i in os.listdir(path):
        file = path+"/"+i
        
        with open(file, "r") as f:
            # print(f.read())
            for i in f.readlines():
                h0.append(i.strip())

    for i in h0:
        h1.append(i.split("|"))

    for i in h1:
        for j in range(len(i)):
            i[j] = i[j].strip()
            h2.append(i[j])
            
    return h2

def list_pn(path):
    h1 = []
    h2 = []
    count = 0
    for i in os.listdir(path):
        file = path+"/"+i
        if i == "negative-words.txt":
            with open(file, "r") as f:
                for i in f.readlines():
                    h1.append(i.strip())
                    
        if i == "positive-words.txt":
            with open(file, "r") as f:
                for i in f.readlines():
                    h2.append(i.strip())

    return h1, h2


stopwords = list_stopwords("./Artifacts/StopWords")
nwords, pwords = list_pn("./Artifacts/MasterDictionary")

def cleaning_np(stopwords):
    for i in nwords:
        if i in stopwords:
            nwords.remove(i)
            
    for i in pwords:
        if i in stopwords:
            pwords.remove(i)

cleaning_np(stopwords)

# ---------------------

def get_scores(path):

    print()
    print("Performing analysis...")

    scores = []
    pronouncing_dict = nltk.corpus.cmudict.dict()
    stopwords_nltk = nltk.corpus.stopwords.words('english')
    
    for i in os.listdir(path):
        file = path + "/" + i
        with open(file, "r", encoding = "utf8") as f:
            # print(f.read())
            article_t = f.read()
                
        article_token = nltk.tokenize.word_tokenize(article_t)
        article_token_uncleaned = nltk.tokenize.word_tokenize(article_t)
        article_sentences = nltk.sent_tokenize(article_t)
        article_token_nltk_cleaned = nltk.tokenize.word_tokenize(article_t)
        
        for x in article_token:
            if x in string.punctuation:
                article_token.remove(x)
                
        for x1 in article_token:
            if x1 in stopwords:
                article_token.remove(x1)
    
        
        for x in article_token_nltk_cleaned:
            if x in string.punctuation:
                article_token_nltk_cleaned.remove(x)
                
        for x1 in article_token_nltk_cleaned:
            if x1 in stopwords_nltk:
                article_token_nltk_cleaned.remove(x1)
    
        helper = []
        
        total_words = len(article_token)
        total_words_nltk_cleaned = len(article_token_nltk_cleaned)
        total_words_uncleaned = len(article_token_uncleaned)
        total_sentences = len(article_sentences)
        personal_pronouns = [ "i", "you", "he", "she", "it", "we", "you", "they", "me", "you", "him", "her", "it", "us", "you", "them", "my", "mine",
        "your", "yours", "his", "hers", "its", "our", "ours", "your", "yours", "their", "theirs", "myself", "yourself", "himself", "herself",
        "itself", "ourselves", "yourselves", "themselves"]
        
        
        complex_words = []
        syl_per_word = 0
        for x4 in article_token_uncleaned:
            if x4.lower() in pronouncing_dict:
                verbal = pronouncing_dict[x4.lower()]
                for p in verbal:
                    syl_count = 0
                    for x5 in p:
                        if x5[-1].isdigit():
                            syl_count += 1
                            syl_per_word += syl_count
                    if syl_count > 2:
                        complex_words.append(x4)
                    syl_per_word += syl_count
        
    
        # calculating scores for all entity
        
        p_score = 0
        n_score = 0
        
        for x3 in article_token:
            if x3 in nwords:
                n_score += 1
            if x3 in pwords:
                p_score += 1
    
        helper.append(p_score)
        helper.append(n_score)
    
        
        pol_score = (p_score - n_score) / ((p_score + n_score) + 0.000001)
        helper.append(pol_score)
        
        sub_score = (p_score + n_score) / ((total_words) + 0.000001)
        helper.append(sub_score)
    
        avg_sentence_length = total_words / total_sentences
        helper.append(avg_sentence_length)
    
        complex_percentage = (len(complex_words) / total_words) * 100
        helper.append(complex_percentage)
    
        fog_index = 0.4 * (avg_sentence_length + complex_percentage)
        helper.append(fog_index)
    
        avg_words_per_sentence = total_words_uncleaned / total_sentences
        helper.append(avg_words_per_sentence)
    
        complex_words_count = len(complex_words)
        helper.append(complex_words_count)
        
        total_words_final = total_words_nltk_cleaned
        helper.append(total_words_final)
        
        avg_syllable_each_word =  total_words / syl_per_word
        helper.append(avg_syllable_each_word)
        
        total_personal_pronoun = 0
        for x6 in article_token_uncleaned:
            if  x6 == "US":
                continue
            elif x6.lower in personal_pronouns:
                total_personal_pronoun += 1
        helper.append(total_personal_pronoun)
    
        sum_char = 0
        for x8 in article_token:
            for j in x8:
                sum_char += 1
        avg_word_length = sum_char / total_words
        helper.append(avg_word_length)
    
        scores.append(helper)
        
    return scores
    
analysis_score = get_scores("./Artifacts/Articles")
    

# -------------------

output_col = [
    "POSITIVE SCORE", "NEGATIVE SCORE", "POLARITY SCORE", "SUBJECTIVITY SCORE", "AVG SENTENCE LENGTH", 
    "PERCENTAGE OF COMPLEX WORDS", "FOG INDEX", "AVG NUMBER OF WORDS PER SENTENCE", "COMPLEX WORD COUNT",
    "WORD COUNT", "SYLLABLE PER WORD", "PERSONAL PRONOUNS", "AVG WORD LENGTH"
]


df0 = pd.DataFrame(analysis_score, columns = output_col)
df0 = df0.astype(float)

error_index = []
for i in error_404:
    error_index.append(int(i[-2:])-1)

for j in error_index:
    empty_row = pd.DataFrame([pd.Series([None] * len(df0.columns), index=df0.columns)])
    df0 = pd.concat([df0[:j], empty_row, df0[j:]], ignore_index=True)

output_df = pd.concat([df, df0], axis = "columns")
output_df.fillna("(PAGE NOT FOUND)", inplace=True)

if os.path.exists("./output.xlsx"):
    os.remove("./output.xlsx")

output_df.to_excel("output.xlsx", "Sheet1", index = False)

print()
print("Analysis complete!, kindly refer to the \"output\" excel file for analysis details")