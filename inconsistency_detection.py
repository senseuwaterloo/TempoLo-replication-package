from nltk.corpus import wordnet as wn
import tempolo_semantic as lcr
import json
import re
from pattern.en import lexeme
from nltk.corpus import stopwords
import psycopg2
from bs4 import BeautifulSoup
from lxml import etree
import spacy

nlp = spacy.load("en_core_web_trf")


def check_return_false_stmt(node):
    if node.name == 'return':
        if 'false' == node.find_next('literal').get_text():
            return True
        return False
    else:
        return False


def check_return_true_stmt(node):
    if node.name == 'return':
        if 'true' == node.find_next('literal').get_text():
            return True
        return False
    else:
        return False


possible_main_verb = ['superseded']
comp_deps = ['pcomp', 'xcomp', 'ccomp']
state_keywords = ['fail', 'connect',
                  'disconnect', 'call', 'make', 'process']

server_keywords = ['start', 'stop']
negation_keywords = ["doesn't", 'not', 'exist', 'nothing', 'wrong', 'disabling', 'may', 'unable', 'exception', "couldn't", 'problem',  'missing', 'suppressing', 'unregister',
                     'exists', 'existed', 'no', 'disabled', 'already', 'invalid', 'unknown', 'enabled', 'success', 'uncaching', "won't", 'insufficient', "can't"]
imperative_keywords = ['please', 'see', 'refer', 'if', 'ensure', 'note:',
                       'press', 'beware', 'consider', 'must', 'want']

so_deps = ['dobj', 'nsubj']
verb_code_mapping = {
    'instantiate': ['new'],
    'set': ['invoke'],
    'supersede': ['set'],
    'create': ['new', 'prepare', 'build'],
    'update': ['set', 'get', 'clear', 'put', 'configure'],
    'configure': ['set', 'put'],
    'install': ['new'],
    'initialize': ['init'],
    'find': ['exist'],
    'read': ['parse', 'get', 'load'],
    'add': ['put', 'define', 'set', 'create', 'contain'],
    'allocate': ['assign'],
    'provision': ['publish'],
    'look': ['get'],
    'report': ['get'],
    'compare': ['equals'],
    'select': ['get'],
    'request': ['get', 'list'],
    'ramp': ['finish'],
    'load': ['forName', 'get', 'parse', 'read', 'open'],
    'terminate': ['shutdown'],
    'reduce': ['remove'],
    'send': ['response', 'return'],
    'identify': ['add'],
    'shut': ['terminate'],
    'kill': ['exit'],
    'disable': ['stop'],
    'overwrite': ['output', 'set'],
    'copy': ['send'],
    'transmit': ['send'],
    'recover': ['move'],
    'unfinalize': ['remove'],
    'move': ['rename'],
    'guess': ['return'],
    'delete': ['trash', 'mark'],
    'bind': ['server'],
    'invoke': ['get'],
    'register': ['add', 'insert'],
    'deliver':['send'],
    'reset':['set'],
    'stop': ['close', 'invoke'],
    'block': ['wait'],
    'detect': ['is', 'equals'],
    'check': ['is'],
    'fail': ['exception'],
    'access': ['get'],
    'roll': ['rollback'],
    'start': ['main', 'generate'],
    'generate': ['gen'],
    'send': ['pump'],
    'touch': ['install'],
    'change': ['set'],
    'match': ['starts'],
    'return': ['get'],
    'allocate':['get'],
    'connect':['create'],
    'clean': ['cleanup'],
    'sync': ['hsync'],
    'pull': ['get'],
    'limit': ['set'],
    'send':['return']
}

verb_op_mapping = {
    'enter': ['='],
    'configure': ['='],
    'set': ['='],
    'give': ['='],
    'update': ['='],
    'advance': ['='],
    'create': ['new'],
    'load': ['new'],
    'initialize': ['new'],
    'issue': ['new'],
    'switch': ['new'],
    'recover': ['new'],
    'overwrite': ['new', 'set']
}

new_op = ['instantiate', 'create', 'install',
          'generate', 'instal', 'initialize', 'switch', 'bind', 'recover', 'load']

verb_stmt_mapping = {
    'stop': ['break'],
    'find': ['exist'],
    'terminate': ['break', 'return'],
    'check': ['if', 'else'],
    'skip': ['break', 'return'],
    'load': ['forName'],
    'schedule': ['allocate'],
    'clean': ['abort'],
    'fetch': ['get', 'response'],
    'return': ['return', 'throw'],
    'deny': [check_return_false_stmt],
    'reject': [check_return_false_stmt],
    'allow': [check_return_true_stmt],
    'bind': ['new'],
    'recover': ['new'],
    'close': ['clear'],
    'create': ['prepare', 'mkdirs'],
    'allocate': ['get']
}
verb_abbr_mapping = {
    'synchronize': ['sync']
}
verb_any_action = ['reprocess', 'do', 'initiate', 'retry', 'perform']
verb_not_detect = ['use', 'find', 'run', 'follow', 'remain', 'nee', 'make', 'need', 'reuse', 'seem', 'receive', 'pend', 'specify', 'keep','skip',
                   'be', 'become', 'listen', 'have', 'take', 'work', 'contain', 'accept', 'fall', 'ensure', 'exist', 'expect', 'assume', 'list', 'report']

verb_no_action = ['return', 'ignore', 'skip', 'abort', 'discard',  'disregard', 'defer', 'swallow', 'delay', 'quit', 'emit', 'avoid', 'monitor', 'continue',
                  'wait', 'exit', 'run', 'get', 'continue', 'leave', 'go', 'pend', 'drop', 'default', 'fail', 'require', 'omit', 'belong']
verb_start = ['got', 'received', 'called', 'call', 'attempted', 'recovered', 'invoked',
              'start', 'started', 'begin', 'requested', 'read']
code_exec = ['execute', 'exec', 'process', 'handle', 'executor', 'do']
log_guard_stmts = ['isDebugEnabled', 'isWarnEnabled',
                   'isLogAll', 'isLogInternalEvents', 'isInfoEnabled', 'logTraceEnabled']
variable_placeholder = 'VID'

ns = {"src": "http://www.srcML.org/srcML/src"}
start_attrib_str = '{http://www.srcML.org/srcML/position}start'
end_attrib_str = '{http://www.srcML.org/srcML/position}end'

with open('../config.json', 'r') as f:
    config = json.load(f)

conn = psycopg2.connect(database=config['db']['database'], user=config['db']['user'], password=config['db']['password'], host=config['db']['host'],
                        port=config['db']['port'])


def fetch_log_context_by_log_id(log_id):
    cur = conn.cursor()
    sql = "SELECT * FROM log_statements_for_log_code_inconsistency_detection WHERE id=%s;"
    cur.execute(sql, (log_id,))
    rows = cur.fetchall()
    cur.close()
    return rows


