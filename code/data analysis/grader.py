#grader.py
#Will Baxley, 1/18/8
#Context Lab, Dartmouth College, Hanover, NH

# reads "testdata" and cleanly outputs which questions the user got correct

# parses the data file and returns, in ordered lists, the questions and answers
def parsedata(filename, startingline):  # the first line of the file is line 0
    qsets = []  # list of the 3 lists of questions
    asets = []  # list of the 3 lists of answers

    infile = open(filename, "r")
    lines = infile.read().split("\n")[startingline:startingline+14]

    qsets.append(lines[1].split("{")) # first set of 10 questions goes in qsets[0]
    qsets.append(lines[6].split("{"))  # second set of 10 questions goes in qsets[1]
    qsets.append(lines[11].split("{"))  # third set of 10 questions goes in qsets[2]

    for set in range(3):         # go through each question set in qsets
        for i in range(len(qsets[set])):          # go through each question in the set...
            if len(qsets[set][i].split("\"")) >= 10:   # (ignoring irrelevant lines) DO I NEED THIS?
                qsets[set][i] = qsets[set][i].split("\"")[10].strip().replace("&#8217;", "\'")   #...and clean it up
        qsets[set] = qsets[set][1:]     # get rid of some junk

    asets.append(lines[2].split(":"))       # first set of 10 answers goes in asets[0]
    asets.append(lines[7].split(":"))       # second set of 10 answers goes in asets[1]
    asets.append(lines[12].split(":"))      # third set of 10 answers goes in asets[2]

    for set in range(3):            # go through each question set in qsets
        for i in range(len(asets[set])):    # go through each question in the set...
            if len(asets[set][i].split("\\")) > 1:  #(ignoring irrelevant lines)
                asets[set][i] = asets[set][i].split("\\")[1].strip(" \"").replace("&#8217;","\'")  #...clean it up
        asets[set] = asets[set][5:15]       # get rid of some junk

    infile.close()

    return (qsets, asets)

# read the file of questions and return ordered lists of the questions and their answers
def readquestions(filename):
    questiondict = {}  # dictionary of the form {question -> (question number, answer)}

    infile = open(filename, "r")
    lines = infile.read().split("\n")

    for qv1 in range(15):   # for each question from video 1
        questiondict[lines[6 + 8*qv1].strip(" ")] = (qv1 + 1, lines[7 + 8*qv1].strip(" "))

    for qv2 in range(15):   # for each question from video 2
        questiondict[lines[129 + 8*qv2].strip(" ")] = (qv2 + 16, lines[130 + 8 * qv2].strip(" "))

    return questiondict

def grade(output, questiondict, qsets, asets):
    outfile = open(output, "w")
    for set in range(3):
        outfile.write("QUESTION SET " + str(1 + set) + "\n")
        for question in range(10):
            if qsets[set][question] in questiondict:
                outfile.write("q" + str(questiondict[qsets[set][question]][0]) + ", ")
                if asets[set][question] == questiondict[qsets[set][question]][1]:
                    outfile.write("right")
                else:
                    outfile.write("wrong")
                outfile.write("\n")
            else:
                outfile.write("error" + "/n")

    outfile.close()

(qsets, asets) = parsedata("testdata", 0)
questiondict = readquestions("testvideoquestions")

# for key in questiondict:
#     print(key)
#     print()
#
# print("-------------------------------------------")
#
# for question in range(10):
#     print(qsets[0][question])
#     print(qsets[0][question] in questiondict)
#     print()
#
grade("testoutput", questiondict, qsets, asets)
