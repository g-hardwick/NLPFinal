from nltk.corpus import stopwords
import csv
import bs4
import urllib.request

# this is a set of 3 dictionarys, unigrams, bigrams, and trigrams, that are the basis for the autocomplete
global ngrams
global spellings

# called only once, this sets the data from the 3 different data sets
def getData():
    global ngrams
    ngrams = []
    valid = ["a", "i"]
    
    # for unigrams, takes in the unigram frequency and saves it
    unigrams = {}
    with open('unigram_freq.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        firstRow = True
        for row in csv_reader:
            if firstRow:
                firstRow = False
                continue
            if len(row[0])>1:
                unigrams[row[0]]=int(row[1])
            elif len(row[0])==1 and row[0] in valid:
                unigrams[row[0]]=int(row[1])
    
    valid = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o",\
            "p","q","r","s","t","u","v","w","x","y","z", " "]
    
    global spellings
    spellings = {}
    
    with open('spelling.txt') as file: 
        for line in file.readlines():
            line = line.replace("..."," ")
            line = line.replace("-"," ")
            line = ''.join(ch for ch in line.lower() if ch in valid)
            line = line.split(" ")
            true_word = line[0]
            if true_word in unigrams and len(true_word)>2:
                for word in line:
                    if word != true_word and len(word)>2:
                        if word in spellings:
                            spellings[word].append(true_word)
                        else:
                            spellings[word]=[true_word]
    
    # for bi and tri grams, first read in the bbc text and save it
    bigrams = {}
    trigrams = {}
    text = []
    with open('bbc-text.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        firstRow = True
        for row in csv_reader:
            if firstRow:
                firstRow = False
                continue
            text.append(row[1])
        
    
    # then for each line, save the bi and tri grams and their frequency
    for line in text:
        line = line.replace("..."," ")
        line = line.replace("-"," ")
        line = ''.join(ch for ch in line.lower() if ch in valid)
        line = line.split(" ")
        phrase = []
        for i in range(len(line)-1):
            if line[i] in unigrams and line[i+1] in unigrams:
                string = line[i]+" "+line[i+1]
                if string not in bigrams:
                    bigrams[string]=1
                else:
                    bigrams[string]+=1
        for i in range(len(line)-2):
            if line[i] in unigrams and line[i+1] in unigrams and line[i+2] in unigrams:
                string = line[i]+" "+line[i+1]+" "+line[i+2]
                if string not in trigrams:
                    trigrams[string]=1
                else:
                    trigrams[string]+=1
                    
    ngrams.append(unigrams)
    ngrams.append(bigrams)
    ngrams.append(trigrams)

# calculated how many grams the current input is
def n_gramCount(current_entry):
    current_grams = 0
    for ch in current_entry:
        if ch == " ":
            current_grams+=1
    return current_grams

# returns any possible suggestions from the parameter string
def getPossible(entry_str):
    current_grams = n_gramCount(entry_str)
    #finds the appropriate string to suggest by frequency
    possible = {}
    grams_possible = {}
    for word in ngrams[current_grams]: # for phrase of appropriate length
        if word.startswith(entry_str):
            possible[word] = ngrams[current_grams][word]
            grams_possible[word] = current_grams
    
    # if the number of suggestions remains below 10, then look for other possibilities
    if len(possible)<10:
        if current_grams>1: # first, if the string was a tri gram, look for a bi gram
            entry_str_cut = entry_str.rsplit(' ', 2)[1]+" "+entry_str.rsplit(' ', 1)[1]
            for word in ngrams[1]:
                if entry_str_cut == " ":
                    continue
                if word.startswith(entry_str_cut) and word not in possible:
                    possible[word] = ngrams[1][word]
                    grams_possible[word] = 1
            
        # if it still isn't above 10 possibilities, look for applicable unigrams (for endings, "the" could be "these")
        if len(possible)<10:
            if current_grams>0 and entry_str[-1]!=" ":
                entry_str_cut = entry_str.rsplit(' ', 1)[1]
                for word in ngrams[0]:
                    if word.startswith(entry_str_cut) and word not in possible:
                        possible[word] = ngrams[0][word]
                        grams_possible[word] = 0
                
            # if still not 10 possibilities, look at if the phrase is contained in a different entry
            if len(possible)<10:
                for word in ngrams[current_grams]:
                    if entry_str in word and word not in possible:
                        possible[word] = ngrams[current_grams][word]
                        grams_possible[word] = 3
    return possible, grams_possible
    
# uses getPossible to find the best matches and sends it on
def mostLikely(current_entry):
    if current_entry!= "":
        checkIfNeedsCorrection(current_entry)
    # if the input is more then a tri-gram, cut the text down to an apropriate size but save the beginning to be readded
    entry_str = current_entry
    current_grams = n_gramCount(entry_str)
    appender = ["", "", "", ""]
    if current_grams>0:
        appender[0] = current_entry.rsplit(' ', 1)[0]+" "
        if current_grams>1:
            appender[1] = current_entry.rsplit(' ', 2)[0]+" "
            if current_grams>2:
                appender[2] = current_entry.rsplit(' ', 3)[0]+" " 
    while current_grams>2:
        entry_str = entry_str.split(' ', 1)[1]
        current_grams = n_gramCount(entry_str)
    
    possible = {}
    possible_ending, grams_possible = getPossible(entry_str)
    for phrase in possible_ending:
        possible[appender[grams_possible[phrase]]+phrase]=possible_ending[phrase] # adds the removed beginning if needed, then the ending supplied
        
    # if the last word is a word in and of itself, there is a chance the next character will be a space, check for those possibilities
    if current_grams>0:
        if current_entry.rsplit(' ', 1)[1] in ngrams[0]:
            entry_str = current_entry+" "
            current_grams = n_gramCount(entry_str)
            while current_grams>2:
                entry_str = entry_str.split(' ', 1)[1]
                current_grams = n_gramCount(entry_str)
            possible_space, grams_possible_space = getPossible(entry_str)
            for phrase in possible_space:
                possible[appender[grams_possible_space[phrase]]+phrase]=possible_space[phrase] # adds the removed beginning if needed, then the ending supplied
    if len(possible)==0:
        possible[current_entry+" "+max(ngrams[0], key=ngrams[0].get)] = 1
        
    if len(possible)<10:
        list_range = len(possible)
    else:
        list_range = 10
        
    # finds the 10 (or appropriate number) best matches by looking at the dictionary and grabbing the one with the highest frequency
    most_likely_list = []
    for i in range(list_range):
        max_word =  max(possible, key=possible.get)
        if max_word == current_entry:
            possible.pop(max_word)
            continue
        most_likely_list.append(max_word)
        possible.pop(max_word)
    print("Most Likely Autocompletes for", current_entry)
    print(most_likely_list)

# given a word, iterates through changing each letter to all the letters of the alphabet as well as space and removal to see if any words are 1 off from being correct words
def checkOffByOne(word):
    alphabet = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o",\
            "p","q","r","s","t","u","v","w","x","y","z", "", " "]
    possible = {}
    for index_to_change in range(len(word)):
        for letter in alphabet:
            potential_word = word[:index_to_change]+letter+word[index_to_change+1:]
            if potential_word in ngrams[0]:
                possible[potential_word] = ngrams[0][potential_word]
            if letter == " " and potential_word in ngrams[1]:
                possible[potential_word] = ngrams[1][potential_word]
    print("Off By One Possibilities for", word, ":")
    print(possible)
    return possible

# gets the last word inputted, and if it is not a word, compares it to the dictionary of misspellings and calls offByOne to see any possibilities, then returns the top 3 (if they exist)
def checkIfNeedsCorrection(current_entry):
    if current_entry[-1]==" ":
        current_entry = current_entry[:-1]
    last_word = current_entry.split(" ")[-1]
    if len(last_word)<4:
        return
    correct = []
    current_grams = n_gramCount(current_entry)
    if last_word not in ngrams[0]:
        possible = checkOffByOne(last_word)
        if last_word in spellings:
            possible_spellings = spellings[last_word]
            possible = {}
            for word in possible_spellings:
                possible[word] = ngrams[0][word]
        i = 3
        while i>0 and len(possible)>0:
            max_word = max(possible, key=possible.get)
            if max_word != current_entry:
                correct.append(max_word)
            possible.pop(max_word, None)
            i=i-1
        if len(correct)!=0:
            if current_grams>0:
                for index in range(len(correct)):
                    correct[index] = current_entry.rsplit(" ",1)[0]+" "+correct[index]
            print("Corrected:", current_entry)
            print(correct)
    return

#pulls the top 2 sentences from some text to return a summary
def summerizer(text):
    stop_words = set(stopwords.words('english'))
    valid = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o",\
            "p","q","r","s","t","u","v","w","x","y","z", " "]
    word_frequencies = {}
    print("Summarized to:")
    if "." in text and len(text.split("."))>2:
        for sentence in text.split("."):
            for word in sentence.split(" "):
                while "[" in word or "]" in word:
                    index_closed = word.index("]")
                    index_open = word.index("[")
                    word = word[:index_open]+word[index_closed+1:]
                word = ''.join(ch for ch in word.lower() if ch in valid)
                if word not in stop_words and len(word)>0:
                    if word in word_frequencies:
                        word_frequencies[word]+=1.0
                    else:
                        word_frequencies[word]=1.0

        max_freq = max(word_frequencies.values())
        for word in word_frequencies:
            word_frequencies[word]=word_frequencies[word]/max_freq

        sentences = {}
        for sentence in text.split("."):
            while "[" in sentence or "]" in sentence:
                index_closed = sentence.index("]")
                index_open = sentence.index("[")
                sentence = sentence[:index_open]+sentence[index_closed+1:]
            sentences[sentence]=0.0
            for word in sentence.split(" "):
                while "[" in word or "]" in word:
                    index_closed = word.index("]")
                    index_open = word.index("[")
                    word = word[:index_open]+word[index_closed+1:]
                word = ''.join(ch for ch in word.lower() if ch in valid)
                if word in word_frequencies:
                    sentences[sentence]+=word_frequencies[word]
        best_2_sentences = max(sentences, key=sentences.get)
        sentences.pop(best_2_sentences)
        best_2_sentences += "."+max(sentences, key=sentences.get)+"."
        print(best_2_sentences)
    else:
        print(text)
    
def summerizeWebpage(url):
    data = urllib.request.urlopen(url).read()
    text = bs4.BeautifulSoup(data,'lxml')
    full = ""
    for paragraph in text.find_all('p'):
        adju_paragraph = paragraph.text
        adju_paragraph = adju_paragraph.replace("\n"," ")
        while "[" in adju_paragraph or "]" in adju_paragraph:
            index_closed = adju_paragraph.index("]")
            index_open = adju_paragraph.index("[")
            adju_paragraph = adju_paragraph[:index_open]+adju_paragraph[index_closed+1:]
        full+= adju_paragraph
    return summerizer(full)

getData()
num = 0
for vals in spellings:
    num+=len(spellings[vals])
    num+=1
print(len(ngrams)+num)
mostLikely("test")
mostLikely("This is a longer test")
checkOffByOne("tsst")
print("Edge cases for Summerizer:")
summerizer("This is an edge case with no proper sentences")
summerizer("This is an edge case with only one sentence.")
summerizer("This is an edge case with only two sentences. This is the second.")
print("Proper example:")
summerizer('Purple is any of a variety of colors with hue between red and blue.[1][2] In the RGB color model used in computer and television screens, purples are produced by mixing red and blue light. In the RYB color model historically used by painters, purples are created with a combination of red and blue pigments. In the CMYK color model used in printing, purples are made by combining magenta pigment with either cyan pigment, black pigment, or both. Purple has long been associated with royalty, originally because Tyrian purple dye, made from the mucus secretion of a species of snail, was extremely expensive in antiquity.[3] Purple was the color worn by Roman magistrates; it became the imperial color worn by the rulers of the Byzantine Empire and the Holy Roman Empire, and later by Roman Catholic bishops. Similarly in Japan, the color is traditionally associated with the emperor and aristocracy.[4]')
print("From webpage:")
summerizeWebpage('https://en.wikipedia.org/wiki/Purple')