def fetch_method_by_filename_and_pos(start_line, end_line, file_name):
    cur = conn.cursor()
    sql = "SELECT * FROM log_methods_for_log_code_inconsistency_detection WHERE file_name=%s and begin_line<=%s and end_line>= %s order by id desc limit 1;"
    cur.execute(sql, (file_name, start_line, end_line,))
    rows = cur.fetchall()
    cur.close()
    return rows


def fetch_method_by_filename_and_pos_commit(start_line, end_line, file_name):
    cur = conn.cursor()
    sql = "SELECT * FROM log_methods_for_log_code_inconsistency_detection WHERE file_name=%s and begin_line<=%s and end_line>= %s and source_data IS NOT NULL order by id desc limit 1;"
    cur.execute(sql, (file_name, start_line, end_line,))
    rows = cur.fetchall()
    cur.close()
    return rows


def get_target_method(log_record, commit_flag=False):
    file_name, log_stat, start_line, end_line = log_record[:4]
    if commit_flag:
        target_method_record = fetch_method_by_filename_and_pos_commit(
            start_line, end_line, file_name)
    else:
        target_method_record = fetch_method_by_filename_and_pos(
            start_line, end_line, file_name)
    return target_method_record


def get_method_elements(method_xml):
    func_attribs = method_xml.attrib
    begin_line, begin_column = [
        int(x) for x in func_attribs.get(start_attrib_str).split(':')]
    end_line, end_column = [
        int(x) for x in func_attribs.get(end_attrib_str).split(':')]
    method_body = method_xml.xpath('./src:name//text()', namespaces=ns)
    return [begin_line, end_line, begin_column, end_column, method_body]


def get_calls_within_scope(surrounding_methods, tgt_log_record, scope):
    related_methods = []
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    for surrounding_method in surrounding_methods:
        begin_line, end_line, begin_column, end_column, method_body = surrounding_method

        if tgt_start_line - (scope + 1) <= begin_line and end_line <= tgt_end_line + (scope + 1):
            related_methods.append(
                [begin_line, end_line, begin_column, end_column, method_body])
    return related_methods


# TODO: remove log statements
def get_surrounding_methods_from_method(tgt_log_record, target_method_record):
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    tgt_log_stmt = tgt_log_record[1]
    surrounding_methods = []
    if target_method_record:
        target_method_record_id = target_method_record[0]
        target_method_xml_str = target_method_record[6]
        xml_object = etree.fromstring(target_method_xml_str)

        methods_call = xml_object.xpath('.//src:call', namespaces=ns)
        for method_call in methods_call:
            begin_line, end_line, begin_column, end_column, method_body = get_method_elements(
                method_call)
            #refine the catch of called methods
            # if tgt_start_line <= begin_line <= tgt_end_line or tgt_start_line <= end_line <= tgt_end_line:
            if tgt_log_record[1].startswith(''.join(method_body)):
                continue
            surrounding_methods.append(
                [begin_line, end_line, begin_column, end_column, method_body])
    return surrounding_methods


def get_attr_lines(method_xml):

    func_attribs = method_xml.attrib
    begin_line, begin_column = [
        int(x) for x in func_attribs.get(start_attrib_str).split(':')]
    end_line, end_column = [
        int(x) for x in func_attribs.get(end_attrib_str).split(':')]
    return begin_line, end_line


def check_if_log_guard(node):
    if node.name == 'if_stmt':

        if '.isDebugEnabled()' in node.find_next('condition').get_text():
            return True
        if '.isWarnEnabled()' in node.find_next('condition').get_text():
            return True
        if '.isTraceEnabled()' in node.find_next('condition').get_text():
            return True
        if 'isLogAll()' in node.find_next('condition').get_text():
            return True
        if 'isLogInternalEvents()' in node.find_next('condition').get_text():
            return True
        if '.isInfoEnabled()' in node.find_next('condition').get_text():
            return True
        if 'logTraceEnabled' in node.find_next('condition').get_text():
            return True
        if 'debug' in node.find_next('condition').get_text():
            return True
    else:
        return False


def remove_log_guard_elements(method_xml_str):
    soup = BeautifulSoup(method_xml_str, "xml")
    for if_stmt in soup.find_all(check_if_log_guard):
        parent = if_stmt.parent
        children = if_stmt.find_all('expr_stmt')
        if_stmt_index = parent.index(if_stmt)
        if_stmt.decompose()
        for node_index, node in enumerate(children):
            parent.insert(if_stmt_index + node_index, node)
    return str(soup.decode_contents())


def flatten(t):
    return [item for sublist in t for item in sublist if item.isidentifier()]


