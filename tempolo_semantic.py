import spacy
from spacy.language import Language
import re

nlp = spacy.load("en_core_web_trf")

# adding rules for detecting the tense
ruler = nlp.get_pipe("attribute_ruler")


pattern = [[{"LOWER": "updating"}], [{"LOWER": "update"}], [{"LOWER": "start"}],
           [{"LOWER": "get"}], [{"LOWER": "getting"}]]
attrs = {"POS": "VERB", "TAG": "VB", "MORPH": "Aspect=Prog"}
ruler.add(patterns=pattern, attrs=attrs)

pattern = [[{"LOWER": "discarded"}]]
attrs = {"POS": "VERB", "TAG": "VBD", "MORPH": "Aspect=Perf"}
ruler.add(patterns=pattern, attrs=attrs)

patterns_prog = [[{"TAG": "VB"}], [{"TAG": "VBP"}], [{"TAG": "VBZ"}], [{"TAG": "VBG"}], [{"LOWER": "updating"}],
                 [{"LOWER": "update"}]]
attrs_prog = {"MORPH": "Aspect=Prog"}
ruler.add(patterns=patterns_prog, attrs=attrs_prog)

patterns_pref = [[{"TAG": "VBD"}], [{"TAG": "VBN"}], [{"LOWER": "got"}]]
attrs_pref = {"MORPH": "Aspect=Perf"}
ruler.add(patterns=patterns_pref, attrs=attrs_pref)

from pattern.en import lexeme

main_verb_list = ['superseded']

main_verb_list_lexeme = [x for y in main_verb_list for x in lexeme(y)]
# adding rules for log split
@Language.component("set_custom_boundaries")
def set_custom_boundaries(doc):
    for token in doc[:-1]:
        if token.text == ",":
            doc[token.i + 1].is_sent_start = True
        elif token.text == "..":
            doc[token.i + 1].is_sent_start = True
        elif token.text == ";":
            doc[token.i + 1].is_sent_start = True
    return doc


# nlp.remove_pipe("set_custom_boundaries")
nlp.add_pipe("set_custom_boundaries", before="parser")
aux_prog_list = ['is', 'are', 'can', 'do', 'does', 'to']
auxpass_pref_list = ['is', 'are']
aux_perf_list = ['was', 'were', 'could', 'did', 'have', 'has', 'had', 'would']


def detecting_main_verb_and_tense(sentence):

    root = [token for token in sentence if token.text in main_verb_list_lexeme]
    if root:
        root = root[0]
    else:
        root = [token for token in sentence if token.head == token][0]

    if root.pos_=='AUX':
        return None, None

    if root.pos_ == 'VERB':
        # check if contains an AUX before the main verb
        for child in root.children:
            if child.dep_ in ['aux', 'auxpass']:
                if child.text in aux_perf_list:
                    return root, ['Perf']
                if child.dep_ is 'auxpass':
                    if child.text in auxpass_pref_list:
                        return root, ['Perf']
                    if child.text == 'being':
                        return root, ['Prog']
                else:
                    if child.text in aux_prog_list:
                        return root, ['Prog']
                # print(x)
                # print(x.morph.get('Aspect'))
        return root, root.morph.get('Aspect')
    else:
        first_verb_flag = True
        for token in sentence:
            if token.pos_ == 'VERB':
                if first_verb_flag:
                    first_verb = token
                    first_verb_flag = False
                if token.head == root:
                    for child in token.children:
                        if child.dep_ in ['aux', 'auxpass']:
                            if child.text in aux_perf_list:
                                return token, ['Perf']
                            if child.dep_ is 'auxpass':
                                if child.text in auxpass_pref_list:
                                    return token, ['Perf']
                                if child.text == 'being':
                                    return token, ['Prog']
                            else:
                                if child.text in aux_prog_list:
                                    return token, ['Prog']
                            # print(x)
                            # print(x.morph.get('Aspect'))
                    return token, token.morph.get('Aspect')
        if first_verb_flag:
            return None, None
        # for child in first_verb.children:
        #     if child.dep_ in ['aux', 'auxpass']:
        #         if child.text in aux_perf_list:
        #             return first_verb, ['Perf']
        #         if child.dep_ is 'auxpass':
        #             if child.text in auxpass_pref_list:
        #                 return first_verb, ['Perf']
        #             if child.text == 'being':
        #                 return first_verb, ['Prog']
        #         else:
        #             if child.text in aux_prog_list:
        #                 return first_verb, ['Prog']
        return first_verb, first_verb.morph.get('Aspect')


def detecting_main_verb_and_tense_all(sentences):
    res_all = []
    res_sents = []
    main_verb = None
    tense = None
    main_sent = None
    for sentence in sentences:
        res = detecting_main_verb_and_tense(sentence)
        if res[0]:
            main_verb, tense = res
            res_all.append(res)
            res_sents.append(sentence)
            main_sent = sentence
    if tense is None and main_verb is not None:
            main_verb, tense = res_all[0]
            main_sent = res_sents[0]
    return main_verb, tense, main_sent, res_all, res_sents


def get_log_content_rel(log_text):
    log_text = re.sub(' {2,}', ' ', log_text)
    if '========== ' in log_text:
        log_text = log_text.strip('========== ').capitalize()
    log_sents = nlp(log_text)
    log_tokens_text = [token.text.lower() for token in log_sents]

    main_verb, tense, mian_sent, res_all, res_sents = detecting_main_verb_and_tense_all(
        log_sents.sents)
    if mian_sent:
        if any([_x in mian_sent.text.lower() for _x in catch_keywords]) and 'interruptCheckPeriodMs' not in mian_sent.text and 'Interrupting' not in mian_sent.text and 'on transport interrupt' not in mian_sent.text:
            return 'after'
        if any([_x in mian_sent.text.lower() for _x in skip_keywords]):
            return 'met-by/finishes'
        
        log_tokens_lemma_ = [token.lemma_ for token in mian_sent]
        if 'will' in log_tokens_text or 'can' in log_tokens_text or 'ready' in log_tokens_text:
            return None
            if mian_sent:
                if any([_x in log_tokens_lemma_ for _x in met_by_keywords]):
                    return 'after'
            return 'meets/starts'
        if any([_x in log_tokens_text for _x in met_by_keywords]):
            return 'met-by/finishes'
        if main_verb is None:
            for _token in log_sents:
                if _token.lemma_ == 'be':
                    return 'after'
            return None
        if any([_x in log_tokens_lemma_ for _x in met_by_keywords]):
            return 'met-by/finishes'
        if main_verb.lemma_ in state_keywords:
            return 'after'
        if main_verb.head.text.lower() in ['after'] or any([_x.text.lower() in ['just'] for _x in main_verb.children]):
            return 'after'
        if tense:
            if tense[0] == 'Perf':
                return 'after'
            if tense[0] == 'Prog':
                return 'meets/starts'
        return None
    return None

catch_keywords = ['failed', 'exception', 'error', 'could not', "couldn't", 'cannot', 'can’t', 'interrupted',
                  'problem', 'cannot', 'fail', 'interrupt', 'couldnt', 'cant', 'unable', "can't", 'stopped', 'when', 'while']

skip_keywords = ['skip']

state_keywords = ['use', 'ignore', 'abort', 'have', 'appear']

met_by_keywords = ['end', 'complete', 'successful', 'succesfully', 'successfully', 'succeed',
                   'completion', 'finished', 'exiting', 'done', 'finishing', 'exited', 'finish', 'timeout']