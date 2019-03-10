import sys
test_file_name = sys.argv[1]
dev_file_name = sys.argv[2]
test_file = open(test_file_name, 'r')
text = test_file.readlines()
dev_file = open(dev_file_name, 'r')
dev_text = dev_file.readlines()

likelihood = {}
pos_dict = {}
# make likelihood table
for i in range(len(text)):
    if text[i] != "\n":
        sep_list = text[i].split()
        if sep_list[1] not in likelihood:
            likelihood[sep_list[1]] = {sep_list[0]: 1}
        elif sep_list[0] not in likelihood[sep_list[1]]:
            likelihood[sep_list[1]][sep_list[0]] = 1
        else:
            likelihood[sep_list[1]][sep_list[0]] += 1

# print(likelihood)


# make pos tag table using two pointers
first = text[0].split()
pos_dict["Begin_Sent"] = {first[1]: 1}
for i in range(len(text)):
    j = i + 1
    if j == len(text):
        break
    # if the first pointer and the second pointer are both not \n
    if text[i] != "\n" and text[j] != "\n":
        pos_first = text[i].split()[1]
        pos_second = text[j].split()[1]
        if pos_first not in pos_dict:
            pos_dict[pos_first] = {pos_second: 1}
        elif pos_second not in pos_dict[pos_first]:
            pos_dict[pos_first][pos_second] = 1
        else:
            pos_dict[pos_first][pos_second] += 1
    # if the first pointer is \n, then the tag of the second pointer should be counted after Begin_Sent
    elif text[i] == "\n" and text[j] != "\n":
        tag = text[j].split()[1]
        if tag not in pos_dict["Begin_Sent"]:
            pos_dict["Begin_Sent"][tag] = 1
        else:
            pos_dict["Begin_Sent"][tag] += 1
    # if the second pointer is \n and then the stat End_Sent should be counted after the first pointer
    elif text[j] == "\n" and text[i] != "\n":
        continue
        # tag = text[i].split()[1]
        # if tag not in pos_dict:
        #     pos_dict[tag] = {"End_Sent": 1}
        # elif "End_Sent" not in pos_dict[tag]:
        #     pos_dict[tag]["End_Sent"] = 1
        # else:
        #     pos_dict[tag]["End_Sent"] += 1

    # if both pointer are pointing to \n, this is the end of file, end the loop.
    elif text[i] == "\n" and text[j] == "\n":
        break

OOV_dict = []
likelihood_prob = {}
pos_prob = {}
num_likelihood = 0
num_pos = 0
# maintain an OOV list to simply check if a word is OOV or not
for tag in likelihood:
    for word in likelihood[tag]:
        if word not in OOV_dict:
            OOV_dict.append(word)
# turn likelihood table into a probability table
for tag in likelihood:
    likelihood_prob[tag] = {}
    for word in likelihood[tag]:
        num_likelihood += likelihood[tag][word]
    for word in likelihood[tag]:
        likelihood_prob[tag][word] = likelihood[tag][word]/num_likelihood
    num_likelihood = 0

# turn pos table into a probability table
for tag in pos_dict:
    pos_prob[tag] = {}
    for value_tag in pos_dict[tag]:
        num_pos += pos_dict[tag][value_tag]
    for value_tag in pos_dict[tag]:
        pos_prob[tag][value_tag] = pos_dict[tag][value_tag]/num_pos
    num_pos = 0

tag_list = []
prob_i = {}
total_i = 0
prob_temp = {}
start_of_sentence = False
#oov_prob = 0.0001
for i in range(len(dev_text)):

    prob_i.clear()
    total_i = 0
    score = 0
    maximize = 0
    result_tag = ""
    # handling the first line
    if i == 0:
        word_i = dev_text[i].split()[0]
        # if the word is OOV
        if word_i not in OOV_dict:
            result_tag = max(pos_prob["Begin_Sent"])
            prob_i = dict.copy(pos_prob["Begin_Sent"])
        else:
            # for all possible tags behind Begin_Sent
            for tag in pos_prob["Begin_Sent"]:
                # if the word has appeared in the likelihood table. compute the score, make the comparison.
                if word_i in likelihood_prob[tag]:
                    score = likelihood_prob[tag][word_i] * pos_prob["Begin_Sent"][tag]
                    prob_i[tag] = score
                    if score > maximize:
                        maximize = score
                        result_tag = tag

        tag_list.append(result_tag)
        prob_temp = dict.copy(prob_i)
    # if it's a blank line, it means that the next line is the begin of sentence
    elif dev_text[i] == "\n":
        start_of_sentence = True
    # handling a normal line
    elif dev_text[i] != "\n" and not start_of_sentence:
        word_i = dev_text[i].split()[0]
        if word_i not in OOV_dict:
            # get possible tags of the previous word
            for pre_tag in prob_temp:
                # get possible tags after the tag of the previous word
                for tag in pos_prob[pre_tag]:
                    score = prob_temp[pre_tag] * pos_prob[pre_tag][tag]
                    prob_i[tag] = score
                    if score > maximize:
                        maximize = score
                        result_tag = tag

        else:
            # get possible tags of the previous word
            for pre_tag in prob_temp:
                # get possible tags after the tag of the previous word
                for tag in pos_prob[pre_tag]:
                    # if the word is in the likelihood table, compute the score, make the comparison.
                    if word_i in likelihood_prob[tag]:
                        score = likelihood_prob[tag][word_i] * prob_temp[pre_tag] * pos_prob[pre_tag][tag]
                        prob_i[tag] = score
                        if score > maximize:
                            maximize = score
                            result_tag = tag

        tag_list.append(result_tag)
        prob_temp = dict.copy(prob_i)

    elif dev_text[i] != "\n" and start_of_sentence:
        word_i = dev_text[i].split()[0]
        if word_i not in OOV_dict:
            result_tag = max(pos_prob["Begin_Sent"])
            prob_i = dict.copy(pos_prob["Begin_Sent"])

        else:
            for tag in pos_prob["Begin_Sent"]:
                if word_i in likelihood_prob[tag]:
                    score = likelihood_prob[tag][word_i] * pos_prob["Begin_Sent"][tag]
                    prob_i[tag] = score
                    if score > maximize:
                        maximize = score
                        result_tag = tag

        tag_list.append(result_tag)
        prob_temp = dict.copy(prob_i)
        start_of_sentence = False

# output. assign tag for the word if the current line of the input file is not a blank line
tag_count = 0
result = open("submission.pos", 'w', newline='\n')
for i in range(len(dev_text)):
    if dev_text[i] != "\n":
        result.write(dev_text[i].split()[0])
        result.write("\t")
        result.write(tag_list[tag_count])
        result.write("\n")
        tag_count += 1
    else:
        result.write("\n")