def camel_case_split(identifier):
    matches = re.finditer(
        '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


def detect_target_method_call_rule_0(surrounding_methods, log_text):
    # If the log have an exact match with the called methods
    log_text_tokens = [x for x in log_text.split() if
                       x != variable_placeholder and x not in stopwords.words('english') and x.isidentifier() and len(
                           camel_case_split(x)) > 1 and not x[0].isupper()]
    result = []
    for surrounding_method in surrounding_methods:

        if '.' in surrounding_method[-1]:
            called_methods = surrounding_method[-1][surrounding_method[-1].index(
                '.')+1:]
        else:
            called_methods = surrounding_method[-1]

        if log_text_tokens and set(called_methods) == set(log_text_tokens):
            result.append(surrounding_method)
    return result


def detect_target_method_call_rule_1(surrounding_methods, log_text):
    # If the log have an exact match with the called methods
    log_text_tokens = [x.lower() for x in re.split(
        r'\W+', log_text) if x != variable_placeholder and x.isidentifier()]
    result = []

    for surrounding_method in surrounding_methods:

        if '.' in surrounding_method[-1]:
            called_methods = surrounding_method[-1][surrounding_method[-1].index(
                '.')+1:][-1]
            called_methods = camel_case_split(called_methods)
        else:
            called_methods = surrounding_method[-1][-1]
            called_methods = camel_case_split(called_methods)

        if log_text_tokens and set([x.lower() for x in called_methods]) == set(log_text_tokens):
            result.append(surrounding_method)
    return result


def detect_target_method_call_rule_2(surrounding_methods, log_text):
    # If all the log tokens are contained by the called method's tokens
    log_text_tokens = [x.lower() for x in re.split(
        r'\W+', log_text) if x != variable_placeholder and x.isidentifier()]
    result = []
    for surrounding_method in surrounding_methods:
        surrounding_method_tokens = flatten(
            [camel_case_split(x) for x in surrounding_method[-1]])
        surrounding_method_tokens = [x.lower()
                                     for x in surrounding_method_tokens]
        if set(log_text_tokens).issubset(set(surrounding_method_tokens)):
            result.append(surrounding_method)
    return result


def detect_target_method_call_rule_3_0(surrounding_methods, main_verb):
    # If the main verb matches some token of the called method
    result = []
    for surrounding_method in surrounding_methods:
        # surrounding_method_tokens = flatten([camel_case_split(x) for x in surrounding_method[-1]])
        surrounding_method_token = surrounding_method[-1][-1]
        # for surrounding_method_token in surrounding_method_tokens:
        if main_verb.lower() in lexeme(surrounding_method_token):
            result.append(surrounding_method)
            break
    return result


def detect_target_method_call_rule_3(surrounding_methods, main_verb, break_flag=True):
    # If the main verb matches some token of the called method
    result = []
    if type(main_verb) is not str:
        if main_verb.lemma_ in state_keywords:
            return result
        main_verb = main_verb.text
    for surrounding_method in surrounding_methods:

        surrounding_method_tokens = flatten(
            [camel_case_split(x) for x in surrounding_method[-1]])
        for surrounding_method_token in surrounding_method_tokens:
            if main_verb.lower() in lexeme(surrounding_method_token):
                result.append(surrounding_method)
                break
        if break_flag and main_verb == surrounding_method[-1][-1]:
            result.append(surrounding_method)
            break
    return result


def get_synonyms(tgt_word):
    synonyms_set = []
    _tgt_word_base = wn.synsets(tgt_word, pos=wn.VERB)
    if _tgt_word_base:
        tgt_word_base = _tgt_word_base[0].lemma_names()[0]
        for synset in wn.synsets(tgt_word, pos=wn.VERB):
            # we only care its most common sense
            if '01' in synset.name() or tgt_word_base.lower() in synset.name():
                synonyms_set += synset.lemma_names()
                for hyper in synset.hypernyms():
                    if '01' in hyper.name():
                        synonyms_set += hyper.lemma_names()[:1]
                for hypo in synset.hyponyms():
                    if '01' in hypo.name():
                        synonyms_set += hypo.lemma_names()[:1]
        return set([x for x in synonyms_set if '_' not in x])
    return set(synonyms_set)


def detect_target_method_call_rule_4(surrounding_methods, main_verb):
    # If one of the synsets of main verb matches some token of the called method
    result = []
    if main_verb.lemma_ in state_keywords:
        return result
    main_verb = main_verb.text
    synonyms = get_synonyms(main_verb)
    for surrounding_method in surrounding_methods:
        surrounding_method_tokens = flatten(
            [camel_case_split(x) for x in surrounding_method[-1]])
        #         print(surrounding_method_tokens)
        for surrounding_method_token in surrounding_method_tokens:
            if synonyms & set(lexeme(surrounding_method_token)):
                result.append(surrounding_method)
                break
    return result


def detect_target_method_call_rule_5(surrounding_methods, main_verb):
    # the open clausal complement of the main verb match the code
    result = []
    for child in main_verb.children:
        if child.dep_ in comp_deps:
            result += detect_target_method_call_rule_3(
                surrounding_methods, child)
            if child.lemma_ in verb_stmt_mapping:
                for mapped_verb in verb_stmt_mapping[child.lemma_]:
                    if type(mapped_verb) is str:
                        result += detect_target_method_call_rule_3(
                            surrounding_methods, mapped_verb)
    return result


def detect_target_method_call_rule_6(surrounding_methods, main_verb):
    # the subject or object of a state verb: start, stop, fail, connect, disconnect, call
    result = []
    if main_verb.lemma_ in state_keywords:
        for child in main_verb.children:
            if child.dep_ in so_deps:
                result += detect_target_method_call_rule_3(
                    surrounding_methods, child)

    return result


def detect_target_method_call_rule_6_0(surrounding_methods, main_verb):
    # the adverbial clause modifier of the main verb
    result = []
    # if main_verb.lemma_ in state_keywords:
    for child in main_verb.children:
        if child.dep_ in ['advcl']:
            result += detect_target_method_call_rule_3(
                surrounding_methods, child)
    return result


def detect_target_method_call_rule_7(surrounding_methods, main_verb):
    # Creating a mapping from the verb to the code
    result = []
    if main_verb.lemma_.lower() in verb_code_mapping:
        for mapped_verb in verb_code_mapping[main_verb.lemma_.lower()]:
            result += detect_target_method_call_rule_3(
                surrounding_methods, mapped_verb, break_flag=False)
    # if main_verb.lemma_ in state_keywords:
    #     for child in main_verb.children:
    #         if child.dep_ in so_deps:
    #             result += detecting_target_method_call_rule_3(surrounding_methods, child.text)
    return result


def detect_target_method_call_rule_8(surrounding_methods, main_verb):
    # for the case: action has a code of execute
    # https://github.com/apache/hadoop/blob/dbd255f4a96474b31af2bd45c952ac7151a265b9/hadoop-yarn-project/hadoop-yarn/hadoop-yarn-server/hadoop-yarn-server-nodemanager/src/main/java/org/apache/hadoop/yarn/server/nodemanager/containermanager/linux/runtime/DockerLinuxContainerRuntime.java/#L1191
    result = []
    for mapped_verb in code_exec:
        result_ = detect_target_method_call_rule_3(
            surrounding_methods, mapped_verb, break_flag=False)
        if mapped_verb == 'process':
            for detected_method in result_:
                if 'processid' not in ''.join(detected_method[-1]).lower():
                    result.append(detected_method)
        else:
            result += result_
    # if main_verb.lemma_ in state_keywords:
    #     for child in main_verb.children:
    #         if child.dep_ in so_deps:
    #             result += detecting_target_method_call_rule_3(surrounding_methods, child.text)
    return result


def get_target_methods(tgt_log_record, target_method_record, log_text):
    result = []
    log_sents = lcr.nlp(log_text)
    main_verb, tense, main_sent, res_all, res_sents = lcr.detecting_main_verb_and_tense_all(
        log_sents.sents)

    surrounding_methods = get_surrounding_methods_from_method(
        tgt_log_record, target_method_record)

    res_rule_0 = detect_target_method_call_rule_0(
        surrounding_methods, log_text)
    result.append(res_rule_0)
    if res_rule_0:
        return result
    res_rule_1 = detect_target_method_call_rule_1(
        surrounding_methods, log_text)
    result.append(res_rule_1)
    if res_rule_1:
        return result
    res_rule_2 = detect_target_method_call_rule_2(
        surrounding_methods, log_text)
    result.append(res_rule_2)
    if res_rule_2:
        return result
    if main_verb:
        res_rule_3_0 = detect_target_method_call_rule_3_0(
            surrounding_methods, main_verb.text)
        result.append(res_rule_3_0)
        result.append(detect_target_method_call_rule_3(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_4(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_5(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_6(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_6_0(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_7(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_8(
            surrounding_methods, main_verb))

    return result


def get_target_block(tgt_log_record, target_method_record, log_text):
    result = []
    log_sents = lcr.nlp(log_text)
    main_verb, tense, main_sent, res_all, res_sents = lcr.detecting_main_verb_and_tense_all(
        log_sents.sents)
    if main_verb:
        target_method_xml_str = target_method_record[6]
        soup = BeautifulSoup(target_method_xml_str, "xml")
        if main_verb.lemma_ in verb_stmt_mapping:
            if main_verb.lemma_ == 'stop':
                for child in main_verb.children:
                    if child.dep_ == 'auxpass':
                        return result
                # for child in main_verb.children:
            for stmt in verb_stmt_mapping[main_verb.lemma_]:
                for matched_code in soup.find_all(stmt):
                    begin_line, begin_column = matched_code.get(
                        'pos:start').split(':')
                    end_line, end_column = matched_code.get(
                        'pos:end').split(':')
                    result.append([int(begin_line), int(end_line), int(
                        begin_column), int(end_column), str(matched_code)])
    return result


def rule_1_0(tgt_log_record, target_method_str, log_text):
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    log_tokens = [x.text.lower() for x in nlp(log_text)]
    # remove log guard statement
    target_method_xml_str = remove_log_guard_elements(target_method_str)
    xml_object = etree.fromstring(target_method_xml_str)
    name_elems = xml_object.xpath('//src:block//src:name', namespaces=ns)
    if name_elems:
        begin_line, end_line = get_attr_lines(name_elems[0])
        if begin_line >= tgt_start_line-1:
            if any([x in verb_start for x in log_tokens]):
                return True
    return False


# rules for detecting anti-patterns
def rule_1(tgt_log_record, target_method_str, target_method_record, log_text, main_verb):
    # after but at the start of a method, and not the method name
    # case id: 18247
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=10)
    # tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    log_tokens = [x.text.lower() for x in nlp(log_text)]
    # print(log_tokens)
    if 'call' in log_tokens or 'got' in log_tokens:
        return False
    # verb operator mapping
    verb_op_flag = False
    xml_object = etree.fromstring(target_method_str)
    if main_verb.lemma_ in verb_no_action:
        return False
    if main_verb.lemma_ in verb_op_mapping:
        for stmt in verb_op_mapping[main_verb.lemma_]:
            name_elems = xml_object.xpath(
                '//src:operator[text()="{}"]'.format(stmt), namespaces=ns)
            if stmt == '=':
                name_elems += xml_object.xpath(
                    '//src:init[text()="{}"]'.format(stmt), namespaces=ns)
            if name_elems and not verb_op_flag:
                for name_elem in name_elems:
                    begin_line, end_line = get_attr_lines(name_elem)
                    if begin_line >= tgt_start_line:
                        verb_op_flag = True
    # remove log guard statement
    target_method_xml_str = remove_log_guard_elements(target_method_str)
    xml_object = etree.fromstring(target_method_xml_str)
    name_elems = xml_object.xpath('//src:block//src:name', namespaces=ns)
    if name_elems:
        begin_line, end_line = get_attr_lines(name_elems[0])
        if begin_line == tgt_start_line:
            if verb_op_flag or any(matched_methods_group):
                return True
    return False


def rule_2(tgt_log_record, target_method_str, target_method_record, log_text, main_verb):
    # After: log appear before calling the corresponding method, but before the log, no corresponding method match
    if main_verb and main_verb.lemma_.lower() in verb_no_action:
        return False
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # verb operator mapping
    verb_op_flag = False
    xml_object = etree.fromstring(target_method_str)
    if main_verb.lemma_ in verb_op_mapping:
        for stmt in verb_op_mapping[main_verb.lemma_]:
            name_elems = xml_object.xpath(
                '//src:operator[text()="{}"]'.format(stmt), namespaces=ns)
            if stmt == '=':
                name_elems += xml_object.xpath(
                    '//src:init[text()="{} "]'.format(stmt), namespaces=ns)
            if name_elems and not verb_op_flag:
                for name_elem in name_elems:
                    begin_line, end_line = get_attr_lines(name_elem)
                    if end_line < tgt_start_line:
                        return False
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=30)
    if any(matched_methods_group):
        for matched_methods in matched_methods_group:
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if end_line < tgt_start_line:
                    return False
    else:
        return False
    return True


def rule_3(tgt_log_record, target_method_record, log_text):
    # After: log appear before calling the corresponding method, but before the log, no corresponding code block match
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=3)
    if any(matched_methods_group):
        for matched_methods in matched_methods_group:
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if end_line <= tgt_start_line:
                    return False

    matched_stmts = get_target_block(
        tgt_log_record, target_method_record, log_text)
    if matched_stmts:
        dis_list = []
        for matched_stmt in matched_stmts:
            begin_line, end_line = matched_stmt[:2]
            if end_line < tgt_start_line:
                dis_list.append(tgt_start_line - end_line)
            else:
                dis_list.append(begin_line - tgt_end_line)
        dis_list_sorted_idx = sorted(
            range(len(dis_list)), key=lambda k: dis_list[k])
        if len(matched_stmts) >= 2 and dis_list[dis_list_sorted_idx[1]] - dis_list[dis_list_sorted_idx[0]] >= 5:
            matched_stmt = matched_stmts[dis_list_sorted_idx[0]]
            begin_line, end_line = matched_stmt[:2]
            if end_line <= tgt_start_line:
                return False
            return True
        else:
            for matched_stmt in matched_stmts:
                begin_line, end_line = matched_stmt[:2]
                if end_line < tgt_start_line:
                    return False
            return True
    return False


def rule_4(tgt_log_record, target_method_record, target_method_str, log_text):
    # log_sents = nlp(log_text)
    log_text = re.sub(' {2,}', ' ', log_text)
    log_sents = lcr.nlp(log_text)
    main_verb, tense, main_sent, res_all, res_sents = lcr.detecting_main_verb_and_tense_all(
        log_sents.sents)
    # meet, but at the end of a method
    # check whether there are methods in log statement
    main_verb_text = main_verb.lemma_
    if main_verb_text.lower() == 'try':
        for child in main_verb.children:
            if child.dep_ in comp_deps:
                if child.lemma_.lower() in verb_no_action:
                    return False
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    # target_method_xml_str = remove_log_guard_elements(target_method_str)
    matched_stmts = get_target_block(
        tgt_log_record, target_method_record, log_text)
    if matched_stmts:
        for matched_stmt in matched_stmts:
            begin_line, end_line = matched_stmt[:2]
            if end_line >= tgt_start_line:
                return False
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=0)
    if any(matched_methods_group) and len(matched_methods_group) > 3:
        return False
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath('//src:block//src:name', namespaces=ns)
    begin_line, end_line = get_attr_lines(name_elems[-1])
    if main_verb and main_verb.lemma_.lower() in verb_no_action and len(matched_methods_group) > 3:
        return False
    if end_line <= tgt_end_line and main_verb.lemma_ not in ['stop']:
        return True
    return False


def check_call_within_return(xml_object, return_begin_line):
    methods_call = xml_object.xpath('.//src:call', namespaces=ns)
    for method_call in methods_call:
        begin_line, end_line, begin_column, end_column, method_body = get_method_elements(
            method_call)
        if begin_line >= return_begin_line:
            return True
    return False


def rule_5(tgt_log_record, target_method_str, log_text):
    log_sents = lcr.nlp(log_text)
    main_verb, tense, main_sent, res_all, res_sents = lcr.detecting_main_verb_and_tense_all(
        log_sents.sents)
    # example: 19020
    # meet, but just before the return statement
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath('//src:block//src:name', namespaces=ns)
    return_elems = xml_object.xpath('//src:return', namespaces=ns)
    if return_elems:
        return_begin_line, return_end_line = get_attr_lines(return_elems[-1])
        if check_call_within_return(xml_object, return_begin_line):
            return False
        if return_begin_line < tgt_start_line:
            return False
        elif main_verb and main_verb.lemma_.lower() in verb_no_action:
            return False
        for name_elem in name_elems:
            begin_line, end_line = get_attr_lines(name_elem)
            if return_begin_line > begin_line > tgt_start_line:
                return False
        return True
    return False


def rule_6(tgt_log_record, target_method_record, target_method_str, main_verb, log_text, tense):
    """
    example: 14034; meet, but at the end of block, need to remove the log guard
    TODO: need to tune the scope of block

    :param tgt_log_record:
    :param target_method_str:
    :return:
    """
    main_verb_text = main_verb.lemma_
    if main_verb_text.lower() == 'try':
        for child in main_verb.children:
            if child.dep_ in comp_deps:
                if child.lemma_.lower() in verb_no_action:
                    return False
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement: done in get_upper_block
    # target_method_str = remove_log_guard_elements(target_method_str)
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=6)
    # if any(matched_methods_group) and len(matched_methods_group) > 3:
    #     return False
    if any(matched_methods_group) and len(matched_methods_group) > 3:
        for matched_methods in matched_methods_group:
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if tense in ['after', 'met-by/finishes']:
                    # if end_line <= tgt_start_line:
                    return False
                if tense == 'meets/starts':
                    if end_line >= tgt_start_line and matched_method[4][0]!='HashSet':
                        return False

    xml_object = etree.fromstring(target_method_str)
    if main_verb.lemma_ in verb_op_mapping:
        for stmt in verb_op_mapping[main_verb.lemma_]:
            name_elems = xml_object.xpath(
                '//src:operator[text()="{}"]'.format(stmt), namespaces=ns)
            if stmt == '=':
                name_elems += xml_object.xpath(
                    '//src:init[text()="{} "]'.format(stmt), namespaces=ns)
            if name_elems:
                for name_elem in name_elems:
                    begin_line, end_line = get_attr_lines(name_elem)
                    if end_line > tgt_start_line:
                        return False
    target_blocks = get_upper_blocks(tgt_log_record, target_method_str)
    # first focusing on the parent block
    target_block = target_blocks[-1]
    soup = BeautifulSoup(etree.tostring(target_block, with_tail=False), 'xml')
    if main_verb and main_verb.lemma_.lower() in verb_no_action:
        return False
    if soup.find('block_content'):
        all_block_elements = soup.find(
            'block_content').findChildren(recursive=False)
        if all_block_elements:
            start_pos = all_block_elements[-1].get('pos:start')
            if start_pos:
                last_element_line = int(start_pos.split(':')[0])
                if last_element_line == tgt_start_line and main_verb.lemma_ not in ['stop', 'give']:
                    return True
    return False


def get_upper_blocks(tgt_log_record, target_method_str):
    # the log guard should be removed
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    target_method_str = remove_log_guard_elements(target_method_str)
    xml_object = etree.fromstring(target_method_str)
    name_lines = xml_object.xpath('//src:block', namespaces=ns)
    target_blocks = []
    for name_line in name_lines:
        begin_line, end_line = get_attr_lines(name_line)
        if begin_line <= tgt_start_line <= end_line:
            target_blocks.append(name_line)
    # first focusing on the parent block
    return target_blocks


def rule_7(tgt_log_record, target_method_str, target_method_record, log_text, tense, main_verb):
    # example: 18889 top priority
    # not met-by/finishes, but appear in the start of catch block, need to remove the log guard
    main_verb_text = main_verb.lemma_
    if main_verb_text.lower() == 'try':
        for child in main_verb.children:
            if child.dep_ in comp_deps:
                if child.lemma_.lower() in verb_no_action:
                    return False
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    target_method_str = remove_log_guard_elements(target_method_str)
    dis = 10
    matched_blocks_group = get_target_block(
        tgt_log_record, target_method_record, log_text)
    if any(matched_blocks_group):
        for matched_method in matched_blocks_group:
            begin_line, end_line = matched_method[:2]
            if min(abs(end_line - tgt_start_line), abs(begin_line - tgt_start_line)) <= dis:
                if end_line >= tgt_start_line:
                    return False
    surrounding_methods = get_surrounding_methods_from_method(
        tgt_log_record, target_method_record)

    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=30)
    if any(matched_methods_group):
        for matched_methods in matched_methods_group:
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if tense in ['after', 'met-by/finishes']:
                    if end_line <= tgt_start_line:
                        return False
                if tense == 'meets/starts':
                    if end_line >= tgt_start_line:
                        return False
        # return True
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath(
        '//src:catch/src:block//src:name', namespaces=ns)
    if name_elems:
        begin_line, end_line = get_attr_lines(name_elems[0])
        if begin_line == tgt_start_line:
            return True
    return False


def filter_matched_methods(log_line_num, log_line_num_end, matched_methods_group, dis=5):
    if len(matched_methods_group) > 3:
        matched_methods_group_new = [[], [], []]
        for matched_methods in matched_methods_group:
            matched_methods_new = []
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if matched_method[-1][-1] in log_guard_stmts:
                    continue
                # if dis!=0:
                if min(abs(end_line - log_line_num), abs(begin_line - log_line_num)) <= dis:
                    matched_methods_new.append(matched_method)
                # else:
                # method in log
                if log_line_num <= begin_line <= end_line <= log_line_num_end:
                    matched_methods_new.append(matched_method)
            matched_methods_group_new.append(matched_methods_new)
        return matched_methods_group_new
    return matched_methods_group


def rule_8(tgt_log_record, target_method_record, log_text, main_verb, scope=5):
    # meet, at almost end of the block but no corresponding method match
    # TODO
    target_method_str = target_method_record[6]
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=28)
    # target_blocks = get_upper_blocks(tgt_log_record, target_method_str)
    # first focusing on the parent block
    # target_block = target_blocks[-1]
    # begin_line, end_line = get_attr_lines(target_block)
    if main_verb and main_verb.lemma_.lower() in verb_no_action and len(matched_methods_group) > 3:
        return False
    # if end_line >= tgt_end_line + scope:
    #     return False
    # else:
    dis = 10
    matched_blocks_group = get_target_block(
        tgt_log_record, target_method_record, log_text)
    if any(matched_blocks_group):
        for matched_method in matched_blocks_group:
            begin_line, end_line = matched_method[:2]
            if min(abs(end_line - tgt_start_line), abs(begin_line - tgt_start_line)) <= dis:
                if end_line >= tgt_start_line:
                    return False

    if any(matched_methods_group):
        for matched_methods in matched_methods_group:
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if end_line >= tgt_start_line:
                    return False
            # set the value to default
        if 'giving up' in log_text.lower():
            return False
        return True
    return False

    # if main_verb_text in lcr.state_keywords:
    #     return False


def rule_9_0(tgt_log_record, target_method_record, main_verb):
    # meet, at the start of a catch block, and no corresponding verb found in later
    # TODO
    if main_verb.text.lower().startswith('re'):
        target_method_str = target_method_record[6]
        tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
        surrounding_methods = get_surrounding_methods_from_method(
            tgt_log_record, target_method_record)
        xml_object = etree.fromstring(target_method_str)
        name_elems = xml_object.xpath(
            '//src:catch/src:block', namespaces=ns)
        if name_elems:
            for name_elem in name_elems:
                begin_line, end_line = get_attr_lines(name_elem)
                if begin_line <= tgt_start_line <= tgt_end_line <= end_line:
                    for surrounding_method in surrounding_methods:
                        # [begin_line, end_line, begin_column, end_column, method_body]
                        if begin_line <= surrounding_method[0] <= surrounding_method[1] <= end_line:
                            if '.' in surrounding_method[-1]:
                                called_methods = surrounding_method[-1][surrounding_method[-1].index(
                                    '.')+1:][-1]
                            else:
                                called_methods = surrounding_method[-1][-1]
                            if called_methods.lower().startswith('re'):
                                return True
    return False


def rule_9(tgt_log_record, target_method_str, target_method_record, log_text, tense, main_verb):
    # example: top priority
    # not after, appear in the catch block, and there are NO actions between the log and the catch
    main_verb_text = main_verb.lemma_.lower()
    if main_verb_text.lower() in verb_no_action:
        return False
    if main_verb_text.lower() == 'try':
        for child in main_verb.children:
            if child.dep_ in comp_deps:
                if child.lemma_.lower() in verb_no_action:
                    return False
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    target_method_str = remove_log_guard_elements(target_method_str)
    dis = 10
    matched_blocks_group = get_target_block(
        tgt_log_record, target_method_record, log_text)
    if any(matched_blocks_group):
        for matched_method in matched_blocks_group:
            begin_line, end_line = matched_method[:2]
            if min(abs(end_line - tgt_start_line), abs(begin_line - tgt_start_line)) <= dis:
                if end_line >= tgt_start_line:
                    return False
    surrounding_methods = get_surrounding_methods_from_method(
        tgt_log_record, target_method_record)
    if any(surrounding_methods):
        for matched_methods in surrounding_methods:
            # [begin_line, end_line, begin_column, end_column, method_body]
            if main_verb_text == 'retry':
                if matched_methods[0] > tgt_start_line:
                    return False
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=28)
    if any(matched_methods_group):
        for matched_methods in matched_methods_group:
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if tense in ['after', 'met-by/finishes']:
                    if end_line <= tgt_start_line:
                        return False
                if tense == 'meets/starts':
                    if end_line >= tgt_start_line:
                        return False
        # return True
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath(
        '//src:catch/src:block//src:name', namespaces=ns)
    if name_elems:
        begin_line, end_line = get_attr_lines(name_elems[0])
        if begin_line == tgt_start_line:
            return True
    return False


def is_match_with_method(target_method_str, log_text):
    result = []
    log_sents = nlp(log_text)
    main_verb, tense, main_sent, res_all, res_sents = lcr.detecting_main_verb_and_tense_all(
        log_sents.sents)
    xml_object = etree.fromstring(target_method_str)
    surrounding_methods = [
        ['', [xml_object.xpath('/src:function/src:name', namespaces=ns)[0].text]]]

    res_rule_0 = detect_target_method_call_rule_0(
        surrounding_methods, log_text)
    result.append(res_rule_0)
    if res_rule_0:
        return result
    res_rule_1 = detect_target_method_call_rule_1(
        surrounding_methods, log_text)
    result.append(res_rule_1)
    if res_rule_1:
        return result
    res_rule_2 = detect_target_method_call_rule_2(
        surrounding_methods, log_text)
    result.append(res_rule_2)
    if res_rule_2:
        return result
    if main_verb:
        res_rule_3_0 = detect_target_method_call_rule_3_0(
            surrounding_methods, main_verb.text)
        result.append(res_rule_3_0)
        if res_rule_3_0:
            return result

        result.append(detect_target_method_call_rule_3(
            surrounding_methods, main_verb.text))
        result.append(detect_target_method_call_rule_5(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_6(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_7(
            surrounding_methods, main_verb))
        result.append(detect_target_method_call_rule_8(
            surrounding_methods, main_verb))

    return result


def rule_11(target_method_str, log_text):
    # example:
    # after met-by/finishes, appear in the catch block
    # remove log guard statement
    if any(is_match_with_method(target_method_str, log_text)):
        return True
    return False


def rule_12(target_method_str):
    error_keywords = ['error', 'exception',
                      'print', 'failure', 'warning', 'log']
    # not detect exception or error log methods
    xml_object = etree.fromstring(target_method_str)
    method_name = xml_object.xpath(
        '/src:function/src:name', namespaces=ns)[0].text
    if any([x in method_name.lower() for x in error_keywords]):
        return True
    else:
        return False


def rule_13(target_method_str, main_verb, tgt_log_record, target_method_record, log_text):
    # main_verb in method name
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    xml_object = etree.fromstring(target_method_str)
    method_name = xml_object.xpath(
        '/src:function/src:name', namespaces=ns)[0].text
    if log_text.split('(')[0] == method_name or log_text.split('(')[0].title() == method_name.title():
        return True

    if main_verb and main_verb.text == method_name and ':' in log_text and '=' in log_text:
        return True
    # if main_verb and main_verb.text.lower() in method_name.lower():
    matched_methods_group = get_target_methods(
        tgt_log_record, target_method_record, log_text)
    matched_methods_group = filter_matched_methods(
        tgt_start_line, tgt_end_line, matched_methods_group, dis=10)
    # check_method_name = False
    if any(matched_methods_group):
        for matched_methods in matched_methods_group:
            for matched_method in matched_methods:
                begin_line, end_line = matched_method[:2]
                if end_line < tgt_start_line:
                    return False
    if main_verb:
        if main_verb and main_verb.text.lower() in method_name.lower():
            return True
        # if main_verb and main_verb.lemma_ in verb_abbr_mapping:
        #     for verb_abbr in verb_abbr_mapping[main_verb.lemma_]:
        #         if verb_abbr in method_name.lower():
        #             return True
        if main_verb.text in ['Relaunching']:
            main_verb_lemma = 'relaunch'
        else:
            main_verb_lemma = main_verb.lemma_
        if main_verb_lemma.lower() in method_name.lower() and main_verb.morph.get('Aspect') == ['Prog'] and main_verb_lemma not in new_op:
            return True
    else:
        return False


def rule_13_0(target_method_str, tgt_log_record, target_method_record, log_text, main_verb):
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    log_tokens = [x.text.lower() for x in nlp(log_text)]
    # remove log guard statement
    target_method_xml_str = remove_log_guard_elements(target_method_str)
    xml_object = etree.fromstring(target_method_xml_str)
    name_elems = xml_object.xpath('//src:block//src:name', namespaces=ns)
    if name_elems:
        begin_line, end_line = get_attr_lines(name_elems[0])
        if begin_line >= tgt_start_line-1:
            if any([x in verb_start for x in log_tokens]):
                return False
    
    log_text_tokens = [x.lower() for x in re.split(
        r'\W+', log_text) if x != variable_placeholder and x.isidentifier()]
    # main_verb in method name
    xml_object = etree.fromstring(target_method_str)
    method_name = xml_object.xpath(
        '/src:function/src:name', namespaces=ns)[0].text
    if main_verb and len(log_text_tokens) == 1:
        if main_verb.lemma_.lower() == method_name.lower() and main_verb.morph.get('Aspect') == ['Perf']:
            tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
            matched_methods_group = get_target_methods(
                tgt_log_record, target_method_record, log_text)
            matched_methods_group = filter_matched_methods(
                tgt_start_line, tgt_end_line, matched_methods_group, dis=10)
            if any(matched_methods_group):
                for matched_methods in matched_methods_group:
                    for matched_method in matched_methods:
                        begin_line, end_line = matched_method[:2]
                        if end_line < tgt_start_line:
                            return False
            surrounding_methods = get_surrounding_methods_from_method(
                tgt_log_record, target_method_record)
            if surrounding_methods:
                last_method = surrounding_methods[-1]
                if last_method[0] > tgt_start_line:
                    return True
    return False


def rule_14(target_method_str, main_verb):
    # the subject or object of a state verb: start, stop, fail, connect, disconnect, call
    # main_verb in method name
    xml_object = etree.fromstring(target_method_str)
    method_name = xml_object.xpath(
        '/src:function/src:name', namespaces=ns)[0].text
    if main_verb and main_verb.lemma_ in state_keywords:
        for child in main_verb.children:
            if child.dep_ in so_deps:
                if child.text.lower().split('.')[-1] in method_name.lower():
                    return True

    # if main_verb and main_verb.text in method_name.lower():
        # return True
    # else:
    return False


def rule_15(target_method_str, log_text):
    # the subject or object of a state verb: start, stop, fail, connect, disconnect, call
    # method name are called in the log
    xml_object = etree.fromstring(target_method_str)
    method_name = xml_object.xpath(
        '/src:function/src:name', namespaces=ns)[0].text
    if method_name in log_text:
        if 'call' in log_text.lower() or 'receive' in log_text.lower():
            return True
    return False


def rule_16(log_text):
    log_tokens = log_text.strip('.').lower().split()
    # negation word in the log text for status description, we skip
    # imperative sentence log
    if [x for x in log_tokens if x in negation_keywords + imperative_keywords]:
        return True
    log_tokens = [x.text for x in nlp(log_text)]
    # print(log_tokens)
    if [x for x in log_tokens if x in negation_keywords + imperative_keywords]:
        return True
    return False


def rule_10(tgt_log_record, target_method_str):
    # example:
    # after met-by/finishes, appear in the catch block
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    target_method_str = remove_log_guard_elements(target_method_str)
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath('//src:catch', namespaces=ns)
    for name_elem in name_elems:
        begin_line, end_line = get_attr_lines(name_elem)
        if begin_line <= tgt_start_line <= end_line:
            return True
    # if name_elems:
    #     begin_line, end_line = get_attr_lines(name_elems[0])
    #     # appear in the catch block
    #     if begin_line <= tgt_start_line <=end_line:
    #         return True
    return False


def rule_17(tgt_log_record, target_method_record, target_method_str, main_verb_text, log_sents):
    # verb_no_action in catch
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    target_method_str = remove_log_guard_elements(target_method_str)
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath('//src:catch', namespaces=ns)
    if not name_elems:
        return False
    for name_elem in name_elems:
        begin_line, end_line = get_attr_lines(name_elem)
        if begin_line <= tgt_start_line <= end_line:
            if main_verb_text.lower() in verb_no_action:
                return True
            surrounding_methods = get_surrounding_methods_from_method(
                tgt_log_record, target_method_record)
            if any(surrounding_methods):
                for matched_methods in surrounding_methods:
                    if begin_line <= matched_methods[0] <= matched_methods[1] <= end_line:
                        # [begin_line, end_line, begin_column, end_column, method_body]
                        if main_verb_text == 'retry':
                            if matched_methods[0] > tgt_start_line:
                                return True
            log_text_lemma = ' '.join([x.lemma_ for x in log_sents])
            # set the value to default
            if 'default to' in log_text_lemma:
                return True
            if 'revert to' in log_text_lemma:
                return True
            if 'fall back to' in log_text_lemma:
                return True
            if 'invalid' in log_text_lemma:
                return True
            if 'give up' in log_text_lemma:
                return True
            if 'down' in log_text_lemma:
                return True
            if log_text_lemma.strip().split()[0] == variable_placeholder.lower():
                return True
    return False


def rule_18(main_sent):
    # case: variable[:=]VID
    main_sent_str = main_sent.text.strip()
    if re.search("^[\#\-\w]+ *[=:] *{}".format(variable_placeholder), main_sent_str):
        return True
    if 'number of' in main_sent.text.lower():
        return True
    if 'returned' in main_sent.text.lower():
        return True
    return False


def rule_19(tgt_log_record, target_method_str):
    # verb_no_action in catch
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    target_blocks = get_upper_blocks(tgt_log_record, target_method_str)
    # if len(target_blocks)>1:
    # target_block = target_blocks[-2]
    # else:
    target_block = target_blocks[-1]
    begin_line_block, end_line_block = get_attr_lines(target_block)
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath(
        '//src:operator[text()="new"]', namespaces=ns)
    if name_elems:
        for name_elem in name_elems:
            begin_line, end_line = get_attr_lines(name_elem)
            # new verb and new code must in the same block
            if end_line_block >= begin_line >= tgt_start_line >= begin_line_block:
                return True
    return False


def rule_20(tgt_log_record, target_method_str):
    # verb: check, vs if statement
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    target_blocks = get_upper_blocks(tgt_log_record, target_method_str)
    target_block = target_blocks[-1]
    begin_line_block, end_line_block = get_attr_lines(target_block)
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath(
        '//src:operator[text()="new"]', namespaces=ns)
    if name_elems:
        for name_elem in name_elems:
            begin_line, end_line = get_attr_lines(name_elem)
            # new verb and new code must in the same block
            if end_line_block >= begin_line >= tgt_start_line >= begin_line_block:
                return True
    return False


def rule_21(tgt_log_record, target_method_record, target_method_str, main_verb_text):
    # verb: check, vs if statement
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    # remove log guard statement
    surrounding_methods = get_surrounding_methods_from_method(
        tgt_log_record, target_method_record)
    if any(surrounding_methods):
        for matched_methods in surrounding_methods:
            # [begin_line, end_line, begin_column, end_column, method_body]
            if main_verb_text in verb_any_action:
                if matched_methods[0] > tgt_start_line:
                    return True
    return False


def rule_22(tgt_log_record, target_method_str, main_verb_text):
    tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
    xml_object = etree.fromstring(target_method_str)
    name_elems = xml_object.xpath('//src:while', namespaces=ns)
    if main_verb_text in ['retry', 'try'] and name_elems:
        for name_elem in name_elems:
            begin_line, end_line = get_attr_lines(name_elem)
            if begin_line <= tgt_start_line <= tgt_end_line <= end_line:
                return True
    return False


def rule_0_0(tgt_log_record, target_method_str, log_text):
    log_text = re.sub(' {2,}', ' ', log_text)
    xml_object = etree.fromstring(target_method_str)
    method_name = xml_object.xpath(
        '/src:function/src:name', namespaces=ns)[0].text
    search_resuls = re.search(
        "([Ee]nd)[ ]*:[ ]*{}.+".format(method_name), log_text)
    if search_resuls:
        # meet, but at the end of a method
        # check whether there are methods in log statement
        tgt_start_line, tgt_end_line = tgt_log_record[2], tgt_log_record[3]
        # remove log guard statement
        xml_object = etree.fromstring(target_method_str)
        name_elems = xml_object.xpath('//src:block//src:name', namespaces=ns)
        begin_line, end_line = get_attr_lines(name_elems[-1])
        if end_line > tgt_end_line:
            return True
    return False


def inconsistency_detection(log_content_relation, log_id, log_text, commit_flag=False):
    tgt_log_record = fetch_log_context_by_log_id(log_id)[0]
    target_method_record = get_target_method(
        tgt_log_record, commit_flag)[0]
    target_method_str = target_method_record[6]
    # log_text = get_log_text(log_id)
    # log_sents = nlp(log_text)
    log_text = re.sub(' {2,}', ' ', log_text)
    log_sents = lcr.nlp(log_text)
    main_verb, tense, main_sent, res_all, res_sents = lcr.detecting_main_verb_and_tense_all(
        log_sents.sents)
    print(main_verb)
    print(main_sent)
    if rule_0_0(tgt_log_record, target_method_str, log_text):
        print("Detected by Rule 0-0.")
        return True, 00
    # get_target_block(tgt_log_record, target_method_record, log_text)
    if not main_verb:
        return False
    if rule_18(main_sent):
        return False
    if rule_21(tgt_log_record, target_method_record, target_method_str, main_verb.lemma_):
        return False
    if rule_22(tgt_log_record, target_method_str, main_verb.lemma_):
        return False
    if main_verb and main_verb.lemma_.lower() in verb_not_detect:
        return False
    if rule_12(target_method_str) or rule_13(target_method_str, main_verb, tgt_log_record, target_method_record, log_text) or rule_14(target_method_str, main_verb):
        return False
    # if rule_11(target_method_str, log_text):
        # return False
    if rule_13_0(target_method_str, tgt_log_record, target_method_record, log_text, main_verb):
        print("Detected by Rule 13-0.")
        return True, 130
    if rule_15(target_method_str, log_text):
        return False
    if rule_16(log_text):
        return False
    if rule_1_0(tgt_log_record, target_method_str, log_text):
        return False
    if main_verb and rule_17(tgt_log_record, target_method_record, target_method_str, main_verb.lemma_, log_sents):
        return False
    if main_verb.lemma_ in new_op and rule_19(tgt_log_record, target_method_str):
        return False
    # detect the relation in catch block
    if log_content_relation in ['after', 'met-by/finishes']:
        # it means it is correct
        if rule_10(tgt_log_record, target_method_str):
            return False
    if log_content_relation != 'after':
        if rule_9_0(tgt_log_record, target_method_record, main_verb):
            return False
        if rule_9(tgt_log_record, target_method_str, target_method_record, log_text, log_content_relation, main_verb):
            print("Detected by Rule 9.")
            return True, 9
    if log_content_relation != 'met-by/finishes':
        if rule_7(tgt_log_record, target_method_str, target_method_record, log_text, log_content_relation, main_verb):
            print("Detected by Rule 7.")
            return True, 7
    if log_content_relation in ['after', 'met-by/finishes']:
        if rule_1(tgt_log_record, target_method_str, target_method_record, log_text, main_verb):
            print("Detected by Rule 1.")
            return True, 1
    if log_content_relation == 'meets/starts':
        if rule_4(tgt_log_record, target_method_record, target_method_str, log_text):
            print("Detected by Rule 4.")
            return True, 4
        if rule_5(tgt_log_record, target_method_str, log_text):
            print("Detected by Rule 5.")
            return True, 5
        if rule_6(tgt_log_record, target_method_record, target_method_str, main_verb, log_text, log_content_relation):
            print("Detected by Rule 6.")
            return True, 6
        if rule_8(tgt_log_record, target_method_record, log_text, main_verb):
            print("Detected by Rule 8.")
            return True, 8
    if log_content_relation == 'after':
        if rule_2(tgt_log_record, target_method_str, target_method_record, log_text, main_verb):
            print("Detected by Rule 2.")
            if 'not' in log_text:
                return False
            return True, 2
        if rule_3(tgt_log_record, target_method_record, log_text):
            print("Detected by Rule 3.")
            return True, 3

    return False